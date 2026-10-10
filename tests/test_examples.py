"""Render every bundled example config end-to-end and assert the output is well-formed.

The examples under tests/examples/ double as the fixtures: adding a new config there
extends coverage without touching this file.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild
from timeglance.year import render as yrender

EXAMPLES = Path(__file__).parent / "examples"
YEAR_EXAMPLES = ["year_aligned.yaml", "year_packed.yaml", "year_sources.yaml"]


def load_year(name):
    """Load an example year config, rooting relative source paths at the examples dir."""
    raw = yaml.safe_load((EXAMPLES / name).read_text())
    for src in raw.get("sources") or []:
        if "path" in src and not Path(src["path"]).is_absolute():
            src["path"] = str(EXAMPLES / src["path"])
    ybuild.assemble(raw)
    return raw


@pytest.mark.parametrize("name", YEAR_EXAMPLES)
def test_year_example_renders_wellformed_svg(name):
    """Each example year config renders to well-formed SVG."""
    svg = yrender.render_svg(yrender.parse(load_year(name)))
    assert svg.startswith("<svg")
    ET.fromstring(svg)  # raises on malformed XML


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("week_align", [True, False])
@pytest.mark.parametrize("layout", ["vertical", "horizontal"])
def test_all_layout_combinations(layout, week_align, theme):
    """Every layout × week_align × theme combination renders to well-formed SVG."""
    raw = load_year("year_aligned.yaml")
    raw.update(layout=layout, week_align=week_align, theme=theme)
    svg = yrender.render_svg(yrender.parse(raw))
    ET.fromstring(svg)


def test_year_sources_example_pulls_calendar_events():
    """The sources example assembles at least one event from its bundled ICS."""
    raw = load_year("year_sources.yaml")
    assert any(e.get("source", "").startswith("ics:") for e in raw["events"])


def test_weekly_example_renders():
    """The weekly example renders with today highlighted, hidden topics dropped, and totals shown."""
    cfg = yaml.safe_load((EXAMPLES / "weekly.yaml").read_text())
    html = wbuild.render(cfg, hide=None, paper="A4", today="Wed")
    assert "My Week" in html
    assert "Work" in html
    assert "Workout" not in html  # gym is visible: false
    assert 'class="col today"' in html  # Wed highlighted
    assert "40h" in html and "5h" in html  # per-topic weekly totals (work 8h×5, sleep 1h×5)
