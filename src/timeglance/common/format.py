"""Small presentation helpers shared across the app (byte sizes, local timezone)."""

import datetime as dt


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
