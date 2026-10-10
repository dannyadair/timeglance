#!/usr/bin/env python3
"""Render a weekly routine (config.yaml) to a printable PDF / HTML sheet."""

import argparse
import datetime as dt
from collections import defaultdict
from pathlib import Path

import pypdfium2 as pdfium
import yaml
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFilter
from weasyprint import HTML

from timeglance import paths
from timeglance.common import wallpaper

HERE = Path(__file__).parent
TEMPLATE = HERE / "config.yaml.in"  # packaged annotated template (see `timeglance-init`)

# Short edge of each page in mm (landscape). Timeline height is derived from it.
PAGE_SHORT_MM = {"A4": 210, "A3": 297}
PAGE_MARGIN_MM = 9
HEADER_RESERVE_MM = 30
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def to_min(t):
    """Convert a ``HH:MM`` string to minutes past midnight."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def fmt(minutes):
    """Format minutes past midnight back to a ``HH:MM`` string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def fmt_hours(minutes):
    """Format a minute count as a compact hour label (e.g. ``7.5h``, ``8h``)."""
    return f"{round(minutes / 60, 1):g}h"


def load(path):
    """Load and parse a weekly config YAML file."""
    return yaml.safe_load(Path(path).read_text())


def hidden_activities(cfg, hide):
    """`hide`: an explicit iterable of activity ids to hide (from the UI/CLI), or None to
    fall back to the YAML defaults (activities marked `visible: false`)."""
    if hide is not None:
        return set(hide)
    return {k for k, a in cfg["activities"].items() if not a.get("visible", True)}


def visible_blocks(cfg, hidden):
    """Return the config's blocks minus any whose activity id is in ``hidden``."""
    return [b for b in cfg.get("blocks", []) if b["activity"] not in hidden]


def layout(cfg, blocks):
    """Build the per-day positioned cells, hour gridlines and totals legend for the sheet."""
    day_start = to_min(cfg["day_start"])
    day_end = to_min(cfg["day_end"])
    span = day_end - day_start
    activities = cfg["activities"]

    by_day = {day: [] for day in cfg["days"]}
    used = {}
    totals = defaultdict(int)
    for b in blocks:
        act = activities[b["activity"]]
        used[b["activity"]] = act
        start, end = to_min(b["start"]), to_min(b["end"])
        totals[b["activity"]] += (end - start) * len(b["days"])
        cell = {
            "top": round((start - day_start) / span * 100, 3),
            "height": round((end - start) / span * 100, 3),
            "color": act["color"],
            "label": b.get("label", act["label"]),
            "time": f"{fmt(start)}\u2013{fmt(end)}",
            "start": start,
        }
        for day in b["days"]:
            by_day[day].append(cell)
    for day in by_day:
        by_day[day].sort(key=lambda c: c["start"])

    hour_lines = []
    step = cfg.get("hour_marks", 1) * 60
    t = day_start
    while t <= day_end:
        hour_lines.append(
            {
                "top": round((t - day_start) / span * 100, 3),
                "label": fmt(t),
                "major": (t - day_start) % (step * 2) == 0,
            }
        )
        t += step

    # Legend follows the `activities:` declaration order (manual control), not block order.
    legend = [
        {"label": a["label"], "color": a["color"], "hours": fmt_hours(totals[aid])}
        for aid, a in activities.items()
        if aid in used
    ]
    return by_day, hour_lines, legend


def render(cfg, hide, paper, today=None):
    """`today`: the weekday label (e.g. "Wed") to highlight as the current day; defaults to the
    render date's weekday so a daily-rebuilt sheet marks today. A label not in `days` highlights
    nothing (e.g. a Sat/Sun render of a Mon–Fri sheet)."""
    by_day, hour_lines, legend = layout(cfg, visible_blocks(cfg, hidden_activities(cfg, hide)))
    track_h = PAGE_SHORT_MM[paper] - 2 * PAGE_MARGIN_MM - HEADER_RESERVE_MM
    today = today or WEEKDAYS[dt.date.today().weekday()]
    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=True)
    return env.get_template("week.html.j2").render(
        title=cfg["title"],
        subtitle=cfg.get("subtitle", ""),
        days=cfg["days"],
        today=today,
        blocks=by_day,
        hour_lines=hour_lines,
        legend=legend,
        paper=paper,
        track_h=track_h,
    )


def render_pdf(cfg, hide, paper):
    """Render the sheet to PDF bytes."""
    return HTML(string=render(cfg, hide, paper), base_url=str(HERE)).write_pdf()


def _fit(inner_w, inner_h, max_w, max_h):
    """Largest (w, h) preserving the inner aspect ratio that fits inside the max box."""
    scale = min(max_w / inner_w, max_h / inner_h)
    return round(inner_w * scale), round(inner_h * scale)


