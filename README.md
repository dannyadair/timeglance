# timeglance

[![Python](https://img.shields.io/python/required-version-toml?color=blue&tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdannyadair%2Ftimeglance%2Fmain%2Fpyproject.toml)](https://github.com/dannyadair/timeglance/blob/main/pyproject.toml)
[![tests](https://github.com/dannyadair/timeglance/actions/workflows/tests.yaml/badge.svg)](https://github.com/dannyadair/timeglance/actions/workflows/tests.yaml)
[![pre-commit](https://img.shields.io/github/actions/workflow/status/dannyadair/timeglance/pre-commit.yaml?label=pre-commit&logo=pre-commit&logoColor=white)](https://github.com/dannyadair/timeglance/actions/workflows/pre-commit.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pip-audit](https://img.shields.io/github/actions/workflow/status/dannyadair/timeglance/pip-audit.yaml?label=pip-audit&logo=python)](https://github.com/dannyadair/timeglance/actions/workflows/pip-audit.yaml)
[![bandit](https://img.shields.io/github/actions/workflow/status/dannyadair/timeglance/bandit.yaml?label=bandit&logo=python)](https://github.com/dannyadair/timeglance/actions/workflows/bandit.yaml)
[![Last commit](https://img.shields.io/github/last-commit/dannyadair/timeglance?color=lightgrey)](https://github.com/dannyadair/timeglance/commits/main)
[![License](https://img.shields.io/github/license/dannyadair/timeglance?color=lightgrey)](https://github.com/dannyadair/timeglance/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/timeglance?color=blue)](https://pypi.org/project/timeglance/)
[![Downloads](https://img.shields.io/pypi/dw/timeglance?color=blue)](https://pypistats.org/packages/timeglance)
[![sigstore](https://img.shields.io/badge/sigstore-signed-blue)](https://github.com/dannyadair/timeglance/releases)
[![OSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/dannyadair/timeglance?label=OSSF%20Scorecard)](https://scorecard.dev/viewer/?uri=github.com/dannyadair/timeglance)

Config-driven time planning at a glance - one web UI controls two tools:

- **Weekly** - your routine sheet with activity layers. Print it or set it as a desktop wallpaper.
- **Year** - a wide year-at-a-glance planner, with layers fed by your own calendars, public holidays, and manually
  added events. Print it or set it as a desktop wallpaper.

One web control panel drives both - preview live, toggle layers, edit the YAML, export, or set the wallpaper:

![The weekly routine in the control panel](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/weekly.png)

![The year planner in the control panel](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/year.png)

...and the rendered output you print or set as a wallpaper:

![Weekly routine sheet](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/weekly_output.png)

![Year-at-a-glance planner](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/year_output.png)

## Quick start (Docker)

```sh
docker compose run --rm timeglance timeglance-init   # first run: scaffold year/ + weekly/ config.yaml
docker compose up                                    # then open http://localhost:8753
```

Config, outputs and scheduler state are bind-mounted under `./year`, `./weekly` and `./state`, so the UI edits
files on your host. Outputs are written as your host user — the compose file defaults to `1000:1000` (the usual
first Linux user), so it just works for most; if your uid differs, run `UID=$(id -u) GID=$(id -g) docker compose up`.

> Wallpaper-setting needs a live Plasma session, so it works only with the **local install** (next section), not in
> Docker; the container UI auto-hides it.

## Quick start (local)

Needs Python 3.13 and [uv](https://docs.astral.sh/uv/). WeasyPrint and CairoSVG load native libraries (Cairo, Pango,
GDK-PixBuf) at runtime; most Linux desktops already have these, but on a minimal or server install add them first
(Debian/Ubuntu):

```sh
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0
uv sync
uv run timeglance-init     # scaffold year/ + weekly/ config.yaml from the templates
uv run timeglance          # the control panel at http://localhost:8753
```

Headless renders (each flag has a YAML equivalent):

```sh
uv run timeglance-year --theme light --layout vertical   # -> year/out/
uv run timeglance-weekly --format both                   # -> weekly/out/
```

## Docs

- [Motivation](docs/motivation.md) - why this exists, and how it fits a GTD/calendar setup
- [The control panel](docs/control-panel.md) - preview, config editor, scheduler & activity log
- [Configuration](docs/configuration.md) - year & weekly YAML, calendar (`.ics`) sources
- [Reference](docs/reference.md) - every CLI flag and YAML key
- [Wallpaper](docs/wallpaper.md) - KDE Plasma, per-screen native-resolution rendering
- [Use as a library](docs/library.md) - import and render PNG/PDF/SVG from Python
- [Contributing](CONTRIBUTING.md) - setup, CI, releasing

## Limitations

- **Wallpaper-setting is host-only.** The container can't reach a Plasma session, so inside Docker the feature
  self-hides and a scheduled "set wallpaper" renders the files but skips the set (logged as
  `wallpaper skipped (no backend)`). Run the server/CLI on the host to set wallpapers.
- **Weekly blocks can't overlap in time.** Two activities over the same slot on the same day render on top of each
  other, so only one reads clearly.
