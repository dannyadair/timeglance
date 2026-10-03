"""Weekly sheet: visibility resolution, layout math, and the today highlight."""

from argparse import Namespace

from timeglance.weekly import build as wbuild

CFG = {
    "activities": {
        "a": {"label": "A", "color": "#111", "visible": True},
        "b": {"label": "B", "color": "#222", "visible": False},
        "c": {"label": "C", "color": "#333", "visible": True},
    },
    "blocks": [
        {"activity": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"},
        {"activity": "b", "days": ["Mon"], "start": "10:00", "end": "11:00"},
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
    """The legend sums an activity's hours across every day it appears on."""
    cfg = {
        "days": ["Mon", "Tue", "Wed"],
        "day_start": "08:00",
        "day_end": "18:00",
        "activities": {"a": {"label": "A", "color": "#111", "visible": True}},
        "blocks": [{"activity": "a", "days": ["Mon", "Tue", "Wed"], "start": "09:00", "end": "11:00"}],
    }
    _, _, legend = wbuild.layout(cfg, wbuild.visible_blocks(cfg, set()))
    assert legend == [{"label": "A", "color": "#111", "hours": "6h"}]  # 2h × 3 days


def test_legend_follows_activities_order_not_block_order():
    """The legend follows activity declaration order and omits unused activities."""
    cfg = {
        "days": ["Mon"],
        "day_start": "08:00",
        "day_end": "18:00",
        "activities": {
            "x": {"label": "X", "color": "#111", "visible": True},
            "y": {"label": "Y", "color": "#222", "visible": True},
            "z": {"label": "Z", "color": "#333", "visible": True},  # declared but never used
        },
        "blocks": [
            {"activity": "y", "days": ["Mon"], "start": "09:00", "end": "10:00"},
            {"activity": "x", "days": ["Mon"], "start": "11:00", "end": "12:00"},
        ],
    }
    _, _, legend = wbuild.layout(cfg, wbuild.visible_blocks(cfg, set()))
    assert [item["label"] for item in legend] == ["X", "Y"]  # declaration order, unused z omitted


def test_hidden_activities_from_yaml_defaults():
    """With no explicit hide list, activities marked not-visible in YAML are hidden."""
    assert wbuild.hidden_activities(CFG, None) == {"b"}


def test_hidden_activities_explicit_overrides_defaults():
    """An explicit hide list replaces the YAML visibility defaults."""
    assert wbuild.hidden_activities(CFG, ["a"]) == {"a"}


def test_visible_blocks_filters_hidden():
    """visible_blocks drops blocks whose activity is hidden."""
    blocks = wbuild.visible_blocks(CFG, {"b"})
    assert [b["activity"] for b in blocks] == ["a"]


def test_resolve_hide_defaults_to_yaml_visibility():
    """With no CLI flags, resolve_hide falls back to the YAML visibility defaults."""
    args = Namespace(only=None, hide=[])
    assert wbuild.resolve_hide(CFG, args) == {"b"}


def test_resolve_hide_only_keeps_listed():
    """``--only`` hides everything except the listed activities."""
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
        "activities": {"a": {"label": "A", "color": "#111", "visible": True}},
        "blocks": [{"activity": "a", "days": ["Mon"], "start": "09:00", "end": "10:00"}],
    }
    assert 'class="col today"' in wbuild.render(cfg, None, "A4", today="Tue")
    assert 'class="col today"' not in wbuild.render(cfg, None, "A4", today="Sun")
