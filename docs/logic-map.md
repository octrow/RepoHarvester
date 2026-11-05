# Logic map

How one repository (git URL or local folder) becomes one text file for LLM context.
The map describes the code as it is today, step by step.
Each step says what it decides, where the flow branches, and which module does it.

There is no glossary file; the terms are in the README ("group" = a named set of skipped extensions, file names or folders).
Known gaps and fixes in progress are in `docs/plans/2026-11-05-logic-map-fixes.md`.

Rule: if you change a step or a branch, update this file in the same commit.
`test_logic_map.py` checks that every `Module:` line points to a real module.
The code is two flat modules at the repo root; there is no package.

## The flow at a glance

```
repo (git URL | local folder) + HarvestOptions
  │
  ├─ 1  Options ........... which groups, folders, globs, size limit apply
  ├─ 2  Source ............ local folder or git clone? what is the output name?
  ├─ 3  Clone ............. shallow clone into a temp dir (git sources only)
  ├─ 4  Collect ........... walk the tree, drop skipped folders/names/extensions/symlinks/big files
  ├─ 5  Select ............ drop the output folder, apply include/exclude globs, drop git-ignored files
  ├─ 6  Render ............ read as UTF-8, optionally strip comments, one section per file
  ├─ 7  Assemble .......... header with file count and token estimate, then all sections
  └─ 8  Write ............. stdout, or <output_dir>/<name>_all_files.txt + skipped_files.txt
  │
Harvest (name, text, file_count, skipped) or the output file path
```

There is no LLM or key. The only external dependency of the core is the `git` binary (steps 3 and 5); the GUI also needs `customtkinter` and the system file opener.
Relative paths (`output_dir`, default `output`) resolve against the process working directory, not the harvested folder.
Steps 2 to 7 run inside `harvest_text`; step 8 is `harvest` (files) or `main` (stdout).

## Where the flow splits by kind

The split is by file kind (what is skipped, how comments are stripped). It is decided in two tables in one module.

| Kind | Switched on by | Steps it changes | What changes |
|---|---|---|---|
| Skip group (18 names, `ALL_GROUPS`) | `HarvestOptions.skip_groups`; default = all groups skipped; `--no-skip` / GUI checkbox removes one | 4 | extension (`EXTENSION_GROUPS`), exact file name (`FILENAME_GROUPS`) or folder name (`FOLDER_GROUPS`) is dropped; `cache_files` is both an extension and a folder group, so one flag unskips both |
| Comment language | lowercased extension in `COMMENT_PATTERNS` (js, css, php, py, lua, shell-like, sql, html/xml/vue ...) | 6 | which regex strips comments; unknown extension: content unchanged |
| Python comments | extension `py` | 6 | tokenizer, exact; falls back to the regex if the file does not tokenize |

