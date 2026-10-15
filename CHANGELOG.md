# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2026-10-16

### Added
- File list with per-file token estimates at the top of the output.
- `--include` / `--exclude-glob` to pick files by glob; the same fields in the GUI.
- `-o -` prints the result to stdout, ready for a pipe or the clipboard.
- `harvest_text()` returns the compiled text without writing files.

### Changed
- Output format: a `### Files: N, ~T tokens` list now precedes the file sections.

## [0.2.2] - 2026-10-16

### Added
- PyPI metadata: keywords, classifiers and project links (changelog, issues).
- Release workflow: a pushed `vX.Y.Z` tag publishes to PyPI (trusted publishing) and creates the GitHub release.
- Secret scanning (gitleaks) and workflow audit (zizmor) in CI, pre-commit config, Dependabot.

## [0.2.1] - 2026-10-16

### Added
- The GUI ships with the package: `uv tool install "repoharvester[gui]"`, then `repoharvester-gui`.

### Changed
- `gui.py` renamed to `repoharvester_gui.py`.

## [0.2.0] - 2026-10-16

First release on PyPI.

### Added
- Respects `.gitignore`: in a git repo only tracked and untracked-but-not-ignored files are harvested.
- Rough token estimate (~4 characters per token) in the log.
- GUI: shows git errors, cancellable clone, remembers settings in `~/.config/repoharvester/gui.json`.
- CI with ruff and pytest.

### Changed
- Python comments are removed with the tokenizer; string literals are kept in every language.
- Core rewritten as plain functions with a `HarvestOptions` parameter object; clone failures raise `CloneError`.

[Unreleased]: https://github.com/octrow/RepoHarvester/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/octrow/RepoHarvester/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/octrow/RepoHarvester/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/octrow/RepoHarvester/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/octrow/RepoHarvester/releases/tag/v0.2.0
