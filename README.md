# RepoHarvester

Clone a git repository (or point at a local folder) and compile all of its text files into one file. Handy for feeding a codebase to an LLM, code review, or offline reading.

## Features
- Works with SSH/HTTPS git URLs (shallow clone into a temp dir) or local folders.
- Skips binary/noise by default: media, archives, executables, lock files, `node_modules`, virtualenvs, caches, `.git`, `.github`, and more.
- Optional comment removal for common languages. String literals are kept, so `"http://..."` and `"#fff"` stay intact.
- Size limit per file. Non-UTF-8 files are skipped and listed in `skipped_files.txt`.
- Each file is headed by its path relative to the repo root. The output folder is never harvested into itself.
- No runtime dependencies. The GUI is optional.

## Install
Requires Python 3.12+ and git.

```shell
uv tool install git+https://github.com/octrow/RepoHarvester   # or: uv run repoharvester ... from a clone
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
| `-o`, `--output-dir` | Output directory (default `output`) |
| `--log FILE` | Also write the log to a file |

Groups: `archive`, `audio`, `cache_files`, `certificate`, `compiled_code`, `configuration`, `database`, `executables`, `font`, `log_files`, `media`, `node_modules`, `office`, `package_locks`, `system`, `temporary`, `video`, `virtual_env`. See `EXTENSION_GROUPS`, `FILENAME_GROUPS` and `FOLDER_GROUPS` in `repoharvester.py`.

Example:
```shell
repoharvester git@github.com:username/repo.git -r --no-skip configuration --max-size 250 --exclude vendor,docs
```

## GUI
```shell
uv run --extra gui python gui.py
```
Paste a git URL or choose a folder, tick anything extra to include, press **Harvest** (or Enter), then **Open file**.
On Linux the project prefers the system Python: uv's bundled builds ship Tk without font antialiasing.

## Output format
```
## <repo-name>
### <relative/path/to/file.ext>
<file contents>
### end of file
...
```
Written to `<output-dir>/<repo-name>_all_files.txt`, with `skipped_files.txt` next to it.

## Development
```shell
uv run --group dev pytest
uvx ruff check .
```

## License
MIT. See `LICENSE`.
