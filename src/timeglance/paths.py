"""Where timeglance reads and writes its working data.

Code and packaged assets (templates, web, the `*.yaml.in` files) live inside the installed
package. The data a user edits and the app writes is split by kind:

- **config** - the planners' `config.yaml` files you edit
- **state** - the scheduler's `schedule.yaml`, the activity log, remembered screens
- **cache** - the ICS fetch cache (regenerable)
- **data** - rendered output you print or set as wallpaper

By default each follows the XDG Base Directory spec (`~/.config`, `~/.local/state`,
`~/.cache`, `~/.local/share`), under a `timeglance/` subdirectory. Setting `TIMEGLANCE_HOME`
overrides all four to a single root - config and output at the root, state and cache beneath
it - which is the layout the Docker bind-mounts and the dev loop rely on.
"""

import os
from pathlib import Path


def _root():
    """The `TIMEGLANCE_HOME` single-root override, or None for XDG mode."""
    home = os.environ.get("TIMEGLANCE_HOME")
    return Path(home) if home else None


def _xdg(var, default):
    """A `timeglance/` dir under the XDG base dir `var` (falling back to `~/default`)."""
    return Path(os.environ.get(var) or Path.home() / default) / "timeglance"


def config_dir():
    """Base directory for the planners' editable `config.yaml` files."""
    return _root() or _xdg("XDG_CONFIG_HOME", ".config")


def state_dir():
    """Base directory for the scheduler state, activity log and remembered screens."""
    root = _root()
    return root / "state" if root else _xdg("XDG_STATE_HOME", ".local/state")


def cache_dir():
    """Base directory for regenerable caches (the ICS fetch cache)."""
    root = _root()
    return root / "state" if root else _xdg("XDG_CACHE_HOME", ".cache")


def data_dir():
    """Base directory for rendered output users print or set as wallpaper."""
    return _root() or _xdg("XDG_DATA_HOME", ".local/share")


def planner_config(planner):
    """Path to ``<planner>/config.yaml`` under the config directory."""
    return config_dir() / planner / "config.yaml"


def planner_out(planner):
    """Output directory ``<planner>/out`` under the data directory."""
    return data_dir() / planner / "out"


def display(path):
    """A compact display form: relative to home as ``~/…`` when possible, else absolute."""
    path = Path(path)
    home = Path.home()
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)
