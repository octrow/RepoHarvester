**English** | [Русский](CONTRIBUTING.ru.md)

# Contributing

Bug reports, ideas and pull requests are welcome. For anything bigger than a small fix, open an issue first so we
can agree on the approach.

## Setup

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and git.

```shell
git clone https://github.com/octrow/RepoHarvester && cd RepoHarvester
uv run --group dev pytest        # tests
uvx ruff check .                 # lint
uvx pre-commit install           # optional: secret scan and workflow lint on commit
uv run --extra gui repoharvester-gui   # GUI
```

## Pull requests

- One change per PR, with a test when behaviour changes.
- Keep it dependency-free: the CLI uses only the standard library.
- Commit messages: `<type>: <description>` (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`).
- Update `CHANGELOG.md` under "Unreleased", and both `README.md` and `README.ru.md` if the docs change.

By contributing you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
