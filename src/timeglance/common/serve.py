#!/usr/bin/env python3
"""timeglance control panel: one web UI driving both planners.

Switch between the weekly routine sheet and the year-at-a-glance planner, edit each
planner's YAML, preview live, export to PNG/PDF, set the desktop wallpaper, and schedule a
daily re-render. Open http://localhost:8753 once it's running.
"""

import argparse
import datetime as dt
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cairosvg
import yaml

from timeglance import paths
from timeglance.common import schedule, wallpaper
from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild
from timeglance.year import render as yrender

WEB = Path(__file__).parent / "web"
STATE = paths.state_dir()
NO_CACHE = {"Cache-Control": "no-store"}


class YearPlanner:
    """Control-panel adapter for the year planner: config, preview, export and wallpaper."""

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
            "wallpaper": _wp_meta(backend, wp),
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


class WeeklyPlanner:
    """Control-panel adapter for the weekly sheet: config, preview, export and wallpaper."""

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

    def meta(self):
        """UI metadata: paper sizes, topic layers and wallpaper info."""
        raw = self._raw()
        backend = wallpaper.detect()
        wp = raw.get("wallpaper") or {}
        return {
            "papers": self.papers,
            "paper": "A4",
            "layers": [
                {"id": k, "label": t["label"], "color": t["color"], "visible": t.get("visible", True)}
                for k, t in raw.get("topics", {}).items()
            ],
            "wallpaper": _wp_meta(backend, wp),
        }

    def preview(self, p):
        """Return the sheet as an HTML preview for the request params."""
        html = wbuild.render(self._raw(), self._hide(p), p.get("paper", "A4"))
        return "text/html; charset=utf-8", html.encode()

    def export(self, p):
        """Render the sheet to a PDF for download."""
        pdf = wbuild.render_pdf(self._raw(), self._hide(p), p.get("paper", "A4"))
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
        pdf = wbuild.render_pdf(raw, self._hide(p), p.get("paper", "A4"))
        render_png = wbuild.make_wallpaper_renderer(
            pdf, wp.get("background", "#2b2f36"), wp.get("margin", 0.05), wbuild.resolve_shadow(wp)
        )
        _, info = wallpaper.apply(backend, screens, self.out, render_png, fill, prefix="weekly-wallpaper")
        return {"ok": True, **info}

    def warnings(self):
        """The weekly sheet has no external event sources, so never any warnings."""
        return []


def _planner_output(planner):
    """Path of the file this planner writes, relative to the project root (for the UI)."""
    return str((planner.out / planner.out_name).relative_to(paths.project_dir()))


def _wp_meta(backend, wp):
    """Build the wallpaper metadata block (availability, backend, screens, selection) for the UI."""
    return {
        "available": backend is not None,
        "backend": backend.name if backend else None,
        "screens": wallpaper.known(backend),
        "selected": wp.get("screens", "all"),
        "fill": wp.get("fill", "preserveAspectCrop"),
    }


PLANNERS = {"year": YearPlanner(), "weekly": WeeklyPlanner()}


def read_config(planner):
    """Read the planner's working config, falling back to its packaged template when absent."""
    path = planner.data if planner.data.exists() else planner.template
    return {"yaml": path.read_text(), "from_template": not planner.data.exists(), "path": planner.data.name}


def write_config(planner, text):
    """Validate ``text`` as YAML and write it to the planner's working config."""
    yaml.safe_load(text)  # validate; raises on bad YAML
    planner.data.write_text(text)


def reset_config(planner):
    """Overwrite the working config with the template, backing up the current file first.
    Returns the backup filename (or None if there was nothing to back up)."""
    backup = None
    if planner.data.exists():
        stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup = planner.data.with_name(f"{planner.data.name}.{stamp}.bak")
        backup.write_text(planner.data.read_text())
    planner.data.write_text(planner.template.read_text())
    return backup.name if backup else None


