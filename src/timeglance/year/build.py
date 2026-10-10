#!/usr/bin/env python3
"""Render year/range plan (config.yaml) to SVG + PNG, optionally set as the KDE wallpaper.

Config precedence: built-in defaults < config.yaml < command-line flags.
Theme and layout may be a comma list or omitted (omitted = render all variants).
"""

import argparse
import datetime as dt
from pathlib import Path

import cairosvg
import holidays as holidays_lib
import yaml

from timeglance import paths
from timeglance.common import wallpaper
from timeglance.year import render, sources

HERE = Path(__file__).parent
TEMPLATE = HERE / "config.yaml.in"  # packaged annotated template (see `timeglance-init`)
ALL_THEMES = list(render.THEMES)
ALL_LAYOUTS = ["vertical", "horizontal"]


def load(path):
    """Load and parse a year config YAML file."""
    return yaml.safe_load(Path(path).read_text())


def add_holidays(raw):
    """Expand a `holidays:` block into single-day events for every year in the range."""
    spec = raw.get("holidays")
    if not spec:
        return None
    start, end = render.resolve_range(raw, dt.date.today())
    years = list(range(start[0], end[0] + 1))
    cal = holidays_lib.country_holidays(spec["country"], subdiv=spec.get("subdiv"), years=years)
    keep_observed = spec.get("observed", True)
    layer = spec.get("layer", "holidays")
    n = 0
    for d in sorted(cal):
        if not keep_observed and "(observed)" in cal[d]:
            continue
        raw["events"].append({"layer": layer, "label": cal[d], "date": d, "source": "holidays"})
        n += 1
    loc = "/".join(filter(None, [spec.get("country"), spec.get("subdiv")]))
    return {"kind": "holidays", "label": f"Public holidays ({loc})", "layer": layer, "count": n}


def assemble(raw):
    """Merge every event source into `raw` (YAML events + holidays + ICS). Returns a provenance summary."""
    raw.setdefault("events", [])
    for e in raw["events"]:
        e.setdefault("source", "yaml")
    summary = []
    n_yaml = len(raw["events"])
    if n_yaml:
        summary.append({"kind": "yaml", "label": "This file (events:)", "layer": None, "count": n_yaml})
    hol = add_holidays(raw)
    if hol:
        summary.append(hol)
    summary.extend(sources.load(raw))
    raw["_warnings"] = [f"{s['label']}: {s['error']}" for s in summary if s.get("error")]
    return summary


def resolve_size(raw):
    """A size may be a named entry in `sizes:` or a raw WxH string."""
    if raw.get("size"):
        raw["size"] = raw.get("sizes", {}).get(raw["size"], raw["size"])


def apply_cli(raw, args):
    """CLI flags override YAML (only when explicitly provided)."""
    if args.week_start:
        raw["week_start"] = args.week_start
    if args.week_align is not None:
        raw["week_align"] = args.week_align
    if args.size:
        raw["size"] = args.size
    if args.only:
        keep = set(args.only.split(","))
        for lyr in raw["layers"]:
            lyr["visible"] = lyr["id"] in keep
    for hid in args.hide:
        for lyr in raw["layers"]:
            if lyr["id"] == hid:
                lyr["visible"] = False


def resolve_list(cli, yaml_val, allowed):
    """Resolve a theme/layout selection (CLI > YAML > all) and validate it against ``allowed``."""
    spec = cli if cli is not None else yaml_val
    if not spec:
        return allowed
    items = [s.strip() for s in str(spec).split(",")]
    bad = [i for i in items if i not in allowed]
    if bad:
        raise SystemExit(f"unknown value(s): {', '.join(bad)} (allowed: {', '.join(allowed)})")
    return items


def _pick(cli, yaml_val, fallback, allowed, what):
    """Choose the single variant for the wallpaper: explicit single CLI value > YAML > fallback."""
    val = None
    if cli:
        items = [s.strip() for s in cli.split(",")]
        if len(items) == 1:
            val = items[0]
    val = val or yaml_val or fallback
    if val not in allowed:
        raise SystemExit(f"unknown wallpaper {what}: {val}  (allowed: {', '.join(allowed)})")
    return val


