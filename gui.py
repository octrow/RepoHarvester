"""Minimal customtkinter front-end for repoharvester."""
import logging
import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from repoharvester import ALL_GROUPS, DEFAULT_MAX_SIZE_KB, DEFAULT_OUTPUT_DIR, harvest

POLL_MS = 100
PAD = 8
GROUP_COLUMNS = 4


class QueueHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self.q = q

    def emit(self, record: logging.LogRecord) -> None:
        self.q.put(self.format(record))


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RepoHarvester")
        self.geometry("760x620")
        self.messages: queue.Queue[str | None] = queue.Queue()  # None = worker finished
        handler = QueueHandler(self.messages)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger("repoharvester").addHandler(handler)
        logging.getLogger("repoharvester").setLevel(logging.INFO)
        self._build()
        self.after(POLL_MS, self._drain_log)

    def _row(self, label: str, default: str = "", browse=None) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=PAD, pady=(PAD, 0))
        ctk.CTkLabel(frame, text=label, width=170, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame)
        entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        if browse:
            button = ctk.CTkButton(frame, text="Browse", width=80, command=lambda: browse(entry))
            button.pack(side="left", padx=(PAD, 0))
        return entry

    def _build(self) -> None:
        self.repo = self._row("Repo URL or folder", browse=self._pick_dir)
        self.out_dir = self._row("Output folder", str(DEFAULT_OUTPUT_DIR), browse=self._pick_dir)
        self.max_size = self._row("Max file size (KB)", str(DEFAULT_MAX_SIZE_KB))
        self.exclude = self._row("Exclude folders (a, b)")

        self.strip = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Remove comments", variable=self.strip).pack(anchor="w", padx=PAD, pady=(PAD, 0))

        groups = ctk.CTkFrame(self)
        groups.pack(fill="x", padx=PAD, pady=(PAD, 0))
        heading = ctk.CTkLabel(groups, text="Include normally skipped:")
        heading.grid(row=0, column=0, columnspan=GROUP_COLUMNS, sticky="w", padx=PAD)
        self.include = {g: ctk.BooleanVar(value=False) for g in ALL_GROUPS}
        for i, (g, var) in enumerate(self.include.items()):
            box = ctk.CTkCheckBox(groups, text=g, variable=var)
            box.grid(row=1 + i // GROUP_COLUMNS, column=i % GROUP_COLUMNS, sticky="w", padx=PAD, pady=2)

        self.start = ctk.CTkButton(self, text="Start", command=self._start)
        self.start.pack(anchor="w", padx=PAD, pady=PAD)
        self.status = ctk.CTkTextbox(self)
        self.status.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def _pick_dir(self, entry: ctk.CTkEntry) -> None:
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _start(self) -> None:
        repo = self.repo.get().strip()
        if not repo:
            self.messages.put("Enter a repository URL or folder")
            return
        if not self.max_size.get().strip().isdigit():
            self.messages.put("Max file size must be a whole number")
            return
        kwargs = self._options()
        self.start.configure(state="disabled")
        threading.Thread(target=self._run, args=(repo,), kwargs=kwargs, daemon=True).start()

    def _options(self) -> dict:
        """Read the form into harvest() keyword arguments."""
        return {
            "output_dir": Path(self.out_dir.get() or DEFAULT_OUTPUT_DIR),
            "strip_comments": self.strip.get(),
            "skip_groups": {g for g, var in self.include.items() if not var.get()},
            "exclude_folders": [f.strip() for f in self.exclude.get().split(",") if f.strip()],
            "max_size_kb": int(self.max_size.get()),
        }

    def _run(self, repo: str, **kwargs) -> None:
        try:
            self.messages.put(f"Done: {harvest(repo, **kwargs)}")
        except Exception as e:  # surface any failure in the log box
            self.messages.put(f"Error: {e}")
        finally:
            self.messages.put(None)

    def _drain_log(self) -> None:
        while not self.messages.empty():
            message = self.messages.get()
            if message is None:
                self.start.configure(state="normal")
                continue
            self.status.insert("end", message + "\n")
            self.status.see("end")
        self.after(POLL_MS, self._drain_log)


if __name__ == "__main__":
    App().mainloop()