class EventLog:
    """Append-only activity log shared by the scheduler and the manual export/wallpaper
    actions, so every durable output (not live previews) leaves a trace under state/.
    A lock keeps concurrent writes from the threading HTTP server interleaved cleanly."""

    def __init__(self):
        """Open (creating as needed) the activity log under ``state/``."""
        STATE.mkdir(parents=True, exist_ok=True)
        self.path = STATE / "activity.log"
        self._lock = threading.Lock()

    def log(self, source, msg):
        """Append a timestamped ``source: msg`` line (thread-safe)."""
        line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {source}: {msg}"
        with self._lock, self.path.open("a") as f:
            f.write(line + "\n")

    def lines(self, n=200):
        """Return the last ``n`` log lines (empty if the log doesn't exist yet)."""
        if not self.path.exists():
            return []
        return self.path.read_text().splitlines()[-n:]

    def clear(self):
        """Empty the activity log."""
        self.path.write_text("")


LOG = EventLog()


class Scheduler:
    """Daily re-render loop. Sleeps until the configured HH:MM and renders the selected
    planners to disk (optionally setting the wallpaper), delegating the actual run to
    ``schedule.run_once``. Runs feed the shared activity log; config lives in
    ``schedule.yaml`` so a container restart keeps it."""

    def __init__(self):
        """Load the schedule config from ``schedule.yaml`` and set up the (stopped) loop."""
        self.cfg = schedule.load()
        self._thread = None
        self._stop = threading.Event()
        self.last_run = None
        self.next_run = None

    def save_cfg(self, cfg):
        """Merge updates into the schedule config (deep-merging per-planner blocks so a partial
        update keeps the rest, e.g. render overrides) and persist it to ``schedule.yaml``."""
        merged = {**self.cfg, **cfg}
        for name in PLANNERS:
            if name in cfg:
                merged[name] = {**(self.cfg.get(name) or {}), **cfg[name]}
        self.cfg = merged
        schedule.save(self.cfg)

    def run_once(self):
        """Render the selected planners now (see ``schedule.run_once``)."""
        self.last_run = dt.datetime.now().isoformat(timespec="seconds")
        schedule.run_once(self.cfg, PLANNERS, LOG)

    def _loop(self):
        """Background loop: sleep until the configured time, run once, repeat until stopped."""
        LOG.log("scheduler", "started")
        while not self._stop.is_set():
            hh, mm = (int(x) for x in self.cfg["time"].split(":"))
            now = dt.datetime.now()
            nxt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if nxt <= now:
                nxt += dt.timedelta(days=1)
            self.next_run = nxt.isoformat(timespec="seconds")
            if self._stop.wait((nxt - now).total_seconds()):
                break
            self.run_once()
        self.next_run = None
        LOG.log("scheduler", "stopped")

    @property
    def running(self):
        """True while the background loop thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """Start the background scheduler loop (no-op if already running)."""
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the background loop to stop."""
        self._stop.set()

    def status(self):
        """Return the scheduler's current state and config for the UI."""
        config = {}
        for name in PLANNERS:
            pc = schedule.planner_cfg(self.cfg, name)
            pc["render_yaml"] = schedule.dump_render(pc["render"])
            config[name] = pc
        return {
            "running": self.running,
            "time": self.cfg["time"],
            "tz": schedule.local_tz(),
            "planners": self.cfg.get("planners", []),
            "config": config,
            "outputs": {name: _planner_output(p) for name, p in PLANNERS.items()},
            "screens": wallpaper.known(wallpaper.detect()),
            "last_run": self.last_run,
            "next_run": self.next_run,
        }


SCHED = Scheduler()


