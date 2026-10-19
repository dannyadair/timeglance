"""Weekly sheet: visibility resolution, layout math, and the today highlight."""

from argparse import Namespace

from timeglance.weekly import build as wbuild

CFG = {
    "topics": {
        "a": {"label": "A", "color": "#111", "visible": True},
        "b": {"label": "B", "color": "#222", "visible": False},
        "c": {"label": "C", "color": "#333", "visible": True},
    },
    "activities": [
        {"topic": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"},
        {"topic": "b", "days": ["Mon"], "start": "10:00", "end": "11:00"},
    ],
}


def test_to_min_and_fmt_roundtrip():
    """to_min and fmt are inverses across HH:MM / minute values."""
    assert wbuild.to_min("06:30") == 390
    assert wbuild.fmt(390) == "06:30"
    assert wbuild.fmt(0) == "00:00"


def test_fmt_hours_strips_trailing_zero():
    """fmt_hours renders whole and fractional hours without trailing zeros."""
    assert wbuild.fmt_hours(2400) == "40h"
    assert wbuild.fmt_hours(90) == "1.5h"
    assert wbuild.fmt_hours(185) == "3.1h"


def test_layout_legend_totals_hours_across_days():
    """The legend sums a topic's hours across every day it appears on."""
    cfg = {
        "days": ["Mon", "Tue", "Wed"],
        "day_start": "08:00",
        "day_end": "18:00",
        "topics": {"a": {"label": "A", "color": "#111", "visible": True}},
        "activities": [{"topic": "a", "days": ["Mon", "Tue", "Wed"], "start": "09:00", "end": "11:00"}],
    }
    _, _, legend = wbuild.positions(cfg, wbuild.visible_activities(cfg, set()))
    assert legend == [{"label": "A", "color": "#111", "hours": "6h", "muted": False}]  # 2h × 3 days


def test_legend_follows_topics_order_not_activity_order():
    """The legend follows topic declaration order and omits unused topics."""
    cfg = {
        "days": ["Mon"],
        "day_start": "08:00",
        "day_end": "18:00",
        "topics": {
            "x": {"label": "X", "color": "#111", "visible": True},
            "y": {"label": "Y", "color": "#222", "visible": True},
            "z": {"label": "Z", "color": "#333", "visible": True},  # declared but never used
        },
        "activities": [
            {"topic": "y", "days": ["Mon"], "start": "09:00", "end": "10:00"},
            {"topic": "x", "days": ["Mon"], "start": "11:00", "end": "12:00"},
        ],
    }
    _, _, legend = wbuild.positions(cfg, wbuild.visible_activities(cfg, set()))
    assert [item["label"] for item in legend] == ["X", "Y"]  # declaration order, unused z omitted


LEGEND_CFG = {
    "title": "T",
    "days": ["Mon"],
    "day_start": "08:00",
    "day_end": "18:00",
    "topics": {
        "a": {"label": "A", "color": "#111", "visible": True},  # drawn (visible, has activity)
        "b": {"label": "B", "color": "#222", "visible": False},  # hidden (toggled off)
        "c": {"label": "C", "color": "#333", "visible": True},  # empty (visible, no activity)
    },
    "activities": [
        {"topic": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"},
        {"topic": "b", "days": ["Mon"], "start": "10:00", "end": "11:00"},
    ],
}


def _legend(**kw):
    """Legend entries for LEGEND_CFG with the given show_* flags."""
    acts = wbuild.visible_activities(LEGEND_CFG, wbuild.hidden_topics(LEGEND_CFG, None))
    return wbuild.positions(LEGEND_CFG, acts, **kw)[2]


def test_legend_defaults_to_drawn_topics_only():
    """Without the add-ons the legend lists only the topics actually on the sheet."""
    assert [(i["label"], i["muted"]) for i in _legend()] == [("A", False)]


def test_legend_show_empty_adds_eventfree_topics_greyed():
    """show_legend_empty appends visible-but-unused topics, greyed and without hours."""
    assert [(i["label"], i["muted"], i["hours"]) for i in _legend(show_legend_empty=True)] == [
        ("A", False, "1h"),
        ("C", True, ""),
    ]


def test_legend_show_hidden_adds_toggled_off_topics_greyed():
    """show_legend_hidden appends topics turned off via visible:false, greyed."""
    assert [(i["label"], i["muted"]) for i in _legend(show_legend_hidden=True)] == [("A", False), ("B", True)]


def test_render_show_legend_false_drops_all_legend_entries():
    """show_legend=False renders the sheet with no legend items."""
    html = wbuild.render(LEGEND_CFG, None, "A4", show_legend=False)
    assert 'class="item' not in html


def test_pack_day_lanes_non_overlapping_keep_full_width():
    """Activities that never clash in time each span the full day width."""
    cells = [{"start": 420, "end": 480}, {"start": 540, "end": 1020}]  # 07-08, 09-17
    wbuild.pack_day_lanes(cells)
    assert all(c["lane_pos"] == 0 and c["lane_size"] == 100 for c in cells)


def test_pack_day_lanes_splits_only_the_overlap():
    """A background block shares width with an overlapping meeting; an unrelated block stays full."""
    gym = {"start": 420, "end": 480}  # 07:00-08:00, no clash
    work = {"start": 540, "end": 1020}  # 09:00-17:00
    meeting = {"start": 600, "end": 660}  # 10:00-11:00, overlaps work
    cells = sorted([gym, work, meeting], key=lambda c: c["start"])
    wbuild.pack_day_lanes(cells)
    assert gym["lane_pos"] == 0 and gym["lane_size"] == 100  # lone -> full width
    assert work["lane_pos"] == 0 and work["lane_size"] == 50  # shares with the meeting
    assert meeting["lane_pos"] == 50 and meeting["lane_size"] == 50


def test_render_blocks_avoid_calc():
    """Blocks must not use `calc()` mixing % and px - WeasyPrint < 63 (Ubuntu 25.10 ships 62.3)
    can't resolve it and collapses the block to its text width."""
    cfg = {
        "title": "T",
        "days": ["Mon"],
        "day_start": "08:00",
        "day_end": "18:00",
        "topics": {"a": {"label": "A", "color": "#111", "visible": True}},
        "activities": [{"topic": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"}],
    }
    for layout in wbuild.ALL_LAYOUTS:
        assert "calc(" not in wbuild.render(cfg, None, "A4", layout=layout)


def test_hidden_topics_from_yaml_defaults():
    """With no explicit hide list, topics marked not-visible in YAML are hidden."""
    assert wbuild.hidden_topics(CFG, None) == {"b"}


def test_hidden_topics_explicit_overrides_defaults():
    """An explicit hide list replaces the YAML visibility defaults."""
    assert wbuild.hidden_topics(CFG, ["a"]) == {"a"}


def test_visible_activities_filters_hidden():
    """visible_activities drops activities whose topic is hidden."""
    activities = wbuild.visible_activities(CFG, {"b"})
    assert [a["topic"] for a in activities] == ["a"]


def test_resolve_hide_defaults_to_yaml_visibility():
    """With no CLI flags, resolve_hide falls back to the YAML visibility defaults."""
    args = Namespace(only=None, hide=[])
    assert wbuild.resolve_hide(CFG, args) == {"b"}


def test_resolve_hide_only_keeps_listed():
    """``--only`` hides everything except the listed topics."""
    args = Namespace(only="a", hide=[])
    assert wbuild.resolve_hide(CFG, args) == {"b", "c"}


def test_resolve_hide_combines_defaults_and_flag():
    """``--hide`` adds to the YAML visibility defaults."""
    args = Namespace(only=None, hide=["c"])
    assert wbuild.resolve_hide(CFG, args) == {"b", "c"}


def test_render_highlights_today_only_when_in_days():
    """The today column is highlighted only when today's weekday is in the sheet's days."""
    cfg = {
        "title": "T",
        "days": ["Mon", "Tue", "Wed"],
        "day_start": "08:00",
        "day_end": "18:00",
        "topics": {"a": {"label": "A", "color": "#111", "visible": True}},
        "activities": [{"topic": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"}],
    }
    assert 'class="lane today"' in wbuild.render(cfg, None, "A4", today="Tue")
    assert 'class="lane today"' not in wbuild.render(cfg, None, "A4", today="Sun")


def test_render_applies_theme_and_layout():
    """Theme feeds the CSS palette and layout flips the sheet between day-columns and day-rows."""
    cfg = {
        "title": "T",
        "days": ["Mon", "Tue"],
        "day_start": "08:00",
        "day_end": "18:00",
        "topics": {"a": {"label": "A", "color": "#111", "visible": True}},
        "activities": [{"topic": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"}],
    }
    dark = wbuild.render(cfg, None, "A4", theme="dark", layout="horizontal")
    assert wbuild.WEEKLY_THEMES["dark"]["bg"] in dark
    assert "time running left to right" in dark

    light = wbuild.render(cfg, None, "A4", theme="light", layout="vertical")
    assert wbuild.WEEKLY_THEMES["light"]["bg"] in light
    assert "time running top to bottom" in light

    for layout in wbuild.ALL_LAYOUTS:
        for theme in wbuild.ALL_THEMES:
            assert wbuild.render_pdf(cfg, None, "A4", theme=theme, layout=layout)
