"""Desktop wallpaper backends, shared by the year planner and the weekly sheet.

detect() returns a backend for the running desktop, or None so callers can hide the
feature. Only KDE Plasma is implemented today; the Backend shape (name, list_screens,
apply) is the seam for adding GNOME, wlroots (swww), etc. later.

Plasma sets each screen independently via a Plasma scripting snippet (evaluateScript
over the session bus), matching containments to outputs by logical geometry, so we can
render one screen at its current resolution and leave the others untouched.

apply() is the generic driver: it walks the chosen screens, hands each to a caller-
supplied render_png(screen, path) callback, and sets the results. The callback is the
only planner-specific part (year rasterises its SVG; weekly composites its PDF).
"""

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from timeglance import paths

# org.kde.image FillMode enum
FILL_MODES = {"stretch": 0, "preserveAspectFit": 1, "preserveAspectCrop": 2, "tile": 3, "pad": 6}


@dataclass
class Screen:
    """One output: logical geometry (for matching Plasma) and physical pixels.

    A remembered-but-disconnected screen has ``connected=False`` and no live geometry (zeros):
    we can still render its file at the remembered ``pw``x``ph``, but can't assign it in Plasma
    until it's back. A screen named in config that we've never seen has ``seen=False`` and no
    resolution either, so it can only be shown as FYI - we can't render a file for it."""

    name: str
    x: int  # logical position
    y: int
    lw: int  # logical size (for matching Plasma's screenGeometry)
    lh: int
    pw: int  # physical size of the current mode (the render target)
    ph: int
    primary: bool = False
    model: str = ""  # friendly name from EDID, e.g. "DELL U3821DW"
    connected: bool = True
    seen: bool = True


def _edid_model(name):
    """Human name from the display's EDID (the 0xFC 'monitor name' descriptor), matched by
    DRM connector (e.g. `DP-8` -> `/sys/class/drm/*-DP-8/edid`). '' when there's no such
    descriptor, as is common for laptop panels."""
    for path in Path("/sys/class/drm").glob(f"*-{name}/edid"):
        data = path.read_bytes()
        if len(data) < 128:
            return ""
        for i in range(54, 126, 18):
            d = data[i : i + 18]
            if d[0:3] == b"\x00\x00\x00" and d[3] == 0xFC:
                return d[5:18].split(b"\n")[0].decode("ascii", "replace").strip()
    return ""


