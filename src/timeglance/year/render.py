"""Render a year/range plan (config.yaml) to an SVG string.

The grid shows an arbitrary contiguous range of months (not a fixed calendar year).

Two orthogonal axes pick the layout:
  layout      `horizontal` (months are rows, days run left-to-right) or `vertical` (months are
              columns, days run top-to-bottom; the wide, wallpaper-friendly default).
  week_align  True  -> days sit in weekday-aligned slots (col/row mod 7 == weekday), so weekends
                       form aligned bands and each month starts at its weekday offset.
              False -> days are packed 1..31 flush from the start (no gaps).
Events become horizontal bars in the horizontal layout, vertical bars in the vertical one.
"""

from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field
from html import escape

from dateutil.rrule import MONTHLY, WEEKLY, rrule, rrulestr

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
WD3 = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]  # index = date.weekday()

THEMES = {
    "light": {
        "bg": "#ffffff",
        "grid": "#ececec",
        "weekend": "#f4f5f7",
        "weekend_tint": "#000000",
        "weekend_tint_op": 0.07,
        "past": "#000000",
        "past_op": 0.05,
        "text": "#1b1b1b",
        "muted": "#9aa0a6",
        "rail": "#3a3a3a",
        "today": "#d23b3b",
    },
    "dark": {
        "bg": "#15171c",
        "grid": "#262a31",
        "weekend": "#1b1e24",
        "weekend_tint": "#ffffff",
        "weekend_tint_op": 0.07,
        "past": "#000000",
        "past_op": 0.28,
        "text": "#e8e8ea",
        "muted": "#6b7280",
        "rail": "#c9ccd1",
        "today": "#ff6b6b",
    },
}


@dataclass
class Layer:
    """A named, coloured category that events belong to (toggled via the legend)."""

    id: str
    label: str
    color: str
    visible: bool = True


@dataclass
class Event:
    """A single resolved occurrence spanning ``start``..``end`` (inclusive) on a layer."""

    layer: str
    label: str
    start: dt.date
    end: dt.date


@dataclass
class Config:
    """Fully resolved render settings: range, layout, theme, dimensions, layers and events."""

    title: str = ""
    week_start: str = "Mon"
    layout: str = "vertical"
    week_align: bool = True
    theme: str = "light"
    width: int = 1920
    height: int = 1080
    show_today: bool = True
    dim_past: bool = True
    start_ym: tuple = (2026, 1)
    end_ym: tuple = (2026, 12)
    layers: list[Layer] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def start_idx(self):
        """Weekday index the week starts on (0=Mon, 6=Sun)."""
        return 0 if self.week_start == "Mon" else 6

    @property
    def months(self):
        """List of ``(year, month)`` tuples spanning the configured range, inclusive."""
        out, ym = [], self.start_ym
        while ym <= self.end_ym:
            out.append(ym)
            ym = _month_add(*ym, 1)
        return out


# ---- range / recurrence resolution ---------------------------------------


def _month_add(y, m, delta):
    """Add ``delta`` months to ``(y, m)``, wrapping years as needed."""
    idx = y * 12 + (m - 1) + delta
    return idx // 12, idx % 12 + 1


_RANGE_HELP = "enter a valid month: YYYY, YYYY-MM, today, today\u00b1N, year-start or year-end"


def _is_int(s):
    """True if ``s`` is an optionally-signed integer string."""
    return s.lstrip("+-").isdigit()


def _resolve_ym(token, today):
    """Resolve a range token (``YYYY``, ``YYYY-MM``, ``today``, ``today±N``, ``year-start/end``) to ``(y, m)``."""
    tok = str(token).strip().lower()
    if tok in ("today", "now"):
        return (today.year, today.month)
    if tok == "year-start":
        return (today.year, 1)
    if tok == "year-end":
        return (today.year, 12)
    if tok.startswith("today") and _is_int(tok[5:]):
        return _month_add(today.year, today.month, int(tok[5:]))
    if "-" in tok:
        y, m = tok.split("-", 1)
        if _is_int(y) and _is_int(m) and 1 <= int(m) <= 12:
            return (int(y), int(m))
    elif _is_int(tok):
        return (int(tok), 1)
    raise ValueError(f"{_RANGE_HELP} (got '{token}')")


