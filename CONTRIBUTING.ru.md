[English](CONTRIBUTING.md) | **Русский**

# Как помочь проекту

Баг-репорты, идеи и pull request'ы приветствуются. Если правка больше мелкого фикса, сначала откройте issue,
чтобы договориться о подходе.

## Окружение

Нужны Python 3.12+, [uv](https://docs.astral.sh/uv/) и git.

```shell
git clone https://github.com/octrow/RepoHarvester && cd RepoHarvester
uv run --group dev pytest        # тесты
uvx ruff check .                 # линтер
uvx pre-commit install           # по желанию: поиск секретов и проверка workflow при коммите
uv run --extra gui repoharvester-gui   # GUI
```

## Pull request'ы

- Одно изменение на PR; если меняется поведение, добавьте тест.
- Без зависимостей: CLI использует только стандартную библиотеку.
- Сообщения коммитов: `<type>: <description>` (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`).
- Допишите `CHANGELOG.md` в раздел «Unreleased» и обновите `README.md` и `README.ru.md`, если меняется документация.

Участвуя в проекте, вы соглашаетесь соблюдать [Кодекс поведения](CODE_OF_CONDUCT.ru.md).