# Shadow geometry as fractions of the screen's short edge (opacity is 0-255 pre-blur).
SHADOW_DEFAULTS = {"opacity": 120, "blur": 0.013, "offset": 0.006, "radius": 0.006}


def resolve_shadow(wp):
    """`wallpaper.shadow`: a dict of overrides, or `false` to disable. Returns dict or None."""
    spec = wp.get("shadow", {})
    if spec is False:
        return None
    return {**SHADOW_DEFAULTS, **spec}


def make_wallpaper_renderer(pdf_bytes, background, margin, shadow):
    """render_png(screen, path): the page-shaped sheet centred on a `background` canvas at
    the screen's current resolution, with `margin` (fraction of the short edge) kept clear
    and an optional soft drop shadow so it reads as a page sitting on the desk."""
    page = pdfium.PdfDocument(pdf_bytes)[0]
    pt_w, pt_h = page.get_size()

    def render_png(scr, path):
        """Render the sheet onto a screen-sized canvas and save it as a PNG."""
        short = min(scr.pw, scr.ph)
        pad = round(short * margin)
        w, h = _fit(pt_w, pt_h, scr.pw - 2 * pad, scr.ph - 2 * pad)
        x, y = (scr.pw - w) // 2, (scr.ph - h) // 2
        sheet = page.render(scale=h / pt_h).to_pil().convert("RGB").resize((w, h))
        canvas = Image.new("RGB", (scr.pw, scr.ph), background)
        if shadow:
            off = round(short * shadow["offset"])
            layer = Image.new("RGBA", (scr.pw, scr.ph), (0, 0, 0, 0))
            box = (x + off, y + off, x + w + off, y + h + off)
            ImageDraw.Draw(layer).rounded_rectangle(
                box, radius=round(short * shadow["radius"]), fill=(0, 0, 0, shadow["opacity"])
            )
            layer = layer.filter(ImageFilter.GaussianBlur(short * shadow["blur"]))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")
        canvas.paste(sheet, (x, y))
        canvas.save(str(path))

    return render_png


def resolve_hide(cfg, args):
    """The hidden-activity set from CLI flags, falling back to the YAML `visible:` defaults."""
    if args.only:
        keep = set(args.only.split(","))
        return {k for k in cfg["activities"] if k not in keep}
    base = {k for k, a in cfg["activities"].items() if not a.get("visible", True)}
    return base | set(args.hide)


def main():
    """CLI entry point: render the weekly sheet to PDF/HTML or set it as the wallpaper."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=paths.tool_config("weekly"), type=Path)
    ap.add_argument("--only", help="show only these activity ids (comma-separated)")
    ap.add_argument("--hide", action="append", default=[], metavar="ACTIVITY", help="hide an activity id")
    ap.add_argument("--paper", choices=["A4", "A3"], help="page size (default: YAML `paper:` or A4)")
    ap.add_argument("--format", choices=["pdf", "html", "both"], help="output format (default: YAML `format:` or pdf)")
    ap.add_argument("--out", default=paths.tool_out("weekly"), type=Path)
    ap.add_argument(
        "--wallpaper", action="store_true", help="set the sheet as the desktop wallpaper (centred on a themed canvas)"
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

    cfg = load(args.data)
    hide = resolve_hide(cfg, args)
    paper = args.paper or cfg.get("paper", "A4")
    out_format = args.format or cfg.get("format", "pdf")

    if args.wallpaper:
        if not backend:
            raise SystemExit("--wallpaper needs a supported desktop (KDE Plasma not detected)")
        wp = cfg.get("wallpaper") or {}
        screens = wallpaper.resolve_screens(backend, args.screen or wp.get("screens", "all"))
        render_png = make_wallpaper_renderer(
            render_pdf(cfg, hide, paper),
            wp.get("background", "#2b2f36"),
            wp.get("margin", 0.05),
            resolve_shadow(wp),
        )
        _, info = wallpaper.apply(backend, screens, args.out, render_png, prefix="weekly-wallpaper")
        applied = ", ".join(info["applied"]) or "(none - no desktop matched)"
        print(f"wallpaper applied on: {applied}; desktops: {info['desktops']}")
        return

    html = render(cfg, hide, paper)
    args.out.mkdir(parents=True, exist_ok=True)
    if out_format in ("html", "both"):
        path = args.out / "weekly.html"
        path.write_text(html)
        print(f"wrote {path}")
    if out_format in ("pdf", "both"):
        path = args.out / "weekly.pdf"
        HTML(string=html, base_url=str(HERE)).write_pdf(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