def resolve_range(raw, today):
    """Resolve the (start_ym, end_ym) to render. A `range.span` preset wins over explicit
    start/end: `this_year` (Jan-Dec of the current year), `upcoming_year` (rolling 12 from
    this month), or `custom` with `before`/`after` month counts around today."""
    r = raw.get("range") or {}
    span = r.get("span")
    if span == "this_year":
        start, end = (today.year, 1), (today.year, 12)
    elif span == "upcoming_year":
        start, end = (today.year, today.month), _month_add(today.year, today.month, 11)
    elif span == "custom":
        start = _month_add(today.year, today.month, -int(r.get("before", 0)))
        end = _month_add(today.year, today.month, int(r.get("after", 11)))
    elif r.get("start"):
        start = _resolve_ym(r["start"], today)
        end = _resolve_ym(r.get("end", "year-end"), today)
    elif "year" in raw:
        start, end = (raw["year"], 1), (raw["year"], 12)
    else:
        start, end = (today.year, today.month), _month_add(today.year, today.month, 11)
    if end < start:
        end = start
    return start, end


def _project(d: dt.date, year: int) -> dt.date:
    """Move ``d`` to ``year``, clamping a Feb-29 to Feb-28 in non-leap years."""
    if d.month == 2 and d.day == 29 and not calendar.isleap(year):
        return dt.date(year, 2, 28)
    return d.replace(year=year)


def _occurrences(e, base_start, ws, we, years):
    """Expand an event's recurrence (rrule/repeat) into the start dates falling within the window."""
    dtstart = dt.datetime(base_start.year, base_start.month, base_start.day)
    wsd, wed = dt.datetime.combine(ws, dt.time()), dt.datetime.combine(we, dt.time(23, 59, 59))
    rr = e.get("rrule")
    if rr:
        return [d.date() for d in rrulestr(rr, dtstart=dtstart).between(wsd, wed, inc=True)]
    rep = e.get("repeat")
    if rep == "yearly":
        return [p for y in years if ws <= (p := _project(base_start, y)) <= we]
    if rep in ("weekly", "monthly"):
        freq = WEEKLY if rep == "weekly" else MONTHLY
        return [d.date() for d in rrule(freq, dtstart=dtstart).between(wsd, wed, inc=True)]
    return [base_start]


def parse(raw) -> Config:
    """Build a resolved :class:`Config` from raw YAML: range, layers and expanded event occurrences."""
    today = dt.date.today()
    start_ym, end_ym = resolve_range(raw, today)
    years = sorted({y for y, _ in _iter_months(start_ym, end_ym)})
    ws, we = dt.date(*start_ym, 1), dt.date(end_ym[0], end_ym[1], calendar.monthrange(*end_ym)[1])

    layers = [Layer(**lyr) for lyr in raw["layers"]]
    events = []
    for e in raw["events"]:
        if "date" in e:
            base_start = e["date"]
        elif "start" in e:
            base_start = e["start"]
        else:
            base_start = ws
        base_end = e.get("end", base_start)
        dur = (base_end - base_start).days
        for occ in _occurrences(e, base_start, ws, we, years):
            events.append(Event(layer=e["layer"], label=e["label"], start=occ, end=occ + dt.timedelta(days=dur)))

    cfg = Config(
        title=str(raw.get("title", _default_title(start_ym, end_ym))),
        week_start=raw.get("week_start", "Mon"),
        layout=raw.get("layout", "vertical"),
        week_align=raw.get("week_align", True),
        theme=raw.get("theme", "light"),
        show_today=raw.get("show_today", True),
        dim_past=raw.get("dim_past", True),
        start_ym=start_ym,
        end_ym=end_ym,
        layers=layers,
        events=events,
    )
    cfg.warnings = list(raw.get("_warnings", []))
    if raw.get("size"):
        cfg.width, cfg.height = (int(v) for v in str(raw["size"]).lower().split("x"))
    return cfg


def _iter_months(start_ym, end_ym):
    """List ``(year, month)`` tuples from ``start_ym`` to ``end_ym`` inclusive."""
    out, ym = [], start_ym
    while ym <= end_ym:
        out.append(ym)
        ym = _month_add(*ym, 1)
    return out


def _default_title(start_ym, end_ym):
    """Derive a title from the range: a bare year for Jan-Dec, else ``Mon YY - Mon YY``."""
    if start_ym[0] == end_ym[0] and start_ym == (start_ym[0], 1) and end_ym == (end_ym[0], 12):
        return str(start_ym[0])
    a = f"{MONTHS[start_ym[1] - 1].title()} {start_ym[0]}"
    b = f"{MONTHS[end_ym[1] - 1].title()} {end_ym[0]}"
    return f"{a} \u2013 {b}"


