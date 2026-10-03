#!/usr/bin/env python3
"""timeglance control panel: one web UI driving both tools.

Switch between the weekly routine sheet and the year-at-a-glance planner, edit each
tool's YAML, preview live, export to PNG/PDF, set the desktop wallpaper, and schedule a
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
from timeglance.common import wallpaper
from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild
from timeglance.year import render as yrender

WEB = Path(__file__).parent / "web"
STATE = paths.state_dir()
NO_CACHE = {"Cache-Control": "no-store"}


class YearTool:
    """Control-panel adapter for the year planner: config, preview, export and wallpaper."""

    name = "year"
    template = ybuild.TEMPLATE

    @property
    def data(self):
        """Path to the working ``year/config.yaml``."""
        return paths.tool_config("year")

    @property
    def out(self):
        """Output directory for rendered year planners."""
        return paths.tool_out("year")

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
        return "image/png", "year.png", png

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


class WeeklyTool:
    """Control-panel adapter for the weekly sheet: config, preview, export and wallpaper."""

    name = "weekly"
    template = wbuild.TEMPLATE
    papers = ["A4", "A3"]

    @property
    def data(self):
        """Path to the working ``weekly/config.yaml``."""
        return paths.tool_config("weekly")

    @property
    def out(self):
        """Output directory for rendered weekly sheets."""
        return paths.tool_out("weekly")

    def _raw(self):
        """Load the raw weekly config dict."""
        return wbuild.load(self.data)

    def _hide(self, p):
        """Hidden-activity set from the request's ``hide`` param, or None to use YAML defaults."""
        return set(filter(None, p["hide"].split(","))) if "hide" in p else None

    def meta(self):
        """UI metadata: paper sizes, activity layers and wallpaper info."""
        raw = self._raw()
        backend = wallpaper.detect()
        wp = raw.get("wallpaper") or {}
        return {
            "papers": self.papers,
            "paper": "A4",
            "layers": [
                {"id": k, "label": a["label"], "color": a["color"], "visible": a.get("visible", True)}
                for k, a in raw.get("activities", {}).items()
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
        return "application/pdf", "weekly.pdf", pdf

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


def _screen_list(backend):
    """Serialise the backend's screens for the UI (empty when there's no backend)."""
    return [
        {"name": s.name, "w": s.pw, "h": s.ph, "primary": s.primary, "model": s.model}
        for s in (backend.list_screens() if backend else [])
    ]


def _human_size(n):
    """Format a byte count as a human-readable KB/MB string."""
    kb = n / 1024
    return f"{kb:.0f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB"


def _wp_meta(backend, wp):
    """Build the wallpaper metadata block (availability, backend, screens, selection) for the UI."""
    return {
        "available": backend is not None,
        "backend": backend.name if backend else None,
        "screens": _screen_list(backend),
        "selected": wp.get("screens", "all"),
        "fill": wp.get("fill", "preserveAspectCrop"),
    }


TOOLS = {"year": YearTool(), "weekly": WeeklyTool()}


def read_config(tool):
    """Read the tool's working config, falling back to its packaged template when absent."""
    path = tool.data if tool.data.exists() else tool.template
    return {"yaml": path.read_text(), "from_template": not tool.data.exists(), "path": tool.data.name}


def write_config(tool, text):
    """Validate ``text`` as YAML and write it to the tool's working config."""
    yaml.safe_load(text)  # validate; raises on bad YAML
    tool.data.write_text(text)


def reset_config(tool):
    """Overwrite the working config with the template, backing up the current file first.
    Returns the backup filename (or None if there was nothing to back up)."""
    backup = None
    if tool.data.exists():
        stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup = tool.data.with_name(f"{tool.data.name}.{stamp}.bak")
        backup.write_text(tool.data.read_text())
    tool.data.write_text(tool.template.read_text())
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
    """Daily re-render loop. Sleeps until the configured HH:MM, runs the selected tools
    (writing outputs and, where a backend exists, setting the wallpaper). Runs feed the
    shared activity log; config persists under state/ so a container restart keeps it."""

    def __init__(self):
        """Load persisted schedule config from ``state/`` and set up the (stopped) loop."""
        STATE.mkdir(parents=True, exist_ok=True)
        self.cfg_path = STATE / "schedule.json"
        self.cfg = self._load_cfg()
        self._thread = None
        self._stop = threading.Event()
        self.last_run = None
        self.next_run = None

    def _load_cfg(self):
        """Load the persisted schedule config, or defaults on first run."""
        if self.cfg_path.exists():
            return json.loads(self.cfg_path.read_text())
        return {"time": "06:00", "tools": ["year"], "wallpaper": True}

    def save_cfg(self, cfg):
        """Merge updates into the schedule config and persist it."""
        self.cfg = {**self.cfg, **cfg}
        self.cfg_path.write_text(json.dumps(self.cfg, indent=2))

    def run_once(self):
        """Render every selected tool, isolating failures so one bad tool/feed can't
        sink the rest; each outcome (including tracebacks) lands in the log."""
        self.last_run = dt.datetime.now().isoformat(timespec="seconds")
        for name in self.cfg.get("tools", []):
            tool = TOOLS[name]
            try:
                ctype, fname, data = tool.export({})
                (tool.out).mkdir(parents=True, exist_ok=True)
                (tool.out / fname).write_bytes(data)
                LOG.log(name, f"wrote {fname} ({_human_size(len(data))})")
                for w in tool.warnings():
                    LOG.log(name, f"WARNING {w}")
                if not self.cfg.get("wallpaper"):
                    continue
                if not wallpaper.detect():
                    LOG.log(name, "wallpaper skipped (no backend)")
                    continue
                scr = (self.cfg.get("screens") or {}).get(name)
                r = tool.set_wallpaper({"screens": scr} if scr else {})
                detail = "set " + ",".join(r["applied"]) if r["ok"] else "FAILED " + r["error"]
                LOG.log(name, f"wallpaper {detail}")
            except Exception:
                LOG.log(name, f"ERROR\n{traceback.format_exc().strip()}")

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
        return {
            "running": self.running,
            "time": self.cfg["time"],
            "tools": self.cfg["tools"],
            "wallpaper": self.cfg.get("wallpaper", True),
            "screens": self.cfg.get("screens", {}),
            "wp_screens": _screen_list(wallpaper.detect()),
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

    def _tool(self, params):
        """Resolve the target tool from request params (defaults to the year planner)."""
        return TOOLS[params.get("tool", "year")]

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
                self._json({"meta": self._tool(p).meta(), **read_config(self._tool(p))})
            elif u.path == "/api/preview":
                ctype, body = self._tool(p).preview(p)
                self._send(200, ctype, body)
            elif u.path == "/api/export":
                tool = self._tool(p)
                ctype, fname, body = tool.export(p)
                fmt = fname.rsplit(".", 1)[-1].upper()
                LOG.log(tool.name, f"exported {fname} ({fmt}, {_human_size(len(body))})")
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
                write_config(self._tool(p), self._body()["yaml"])
                self._json({"ok": True})
            elif u.path == "/api/config/reset":
                backup = reset_config(self._tool(p))
                self._json({"meta": self._tool(p).meta(), "backup": backup, **read_config(self._tool(p))})
            elif u.path == "/api/wallpaper":
                tool = self._tool(p)
                r = tool.set_wallpaper(self._body())
                if r["ok"]:
                    LOG.log(tool.name, f"wallpaper set {','.join(r['applied']) or 'nothing matched'} (manual)")
                else:
                    LOG.log(tool.name, f"wallpaper FAILED {r['error']} (manual)")
                self._json(r)
            elif u.path == "/api/log/clear":
                LOG.clear()
                self._json({"ok": True})
            elif u.path == "/api/schedule":
                body = self._body()
                SCHED.save_cfg({k: body[k] for k in ("time", "tools", "wallpaper", "screens") if k in body})
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
