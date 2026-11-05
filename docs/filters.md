# Filters

Groups: `archive`, `audio`, `cache_files`, `certificate`, `compiled_code`, `configuration`, `database`, `executables`, `font`, `log_files`, `media`, `node_modules`, `office`, `package_locks`, `system`, `temporary`, `video`, `virtual_env`. See `EXTENSION_GROUPS`, `FILENAME_GROUPS` and `FOLDER_GROUPS` in `repoharvester.py`.

Globs (`--include`, `--exclude-glob`):

Globs match the path relative to the repo root or the bare file name; `*` also crosses `/`, so write `test_*.py` or `docs/*` (not `**/test_*.py` or `docs/`). Output to stdout is always UTF-8. They apply on top of the groups and `.gitignore`.