# ---- geometry -------------------------------------------------------------


def month_offset(cfg: Config, y: int, m: int) -> int:
    """Slot offset of a month's first day: its weekday offset when aligned, else 0."""
    if not cfg.week_align:
        return 0
    return (dt.date(y, m, 1).weekday() - cfg.start_idx) % 7


def col_of(cfg: Config, d: dt.date) -> int:
    """Day-axis slot index for date ``d`` within its month."""
    return month_offset(cfg, d.year, d.month) + (d.day - 1)


def day_slots(cfg: Config) -> int:
    """How many slots the day axis needs: 31 when packed, else the widest weekday-aligned month."""
    if not cfg.week_align:
        return 31
    best = 0
    for y, m in cfg.months:
        best = max(best, month_offset(cfg, y, m) + calendar.monthrange(y, m)[1])
    return best


def is_weekend(d: dt.date) -> bool:
    """True if ``d`` falls on a Saturday or Sunday."""
    return d.weekday() >= 5


# ---- lane packing ---------------------------------------------------------


def pack_lanes(segments):
    """Assign each segment the lowest non-overlapping lane index (greedy interval packing)."""
    lane_ends = []
    for seg in sorted(segments, key=lambda s: (s["c0"], s["c1"])):
        for i, end in enumerate(lane_ends):
            if seg["c0"] > end:
                seg["lane"] = i
                lane_ends[i] = seg["c1"]
                break
        else:
            seg["lane"] = len(lane_ends)
            lane_ends.append(seg["c1"])
    return segments


# ---- svg primitives -------------------------------------------------------


def _rect(x, y, w, h, fill, rx=0, opacity=1.0, stroke=None, sw=0):
    """Build an SVG ``<rect>`` element string."""
    s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
    if rx:
        s += f' rx="{rx:.1f}"'
    if opacity != 1.0:
        s += f' opacity="{opacity}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    return s + "/>"


def _text(x, y, s, size, fill, weight="normal", anchor="start", opacity=1.0):
    """Build an SVG ``<text>`` element string (content is HTML-escaped)."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" opacity="{opacity}">{escape(str(s))}</text>'
    )


def _line(x1, y1, x2, y2, stroke, sw=1.0):
    """Build an SVG ``<line>`` element string."""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"/>'


def _fit(label, width, size):
    """Truncate ``label`` with an ellipsis to fit ``width`` at font ``size`` (single line)."""
    n = max(0, int(width / (size * 0.56)))
    if len(label) <= n:
        return label
    return label[: max(0, n - 1)] + "\u2026" if n >= 2 else ""


def _wrap(label, width, size, max_lines):
    """Greedy word-wrap into at most max_lines that fit width.

    Returns (lines, truncated, hard_split); hard_split marks a word broken mid-word.
    """
    cpl = max(1, int(width / (size * 0.56)))
    words = label.split()
    lines, i, hard = [], 0, False
    while i < len(words) and len(lines) < max_lines:
        cur = words[i]
        i += 1
        while i < len(words) and len(cur) + 1 + len(words[i]) <= cpl:
            cur += " " + words[i]
            i += 1
        if " " not in cur and len(cur) > cpl:  # single word wider than a line
            words.insert(i, cur[cpl:])
            cur = cur[:cpl]
            hard = True
        lines.append(cur)
    truncated = i < len(words)
    if truncated:
        lines[-1] = lines[-1][: max(1, cpl - 1)].rstrip() + "\u2026"
    return lines, truncated, hard


def _fit_box(label, w, h, sizes=(12, 11, 10, 9, 8, 7.5)):
    """Largest font that fits label in a w*h box, preferring clean word-breaks over bigger text."""
    fallback = smallest = None
    for size in sizes:
        max_lines = max(1, int((h + 2) / (size + 0.8)))
        lines, truncated, hard = _wrap(label, w, size, max_lines)
        smallest = (size, lines)
        if not truncated:
            if not hard:
                return size, lines
            if fallback is None:
                fallback = (size, lines)
    return fallback or smallest


# ---- main render ----------------------------------------------------------


def _svg_open(W, H):
    """Build the opening ``<svg>`` tag for a ``W``x``H`` canvas."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="Noto Sans, DejaVu Sans, sans-serif">'
    )


