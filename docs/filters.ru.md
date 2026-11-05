# Фильтры

Группы: `archive`, `audio`, `cache_files`, `certificate`, `compiled_code`, `configuration`, `database`, `executables`, `font`, `log_files`, `media`, `node_modules`, `office`, `package_locks`, `system`, `temporary`, `video`, `virtual_env`. Подробности в `EXTENSION_GROUPS`, `FILENAME_GROUPS` и `FOLDER_GROUPS` в `repoharvester.py`.

Маски (`--include`, `--exclude-glob`):

Маски сравниваются с путём от корня репозитория или с именем файла; `*` захватывает и `/`, поэтому пишите `test_*.py` или `docs/*` (а не `**/test_*.py` или `docs/`). Вывод в stdout всегда в UTF-8. Они применяются поверх групп и `.gitignore`.
