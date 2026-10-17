"""Control-panel adapter for the weekly sheet: config, preview, export and wallpaper."""

from timeglance import paths
from timeglance.common import wallpaper
from timeglance.weekly import build as wbuild


class WeeklyPlanner:
    """Adapts the weekly routine renderer to the control panel's planner protocol."""

    name = "weekly"
    out_name = "weekly.pdf"
    template = wbuild.TEMPLATE
    papers = ["A4", "A3"]

    @property
    def data(self):
        """Path to the working ``weekly/config.yaml``."""
        return paths.planner_config("weekly")

    @property
    def out(self):
        """Output directory for rendered weekly sheets."""
        return paths.planner_out("weekly")

    def _raw(self):
        """Load the raw weekly config dict."""
        return wbuild.load(self.data)

    def _hide(self, p):
        """Hidden-topic set from the request's ``hide`` param, or None to use YAML defaults."""
        return set(filter(None, p["hide"].split(","))) if "hide" in p else None

    def _variant(self, raw, p):
        """Resolve (theme, layout) with request params overriding the YAML, falling back to defaults."""
        return (
            p.get("theme") or raw.get("theme") or "light",
            p.get("layout") or raw.get("layout") or "vertical",
        )

    def meta(self):
        """UI metadata: paper sizes, themes, layouts, topic layers and wallpaper info."""
        raw = self._raw()
        backend = wallpaper.detect()
        wp = raw.get("wallpaper") or {}
        theme, layout = self._variant(raw, {})
        return {
            "papers": self.papers,
            "paper": raw.get("paper", "A4"),
            "themes": wbuild.ALL_THEMES,
            "layouts": wbuild.ALL_LAYOUTS,
            "theme": theme,
            "layout": layout,
            "layers": [
                {"id": k, "label": t["label"], "color": t["color"], "visible": t.get("visible", True)}
                for k, t in raw.get("topics", {}).items()
            ],
            "wallpaper": wallpaper.ui_meta(backend, wp),
        }

    def preview(self, p):
        """Return the sheet as an HTML preview for the request params."""
        raw = self._raw()
        theme, layout = self._variant(raw, p)
        html = wbuild.render(raw, self._hide(p), p.get("paper", "A4"), theme=theme, layout=layout)
        return "text/html; charset=utf-8", html.encode()

    def export(self, p):
        """Render the sheet to a PDF for download."""
        raw = self._raw()
        theme, layout = self._variant(raw, p)
        pdf = wbuild.render_pdf(raw, self._hide(p), p.get("paper", "A4"), theme=theme, layout=layout)
        return "application/pdf", self.out_name, pdf

    def set_wallpaper(self, p):
        """Composite the sheet onto a themed canvas and set it as the desktop wallpaper."""
        backend = wallpaper.detect()
        if not backend:
            return {"ok": False, "error": "no supported wallpaper backend"}
        raw = self._raw()
        wp = raw.get("wallpaper") or {}
        screens = wallpaper.resolve_screens(backend, p.get("screens") or wp.get("screens", "all"))
        fill = p.get("fill") or wp.get("fill", "preserveAspectCrop")
        theme, layout = self._variant(raw, p)
        pdf = wbuild.render_pdf(raw, self._hide(p), p.get("paper", "A4"), theme=theme, layout=layout)
        render_png = wbuild.make_wallpaper_renderer(
            pdf, wp.get("background", "#2b2f36"), wp.get("margin", 0.05), wbuild.resolve_shadow(wp)
        )
        _, info = wallpaper.apply(backend, screens, self.out, render_png, fill, prefix="weekly-wallpaper")
        return {"ok": True, **info}

    def warnings(self):
        """The weekly sheet has no external event sources, so never any warnings."""
        return []
