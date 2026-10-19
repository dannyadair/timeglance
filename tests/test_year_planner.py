"""Year control-panel adapter: meta() surfaces the range the way the user wrote it."""

import re

from timeglance.common import wallpaper
from timeglance.planners.year import YearPlanner


def _meta(monkeypatch, tmp_path, raw):
    """Run meta() over a given raw config with no wallpaper backend."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    monkeypatch.setattr(wallpaper, "detect", lambda: None)
    monkeypatch.setattr(YearPlanner, "_raw", lambda self: raw)
    return YearPlanner().meta()


def test_meta_echoes_relative_range_tokens(monkeypatch, tmp_path):
    """Relative tokens (today±N) come back verbatim, not resolved to a fixed month."""
    raw = {"layers": [], "range": {"start": "today-2", "end": "today+10"}}
    assert _meta(monkeypatch, tmp_path, raw)["range"] == {"start": "today-2", "end": "today+10"}


def test_meta_echoes_start_resolves_missing_end(monkeypatch, tmp_path):
    """A given start is echoed; an omitted end falls back to its resolved month."""
    rng = _meta(monkeypatch, tmp_path, {"layers": [], "range": {"start": "year-start"}})["range"]
    assert rng["start"] == "year-start"
    assert re.fullmatch(r"\d{4}-\d{2}", rng["end"])


def test_meta_resolves_span_preset(monkeypatch, tmp_path):
    """A span preset has no explicit tokens, so both ends show the resolved month."""
    rng = _meta(monkeypatch, tmp_path, {"layers": [], "range": {"span": "upcoming_year"}})["range"]
    assert re.fullmatch(r"\d{4}-\d{2}", rng["start"])
    assert re.fullmatch(r"\d{4}-\d{2}", rng["end"])
