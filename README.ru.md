# RepoHarvester

[![CI](https://github.com/octrow/RepoHarvester/actions/workflows/ci.yml/badge.svg)](https://github.com/octrow/RepoHarvester/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/repoharvester)](https://pypi.org/project/repoharvester/)
[![Python](https://img.shields.io/pypi/pyversions/repoharvester)](https://pypi.org/project/repoharvester/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[English](README.md) | **Русский**

Клонирует git-репозиторий (или берёт локальную папку) и собирает все его текстовые файлы в один. Результат можно вставить в ChatGPT или Claude как контекст для LLM, искать по нему, ревьюить или читать офлайн. Консольная утилита и необязательный GUI. Зависимостей нет.

```shell
uvx repoharvester https://github.com/psf/requests
```
```
Cloning https://github.com/psf/requests
Wrote 92 files to output/requests_all_files.txt, ~154.7k tokens (0 non-UTF-8 skipped)
```

## Возможности
- Принимает SSH/HTTPS-адреса git (неглубокий клон во временную папку) или локальные папки.
- По умолчанию пропускает бинарники и мусор: медиа, архивы, исполняемые файлы, lock-файлы, `node_modules`, виртуальные окружения, кэши, `.git`, `.github` и другое.
- Может удалять комментарии в распространённых языках. Строковые литералы не трогает, так что `"http://..."` и `"#fff"` остаются целыми. Для Python используется настоящий токенизатор, для остальных языков регулярные выражения.
- Лимит размера на файл. Файлы не в UTF-8 пропускаются и попадают в список `skipped_files.txt`.
- Учитывает `.gitignore`: в git-репозитории берутся только отслеживаемые файлы и неотслеживаемые, но не игнорируемые.
- Пишет в лог примерную оценку токенов (~4 символа на токен), чтобы было видно, влезет ли результат в контекст LLM.
- Перед каждым файлом стоит его путь относительно корня репозитория. Папка с результатом никогда не попадает в сам результат.
- Никаких зависимостей во время работы. GUI ставится отдельно, по желанию.

## Установка
Нужны Python 3.12+ и git.

```shell
uv tool install repoharvester            # или: pipx install repoharvester
uv tool install "repoharvester[gui]"     # вместе с GUI
```

## Использование
```shell
repoharvester <repo-url-or-folder> [options]
```

| Опция | Описание |
|---|---|
| `-r`, `--remove` | Удалять комментарии из кода |
| `--no-skip GROUP[,GROUP]` | Включить группы, которые по умолчанию пропускаются (можно повторять) |
| `--max-size KB` | Пропускать файлы больше этого размера (по умолчанию 1000). Файлы больше 500 KB попадают в лог |
| `--exclude DIR[,DIR]` | Имена папок, которые исключаются вместе с содержимым (можно повторять) |
| `-o`, `--output-dir` | Папка для результата (по умолчанию `output`) |
| `--log FILE` | Дополнительно писать лог в файл |

Группы: `archive`, `audio`, `cache_files`, `certificate`, `compiled_code`, `configuration`, `database`, `executables`, `font`, `log_files`, `media`, `node_modules`, `office`, `package_locks`, `system`, `temporary`, `video`, `virtual_env`. Подробности в `EXTENSION_GROUPS`, `FILENAME_GROUPS` и `FOLDER_GROUPS` в `repoharvester.py`.

Пример:
```shell
repoharvester git@github.com:username/repo.git -r --no-skip configuration --max-size 250 --exclude vendor,docs
```

## GUI
```shell
repoharvester-gui                         # после установки с [gui]
uv run --extra gui repoharvester-gui      # из клона репозитория
```

<img src="docs/gui.png" width="520" alt="Окно RepoHarvester: поля для адреса репозитория и папки результата, максимальный размер файла, исключаемые папки, флажок удаления комментариев, сетка групп файлов и кнопка Harvest над пустым логом">

Вставьте git-адрес или выберите папку, отметьте, что ещё включить, нажмите **Harvest** (или Enter), затем **Open file**.
Пока идёт клонирование, кнопка превращается в **Cancel**. Настройки сохраняются в `~/.config/repoharvester/gui.json`.
На Linux проект использует системный Python: в сборках, которые ставит uv, Tk идёт без сглаживания шрифтов.

## Формат результата
```
## <repo-name>
### <relative/path/to/file.ext>
<file contents>
### end of file
...
```
Пишется в `<output-dir>/<repo-name>_all_files.txt`, рядом лежит `skipped_files.txt`.

## Альтернативы
- [repomix](https://github.com/yamadashy/repomix) (Node.js): больше форматов вывода, точный подсчёт токенов, намного больше опций. Берите его, если у вас есть Node и это нужно.
- [gitingest](https://github.com/coderamp-labs/gitingest) (Python): есть ещё сайт, на котором достаточно заменить `hub` на `ingest` в адресе GitHub.
- [files-to-prompt](https://github.com/simonw/files-to-prompt) (Python): работает с локальными файлами и папками, без клонирования.

RepoHarvester — один модуль на стандартной библиотеке: кроме Python и git ничего ставить не нужно, а для тех, кому удобнее мышкой, есть небольшой GUI.

## Разработка
См. [CONTRIBUTING.ru.md](CONTRIBUTING.ru.md).

```shell
uv run --group dev pytest
uvx ruff check .
```

## Лицензия
MIT. См. `LICENSE`.
