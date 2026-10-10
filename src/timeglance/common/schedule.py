"""Daily re-render schedule: its on-disk config plus a trigger-agnostic runner.

The config lives in `schedule.yaml` at the project root (beside `year/` and `weekly/`), so
it sits with the working data and is easy to edit by hand or from the control panel. The
job is to re-render each selected planner and write its file to disk; setting that file as
the desktop wallpaper is an optional extra. `Schedule.run_once` takes the planner registry
and a log as arguments so the panel's timer, a CLI entry point or cron can all drive it
without importing the server.
"""

import traceback
from dataclasses import dataclass
from pathlib import Path

import yaml

from timeglance import paths
from timeglance.common import wallpaper
from timeglance.common.format import human_size

DEFAULTS = {
    "time": "06:00",
    "autostart": False,
    "planners": ["year"],
}

PLANNER_DEFAULTS = {"wallpaper": True, "screens": [], "render": {}}


def parse_render(text):
    """Parse the panel's render-override box (top-level YAML, same shape as a planner's
    config.yaml) into a dict; empty text means no overrides."""
    return yaml.safe_load(text) or {}


def dump_render(block):
    """Serialise a render-override block back to the YAML shown in the panel's box ('' if empty)."""
    return yaml.safe_dump(block, sort_keys=False).strip() if block else ""


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


@dataclass
class Schedule:
    """The schedule and where it lives on disk.

    `cfg` is read once at construction, so build a fresh `Schedule.load()` wherever external
    edits must show up (the control panel reloads per request); a long-lived timer can keep a
    single instance and mutate `cfg` through `save`.
    """

    path: Path
    cfg: dict

    @classmethod
    def load(cls, path=None):
        """Return a Schedule with defaults merged under any `schedule.yaml` on disk."""
        path = path or paths.project_dir() / "schedule.yaml"
        data = yaml.safe_load(path.read_text()) if path.exists() else {}
        return cls(path, {**DEFAULTS, **(data or {})})

    def save(self):
        """Persist `cfg` to `schedule.yaml` in a stable key order (DEFAULTS first, then extras)."""
        ordered = {k: self.cfg[k] for k in DEFAULTS if k in self.cfg}
        ordered.update({k: v for k, v in self.cfg.items() if k not in ordered})
        self.path.write_text(yaml.safe_dump(ordered, sort_keys=False))

    def planner_block(self, name):
        """A planner's schedule block (wallpaper / target screens / render overrides) with defaults."""
        return {**PLANNER_DEFAULTS, **(self.cfg.get(name) or {})}

    def run_once(self, planners, log):
        """Render each selected planner's file to disk and, per its block, set it as the wallpaper.

        Failures - including the SystemExit a bad screen name raises - are isolated per planner so
        one can't sink the rest; every outcome (and traceback) lands in the log."""
        backend = wallpaper.detect()
        for name in self.cfg.get("planners", []):
            planner = planners[name]
            pc = self.planner_block(name)
            params = _params(pc["render"])
            try:
                _, fname, data = planner.export(params)
                planner.out.mkdir(parents=True, exist_ok=True)
                (planner.out / fname).write_bytes(data)
                log.log(name, f"wrote {fname} ({human_size(len(data))})")
                for w in planner.warnings():
                    log.log(name, f"WARNING {w}")
                if not pc["wallpaper"]:
                    continue
                if not backend:
                    log.log(name, "wallpaper skipped (no backend)")
                    continue
                scr = pc["screens"]
                r = planner.set_wallpaper({**params, "screens": ",".join(scr)} if scr else params)
                if not r["ok"]:
                    log.log(name, f"wallpaper FAILED {r['error']}")
                    continue
                detail = "set " + (",".join(r["applied"]) or "nothing matched")
                if r.get("pending"):
                    detail += f"; pending {','.join(r['pending'])}"
                if r.get("unseen"):
                    detail += f"; unseen {','.join(r['unseen'])}"
                log.log(name, f"wallpaper {detail}")
            except (Exception, SystemExit):
                log.log(name, f"ERROR\n{traceback.format_exc().strip()}")
