"""``timeglance install``: a systemd user timer for the nightly render.

Writes a oneshot ``timeglance.service`` (runs ``timeglance run``, honouring ``schedule.yaml``)
and a ``timeglance.timer`` (nightly, ``Persistent=true`` so a run missed while the machine was
off catches up) into the user unit directory, then enables the timer. ``uninstall`` reverses it.

Setting the Plasma wallpaper needs an active graphical session, so a run while you're fully
logged out renders the files but can't paint; ``Persistent=true`` repaints on the next session.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from timeglance.common import schedule

SERVICE = "timeglance.service"
TIMER = "timeglance.timer"


def _unit_dir():
    """The systemd user unit directory, honouring ``XDG_CONFIG_HOME``."""
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "systemd" / "user"


def _exec_start():
    """The command the service runs: the installed console script, or the module fallback."""
    exe = shutil.which("timeglance")
    return f"{exe} run" if exe else f"{sys.executable} -m timeglance.cli run"


def _service_unit():
    """The oneshot service that renders the scheduled planners."""
    return (
        "[Unit]\n"
        "Description=timeglance nightly render\n"
        "Documentation=https://github.com/dannyadair/timeglance\n\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"ExecStart={_exec_start()}\n"
    )


def _timer_unit(time):
    """The nightly timer firing at ``HH:MM``, catching up a missed run on next boot."""
    hh, mm = (int(x) for x in time.split(":"))
    return (
        "[Unit]\n"
        "Description=timeglance nightly render timer\n\n"
        "[Timer]\n"
        f"OnCalendar=*-*-* {hh:02d}:{mm:02d}:00\n"
        "Persistent=true\n\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


def _systemctl(*args, check=True):
    """Run ``systemctl --user`` with the given arguments."""
    subprocess.run(["systemctl", "--user", *args], check=check)


def install(time=None):
    """Write the service+timer units and enable the timer (time defaults to schedule.yaml's)."""
    if not shutil.which("systemctl"):
        raise SystemExit("systemctl not found - a systemd user instance is required")
    time = time or schedule.Schedule.load().cfg["time"]
    unit_dir = _unit_dir()
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / SERVICE).write_text(_service_unit())
    (unit_dir / TIMER).write_text(_timer_unit(time))
    _systemctl("daemon-reload")
    _systemctl("enable", "--now", TIMER)
    print(f"installed {TIMER} (nightly at {time})")
    print(f"  units written to {unit_dir}")
    print(f"  next run: systemctl --user list-timers {TIMER}")


def enabled():
    """True if the user timer is enabled."""
    if not shutil.which("systemctl"):
        return False
    r = subprocess.run(["systemctl", "--user", "is-enabled", TIMER], capture_output=True, text=True, check=False)
    return r.stdout.strip() == "enabled"


def enable():
    """Enable and start the timer, installing the units first if they're missing."""
    if (_unit_dir() / TIMER).exists():
        _systemctl("enable", "--now", TIMER)
    else:
        install()


def disable():
    """Stop and disable the timer, leaving the unit files in place."""
    _systemctl("disable", "--now", TIMER, check=False)


def uninstall():
    """Disable the timer and remove the unit files."""
    if not shutil.which("systemctl"):
        raise SystemExit("systemctl not found - a systemd user instance is required")
    _systemctl("disable", "--now", TIMER, check=False)
    unit_dir = _unit_dir()
    for name in (SERVICE, TIMER):
        (unit_dir / name).unlink(missing_ok=True)
    _systemctl("daemon-reload")
    print(f"removed {TIMER} and {SERVICE}")
