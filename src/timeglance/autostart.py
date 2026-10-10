"""The tray's "Autostart": an XDG autostart entry that launches ``timeglance tray`` at login.
Plasma and other XDG desktops read ``~/.config/autostart/`` at session start. This is the tray
launcher only - the scheduled render is the systemd timer from ``timeglance install``.
"""

import os
import shutil
import sys
from pathlib import Path

DESKTOP = "timeglance-tray.desktop"


def _path():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "autostart" / DESKTOP


def _exec():
    """The command the autostart entry runs: the installed console script, or the module fallback."""
    exe = shutil.which("timeglance")
    return f"{exe} tray" if exe else f"{sys.executable} -m timeglance.cli tray"


def enabled():
    """True if the autostart entry is in place."""
    return _path().exists()


def enable():
    """Write the autostart entry so the tray launches at login."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=timeglance tray\n"
        f"Exec={_exec()}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def disable():
    """Remove the autostart entry."""
    _path().unlink(missing_ok=True)