class Handler(BaseHTTPRequestHandler):
    """HTTP handler serving the SPA assets and the ``/api/*`` endpoints."""

    def log_message(self, *a):
        """Silence the default per-request stderr logging."""
        pass

    def _send(self, code, ctype, body, extra=None):
        """Send a response with the given status, content type, body and extra headers."""
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        """Send ``obj`` as a JSON response."""
        self._send(code, "application/json", json.dumps(obj).encode())

    def _planner(self, params):
        """Resolve the target planner from request params (defaults to the year planner)."""
        return PLANNERS[params.get("planner", "year")]

    def _body(self):
        """Parse and return the JSON request body (empty dict if none)."""
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        """Route GET requests: static assets, config, preview, export, schedule and log."""
        u = urlparse(self.path)
        p = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                self._send(200, "text/html; charset=utf-8", (WEB / "index.html").read_bytes(), NO_CACHE)
            elif u.path == "/app.js":
                self._send(200, "text/javascript", (WEB / "app.js").read_bytes(), NO_CACHE)
            elif u.path == "/favicon.svg":
                self._send(200, "image/svg+xml", (WEB / "favicon.svg").read_bytes())
            elif u.path == "/favicon.ico":
                self._send(200, "image/x-icon", (WEB / "favicon.ico").read_bytes())
            elif u.path == "/icon.png":
                self._send(200, "image/png", (WEB / "icon.png").read_bytes())
            elif u.path == "/api/config":
                self._json({"meta": self._planner(p).meta(), **read_config(self._planner(p))})
            elif u.path == "/api/preview":
                ctype, body = self._planner(p).preview(p)
                self._send(200, ctype, body)
            elif u.path == "/api/export":
                planner = self._planner(p)
                ctype, fname, body = planner.export(p)
                fmt = fname.rsplit(".", 1)[-1].upper()
                LOG.log(planner.name, f"exported {fname} ({fmt}, {schedule.human_size(len(body))})")
                self._send(200, ctype, body, {"Content-Disposition": f'inline; filename="{fname}"'})
            elif u.path == "/api/schedule":
                self._json(SCHED.status())
            elif u.path == "/api/log":
                self._json({"log": LOG.lines()})
            else:
                self._send(404, "text/plain", "not found")
        except ValueError as e:
            self._json({"error": str(e)}, 400)
        except Exception:
            self._json({"error": traceback.format_exc().strip()}, 500)

    def do_POST(self):
        """Route POST requests: config save/reset, wallpaper, log clear and schedule control."""
        u = urlparse(self.path)
        p = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/config":
                write_config(self._planner(p), self._body()["yaml"])
                self._json({"ok": True})
            elif u.path == "/api/config/reset":
                backup = reset_config(self._planner(p))
                self._json({"meta": self._planner(p).meta(), "backup": backup, **read_config(self._planner(p))})
            elif u.path == "/api/wallpaper":
                planner = self._planner(p)
                r = planner.set_wallpaper(self._body())
                if r["ok"]:
                    detail = ",".join(r["applied"]) or "nothing matched"
                    if r.get("pending"):
                        detail += f"; pending {','.join(r['pending'])}"
                    if r.get("unseen"):
                        detail += f"; unseen {','.join(r['unseen'])}"
                    LOG.log(planner.name, f"wallpaper set {detail} (manual)")
                else:
                    LOG.log(planner.name, f"wallpaper FAILED {r['error']} (manual)")
                self._json(r)
            elif u.path == "/api/log/clear":
                LOG.clear()
                self._json({"ok": True})
            elif u.path == "/api/screens/forget":
                wallpaper.forget(self._body()["name"])
                self._json({"ok": True})
            elif u.path == "/api/schedule":
                body = self._body()
                keys = ("time", "planners", "autostart", *PLANNERS)
                cfg = {k: body[k] for k in keys if k in body}
                for name in PLANNERS:
                    if name in cfg and "render" in cfg[name]:
                        try:
                            cfg[name]["render"] = schedule.parse_render(cfg[name]["render"])
                        except yaml.YAMLError as e:
                            return self._json({"error": f"{name}: invalid override YAML - {e}"}, 400)
                SCHED.save_cfg(cfg)
                if body.get("action") == "start":
                    SCHED.start()
                elif body.get("action") == "stop":
                    SCHED.stop()
                elif body.get("action") == "run":
                    threading.Thread(target=SCHED.run_once, daemon=True).start()
                self._json(SCHED.status())
            else:
                self._send(404, "text/plain", "not found")
        except Exception:
            self._json({"error": traceback.format_exc().strip()}, 500)


def main():
    """CLI entry point: start the scheduler (if autostart) and serve the control panel."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 in a container)")
    ap.add_argument("--port", type=int, default=8753)
    args = ap.parse_args()
    if SCHED.cfg.get("autostart"):
        SCHED.start()
    print(f"timeglance -> http://{args.host}:{args.port}  (Ctrl-C to stop)")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