class PlasmaBackend:
    """KDE Plasma wallpaper backend: reads outputs via kscreen-doctor, sets images via dbus."""

    name = "plasma"

    def list_screens(self):
        """Return the enabled outputs as :class:`Screen` objects (via ``kscreen-doctor --json``)."""
        out = subprocess.run(["kscreen-doctor", "--json"], capture_output=True, text=True, check=True)
        screens = []
        for o in json.loads(out.stdout)["outputs"]:
            if not o["enabled"]:
                continue
            mode = next(m for m in o["modes"] if m["id"] == o["currentModeId"])
            pw, ph = mode["size"]["width"], mode["size"]["height"]
            scale = o["scale"] or 1
            screens.append(
                Screen(
                    name=o["name"],
                    x=o["pos"]["x"],
                    y=o["pos"]["y"],
                    lw=round(pw / scale),
                    lh=round(ph / scale),
                    pw=pw,
                    ph=ph,
                    primary=o["priority"] == 1,
                    model=_edid_model(o["name"]),
                )
            )
        return screens

    def _script(self, assignments, fill, bust=""):
        """Build the Plasma scripting snippet that matches desktops by geometry and sets images.

        ``bust`` is appended as a URL fragment (``file://…#bust``); Qt drops it when resolving the
        file, so the same stable path is loaded but the changed string forces org.kde.image to
        reload instead of keeping its cached pixmap."""
        mode = FILL_MODES.get(fill, 2)
        frag = f"#{bust}" if bust else ""
        want = ",".join(f"{{x:{s.x},y:{s.y},w:{s.lw},h:{s.lh},path:'file://{path}{frag}'}}" for s, path in assignments)
        # Match each Plasma desktop to a target by logical geometry, set the image, and report
        # back which geometries exist and which got set so callers can tell if a match happened.
        return (
            f"var want=[{want}]; var ds=desktops(); var found=[], done=[];"
            "for (var i=0;i<ds.length;i++){"
            " var d=ds[i], g=screenGeometry(d.screen), key=g.x+','+g.y+','+g.width+'x'+g.height, hit=null;"
            " found.push(key);"
            " for (var j=0;j<want.length;j++){"
            "  if(g.x==want[j].x&&g.y==want[j].y&&g.width==want[j].w&&g.height==want[j].h){hit=want[j];break;}"
            " }"
            " if(hit){"
            "  d.wallpaperPlugin='org.kde.image';"
            "  d.currentConfigGroup=['Wallpaper','org.kde.image','General'];"
            f"  d.writeConfig('FillMode',{mode});"
            "  d.writeConfig('Image',hit.path); done.push(key);"
            " }"
            "}"
            # evaluateScript returns the script's print() output, not its last expression.
            "print(JSON.stringify({desktops:found, set:done}));"
        )

    def apply(self, assignments, fill="preserveAspectCrop", bust=""):
        """assignments: list of (Screen, png Path). Returns {"desktops": [...], "set": [...]}
        of logical-geometry keys (x,y,wxh) so callers can see which desktops actually matched."""
        r = subprocess.run(
            [
                "dbus-send",
                "--session",
                "--print-reply=literal",
                "--type=method_call",
                "--dest=org.kde.plasmashell",
                "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript",
                "string:" + self._script(assignments, fill, bust),
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"plasma evaluateScript failed: {(r.stderr or r.stdout).strip()}")
        m = re.search(r"\{.*\}", r.stdout, re.S)
        return json.loads(m.group(0)) if m else {"desktops": [], "set": []}


def detect():
    """Return a backend for the running desktop (only Plasma today), or None if unsupported."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    plasma = "KDE" in desktop.split(":") or os.environ.get("KDE_FULL_SESSION") == "true"
    if plasma and shutil.which("kscreen-doctor") and shutil.which("dbus-send"):
        return PlasmaBackend()
    return None


def _registry_path():
    """Path to the remembered-screens registry under ``state/``."""
    return paths.state_dir() / "screens.json"


def _load_registry():
    """Load the remembered-screens registry (name -> model/pw/ph/last_seen), or empty."""
    p = _registry_path()
    return json.loads(p.read_text()) if p.exists() else {}


def remember(screens):
    """Record each connected screen's model, pixel size and today's date, so a later run or
    the UI can still target it once it's unplugged. No-op write when nothing changed."""
    reg = _load_registry()
    today = dt.date.today().isoformat()
    for s in screens:
        reg[s.name] = {"model": s.model, "pw": s.pw, "ph": s.ph, "last_seen": today}
    text = json.dumps(reg, indent=2)
    p = _registry_path()
    if not p.exists() or p.read_text() != text:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def forget(name):
    """Drop a screen from the registry (e.g. a retired monitor)."""
    reg = _load_registry()
    if reg.pop(name, None) is not None:
        _registry_path().write_text(json.dumps(reg, indent=2))


def known(backend, prune_days=30):
    """Screens the UI should offer: every connected output plus remembered ones seen within
    ``prune_days`` (each tagged ``connected``). Refreshes the registry and prunes staler ones."""
    live = {s.name: s for s in (backend.list_screens() if backend else [])}
    remember(live.values())
    reg = _load_registry()
    cutoff = (dt.date.today() - dt.timedelta(days=prune_days)).isoformat()
    out, stale = [], []
    for name, info in reg.items():
        if name in live:
            s = live[name]
            out.append(
                {
                    "name": name,
                    "model": s.model,
                    "w": s.pw,
                    "h": s.ph,
                    "primary": s.primary,
                    "connected": True,
                    "last_seen": info["last_seen"],
                }
            )
        elif info["last_seen"] >= cutoff:
            out.append(
                {
                    "name": name,
                    "model": info["model"],
                    "w": info["pw"],
                    "h": info["ph"],
                    "primary": False,
                    "connected": False,
                    "last_seen": info["last_seen"],
                }
            )
        else:
            stale.append(name)
    if stale:
        for name in stale:
            reg.pop(name)
        _registry_path().write_text(json.dumps(reg, indent=2))
    return out


def ui_meta(backend, wp):
    """Wallpaper metadata (availability, backend, known screens, current selection) for the UI."""
    return {
        "available": backend is not None,
        "backend": backend.name if backend else None,
        "screens": known(backend),
        "selected": wp.get("screens", "all"),
        "fill": wp.get("fill", "preserveAspectCrop"),
    }


def resolve_screens(backend, spec):
    """spec: 'all' | 'primary' | comma-string | list of names. 'all'/'primary' cover connected
    outputs only. An explicit name may be a remembered-but-disconnected screen (resolved from the
    registry so its file is still rendered and applied once it reconnects) or one we've never seen
    - a hand-edited config id, or state that was cleared - returned flagged ``seen=False`` with no
    resolution, so callers can list it as FYI and skip rendering it."""
    screens = backend.list_screens()
    if not spec or spec == "all":
        return screens
    if spec == "primary":
        return [s for s in screens if s.primary] or screens[:1]
    want = spec if isinstance(spec, list) else [s.strip() for s in str(spec).split(",")]
    by_name = {s.name: s for s in screens}
    reg = _load_registry()
    resolved = []
    for w in want:
        if w in by_name:
            resolved.append(by_name[w])
        elif w in reg:
            info = reg[w]
            resolved.append(Screen(w, 0, 0, 0, 0, info["pw"], info["ph"], model=info["model"], connected=False))
        else:
            resolved.append(Screen(w, 0, 0, 0, 0, 0, 0, connected=False, seen=False))
    return resolved


def apply(backend, screens, out, render_png, fill="preserveAspectCrop", prefix="wallpaper"):
    """Render each screen via render_png(screen, path) and set the results.

    render_png must write a PNG for `screen` to `path` (sized however the planner wants;
    for a crisp result render at screen.pw x screen.ph). Screens that share a resolution
    reuse one render. Each screen gets a stable `{prefix}-{name}.png`, overwritten in place:
    a disconnected output then picks up the fresh image when it reconnects, since Plasma
    restores its remembered path and reloads from disk. A connected output is nudged to
    reload via the `#stamp` cache-bust (see PlasmaBackend._script). `prefix` is planner-scoped
    (e.g. `year-wallpaper`) so both planners' files can share one directory.

    Disconnected screens (``connected=False``) are rendered and written but not assigned in
    Plasma - their fresh file waits on disk for reconnection. Never-seen screens (``seen=False``)
    have no resolution, so they're neither rendered nor assigned, only reported. Returns
    (assignments, info) where info has `requested`, `written`, `applied`, `pending`
    (written-but-disconnected) and `unseen` (skipped) names plus the detected `desktops`
    geometries, so a geometry mismatch is visible, not silent.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = str(int(time.time() * 1000))
    rendered = {}  # (w, h) -> png path to copy from for same-resolution screens
    assignments = []  # connected screens, to assign in Plasma
    for scr in screens:
        if not scr.seen:
            continue
        png = out / f"{prefix}-{scr.name}.png"
        res = (scr.pw, scr.ph)
        if res in rendered:
            shutil.copyfile(rendered[res], png)
        else:
            render_png(scr, png)
            rendered[res] = png
        if scr.connected:
            assignments.append((scr, png))
    report = backend.apply(assignments, fill, bust=stamp) if assignments else {"desktops": [], "set": []}
    by_key = {f"{s.x},{s.y},{s.lw}x{s.lh}": s.name for s, _ in assignments}
    info = {
        "requested": [s.name for s in screens],
        "written": [s.name for s in screens if s.seen],
        "applied": [by_key[k] for k in report.get("set", []) if k in by_key],
        "pending": [s.name for s in screens if s.seen and not s.connected],
        "unseen": [s.name for s in screens if not s.seen],
        "desktops": report.get("desktops", []),
    }
    return assignments, info
