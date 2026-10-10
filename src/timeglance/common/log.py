"""Append-only activity log: what timeglance does, in one place.

Server startup, config scaffolding and edits, and every durable output (renders, exports,
wallpaper changes - scheduled or manual, but not live previews) leave a trace under ``state/``.
A lock keeps concurrent writes from the threading HTTP server interleaved cleanly.
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
        """Append a timestamped ``source: msg`` line (thread-safe) and echo it to stdout.

        The file backs the UI's Log view; the stdout echo lands in the terminal now and in
        journald once the systemd service runs it, so every surface agrees."""
        line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {source}: {msg}"
        with self._lock:
            with self.path.open("a") as f:
                f.write(line + "\n")
            print(line, flush=True)

    def lines(self, n=200):
        """Return the last ``n`` log lines (empty if the log doesn't exist yet)."""
        if not self.path.exists():
            return []
        return self.path.read_text().splitlines()[-n:]

    def clear(self):
        """Empty the activity log."""
        self.path.write_text("")


LOG = EventLog()
