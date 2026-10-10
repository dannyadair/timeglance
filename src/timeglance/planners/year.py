"""Control-panel adapter for the year planner: config, preview, export and wallpaper."""

import cairosvg

from timeglance import paths
from timeglance.common import wallpaper
from timeglance.year import build as ybuild
from timeglance.year import render as yrender


class YearPlanner:
    """Adapts the year-at-a-glance renderer to the control panel's planner protocol."""

    name = "year"
    out_name = "year.png"
    template = ybuild.TEMPLATE

    @property
    def data(self):
        """Path to the working ``year/config.yaml``."""
        return paths.planner_config("year")

    @property
    def out(self):
        """Output directory for rendered year planners."""
        return paths.planner_out("year")

    def _raw(self):
        """Load the raw year config dict."""
        return ybuild.load(self.data)

    def build_cfg(self, p):
        """Build a resolved render config, applying the request's UI overrides onto the YAML."""
        raw = self._raw()
        for key in ("theme", "layout", "week_start", "size"):
            if p.get(key):
                raw[key] = p[key]
        if "week_align" in p:
            raw["week_align"] = p["week_align"] == "true"
        if p.get("start") or p.get("end"):
            r = raw.get("range") or {}
            raw["range"] = {
                "start": p.get("start") or r.get("start", "year-start"),
                "end": p.get("end") or r.get("end", "year-end"),
            }
        ybuild.assemble(raw)
        ybuild.resolve_size(raw)
        if "hide" in p:
            hide = set(filter(None, p["hide"].split(",")))
            for lyr in raw["layers"]:
                lyr["visible"] = lyr["id"] not in hide
        return yrender.parse(raw)

    def meta(self):
        """UI metadata: layers, themes, layouts, sizes, range, source summary and wallpaper info."""
        raw = self._raw()
        summary = ybuild.assemble(raw)
        backend = wallpaper.detect()
        wp = raw.get("wallpaper") or {}
        return {
            "layers": [
                {"id": lyr["id"], "label": lyr["label"], "color": lyr["color"], "visible": lyr.get("visible", True)}
                for lyr in raw["layers"]
            ],
            "themes": list(yrender.THEMES),
            "layouts": ybuild.ALL_LAYOUTS,
            "sizes": list(raw.get("sizes") or {}),
            "range": raw.get("range") or {"start": "year-start", "end": "year-end"},
            "week_start": raw.get("week_start", "Mon"),
            "theme": raw.get("theme") or "light",
            "layout": raw.get("layout") or "vertical",
            "week_align": raw.get("week_align", True),
            "size": raw.get("size", ""),
            "sources": summary,
            "wallpaper": wallpaper.ui_meta(backend, wp),
        }

    def preview(self, p):
        """Return the planner as an SVG preview for the request params."""
        return "image/svg+xml", yrender.render_svg(self.build_cfg(p)).encode()

    def export(self, p):
        """Render the planner to a PNG for download."""
        cfg = self.build_cfg(p)
        png = cairosvg.svg2png(
            bytestring=yrender.render_svg(cfg).encode(), output_width=cfg.width, output_height=cfg.height
        )
        return "image/png", self.out_name, png

    def set_wallpaper(self, p):
        """Render per-screen and set the planner as the desktop wallpaper."""
        backend = wallpaper.detect()
        if not backend:
            return {"ok": False, "error": "no supported wallpaper backend"}
        cfg = self.build_cfg(p)
        wp = self._raw().get("wallpaper") or {}
        screens = wallpaper.resolve_screens(backend, p.get("screens") or wp.get("screens", "all"))
        fill = p.get("fill") or wp.get("fill", "preserveAspectCrop")
        _, info = ybuild.apply_wallpaper(cfg, backend, screens, fill, self.out)
        return {"ok": True, **info}

    def warnings(self):
        """Return any event-source warnings from assembling the config."""
        raw = self._raw()
        ybuild.assemble(raw)
        return raw.get("_warnings", [])