def _draw_header(out, cfg, t, pad, visible):
    """Title + colour legend across the top; hidden layers render at low opacity."""
    out.append(_text(pad, pad + 40, cfg.title, 40, t["text"], weight="700"))
    lx = pad + 24 + len(cfg.title) * 23
    for lyr in cfg.layers:
        op = 1.0 if lyr.id in visible else 0.28
        out.append(_rect(lx, pad + 22, 13, 13, lyr.color, rx=3, opacity=op))
        out.append(_text(lx + 18, pad + 33, lyr.label, 13, t["text"], opacity=op))
        lx += 18 + len(lyr.label) * 7.4 + 22


def _draw_warnings(out, cfg, t, pad, W):
    """Append a top-right warning badge when any event source failed to load."""
    if not cfg.warnings:
        return
    n = len(cfg.warnings)
    msg = "\u26a0 " + (cfg.warnings[0] if n == 1 else f"{n} sources unavailable \u2014 showing cached/none")
    bw = min(W - 2 * pad, 16 + len(msg) * 6.6)
    bx = W - pad - bw
    out.append(_rect(bx, pad + 4, bw, 22, "#C4553B", rx=5, opacity=0.94))
    out.append(_text(bx + 8, pad + 19, _fit(msg, bw - 14, 12), 12, "#ffffff", weight="600"))


def render_svg(cfg: Config) -> str:
    """Render the planner to an SVG string, dispatching to the vertical or horizontal layout."""
    if cfg.layout == "vertical":
        return _render_vertical(cfg)
    t = THEMES[cfg.theme]
    W, H = cfg.width, cfg.height
    pad = 26
    rail_w = 52
    header_h = 84
    cols = day_slots(cfg)
    months = cfg.months
    rows = len(months)

    grid_left = pad + rail_w
    grid_top = pad + header_h
    grid_w = W - pad - grid_left
    grid_h = H - pad - grid_top
    col_w = grid_w / cols
    row_h = grid_h / rows

    num_band = 17
    lane_gap = 2
    lane_min, lane_max = 14, 24
    lane_avail = row_h - num_band - 2
    lane_cap = max(1, int(lane_avail / lane_min))

    layer_by_id = {lyr.id: lyr for lyr in cfg.layers}
    visible = {lyr.id for lyr in cfg.layers if lyr.visible}
    today = dt.date.today()

    out = [_svg_open(W, H), _rect(0, 0, W, H, t["bg"])]
    _draw_header(out, cfg, t, pad, visible)

    # day cells + weekend bands + past dimming
    today_box = None
    prev_year = None
    for ri, (y, m) in enumerate(months):
        row_top = grid_top + ri * row_h
        ndays = calendar.monthrange(y, m)[1]

        label = MONTHS[m - 1]
        if m == 1 or y != prev_year:
            label += f" {y % 100:02d}"
        prev_year = y
        out.append(_text(pad + rail_w - 8, row_top + row_h / 2 + 4, label, 13, t["rail"], weight="700", anchor="end"))

        for day in range(1, ndays + 1):
            d = dt.date(y, m, day)
            c = col_of(cfg, d)
            x = grid_left + c * col_w
            if is_weekend(d):
                out.append(_rect(x, row_top, col_w, row_h, t["weekend"]))
            if cfg.dim_past and d < today:
                out.append(_rect(x, row_top, col_w, row_h, t["past"], opacity=t["past_op"]))
            if cfg.show_today and d == today:
                today_box = (x, row_top)
            out.append(_text(x + 3, row_top + 12, day, 10.5, t["text"], weight="600"))
            out.append(_text(x + 3, row_top + 12 + 8, WD3[d.weekday()], 6.5, t["muted"]))

        out.append(_line(grid_left, row_top, grid_left + grid_w, row_top, t["grid"], 1))

    out.append(_line(grid_left, grid_top + grid_h, grid_left + grid_w, grid_top + grid_h, t["grid"], 1))

    # event bars, lane-packed per month row
    for ri, (y, m) in enumerate(months):
        row_top = grid_top + ri * row_h
        m_first = dt.date(y, m, 1)
        m_last = dt.date(y, m, calendar.monthrange(y, m)[1])

        segs = []
        for ev in cfg.events:
            if ev.layer not in visible:
                continue
            s = max(ev.start, m_first)
            e = min(ev.end, m_last)
            if s > e:
                continue
            segs.append({"c0": col_of(cfg, s), "c1": col_of(cfg, e), "s": s, "e": e, "ev": ev})
        pack_lanes(segs)

        n_lanes = 1 + max((s["lane"] for s in segs), default=-1)
        if not n_lanes:
            continue
        used = min(n_lanes, lane_cap)
        lane_h = min(lane_max, lane_avail / used)
        bh = lane_h - lane_gap
        span_font = min(11.0, max(8.0, bh - 7))

        lanes = defaultdict(list)
        for seg in segs:
            if seg["lane"] < used:
                lanes[seg["lane"]].append(seg)

        for lane, items in lanes.items():
            by = row_top + num_band + lane * lane_h
            for seg in items:
                ev = seg["ev"]
                color = layer_by_id[ev.layer].color
                if seg["c1"] > seg["c0"]:  # span -> filled bar
                    bx = grid_left + seg["c0"] * col_w
                    bw = (seg["c1"] - seg["c0"] + 1) * col_w
                    out.append(_rect(bx + 1, by, bw - 2, bh, color, rx=3))
                    d = seg["s"]
                    while d <= seg["e"]:
                        if is_weekend(d):
                            cl = grid_left + col_of(cfg, d) * col_w
                            ox, orr = max(cl, bx + 1), min(cl + col_w, bx + bw - 1)
                            if orr > ox:
                                out.append(_rect(ox, by, orr - ox, bh, t["weekend_tint"], opacity=t["weekend_tint_op"]))
                        d += dt.timedelta(days=1)
                    lab = _fit(ev.label, bw - 10, span_font)
                    if lab:
                        out.append(
                            _text(bx + 6, by + bh / 2 + span_font * 0.35, lab, span_font, "#ffffff", weight="600")
                        )
                else:  # single day -> colored tick + label filling its own column
                    cx = grid_left + seg["c0"] * col_w
                    out.append(_rect(cx + 1, by, 2.5, bh, color, rx=1))
                    size, lines = _fit_box(ev.label, col_w - 8, bh)
                    pitch = size + 0.8
                    y0 = by + (bh - len(lines) * pitch) / 2 + size
                    for k, ln in enumerate(lines):
                        out.append(_text(cx + 6, y0 + k * pitch, ln, size, t["text"], weight="600"))

    if today_box:
        x, row_top = today_box
        out.append(_rect(x + 0.5, row_top + 0.5, col_w - 1, row_h - 1, "none", rx=3, stroke=t["today"], sw=1.8))

    _draw_warnings(out, cfg, t, pad, W)
    out.append("</svg>")
    return "\n".join(out)


