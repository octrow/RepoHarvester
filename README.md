# RepoHarvester

[![CI](https://github.com/octrow/RepoHarvester/actions/workflows/ci.yml/badge.svg)](https://github.com/octrow/RepoHarvester/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/repoharvester)](https://pypi.org/project/repoharvester/)
[![Python](https://img.shields.io/pypi/pyversions/repoharvester)](https://pypi.org/project/repoharvester/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**English** | [Русский](README.ru.md)

Clone a git repository (or point at a local folder) and get all of its text files in one file. Paste it into ChatGPT or Claude as LLM context, search it, review it, or read it offline. A command-line tool plus an optional GUI. No runtime dependencies.

```shell
uvx repoharvester https://github.com/psf/requests
```
```
Cloning https://github.com/psf/requests
Wrote 92 files to output/requests_all_files.txt, ~154.7k tokens (0 non-UTF-8 skipped)
```

## Features
- Works with SSH/HTTPS git URLs (shallow clone into a temp dir) or local folders.
- Skips binary/noise by default: media, archives, executables, lock files, `node_modules`, virtualenvs, caches, `.git`, `.github`, and more.
- Optional comment removal for common languages. String literals are kept, so `"http://..."` and `"#fff"` stay intact. Python uses the real tokenizer; other languages use regexes.
- Size limit per file. Non-UTF-8 files are skipped and listed in `skipped_files.txt`.
- Respects `.gitignore`: in a git repo only tracked and untracked-but-not-ignored files are harvested.
- Logs a rough token estimate (~4 characters per token) so you know if it fits an LLM context.
- Each file is headed by its path relative to the repo root. The output folder is never harvested into itself.
- No runtime dependencies. The GUI is optional.

## Install
Requires Python 3.12+ and git.

```shell
uv tool install repoharvester            # or: pipx install repoharvester
uv tool install "repoharvester[gui]"     # with the GUI
```

## Usage
```shell
repoharvester <repo-url-or-folder> [options]
```

| Option | Description |
|---|---|
| `-r`, `--remove` | Remove comments from code files |
| `--no-skip GROUP[,GROUP]` | Include groups that are skipped by default (repeatable) |
| `--max-size KB` | Skip files larger than this (default 1000). Files over 500 KB are logged |
| `--exclude DIR[,DIR]` | Folder names to exclude, along with their contents (repeatable) |
| `--include GLOB[,GLOB]` | Only harvest files matching these globs, e.g. `*.py,*.md` (repeatable) |
| `--exclude-glob GLOB[,GLOB]` | Skip files matching these globs, e.g. `tests/*` (repeatable) |
| `-o`, `--output-dir` | Output directory (default `output`), or `-` to print to stdout |
| `--log FILE` | Also write the log to a file |

Groups: `archive`, `audio`, `cache_files`, `certificate`, `compiled_code`, `configuration`, `database`, `executables`, `font`, `log_files`, `media`, `node_modules`, `office`, `package_locks`, `system`, `temporary`, `video`, `virtual_env`. See `EXTENSION_GROUPS`, `FILENAME_GROUPS` and `FOLDER_GROUPS` in `repoharvester.py`.

Example:
```shell
repoharvester git@github.com:username/repo.git -r --no-skip configuration --max-size 250 --exclude vendor,docs

# only Python and Markdown, no tests, straight to the clipboard
repoharvester . --include '*.py,*.md' --exclude-glob 'tests/*' -o - | xclip -selection clipboard   # macOS: | pbcopy
```
Globs match the path relative to the repo root or the bare file name; `*` also crosses `/`, so write `test_*.py` or `docs/*` (not `**/test_*.py` or `docs/`). Output to stdout is always UTF-8. They apply on top of the groups and `.gitignore`.

## GUI
```shell
repoharvester-gui                         # after installing with [gui]
uv run --extra gui repoharvester-gui      # from a clone
```

<img src="docs/gui.png" width="520" alt="RepoHarvester window: repository URL and output folder fields, max file size, skip folders, only-files and skip-files globs, a strip-comments checkbox, a grid of file groups to include, and a Harvest button above an empty log">

Paste a git URL or choose a folder, tick anything extra to include, press **Harvest** (or Enter), then **Open file**.
While a clone runs the button turns into **Cancel**. Settings are remembered in `~/.config/repoharvester/gui.json`.
On Linux the project prefers the system Python: uv's bundled builds ship Tk without font antialiasing.

## Output format
```
## <repo-name>
### Files: <count>, ~<tokens> tokens
<relative/path/one.ext>  ~<tokens>
<relative/path/two.ext>  ~<tokens>

### <relative/path/one.ext>
<file contents>
### end of file
...
```
The file list up front shows the model the repository's shape and shows you which files eat the context. Token counts are estimates (~4 characters per token).

Written to `<output-dir>/<repo-name>_all_files.txt`, with `skipped_files.txt` next to it.

## Alternatives
- [repomix](https://github.com/yamadashy/repomix) (Node.js): more output formats, exact token counts, many more options. Pick it if you have Node and want those.
- [gitingest](https://github.com/coderamp-labs/gitingest) (Python): also has a website where you swap `hub` for `ingest` in a GitHub URL.
- [files-to-prompt](https://github.com/simonw/files-to-prompt) (Python): local files and folders, no cloning.

RepoHarvester is a single standard-library module: nothing to install besides Python and git, plus a small desktop GUI if you prefer clicking.

## Development
See [CONTRIBUTING.md](CONTRIBUTING.md).

```shell
uv run --group dev pytest
uvx ruff check .
```

## License
MIT. See `LICENSE`.
