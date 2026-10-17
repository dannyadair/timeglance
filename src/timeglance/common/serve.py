#!/usr/bin/env python3
"""timeglance control panel: one web UI driving both planners.

Switch between the weekly routine sheet and the year-at-a-glance planner, edit each
planner's YAML, preview live, export to PNG/PDF, set the desktop wallpaper, and schedule a
daily re-render. Open http://localhost:8753 once it's running.

This module is just the HTTP layer: it routes ``/api/*`` to the planners, the config
plumbing, the activity log and the scheduler, and serves the single-page UI assets.
"""

import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from timeglance import __version__, init, service
from timeglance.common import schedule, wallpaper
from timeglance.common.config import read_config, reset_config, write_config
from timeglance.common.format import png_size
from timeglance.common.log import LOG
from timeglance.common.scheduler import SCHED
from timeglance.planners import PLANNERS

WEB = Path(__file__).parent / "web"
NO_CACHE = {"Cache-Control": "no-store"}


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
        """Resolve the target planner from request params (defaults to the weekly planner)."""
        return PLANNERS[params.get("planner", "weekly")]

    def _sched_status(self):
        """Scheduler state plus whether the systemd render service is available/installed."""
        return {**SCHED.status(), "systemd": service.available(), "installed": service.enabled()}

    def _body(self):
        """Parse and return the JSON request body (empty dict if none)."""
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        """Route GET requests: static assets, config, preview, export, schedule and log."""
        u = urlparse(self.path)
        p = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
        try:
            if u.path == "/":
                html = (WEB / "index.html").read_text().replace("__TG_VERSION__", __version__)
                self._send(200, "text/html; charset=utf-8", html, NO_CACHE)
            elif u.path.startswith("/js/") and u.path.count("/") == 2 and u.path.endswith(".js"):
                mod = WEB / "js" / u.path.rsplit("/", 1)[-1]
                if mod.is_file():
                    self._send(200, "text/javascript", mod.read_bytes(), NO_CACHE)
                else:
                    self._send(404, "text/plain", "not found")
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
                detail = f" ({png_size(body)})" if ctype == "image/png" else ""
                LOG.log(planner.name, f"exported {fname}{detail}")
                self._send(200, ctype, body, {"Content-Disposition": f'inline; filename="{fname}"'})
            elif u.path == "/api/schedule":
                self._json(self._sched_status())
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
        p = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
        try:
            if u.path == "/api/config":
                planner = self._planner(p)
                write_config(planner, self._body()["yaml"])
                LOG.log(planner.name, "config saved")
                self._json({"ok": True})
            elif u.path == "/api/config/reset":
                planner = self._planner(p)
                backup = reset_config(planner)
                LOG.log(planner.name, f"config reset to template{f'; backup {backup}' if backup else ''}")
                self._json({"meta": planner.meta(), "backup": backup, **read_config(planner)})
            elif u.path == "/api/wallpaper":
                planner = self._planner(p)
                r = planner.set_wallpaper(self._body())
                if r["ok"]:
                    lines = wallpaper.describe_apply(r)
                    lines[-1] += " (manual)"
                    for line in lines:
                        LOG.log(planner.name, line)
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
                keys = ("time", "planners", "enabled", *PLANNERS)
                cfg = {k: body[k] for k in keys if k in body}
                for name in PLANNERS:
                    if name in cfg and "render" in cfg[name]:
                        try:
                            cfg[name]["render"] = schedule.parse_render(cfg[name]["render"])
                        except yaml.YAMLError as e:
                            return self._json({"error": f"{name}: invalid override YAML - {e}"}, 400)
                SCHED.save_cfg(cfg)
                action = body.get("action")
                if action == "install":
                    service.install()
                    SCHED.stop()
                elif action == "uninstall":
                    service.uninstall()
                    SCHED.start()
                elif action == "run":
                    threading.Thread(target=SCHED.run_once, daemon=True).start()
                elif service.enabled():
                    service.install()
                self._json(self._sched_status())
            else:
                self._send(404, "text/plain", "not found")
        except Exception:
            self._json({"error": traceback.format_exc().strip()}, 500)


def run(host, port):
    """Scaffold any missing config, start the scheduler if configured, and serve the panel."""
    written = init.ensure()
    if written:
        noun = "a sample one" if len(written) == 1 else "samples"
        LOG.log("init", f"no config found, created {noun}: {', '.join(str(p) for p in written)}")
    if not service.enabled():
        SCHED.start()
    try:
        httpd = ThreadingHTTPServer((host, port), Handler)
    except OSError as e:
        raise SystemExit(f"cannot serve on {host}:{port} - {e.strerror or e}") from e
    LOG.log("server", f"listening on http://{host}:{port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        LOG.log("server", "stopped")
