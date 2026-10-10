"""Daily re-render schedule: its on-disk config plus a trigger-agnostic runner.

The config lives in `schedule.yaml` at the project root (beside `year/` and `weekly/`), so
it sits with the working data and is easy to edit by hand or from the control panel. The
job is to re-render each selected planner and write its file to disk; setting that file as
the desktop wallpaper is an optional extra. `run_once` takes the planner registry and a log
as arguments so the panel's timer, a CLI entry point or cron can all drive it without
importing the server.
"""

import datetime as dt
import traceback

import yaml

from timeglance import paths
from timeglance.common import wallpaper

DEFAULTS = {
    "time": "06:00",
    "autostart": False,
    "wallpaper": True,
    "planners": ["year"],
    "screens": {},
    "render": {},
}


def path():
    """Path to `schedule.yaml` under the project root."""
    return paths.project_dir() / "schedule.yaml"


def load():
    """Return the schedule config, defaults merged under any `schedule.yaml` on disk."""
    p = path()
    data = yaml.safe_load(p.read_text()) if p.exists() else {}
    return {**DEFAULTS, **(data or {})}


def save(cfg):
    """Persist the schedule config to `schedule.yaml` in a stable key order."""
    ordered = {k: cfg[k] for k in DEFAULTS if k in cfg}
    ordered.update({k: v for k, v in cfg.items() if k not in ordered})
    path().write_text(yaml.safe_dump(ordered, sort_keys=False))


def human_size(n):
    """Format a byte count as a human-readable KB/MB string."""
    kb = n / 1024
    return f"{kb:.0f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB"


def local_tz():
    """Describe the machine's local timezone (abbreviation + UTC offset) the schedule runs in."""
    now = dt.datetime.now().astimezone()
    minutes = int(now.utcoffset().total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    hh, mm = divmod(abs(minutes), 60)
    return f"{now.tzname()} (UTC{sign}{hh}" + (f":{mm:02d})" if mm else ")")


def _params(block):
    """Translate a YAML render-override block into the control panel's string params."""
    out = {}
    for key, value in block.items():
        if isinstance(value, list):
            out[key] = ",".join(map(str, value))
        elif isinstance(value, bool):
            out[key] = "true" if value else "false"
        else:
            out[key] = str(value)
    return out


def run_once(cfg, planners, log):
    """Render each selected planner's file to disk and, if enabled, set it as the wallpaper.

    Failures - including the SystemExit a bad screen name raises - are isolated per planner so
    one can't sink the rest; every outcome (and traceback) lands in the log."""
    render = cfg.get("render", {})
    screens = cfg.get("screens", {})
    set_wallpaper = cfg.get("wallpaper", True)
    backend = wallpaper.detect()
    for name in cfg.get("planners", []):
        planner = planners[name]
        params = _params(render.get(name) or {})
        try:
            _, fname, data = planner.export(params)
            planner.out.mkdir(parents=True, exist_ok=True)
            (planner.out / fname).write_bytes(data)
            log.log(name, f"wrote {fname} ({human_size(len(data))})")
            for w in planner.warnings():
                log.log(name, f"WARNING {w}")
            if not set_wallpaper:
                continue
            if not backend:
                log.log(name, "wallpaper skipped (no backend)")
                continue
            scr = screens.get(name)
            r = planner.set_wallpaper({**params, "screens": ",".join(scr)} if scr else params)
            log.log(name, "wallpaper " + ("set " + ",".join(r["applied"]) if r["ok"] else "FAILED " + r["error"]))
        except (Exception, SystemExit):
            log.log(name, f"ERROR\n{traceback.format_exc().strip()}")
