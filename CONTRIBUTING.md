# Contributing

Patches welcome! Open an issue for bugs and ideas, or a PR for changes.

## Setup

```sh
uv sync
pre-commit install
```

Hooks: **ruff** (lint + format) for Python, **prettier** for Markdown.

The code lives under `src/timeglance/` (`common`, `year`, `weekly` subpackages); packaged assets (web UI, Jinja
templates, the `config.yaml.in` files) ship inside it. Working data - each tool's `config.yaml` and `out/`, plus
shared `state/` - resolves from the current working directory (override with `TIMEGLANCE_HOME`).

## Before you push

`uv run pytest` and `pre-commit run --all-files` should pass. Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org) (`feat:`, `fix:`, `docs:`, …) - they drive the automated
version bumps and changelog.

## Continuous integration

Every pull request runs **pre-commit** (ruff + prettier) and the **pytest** suite (with the WeasyPrint/CairoSVG
system libraries installed), plus **pip-audit** (dependency CVEs) and **bandit** (security lint). Pushes to `main`
run those again and then the release job.

## Releasing

Versioning is automated with [python-semantic-release](https://python-semantic-release.readthedocs.io), driven by
[Conventional Commits](https://www.conventionalcommits.org):

- `feat: …` → minor bump, `fix: …` → patch bump, breaking change (`feat!: …` or a `BREAKING CHANGE:` footer) →
  major bump; `docs:` / `refactor:` / `perf:` show up in the changelog.
- An optional scope narrows the area, e.g. `feat(weekly): …` or `fix(year): …`.

On every push to `main`, CI runs semantic-release. When the new commits warrant a bump (per the rules above) it
raises the version in `pyproject.toml` (and `src/timeglance/__init__.py:__version__`), updates the changelog, tags,
and cuts a GitHub Release; otherwise it does nothing. This needs a `SEMANTIC_RELEASE_TOKEN` secret (a PAT with
`contents: write`). That same version bump then publishes the build to PyPI via
[trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC, no API token) from the `pypi` environment.
