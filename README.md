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

Config-driven time planning at a glance - one web UI controls two planners:

- **Weekly** - your routine sheet with topic layers. Print it or set it as a desktop wallpaper.
- **Year** - a wide year-at-a-glance planner, with layers fed by your own calendars, public holidays, and manually
  added events. Print it or set it as a desktop wallpaper.

One web control panel drives both - preview live, toggle layers, edit the YAML, export, or set the wallpaper:

![The weekly routine in the control panel](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/weekly.png)

![The year planner in the control panel](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/year.png)

...and the rendered output you print or set as a wallpaper:

![Weekly routine sheet](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/weekly_output.png)

![Year-at-a-glance planner](https://raw.githubusercontent.com/dannyadair/timeglance/main/docs/images/year_output.png)

## Try it instantly (Docker)

The zero-install way to see the control panel and renders - a **test drive, not a deployment target**. A container
can't reach your desktop session, so **Docker can never set the wallpaper** (the UI auto-hides it, and a scheduled
"set wallpaper" renders the file but skips the set). Bridging the host display/DBus into a container isn't something
we intend to solve - to actually use timeglance on your desktop, install it locally (next section).

```sh
docker compose run --rm timeglance timeglance init   # first run: scaffold year/ + weekly/ config.yaml
docker compose up                                    # then open http://localhost:8753
```

Config, outputs and scheduler state are bind-mounted under `./year`, `./weekly` and `./state`, so the UI edits
files on your host. Outputs are written as your host user — the compose file defaults to `1000:1000` (the usual
first Linux user), so it just works for most; if your uid differs, run `UID=$(id -u) GID=$(id -g) docker compose up`.

## Install (Ubuntu/Debian)

The simplest way on a Debian-based desktop. Grab the `.deb` from the
[latest release](https://github.com/dannyadair/timeglance/releases/latest) and install it - `apt` pulls every
dependency (the Python libraries, poppler, native Cairo/Pango stack, tray AppIndicator, fonts) from your distro:

```sh
sudo apt install ./timeglance_<version>_all.deb
```

Then launch **timeglance** from your applications menu - the tray icon appears and opens the control panel, no
terminal needed. Or drive it from the CLI (`timeglance` is now on your `PATH`):

```sh
timeglance init     # scaffold year/ + weekly/ config.yaml from the templates
timeglance serve    # the control panel at http://localhost:8753
```

A pure-Python install under `/usr/lib/python3/dist-packages` run by your system Python, with every dependency
satisfied by your distro's own apt packages. CI builds and install-tests the `.deb` on Ubuntu 24.04, 25.10 and
26.04; other recent releases may work.

**Uninstalling.** timeglance sets up _user_-level bits that `apt` can't remove: a systemd timer for the daily
render and, if you enabled it, a tray autostart entry. Run `timeglance uninstall` first - it stops a running
tray, disables the timer, and removes both the unit files and the autostart entry - then `sudo apt remove
timeglance`. Your per-user configs and output (`~/.config/timeglance`, `~/.local/state/timeglance`,
`~/.local/share/timeglance`) are left untouched either way.

## Install (Python/uv)

Needs Python 3.12+ and [uv](https://docs.astral.sh/uv/). WeasyPrint and CairoSVG load native libraries (Cairo, Pango,
GDK-PixBuf) at runtime, and the wallpaper feature rasterizes the sheet with poppler's `pdftocairo`; most Linux desktops
already have these, but on a minimal or server install add them first (Debian/Ubuntu):

```sh
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 poppler-utils
uv sync
uv run timeglance init      # scaffold year/ + weekly/ config.yaml from the templates
uv run timeglance serve     # the control panel at http://localhost:8753
```

Config, state and rendered output live under the XDG base directories by default
(`~/.config/timeglance`, `~/.local/state/timeglance`, `~/.local/share/timeglance`); set
`TIMEGLANCE_HOME=$PWD` to keep it all in the current folder instead.

Headless renders (each flag has a YAML equivalent):

```sh
uv run timeglance render year --theme light --layout vertical   # render the year planner
uv run timeglance render weekly --format both                   # render the weekly sheet
```

## Set and forget (systemd timer)

To re-render (and optionally re-wallpaper) on a schedule with nothing running and nothing to start after a reboot:

```sh
timeglance install              # write a user service + timer and enable it now
timeglance install --time 06:30 # or pick the time (default: schedule.yaml's)
timeglance uninstall            # remove it
```

(From a source checkout, prefix these with `uv run`.) This drops `timeglance-render.service` (a oneshot that runs
`timeglance run`, honouring your `schedule.yaml`) and `timeglance-render.timer` into `~/.config/systemd/user/`, then
enables the timer. `Persistent=true` means a run missed while the machine was off happens on the next boot. Change
the time by re-running `timeglance install --time HH:MM`.

Setting the Plasma wallpaper needs an active graphical session, so a render while you're fully logged out writes the
files but can't paint - it repaints on your next session. For renders while logged out (no wallpaper), enable
lingering: `loginctl enable-linger $USER`.

## Tray controller

A system-tray menu to open the panel and flip the schedule - a launcher and quick toggles, _not_ the scheduler (the
timer above keeps running whether or not the tray is open).

The `.deb` already includes it: after `apt install`, launch **timeglance** from your applications menu and the tray
icon appears (it pulls the system AppIndicator/GObject libraries as dependencies). From a source checkout, add the
extra and the system libraries, then run it:

```sh
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1
uv sync --extra tray
uv run timeglance tray
```

The menu opens the control panel (starting the server first if needed), starts/stops it, picks the port, and toggles
the schedule: enabled, time, which planners render, and which set the wallpaper. **Autostart** adds an XDG
autostart entry so the tray is there every session (the same thing KDE's System Settings → Autostart manages).
Quitting the tray only closes the panel it started - the systemd timer keeps running regardless.

## Docs

- [Motivation](docs/motivation.md) - why this exists, and how it fits a GTD/calendar setup
- [The control panel](docs/control-panel.md) - preview, config editor, scheduler & activity log
- [Configuration](docs/configuration.md) - year & weekly YAML, calendar (`.ics`) sources
- [Reference](docs/reference.md) - every CLI flag and YAML key
- [Wallpaper](docs/wallpaper.md) - KDE Plasma, per-screen native-resolution rendering
- [Use as a library](docs/library.md) - import and render PNG/PDF/SVG from Python
- [Contributing](CONTRIBUTING.md) - setup, CI, releasing

## Limitations

- **Weekly activities can't overlap in time.** Two activities over the same slot on the same day render on top of
  each other, so only one reads clearly.
