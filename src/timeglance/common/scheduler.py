"""The daily re-render timer that drives a ``Schedule``.

Sleeps until the configured HH:MM and renders the selected planners to disk (optionally
setting the wallpaper), delegating the actual run to ``Schedule.run_once``. Runs feed the
shared activity log; config lives in ``schedule.yaml`` so a container restart keeps it.
"""

import datetime as dt
import threading

from timeglance.common import schedule, wallpaper
from timeglance.common.format import local_tz
from timeglance.common.log import LOG
from timeglance.planners import PLANNERS, output_path


class Scheduler:
    """A background loop around a ``Schedule``: start/stop, run-now, and status for the UI."""

    def __init__(self):
        """Load the schedule from ``schedule.yaml`` and set up the (stopped) loop."""
        self.schedule = schedule.Schedule.load()
        self._thread = None
        self._stop = threading.Event()
        self.last_run = None
        self.next_run = None

    def save_cfg(self, cfg):
        """Merge updates into the schedule config (deep-merging per-planner blocks so a partial
        update keeps the rest, e.g. render overrides) and persist it to ``schedule.yaml``."""
        current = self.schedule.cfg
        merged = {**current, **cfg}
        for name in PLANNERS:
            if name in cfg:
                merged[name] = {**(current.get(name) or {}), **cfg[name]}
        self.schedule.cfg = merged
        self.schedule.save()

    def run_once(self):
        """Render the selected planners now (see ``Schedule.run_once``)."""
        self.last_run = dt.datetime.now().isoformat(timespec="seconds")
        self.schedule.run_once(PLANNERS, LOG)

    def _loop(self):
        """Background loop: sleep until the configured time, run once, repeat until stopped."""
        LOG.log("scheduler", "started")
        while not self._stop.is_set():
            hh, mm = (int(x) for x in self.schedule.cfg["time"].split(":"))
            now = dt.datetime.now()
            nxt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if nxt <= now:
                nxt += dt.timedelta(days=1)
            self.next_run = nxt.isoformat(timespec="seconds")
            if self._stop.wait((nxt - now).total_seconds()):
                break
            self.run_once()
        self.next_run = None
        LOG.log("scheduler", "stopped")

    @property
    def running(self):
        """True while the background loop thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """Start the background scheduler loop (no-op if already running)."""
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the background loop to stop."""
        self._stop.set()

    def status(self):
        """Return the scheduler's current state and config for the UI."""
        config = {}
        for name in PLANNERS:
            pc = self.schedule.planner_block(name)
            pc["render_yaml"] = schedule.dump_render(pc["render"])
            config[name] = pc
        return {
            "running": self.running,
            "time": self.schedule.cfg["time"],
            "tz": local_tz(),
            "planners": self.schedule.cfg.get("planners", []),
            "config": config,
            "outputs": {name: output_path(p) for name, p in PLANNERS.items()},
            "screens": wallpaper.known(wallpaper.detect()),
            "last_run": self.last_run,
            "next_run": self.next_run,
        }


SCHED = Scheduler()
