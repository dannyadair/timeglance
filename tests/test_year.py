"""Year planner pure logic: range-token resolution, recurrence expansion, geometry."""

import datetime as dt

import pytest

from timeglance.year import render as yrender
from timeglance.year.render import _month_add, _occurrences, _resolve_ym, resolve_range

TODAY = dt.date(2026, 7, 15)


@pytest.mark.parametrize(
    "token,expected",
    [
        ("today", (2026, 7)),
        ("now", (2026, 7)),
        ("year-start", (2026, 1)),
        ("year-end", (2026, 12)),
        ("today+3", (2026, 10)),
        ("today-8", (2025, 11)),
        ("2027-03", (2027, 3)),
        ("2028", (2028, 1)),
    ],
)
def test_resolve_ym_tokens(token, expected):
    """Each range token resolves to the expected (year, month)."""
    assert _resolve_ym(token, TODAY) == expected


@pytest.mark.parametrize("bad", ["garbage", "2026-13", "2026-00", "-"])
def test_resolve_ym_invalid_raises(bad):
    """Malformed range tokens raise ValueError."""
    with pytest.raises(ValueError):
        _resolve_ym(bad, TODAY)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ({"range": {"span": "this_year"}}, ((2026, 1), (2026, 12))),
        ({"range": {"span": "upcoming_year"}}, ((2026, 7), (2027, 6))),
        ({"range": {"span": "custom", "before": 2, "after": 3}}, ((2026, 5), (2026, 10))),
        ({"range": {"start": "2026-03", "end": "2026-08"}}, ((2026, 3), (2026, 8))),
        ({"range": {"start": "today"}}, ((2026, 7), (2026, 12))),  # end defaults to year-end
        ({"year": 2030}, ((2030, 1), (2030, 12))),
        ({}, ((2026, 7), (2027, 6))),  # default rolling 12 months
    ],
)
def test_resolve_range(raw, expected):
    """Span presets, explicit start/end, bare year and the empty default each resolve correctly."""
    assert resolve_range(raw, TODAY) == expected


def test_resolve_range_clamps_reversed():
    """A reversed start/end collapses to a single month rather than an inverted range."""
    assert resolve_range({"range": {"start": "2026-08", "end": "2026-03"}}, TODAY) == ((2026, 8), (2026, 8))


# ---- recurrence expansion ----

WS, WE = dt.date(2026, 1, 1), dt.date(2026, 12, 31)
YEARS = [2026]


def test_occurrence_single():
    """A non-recurring event yields exactly its own date."""
    assert _occurrences({}, dt.date(2026, 3, 10), WS, WE, YEARS) == [dt.date(2026, 3, 10)]


def test_occurrence_yearly_projects_into_range():
    """A yearly repeat projects its month/day onto the window's year."""
    assert _occurrences({"repeat": "yearly"}, dt.date(1990, 6, 1), WS, WE, YEARS) == [dt.date(2026, 6, 1)]


def test_occurrence_yearly_leap_day_clamps():
    """A yearly Feb-29 repeat clamps to Feb-28 in a non-leap year."""
    assert _occurrences({"repeat": "yearly"}, dt.date(2000, 2, 29), WS, WE, YEARS) == [dt.date(2026, 2, 28)]


def test_occurrence_monthly():
    """A monthly repeat yields one occurrence per month on the same day."""
    occ = _occurrences({"repeat": "monthly"}, dt.date(2026, 1, 15), WS, WE, YEARS)
    assert len(occ) == 12
    assert all(d.day == 15 for d in occ)


def test_occurrence_weekly_all_same_weekday():
    """A weekly repeat yields occurrences all falling on the start weekday."""
    occ = _occurrences({"repeat": "weekly"}, dt.date(2026, 1, 5), WS, WE, YEARS)  # a Monday
    assert len(occ) > 50
    assert all(d.weekday() == 0 for d in occ)


def test_occurrence_rrule():
    """An explicit RRULE expands to the dates it describes."""
    occ = _occurrences({"rrule": "FREQ=WEEKLY;BYDAY=MO"}, dt.date(2026, 1, 1), WS, WE, YEARS)
    assert occ and all(d.weekday() == 0 for d in occ)


# ---- geometry ----


def test_month_add_wraps_years():
    """Month arithmetic wraps across year boundaries in both directions."""
    assert _month_add(2026, 11, 3) == (2027, 2)
    assert _month_add(2026, 2, -4) == (2025, 10)


def test_day_slots_packed_is_31():
    """A packed (non-week-aligned) layout always uses 31 day slots."""
    cfg = yrender.parse({"layers": [], "events": [], "week_align": False})
    assert yrender.day_slots(cfg) == 31


def test_parse_rejects_invalid_range_token():
    """parse() surfaces an invalid range token as a ValueError."""
    with pytest.raises(ValueError):
        yrender.parse({"layers": [], "events": [], "range": {"start": "nonsense"}})
