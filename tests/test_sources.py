"""ICS sources: TTL cache, stale fallback, event mapping, and the full load pipeline."""

import datetime as dt
import os
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError

import icalendar
import pytest

from timeglance.year import sources

URL = "http://example.com/cal.ics"
EXAMPLES = Path(__file__).parent / "examples"


class FakeResponse:
    """A minimal context-manager stand-in for urlopen's response object."""

    def __init__(self, data):
        """Store the bytes this fake response will return from read()."""
        self.data = data

    def __enter__(self):
        """Enter the context, returning self."""
        return self

    def __exit__(self, *exc):
        """Exit the context without suppressing exceptions."""
        return False

    def read(self):
        """Return the canned response bytes."""
        return self.data


@pytest.fixture
def clean_cache(tmp_path, monkeypatch):
    """Point the ICS cache at a temp dir and clear the in-memory cache around each test."""
    monkeypatch.setattr(sources, "CACHE", tmp_path)
    sources._mem.clear()
    yield tmp_path
    sources._mem.clear()


def test_fetch_writes_cache_then_serves_from_memory(clean_cache, monkeypatch):
    """A first fetch writes the disk cache; a second within TTL serves from memory without refetch."""
    calls = {"n": 0}

    def fake_urlopen(url, timeout=0):
        """Count calls and return a canned ICS body."""
        calls["n"] += 1
        return FakeResponse(b"ICS-BODY")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    text, stale = sources._fetch_url(URL, ttl=300)
    assert (text, stale) == ("ICS-BODY", False)
    assert sources._cache_file(URL).exists()

    text2, stale2 = sources._fetch_url(URL, ttl=300)  # memory hit, no refetch
    assert (text2, stale2, calls["n"]) == ("ICS-BODY", False, 1)


def test_fetch_falls_back_to_stale_disk_on_failure(clean_cache, monkeypatch):
    """When a refresh fails but a stale disk copy exists, it's served and flagged stale."""
    cf = sources._cache_file(URL)
    cf.write_text("OLD-BODY", encoding="utf-8")
    old = time.time() - 10_000
    os.utime(cf, (old, old))  # force the TTL to be considered expired

    def boom(url, timeout=0):
        """Simulate a network failure."""
        raise URLError("network down")

    monkeypatch.setattr(urllib.request, "urlopen", boom)

    text, stale = sources._fetch_url(URL, ttl=300)
    assert (text, stale) == ("OLD-BODY", True)


def test_fetch_raises_when_no_cache(clean_cache, monkeypatch):
    """A fetch failure with no cached copy re-raises the error."""

    def boom(url, timeout=0):
        """Simulate a network failure."""
        raise URLError("network down")

    monkeypatch.setattr(urllib.request, "urlopen", boom)

    with pytest.raises(URLError):
        sources._fetch_url("http://example.com/missing.ics", ttl=300)


def _event(summary, start, end):
    """Build an icalendar VEVENT with the given summary and start/end."""
    ev = icalendar.Event()
    ev.add("SUMMARY", summary)
    ev.add("DTSTART", start)
    ev.add("DTEND", end)
    return ev


def test_to_event_all_day_end_is_inclusive():
    """A multi-day all-day event's exclusive DTEND becomes an inclusive end date."""
    out = sources._to_event(_event("Trip", dt.date(2026, 1, 10), dt.date(2026, 1, 13)), "work", "ics:test")
    assert out == {
        "layer": "work",
        "label": "Trip",
        "source": "ics:test",
        "start": dt.date(2026, 1, 10),
        "end": dt.date(2026, 1, 12),
    }


def test_to_event_single_all_day():
    """A one-day all-day event collapses to a single ``date`` with no span."""
    out = sources._to_event(_event("Note", dt.date(2026, 2, 1), dt.date(2026, 2, 2)), "work", "ics:test")
    assert out["date"] == dt.date(2026, 2, 1) and "start" not in out


def test_to_event_timed():
    """A timed event maps to its start date."""
    out = sources._to_event(_event("Call", dt.datetime(2026, 3, 1, 9), dt.datetime(2026, 3, 1, 10)), "work", "ics:test")
    assert out["date"] == dt.date(2026, 3, 1)


def test_load_bundled_ics(tmp_path, monkeypatch):
    """load() reads a local ICS file and appends its events with no errors."""
    monkeypatch.setattr(sources, "CACHE", tmp_path)
    raw = {
        "layers": [{"id": "work", "label": "Work", "color": "#000", "visible": True}],
        "events": [],
        "range": {"start": "2026-01", "end": "2026-12"},
        "sources": [{"path": str(EXAMPLES / "sample.ics"), "layer": "work"}],
    }
    summary = sources.load(raw)
    assert summary[0]["count"] == 2
    assert len(raw["events"]) == 2
    assert not summary[0].get("error")
