"""Load events from external iCalendar (.ics) sources: URLs and local files.

Each source in `sources:` maps to a layer (an existing `layers:` id, or one created
inline from `label`/`color`). Recurrences, EXDATEs and all-day/timed spans are expanded
within the render window by recurring_ical_events. Fetched URLs are cached in memory and
on disk (state/ics-cache) with a TTL, so repeated renders don't refetch and a failed
refresh falls back to the last good copy.
"""

import calendar
import datetime as dt
import hashlib
import time
import urllib.request
from pathlib import Path

import icalendar
import recurring_ical_events

from timeglance import paths
from timeglance.year import render

DEFAULT_TTL = 300  # seconds; override per source with `refresh:`
PALETTE = ["#3FA7A0", "#9B6B9E", "#E4884A", "#4E9A51", "#C4553B", "#3D6FB4", "#7A7F87"]

CACHE = paths.state_dir() / "ics-cache"
_mem = {}  # url -> (fetched_at, text)


def _cache_file(url):
    """On-disk cache path for a URL, keyed by its SHA-256."""
    return CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".ics")


def _fetch_url(url, ttl):
    """Return (text, stale). Memory + on-disk TTL cache; on a failed refresh, fall back
    to the last good copy on disk (stale=True) so a network blip doesn't drop the feed."""
    now = time.time()
    hit = _mem.get(url)
    if hit and now - hit[0] < ttl:
        return hit[1], False
    cf = _cache_file(url)
    if cf.exists() and now - cf.stat().st_mtime < ttl:
        text = cf.read_text(encoding="utf-8")
        _mem[url] = (cf.stat().st_mtime, text)
        return text, False
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception:
        if cf.exists():
            return cf.read_text(encoding="utf-8"), True
        raise
    CACHE.mkdir(parents=True, exist_ok=True)
    cf.write_text(text, encoding="utf-8")
    _mem[url] = (now, text)
    return text, False


def _read(src):
    """Read a source's ICS text, returning ``(text, origin, stale)`` for a URL or local path."""
    if "url" in src:
        text, stale = _fetch_url(src["url"], src.get("refresh", DEFAULT_TTL))
        return text, src["url"], stale
    path = Path(src["path"]).expanduser()
    return path.read_text(encoding="utf-8"), str(path), False


def _ensure_layer(raw, src, cal_name):
    """Return the source's layer id, appending an inline layer to ``raw`` if it doesn't exist yet."""
    existing = {lyr["id"] for lyr in raw["layers"]}
    lid = src.get("layer") or _slug(cal_name or "calendar")
    if lid not in existing:
        raw["layers"].append(
            {
                "id": lid,
                "label": src.get("label") or cal_name or lid,
                "color": src.get("color") or PALETTE[len(raw["layers"]) % len(PALETTE)],
                "visible": True,
            }
        )
    return lid


def _slug(name):
    """Slugify a calendar name into a layer id (lowercase, non-alphanumerics to hyphens)."""
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-") or "calendar"


def _to_event(comp, layer, provenance):
    """Convert an ICS component to an event dict, making all-day DTEND inclusive."""
    start = comp["DTSTART"].dt
    end_prop = comp.get("DTEND")
    end = end_prop.dt if end_prop is not None else start

    if isinstance(start, dt.datetime):  # timed event
        sd, ed = start.date(), (end.date() if isinstance(end, dt.datetime) else end)
    else:  # all-day: DTEND is exclusive
        sd, ed = start, end - dt.timedelta(days=1)
    ed = max(ed, sd)

    label = str(comp.get("SUMMARY", "")).strip() or "(untitled)"
    ev = {"layer": layer, "label": label, "source": provenance}
    if ed == sd:
        ev["date"] = sd
    else:
        ev["start"], ev["end"] = sd, ed
    return ev


def load(raw):
    """Append ICS events (and any inline layers) to `raw`. Returns a provenance summary."""
    srcs = raw.get("sources") or []
    if not srcs:
        return []

    start_ym, end_ym = render.resolve_range(raw, dt.date.today())
    ws = dt.date(*start_ym, 1)
    we = dt.date(end_ym[0], end_ym[1], calendar.monthrange(*end_ym)[1])

    summary = []
    for src in srcs:
        kind = "url" if "url" in src else "file"
        origin = src.get("url") or str(Path(src.get("path", "")).expanduser())
        label = src.get("label") or Path(origin).name
        try:
            text, origin, stale = _read(src)
            cal = icalendar.Calendar.from_ical(text)
            cal_name = str(cal.get("X-WR-CALNAME", "")).strip()
            layer = _ensure_layer(raw, src, cal_name)
            label = src.get("label") or cal_name or Path(origin).name
            events = recurring_ical_events.of(cal).between(ws, we + dt.timedelta(days=1))
            for comp in events:
                raw["events"].append(_to_event(comp, layer, f"ics:{label}"))
            entry = {"kind": kind, "label": label, "layer": layer, "count": len(events), "origin": origin}
            if stale:
                entry["error"] = "refresh failed - showing cached copy"
            summary.append(entry)
        except Exception as e:
            summary.append(
                {
                    "kind": kind,
                    "label": label,
                    "layer": src.get("layer"),
                    "count": 0,
                    "origin": origin,
                    "error": f"{type(e).__name__}: {e}",
                }
            )
    return summary
