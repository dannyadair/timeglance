# Use as a library

Both tools are plain subpackages of `timeglance`, so you can skip the CLI/server and render straight from your own
code. The functions below are exactly what the CLI and server call. Config input is just a `dict` (load it from
YAML with the provided `load()`, or build it yourself). The same system C libraries as the CLI are needed
(CairoSVG/WeasyPrint).

**Year - dict → SVG → PNG:**

```python
import cairosvg
from timeglance.year import build, render

raw = build.load("year/config.yaml")  # -> dict  (or pass your own dict)
build.assemble(raw)  # merge events: + holidays: + ics sources:
build.resolve_size(raw)  # expand a named `size:` to WxH
raw["theme"], raw["layout"] = "light", "vertical"  # pick a single variant

cfg = render.parse(raw)  # dict -> typed layout
svg = render.render_svg(cfg)  # -> SVG string
png = cairosvg.svg2png(bytestring=svg.encode(), output_width=cfg.width, output_height=cfg.height)
```

**Weekly - dict → HTML / PDF:**

```python
from timeglance.weekly import build

cfg = build.load("weekly/config.yaml")  # -> dict  (or pass your own dict)
html = build.render(cfg, None, "A4")  # -> HTML string
pdf = build.render_pdf(cfg, None, "A4")  # -> PDF bytes
```

The second argument to `render`/`render_pdf` is `hide` - an iterable of activity ids to hide, or `None` to honour
the YAML `visible:` defaults. No network is used unless the year config has URL `sources:` (a `holidays:` block is
computed locally). Setting the desktop wallpaper lives in `timeglance.common.wallpaper` (KDE Plasma only; see
[Wallpaper](wallpaper.md)).