def _render_vertical(cfg: Config) -> str:
    """Months left-to-right (one column each), days top-to-bottom (rows); wide and
    wallpaper-friendly, since each month column gets `grid_w / n_months` and fewer months buys
    more label width. Multi-day events are vertical bars, lane-packed into sub-columns within
    their month. When `week_align`, rows are weekday slots (same weekday across every column, so
    weekends form aligned horizontal bands) and the left rail labels weekdays; otherwise rows are
    days 1..31 packed flush and the rail numbers them."""
    t = THEMES[cfg.theme]
    aligned = cfg.week_align
    W, H = cfg.width, cfg.height
    pad = 26
    header_h = 84
    mhdr_h = 24
    rail_w = 30
    lane_gap = 2
    gutter = 14 if aligned else 1  # aligned rows aren't day-numbered, so number cells in a left strip
    months = cfg.months
    ncols = len(months)
    nrows = day_slots(cfg)

    grid_left = pad + rail_w
    grid_top = pad + header_h + mhdr_h
    grid_w = W - pad - grid_left
    grid_h = H - pad - grid_top
    col_w = grid_w / ncols
    row_h = grid_h / nrows

    layer_by_id = {lyr.id: lyr for lyr in cfg.layers}
    visible = {lyr.id for lyr in cfg.layers if lyr.visible}
    today = dt.date.today()

    out = [_svg_open(W, H), _rect(0, 0, W, H, t["bg"])]
    _draw_header(out, cfg, t, pad, visible)

    # left rail + row grid: weekday letters (aligned) or day numbers (packed);
    # today's row label is picked out in the accent colour so the far-left rail ties to its cell
    today_row = col_of(cfg, today) if cfg.show_today and (today.year, today.month) in months else None
    for r in range(nrows):
        ry = grid_top + r * row_h
        rail = WD3[(r + cfg.start_idx) % 7] if aligned else str(r + 1)
        hot = r == today_row
        out.append(
            _text(
                grid_left - 6,
                ry + row_h / 2 + 3.5,
                rail,
                8.5,
                t["today"] if hot else t["muted"],
                weight="700" if hot else "normal",
                anchor="end",
            )
        )
        out.append(_line(grid_left, ry, grid_left + grid_w, ry, t["grid"], 1))
    out.append(_line(grid_left, grid_top + grid_h, grid_left + grid_w, grid_top + grid_h, t["grid"], 1))

    today_box = None
    prev_year = None
    for ci, (y, m) in enumerate(months):
        cx = grid_left + ci * col_w
        label = MONTHS[m - 1]
        if m == 1 or y != prev_year:
            label += f" {y % 100:02d}"
        prev_year = y
        mlx = cx + col_w / 2
        out.append(_text(mlx, grid_top - mhdr_h / 2 + 4, label, 13, t["rail"], weight="700", anchor="middle"))

        for day in range(1, calendar.monthrange(y, m)[1] + 1):
            d = dt.date(y, m, day)
            ry = grid_top + col_of(cfg, d) * row_h
            if is_weekend(d):
                out.append(_rect(cx, ry, col_w, row_h, t["weekend"]))
            if cfg.dim_past and d < today:
                out.append(_rect(cx, ry, col_w, row_h, t["past"], opacity=t["past_op"]))
            if cfg.show_today and d == today:
                today_box = (cx, ry)
            if aligned:
                out.append(_text(cx + 3, ry + row_h / 2 + 3, day, 8, t["muted"]))
        out.append(_line(cx, grid_top, cx, grid_top + grid_h, t["grid"], 1))
    out.append(_line(grid_left + grid_w, grid_top, grid_left + grid_w, grid_top + grid_h, t["grid"], 1))

    # events: vertical bars, lane-packed into sub-columns within each month
    for ci, (y, m) in enumerate(months):
        cx = grid_left + ci * col_w
        m_first = dt.date(y, m, 1)
        m_last = dt.date(y, m, calendar.monthrange(y, m)[1])

        segs = []
        for ev in cfg.events:
            if ev.layer not in visible:
                continue
            s = max(ev.start, m_first)
            e = min(ev.end, m_last)
            if s > e:
                continue
            segs.append({"c0": col_of(cfg, s), "c1": col_of(cfg, e), "s": s, "e": e, "ev": ev})
        pack_lanes(segs)

        n_lanes = 1 + max((seg["lane"] for seg in segs), default=-1)
        if not n_lanes:
            continue
        avail = col_w - gutter - 1
        used = min(n_lanes, max(1, int(avail / 11)))
        lane_w = avail / used
        bw = lane_w - lane_gap
        for seg in segs:
            if seg["lane"] >= used:
                continue
            ev = seg["ev"]
            bx = cx + gutter + seg["lane"] * lane_w
            by = grid_top + seg["c0"] * row_h
            bh = (seg["c1"] - seg["c0"] + 1) * row_h
            out.append(_rect(bx, by + 1, bw, bh - 2, layer_by_id[ev.layer].color, rx=3))
            d = seg["s"]
            while d <= seg["e"]:
                if is_weekend(d):
                    ct = grid_top + col_of(cfg, d) * row_h
                    oy, ob = max(ct, by + 1), min(ct + row_h, by + bh - 1)
                    if ob > oy:
                        out.append(_rect(bx, oy, bw, ob - oy, t["weekend_tint"], opacity=t["weekend_tint_op"]))
                d += dt.timedelta(days=1)
            size, lines = _fit_box(ev.label, bw - 6, bh - 4)
            pitch = size + 0.8
            y0 = by + 1 + (bh - 2 - len(lines) * pitch) / 2 + size
            for k, ln in enumerate(lines):
                out.append(_text(bx + 4, y0 + k * pitch, ln, size, "#ffffff", weight="600"))

    if today_box:
        cx, ry = today_box
        out.append(_rect(cx + 0.5, ry + 0.5, col_w - 1, row_h - 1, "none", rx=3, stroke=t["today"], sw=1.8))

    _draw_warnings(out, cfg, t, pad, W)
    out.append("</svg>")
    return "\n".join(out)