Examples:
- `logo.png` → group `media` → dropped in step 4 unless `--no-skip media`.
- `a.py` with `-r` → comments removed by the tokenizer; a shebang on line 1 is kept.
- `Makefile`, `.env` (suffix is empty) → no extension group matches → kept (see #1).

Module: `repoharvester`

## Entry points

Both entry points call `harvest_text` (through `harvest` for GUI and file mode). They differ in defaults and output.

| Entry | Skip groups | Output | Notes |
|---|---|---|---|
| CLI `repoharvester` (`main`) | all skipped; `--no-skip` unskips | `-o -` → stdout, no files; else `harvest` → `output/` | log INFO to stderr (+ `--log` file); only `CloneError` is caught (exit 1); `--max-size` default 1000 KB |
| GUI `repoharvester-gui` (`App`) | all skipped; ticked boxes unskip | always `harvest` (a "Save to" of `-` is a folder named `-`) | runs in a worker thread; cancel works only during the clone; form saved to `$XDG_CONFIG_HOME/repoharvester/gui.json` (default `~/.config`) on every Harvest click that passes validation |

CLI flags `--include`, `--exclude-glob`, `--exclude` are repeatable and comma-split. `--include` cannot bring back a skipped group.

Module: `repoharvester`, `repoharvester_gui`

## Steps

### 1. Options

Decides: which files the harvest may take.
In: argv or GUI form. Out: frozen `HarvestOptions`.
Branches:
- CLI: unknown `--no-skip` group → `parser.error`, exit 2;
- GUI: empty repo or non-digit max size → status line error, nothing starts;
- GUI "Save to" empty → `output`;
- `skip_groups` = all groups minus the unskipped ones.
`--max-size` is not range-checked: 0 keeps only empty files, a negative value drops every file (each with a WARNING).
Fails: invalid CLI group stops before logging is set up; invalid GUI form stops before saving settings.
Module: `repoharvester`, `repoharvester_gui`

### 2. Source

Decides: local folder or git clone, and the output name.
In: `repo` string. Out: `root`, `name`.
Branches:
- `Path(repo).expanduser().is_dir()` → local: root is that folder, name is its resolved folder name;
- anything else (including a mistyped local path) → git source: name from `get_repo_name` (last segment after `/` and `:`, `.git` removed, fallback `repo`).
Fails: a mistyped path is passed to `git clone` and fails in step 3 with git's message.
Module: `repoharvester`

### 3. Clone

Decides: whether the clone finished, failed or was cancelled.
In: URL, temp dir, optional `threading.Event`. Out: files in the temp dir.
Branches:
- runs `git clone --depth 1 --quiet <repo> <tmp>` in its own session (no controlling terminal, so git cannot prompt for a password or host key, #11), polled every 0.2 s with an overall deadline of `CLONE_TIMEOUT_S` (600 s); no submodules;
- cancel event set while running → kill the process group (Windows: the process), raise `HarvestCancelled`;
- deadline passed → kill the process group, `CloneError("git clone of <repo> timed out after 600 s")`;
- non-zero exit → `CloneError("git clone of <repo> failed: <first stderr line | exit code N>")`.
Local folder: step is skipped; the cancel event is never read.
Fails: stops the run; `harvest` has written nothing yet, so an old output file stays. Missing `git` binary raises `FileNotFoundError` (not handled, #2). Ctrl+C in the CLI or closing the GUI does not reach git, which keeps running detached (#12).
Module: `repoharvester`

### 4. Collect

Decides: which files survive the static rules.
In: `root`, options. Out: sorted `list[Path]`.
Branches (per directory, sorted):
- directory name in `.git`, `.github`, `--exclude` names or an active folder group (`venv`, `.venv`, `env`, `node_modules`, caches) → not entered, at any depth;
- file name in an active filename group (lock files), lowercased extension in an active extension group, or a symlink → dropped;
- size over `max_size_kb` → dropped with a WARNING; over 500 KB → INFO "Large file".
Extension is `Path.suffix`, so `.DS_Store` and `.env` have an empty extension (#1).
`Path.walk` does not follow links and lists a symlinked folder as a file, so it is dropped as a symlink. File-name groups match case-sensitively.
Fails: a file that vanishes during the walk raises `OSError` from `stat` and stops the run; an unreadable folder is skipped silently (`Path.walk` ignores `scandir` errors).
Module: `repoharvester`

### 5. Select

Decides: which collected files are really part of the repository.
In: collected files. Out: filtered list.
Branches, in this order:
- file resolves inside the current `output_dir` → dropped (keeps the previous output out of the next one). Only the current one: with `-o -` or another `-o`, an old `output/` inside the folder is harvested (#10);
- `--include` globs given and none matches → dropped; any `--exclude-glob` matches → dropped. A glob is tested case-sensitively (`fnmatchcase`) against the relative path and the bare name, `*` crosses `/`;
- `git -C root ls-files --cached --others --exclude-standard`: files not in that list (git-ignored) → dropped. Non-zero exit (not a git repo) → keep all.
Local folder inside a bigger git repo: the list covers only `root`.
A nested git repo or submodule is listed by git as one `inner/` entry, so every file inside it is dropped silently (#9).
Size warnings from step 4 are logged before this step, so ignored or glob-excluded files can still log a warning (#4).
Fails: git exits non-zero → fail-open, keep everything; git missing → `FileNotFoundError` (#2).
Module: `repoharvester`

### 6. Render

Decides: the text of each file and which files are unreadable.
In: files. Out: `dict[rel path → section]`, list of skipped paths.
Branches:
- `read_text(utf-8)` raises `UnicodeDecodeError` → the path goes to `skipped`, INFO log;
- `strip_comments` and extension `py` → tokenizer removal; `TokenError`/`SyntaxError` → regex fallback. Token rows are applied to `str.splitlines` lines, which also split on `\x0c`, ` ` and similar: such a file keeps comments or gets code merged into a comment (#8);
- `strip_comments` and another known extension → regex removal, string literals kept;
- unknown extension → unchanged.
Section format: `### <rel>\n<content>\n### end of file\n`.
Fails: non-UTF-8 files are left out and listed; other `OSError` (permissions) stops the run.
Module: `repoharvester`

### 7. Assemble

Decides: the header and the size figure.
In: sections. Out: one string.
Token estimate = `round(len / 4)` per section, summed; shown as `1.2k` from 1000 up. The same sum goes to the log line.
Layout: `## <name>`, `### Files: N, ~T tokens`, one `<rel>  ~tokens` line per file, blank line, sections in walk order.
Module: `repoharvester`

### 8. Write

Decides: where the text goes.
In: `Harvest`. Out: stdout or files.
Branches:
- CLI `-o -` → UTF-8 bytes to stdout; no `skipped_files.txt`; skipped non-UTF-8 files appear only in the INFO log;
- otherwise `output_dir` is created, `<name>_all_files.txt` and `skipped_files.txt` (only the non-UTF-8 files of step 6; empty when none) are overwritten atomically (temp file `<file>.tmp`, e.g. `<name>_all_files.txt.tmp`, next to the target + `os.replace`; a failed write keeps the old file).
Both files are overwritten without asking. Two repositories with the same name, or any two runs into one folder, share the file names (#3).
CLI prints `All files have been written to <path>`; GUI shows `Saved <name>_all_files.txt` and an "Open file" button (`xdg-open` / `open` / `startfile`).
Fails: write errors (`OSError`) are not caught by the CLI (traceback); the GUI shows them as an error status.
Module: `repoharvester`, `repoharvester_gui`

## Side flows

### GUI worker and log

`App._start` validates, saves settings, then runs `harvest` in a daemon thread. The worker only puts messages on a queue; the Tk thread drains it every 100 ms. Log lines of logger `repoharvester` are queued through `QueueHandler`.
Outcomes: `HarvestCancelled` → "Cancelled. Nothing was saved."; any other exception → its text in the status and log; success → result path.
The Harvest button turns into "Cancel"; pressing it sets the event. For a local folder, or a git source whose clone has finished, nothing reads the event, so the run finishes and saves (#5).
Closing the window mid-run kills the daemon worker; a running git clone keeps going detached (#12).
Settings: `_load_settings` ignores a missing or broken file (invalid JSON or `OSError`); `_apply_settings` skips empty saved values, so a saved empty field never overrides the default.
Feeds: steps 1, 3, 8.
Module: `repoharvester_gui`

## Known gaps

Details and fixes are in the plan (number in brackets).
- Dotfiles without a suffix (`.env`, `.DS_Store`) match no extension group; a `.env` in a non-git local folder is harvested (#1).
- Missing `git` binary crashes with a traceback in the CLI (#2).
- A `repo` argument starting with `-` is parsed by `git clone` as an option (#6).
- `-r` on a Python file with a form feed or ` ` can merge code into a comment (#8).
- Files inside nested git repos and submodules of a local folder are dropped silently (#9).
