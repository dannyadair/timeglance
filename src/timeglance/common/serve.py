#!/usr/bin/env python3
"""timeglance control panel: one web UI driving both planners.

Switch between the weekly routine sheet and the year-at-a-glance planner, edit each
planner's YAML, preview live, export to PNG/PDF, set the desktop wallpaper, and schedule a
daily re-render. Open http://localhost:8753 once it's running.

This module is just the HTTP layer: it routes ``/api/*`` to the planners, the config
plumbing, the activity log and the scheduler, and serves the single-page UI assets.
"""

import argparse
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from timeglance.common import schedule, wallpaper
from timeglance.common.config import read_config, reset_config, write_config
from timeglance.common.format import human_size
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
                fmt = fname.rsplit(".", 1)[-1].upper()
                LOG.log(planner.name, f"exported {fname} ({fmt}, {human_size(len(body))})")
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
    if SCHED.schedule.cfg.get("autostart"):
        SCHED.start()
    print(f"timeglance -> http://{args.host}:{args.port}  (Ctrl-C to stop)")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
