"""Small user settings that aren't a planner config or the schedule - currently just the
control-panel port, so the tray and ``timeglance serve`` agree on where the panel lives.
"""

import yaml

from timeglance import paths

DEFAULT_PORT = 8753


def _path():
    return paths.config_dir() / "settings.yaml"


def load():
    """The settings dict from disk (empty if there's no settings.yaml yet)."""
    path = _path()
    return yaml.safe_load(path.read_text()) or {} if path.exists() else {}


def get_port():
    """The control-panel port."""
    return load().get("port", DEFAULT_PORT)


def set_port(port):
    """Persist the control-panel port."""
    data = load()
    data["port"] = port
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
