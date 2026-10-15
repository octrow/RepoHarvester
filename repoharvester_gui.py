"""customtkinter front-end for repoharvester."""
import json
import logging
import os
import queue
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from tkinter import font as tkfont

import customtkinter as ctk

from repoharvester import (
    ALL_GROUPS,
    DEFAULT_MAX_SIZE_KB,
    DEFAULT_OUTPUT_DIR,
    HarvestCancelled,
    HarvestOptions,
    harvest,
)

POLL_MS = 100
SETTINGS_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "repoharvester" / "gui.json"
GUTTER = 20
GAP = 10
GROUP_COLUMNS = 3
LABEL_WIDTH = 110

# (light, dark) pairs; customtkinter picks one by appearance mode.
FIELD = ("#E8ECE3", "#18201B")
CARD = ("#F6F7F2", "#212B25")
INK = ("#1F2A24", "#E4E8DF")
MUTED = ("#5F6B62", "#9AA59C")
LINE = ("#CDD5C8", "#3A4741")
WHEAT = ("#D9B23A", "#D4AF37")
WHEAT_HOVER = ("#C49E2C", "#BF9C2E")
ON_WHEAT = ("#1F2A24", "#1F2A24")
LOG_BG = ("#22302A", "#141C17")
LOG_INK = ("#E9E4C9", "#D9D4B8")
ERROR = ("#A3402E", "#E58A74")

SANS = ("Ubuntu Sans", "Ubuntu", "Noto Sans", "DejaVu Sans")
MONO = ("Ubuntu Sans Mono", "Ubuntu Mono", "Noto Sans Mono", "DejaVu Sans Mono")


def _first_installed(candidates: tuple[str, ...]) -> str:
    installed = set(tkfont.families())
    return next((f for f in candidates if f in installed), "TkDefaultFont")


def _make_fonts() -> dict[str, ctk.CTkFont]:
    """Type scale: 22 title, 13 body, 11 small; mono only for the log. Needs a Tk root."""
    sans, mono = _first_installed(SANS), _first_installed(MONO)
    return {
        "title": ctk.CTkFont(sans, 22, "bold"),
        "body": ctk.CTkFont(sans, 13),
        "strong": ctk.CTkFont(sans, 13, "bold"),
        "small": ctk.CTkFont(sans, 11),
        "log": ctk.CTkFont(mono, 12),
    }


def _items(entry: ctk.CTkEntry) -> tuple[str, ...]:
    """Comma-separated entry text as a tuple of non-empty items."""
    return tuple(item.strip() for item in entry.get().split(",") if item.strip())


def _load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        logging.getLogger("repoharvester").warning("Ignoring unreadable settings %s: %s", SETTINGS_FILE, e)
        return {}


def _save_settings(settings: dict) -> None:
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError as e:
        logging.getLogger("repoharvester").warning("Could not save settings %s: %s", SETTINGS_FILE, e)


def _open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


class QueueHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self.q = q

    def emit(self, record: logging.LogRecord) -> None:
        self.q.put(self.format(record))


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=FIELD)
        self.title("RepoHarvester")
        self.geometry("720x860")
        self.minsize(600, 700)
        self.fonts = _make_fonts()
        # str = log line; callable = completion step the worker hands to the Tk thread.
        self.messages: queue.Queue[str | Callable[[], None]] = queue.Queue()
        self.result: Path | None = None
        self.cancel: threading.Event | None = None  # set while a harvest is running
        self._capture_log()
        self._build()
        self._apply_settings(_load_settings())
        self.bind("<Return>", lambda _e: self._start())
        self.after(POLL_MS, self._drain)

    def _capture_log(self) -> None:
        handler = QueueHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("repoharvester")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # --- layout ---------------------------------------------------------

    def _build(self) -> None:
        ctk.CTkLabel(self, text="RepoHarvester", font=self.fonts["title"], text_color=INK).pack(
            anchor="w", padx=GUTTER, pady=(GUTTER, 0))
        ctk.CTkLabel(self, text="Turn a repository into one text file you can read, search or paste.",
                     font=self.fonts["body"], text_color=MUTED).pack(anchor="w", padx=GUTTER, pady=(0, GAP))

        self._build_source()
        self._build_filters()
        self._build_groups()
        self._build_actions()
        self.log = ctk.CTkTextbox(self, font=self.fonts["log"], fg_color=LOG_BG, text_color=LOG_INK,
                                  corner_radius=6, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=GUTTER, pady=(0, GUTTER))

    def _build_source(self) -> None:
        card = self._card()
        self.repo = self._folder_field(card, "Repository", "git@github.com:user/repo.git or a local folder")
        self.out_dir = self._folder_field(card, "Save to", "")
        self.out_dir.insert(0, str(DEFAULT_OUTPUT_DIR))
        self._spacer(card)

    def _build_filters(self) -> None:
        card = self._card()
        self.max_size = self._field(card, "Max file size", "KB")
        self.max_size.insert(0, str(DEFAULT_MAX_SIZE_KB))
        self.exclude = self._field(card, "Skip folders", "vendor, docs")
        self.only_globs = self._field(card, "Only files", "*.py, *.md  (empty = all)")
        self.skip_globs = self._field(card, "Skip files", "tests/*, *.min.js")
        self.strip = ctk.BooleanVar(value=False)
        self._checkbox(card, "Strip code comments", self.strip).pack(anchor="w", padx=GAP, pady=GAP)

    def _build_groups(self) -> None:
        card = self._card()
        ctk.CTkLabel(card, text="Also include", font=self.fonts["strong"], text_color=INK).grid(
            row=0, column=0, columnspan=GROUP_COLUMNS, sticky="w", padx=GAP, pady=(GAP, 0))
        ctk.CTkLabel(card, text="These are skipped unless you tick them.", font=self.fonts["small"],
                     text_color=MUTED).grid(row=1, column=0, columnspan=GROUP_COLUMNS, sticky="w", padx=GAP)
        self.include = {g: ctk.BooleanVar(value=False) for g in ALL_GROUPS}
        for i, (group, var) in enumerate(self.include.items()):
            box = self._checkbox(card, group.replace("_", " ").capitalize(), var)
            box.grid(row=2 + i // GROUP_COLUMNS, column=i % GROUP_COLUMNS, sticky="w", padx=GAP, pady=3)
        card.grid_columnconfigure(tuple(range(GROUP_COLUMNS)), weight=1)
        ctk.CTkFrame(card, height=GAP, width=1, fg_color="transparent").grid(row=99, column=0)

    def _build_actions(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=GUTTER, pady=(0, GAP))
        self.start = ctk.CTkButton(row, text="Harvest", command=self._on_harvest_button, height=40, width=150,
                                   font=self.fonts["strong"], fg_color=WHEAT, hover_color=WHEAT_HOVER,
                                   text_color=ON_WHEAT, text_color_disabled=ON_WHEAT, corner_radius=6)
        self.start.pack(side="left")
        self.open_button = self._secondary(row, "Open file", self._open_result)
        self.status = ctk.CTkLabel(row, text="Ready", font=self.fonts["body"], text_color=MUTED, anchor="w")
        self.status.pack(side="left", fill="x", expand=True, padx=GAP)

    def _card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=CARD, border_color=LINE, border_width=1, corner_radius=8)
        card.pack(fill="x", padx=GUTTER, pady=(0, GAP))
        return card

    def _spacer(self, card: ctk.CTkFrame) -> None:
        ctk.CTkFrame(card, height=GAP, width=1, fg_color="transparent").pack()

    def _field(self, card: ctk.CTkFrame, label: str, hint: str) -> ctk.CTkEntry:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=GAP, pady=(GAP, 0))
        ctk.CTkLabel(row, text=label, width=LABEL_WIDTH, anchor="w", font=self.fonts["body"],
                     text_color=INK).pack(side="left")
        entry = ctk.CTkEntry(row, placeholder_text=hint, font=self.fonts["body"], border_color=LINE,
                             border_width=1, fg_color=FIELD, text_color=INK, corner_radius=6)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _folder_field(self, card: ctk.CTkFrame, label: str, hint: str) -> ctk.CTkEntry:
        entry = self._field(card, label, hint)
        button = self._secondary(entry.master, "Choose folder", lambda: self._pick_dir(entry))
        button.pack(side="left", padx=(GAP, 0))
        return entry

    def _checkbox(self, parent, text: str, var: ctk.BooleanVar) -> ctk.CTkCheckBox:
        return ctk.CTkCheckBox(parent, text=text, variable=var, font=self.fonts["body"], text_color=INK,
                               fg_color=WHEAT, hover_color=WHEAT_HOVER, border_color=MUTED, border_width=2,
                               checkmark_color=ON_WHEAT, checkbox_width=18, checkbox_height=18, corner_radius=4)

    def _secondary(self, parent, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(parent, text=text, command=command, width=0, height=30, font=self.fonts["body"],
                             fg_color="transparent", hover_color=LINE, border_color=LINE, border_width=1,
                             text_color=INK, corner_radius=6)

    # --- behaviour ------------------------------------------------------

    def _pick_dir(self, entry: ctk.CTkEntry) -> None:
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _set_status(self, text: str, color=MUTED) -> None:
        self.status.configure(text=text, text_color=color)

    def _on_harvest_button(self) -> None:
        if self.cancel is None:
            self._start()
            return
        self.cancel.set()
        self.start.configure(state="disabled", text="Cancelling…")

    def _start(self) -> None:
        if self.cancel is not None:
            return
        repo = self.repo.get().strip()
        if not repo:
            self._set_status("Enter a git URL or choose a local folder.", ERROR)
            return
        if not self.max_size.get().strip().isdigit():
            self._set_status("Max file size must be a whole number of KB.", ERROR)
            return
        options = self._form_values()
        _save_settings(self._settings())
        self.cancel = threading.Event()
        self.start.configure(text="Cancel")
        self.open_button.pack_forget()
        self._set_status(f"Harvesting {repo}")
        threading.Thread(target=self._run, args=(repo, options, self.cancel), daemon=True).start()

    def _form_values(self) -> HarvestOptions:
        """Read the form into harvest() options."""
        return HarvestOptions(
            output_dir=Path(self.out_dir.get().strip() or DEFAULT_OUTPUT_DIR),
            strip_comments=self.strip.get(),
            skip_groups=frozenset(g for g, var in self.include.items() if not var.get()),
            exclude_folders=_items(self.exclude),
            max_size_kb=int(self.max_size.get()),
            include_globs=_items(self.only_globs),
            exclude_globs=_items(self.skip_globs),
        )

    def _settings(self) -> dict:
        return {
            "repo": self.repo.get().strip(),
            "output_dir": self.out_dir.get().strip(),
            "max_size_kb": self.max_size.get().strip(),
            "exclude": self.exclude.get().strip(),
            "only_globs": self.only_globs.get().strip(),
            "skip_globs": self.skip_globs.get().strip(),
            "strip_comments": self.strip.get(),
            "include": sorted(g for g, var in self.include.items() if var.get()),
        }

    def _apply_settings(self, settings: dict) -> None:
        for entry, key in ((self.repo, "repo"), (self.out_dir, "output_dir"),
                           (self.max_size, "max_size_kb"), (self.exclude, "exclude"),
                           (self.only_globs, "only_globs"), (self.skip_globs, "skip_globs")):
            if settings.get(key):
                entry.delete(0, "end")
                entry.insert(0, str(settings[key]))
        self.strip.set(bool(settings.get("strip_comments")))
        for group in settings.get("include", []):
            if group in self.include:
                self.include[group].set(True)

    def _run(self, repo: str, options: HarvestOptions, cancel: threading.Event) -> None:
        """Worker thread: never touches Tk, only the queue."""
        try:
            result = harvest(repo, options, cancel)
        except HarvestCancelled:
            self.messages.put(self._cancelled)
        except Exception as e:  # CloneError and anything else: shown, not swallowed
            error = str(e) or type(e).__name__
            self.messages.put(lambda: self._failed(error))
        else:
            self.messages.put(lambda: self._succeeded(result))

    def _drain(self) -> None:
        while not self.messages.empty():
            message = self.messages.get()
            if callable(message):
                message()
            else:
                self._append_log(message)
        self.after(POLL_MS, self._drain)

    def _idle(self) -> None:
        self.cancel = None
        self.start.configure(state="normal", text="Harvest")

    def _cancelled(self) -> None:
        self._idle()
        self._set_status("Cancelled. Nothing was saved.")
        self._append_log("Cancelled")

    def _succeeded(self, result: Path) -> None:
        self._idle()
        self.result = result
        self._set_status(f"Saved {result.name}", INK)
        self.open_button.pack(side="right", before=self.status)

    def _failed(self, error: str) -> None:
        self._idle()
        self._set_status(error, ERROR)
        self._append_log(error)

    def _append_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _open_result(self) -> None:
        if self.result:
            _open_file(self.result)


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