def apply_wallpaper(cfg, backend, screens, fill, out):
    """Render each screen at its current resolution and set it as that screen's wallpaper."""

    def render_png(scr, path):
        """Render the planner SVG at the screen's current resolution and save it as a PNG."""
        cfg.width, cfg.height = scr.pw, scr.ph
        cairosvg.svg2png(
            bytestring=render.render_svg(cfg).encode(), write_to=str(path), output_width=scr.pw, output_height=scr.ph
        )

    return wallpaper.apply(backend, screens, out, render_png, fill, prefix="year-wallpaper")


def main():
    """CLI entry point: render the planner to SVG/PNG variants or set it as the wallpaper."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=paths.planner_config("year"), type=Path)
    ap.add_argument("--layout", help="vertical / horizontal / comma list; omit for all")
    ap.add_argument("--theme", help="light / dark / comma list; omit for all")
    ap.add_argument("--week-start", dest="week_start", choices=["Mon", "Sun"])
    ap.add_argument(
        "--week-align",
        dest="week_align",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="weekday-aligned slots (--no-week-align packs days 1..31 flush)",
    )
    ap.add_argument("--only", help="show only these layer ids (comma-separated)")
    ap.add_argument("--hide", action="append", default=[], metavar="LAYER", help="hide a layer id")
    ap.add_argument("--size", help="named size (from YAML `sizes:`) or raw WxH, e.g. laptop / 3440x1440")
    ap.add_argument("--out", default=paths.planner_out("year"), type=Path)
    ap.add_argument(
        "--wallpaper",
        action="store_true",
        help="set as the desktop wallpaper (variant: single --theme/--layout > wallpaper.theme/layout > default)",
    )
    ap.add_argument("--screen", help="which screen(s) to set: all / primary / comma list of names (overrides YAML)")
    ap.add_argument("--list-screens", action="store_true", help="list detected screens and exit")
    args = ap.parse_args()

    backend = wallpaper.detect()
    if args.list_screens:
        if not backend:
            raise SystemExit("no supported wallpaper backend detected (need KDE Plasma)")
        for s in backend.list_screens():
            print(f"{s.name:12} {s.pw}x{s.ph} @ {s.x},{s.y}" + ("  *primary" if s.primary else ""))
        return

    raw = load(args.data)
    assemble(raw)
    apply_cli(raw, args)
    resolve_size(raw)

    themes = resolve_list(args.theme, raw.get("theme"), ALL_THEMES)
    layouts = resolve_list(args.layout, raw.get("layout"), ALL_LAYOUTS)
    args.out.mkdir(parents=True, exist_ok=True)

    if args.wallpaper:
        if not backend:
            raise SystemExit("--wallpaper needs a supported desktop (KDE Plasma not detected)")
        wp = raw.get("wallpaper") or {}
        raw["theme"] = _pick(args.theme, wp.get("theme"), themes[0], ALL_THEMES, "theme")
        raw["layout"] = _pick(args.layout, wp.get("layout"), layouts[0], ALL_LAYOUTS, "layout")
        if args.week_align is None and "week_align" in wp:
            raw["week_align"] = wp["week_align"]
        cfg = render.parse(raw)
        screens = wallpaper.resolve_screens(backend, args.screen or wp.get("screens", "all"))
        _, info = apply_wallpaper(cfg, backend, screens, wp.get("fill", "preserveAspectCrop"), args.out)
        applied = ", ".join(info["applied"]) or "(none - no desktop matched)"
        extra = "".join(f"; {k} {', '.join(info[k])}" for k in ("pending", "unseen") if info.get(k))
        print(f"wallpaper ({raw['theme']}/{raw['layout']}) applied on: {applied}; desktops: {info['desktops']}{extra}")
        return

    for layout in layouts:
        for theme in themes:
            raw["theme"], raw["layout"] = theme, layout
            cfg = render.parse(raw)
            svg = render.render_svg(cfg)
            stem = "year" + (f"-{layout}" if len(layouts) > 1 else "") + f"-{theme}"
            (args.out / f"{stem}.svg").write_text(svg)
            png = args.out / f"{stem}.png"
            cairosvg.svg2png(
                bytestring=svg.encode(), write_to=str(png), output_width=cfg.width, output_height=cfg.height
            )
            print(f"wrote {png}  ({cfg.width}x{cfg.height}, {layout}, {theme})")


if __name__ == "__main__":
    main()
