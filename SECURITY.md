**English** | [Русский](SECURITY.ru.md)

# Security policy

## Supported versions

Only the latest release gets fixes.

## Reporting a vulnerability

Please don't open a public issue. Report it privately through
[GitHub security advisories](https://github.com/octrow/RepoHarvester/security/advisories/new).
I'll reply within a week and tell you what happens next.

RepoHarvester runs `git` on URLs you give it and reads local files, so the interesting cases are things like
argument injection through a crafted URL, path traversal out of the cloned repo, or the output folder ending
up somewhere unexpected.
