"""Append-only activity log shared by the scheduler and the manual export/wallpaper actions.

Every durable output (not live previews) leaves a trace under ``state/`` so the UI's Log view
and a container's logs agree. A lock keeps concurrent writes from the threading HTTP server
interleaved cleanly.
"""

import datetime as dt
import threading

from timeglance import paths

STATE = paths.state_dir()


class EventLog:
    """A timestamped text log under ``state/activity.log``."""

    def __init__(self):
        """Open (creating as needed) the activity log under ``state/``."""
        STATE.mkdir(parents=True, exist_ok=True)
        self.path = STATE / "activity.log"
        self._lock = threading.Lock()

    def log(self, source, msg):
        """Append a timestamped ``source: msg`` line (thread-safe)."""
        line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {source}: {msg}"
        with self._lock, self.path.open("a") as f:
            f.write(line + "\n")

    def lines(self, n=200):
        """Return the last ``n`` log lines (empty if the log doesn't exist yet)."""
        if not self.path.exists():
            return []
        return self.path.read_text().splitlines()[-n:]

    def clear(self):
        """Empty the activity log."""
        self.path.write_text("")


LOG = EventLog()
