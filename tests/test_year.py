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


def test_lane_span_lone_event_fills_full_width():
    """A pair of same-day events splits only that day; events on other days keep the full width."""
    sixth = {"c0": 5, "c1": 5, "lane": 0}
    thirteenth = {"c0": 12, "c1": 12, "lane": 0}
    twentieth_a = {"c0": 19, "c1": 19, "lane": 0}
    twentieth_b = {"c0": 19, "c1": 19, "lane": 1}
    segs = [sixth, thirteenth, twentieth_a, twentieth_b]
    assert yrender.lane_span(sixth, segs, 2) == 2
    assert yrender.lane_span(thirteenth, segs, 2) == 2
    assert yrender.lane_span(twentieth_a, segs, 2) == 1
    assert yrender.lane_span(twentieth_b, segs, 2) == 1


def test_lane_span_stops_at_next_overlap():
    """Expansion reaches across free lanes but stops at the first overlapping neighbour."""
    seg = {"c0": 0, "c1": 10, "lane": 0}
    gap_lane = {"c0": 0, "c1": 10, "lane": 2}
    segs = [seg, {"c0": 20, "c1": 25, "lane": 1}, gap_lane]
    assert yrender.lane_span(seg, segs, 3) == 2


def test_pack_event_lanes_stable_across_months():
    """Two events that both cross a month boundary keep their lanes instead of swapping sides;
    a later non-overlapping block reuses the freed lane."""
    annual = yrender.Event(layer="l", label="Annual", start=dt.date(2026, 12, 21), end=dt.date(2026, 12, 31))
    yimei = yrender.Event(layer="l", label="Yimei", start=dt.date(2026, 12, 23), end=dt.date(2027, 1, 24))
    jan_annual = yrender.Event(layer="l", label="Annual", start=dt.date(2027, 1, 4), end=dt.date(2027, 1, 14))
    lane_of = yrender.pack_event_lanes([yimei, annual, jan_annual])  # unsorted input
    assert lane_of[id(annual)] == 0
    assert lane_of[id(yimei)] == 1  # overlaps the December block, so a second lane
    assert lane_of[id(jan_annual)] == 0  # no overlap with the December block -> reuses lane 0


def test_assign_month_lanes_compacts_preserving_order():
    """A month missing a lower global lane still packs flush from 0, keeping higher lanes to the right."""
    a, b = (
        yrender.Event("l", "a", dt.date(2027, 1, 1), dt.date(2027, 1, 5)),
        yrender.Event("l", "b", dt.date(2027, 1, 2), dt.date(2027, 1, 9)),
    )
    lane_of = {id(a): 0, id(b): 2}  # global lane 1 belongs to an event not in this month
    segs = [{"ev": b}, {"ev": a}]
    n = yrender.assign_month_lanes(segs, lane_of)
    assert n == 2
    assert next(s["lane"] for s in segs if s["ev"] is a) == 0
    assert next(s["lane"] for s in segs if s["ev"] is b) == 1  # stays right of a


def test_parse_rejects_invalid_range_token():
    """parse() surfaces an invalid range token as a ValueError."""
    with pytest.raises(ValueError):
        yrender.parse({"layers": [], "events": [], "range": {"start": "nonsense"}})


LEGEND_RAW = {
    "range": {"start": "2026-01", "end": "2026-12"},
    "layers": [
        {"id": "work", "label": "Work", "color": "#111", "visible": True},  # drawn
        {"id": "gym", "label": "Gym", "color": "#222", "visible": False},  # hidden
        {"id": "trips", "label": "Trips", "color": "#333", "visible": True},  # empty (visible, no event)
    ],
    "events": [{"layer": "work", "date": dt.date(2026, 3, 2), "label": "Kickoff"}],
}


def test_legend_defaults_to_drawn_layers_only():
    """By default the legend lists only layers with events in range; hidden and empty are dropped."""
    svg = yrender.render_svg(yrender.parse(LEGEND_RAW))
    assert ">Work<" in svg
    assert ">Gym<" not in svg
    assert ">Trips<" not in svg


def test_legend_addons_include_hidden_and_empty():
    """show_legend_empty/show_legend_hidden surface the event-free and toggled-off layers."""
    svg = yrender.render_svg(yrender.parse({**LEGEND_RAW, "show_legend_empty": True, "show_legend_hidden": True}))
    assert ">Work<" in svg and ">Gym<" in svg and ">Trips<" in svg


def test_show_legend_false_omits_the_whole_legend():
    """show_legend=False drops every legend entry (the title still renders)."""
    svg = yrender.render_svg(yrender.parse({**LEGEND_RAW, "show_legend": False, "show_legend_hidden": True}))
    assert ">Work<" not in svg


def test_parse_rejects_non_date_event_field():
    """A mistyped date (YAML keeps `2027-01-3` as a string) is a clear ValueError, not a TypeError."""
    raw = {
        "layers": [{"id": "work", "label": "Work", "color": "#000"}],
        "events": [{"layer": "work", "label": "Trip", "start": dt.date(2027, 1, 10), "end": "2027-01-3"}],
    }
    with pytest.raises(ValueError, match="'Trip': end is not a date"):
        yrender.parse(raw)
