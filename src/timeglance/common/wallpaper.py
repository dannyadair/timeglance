"""Desktop wallpaper backends, shared by the year planner and the weekly sheet.

detect() returns a backend for the running desktop, or None so callers can hide the
feature. Only KDE Plasma is implemented today; the Backend shape (name, list_screens,
apply) is the seam for adding GNOME, wlroots (swww), etc. later.

Plasma sets each screen independently via a Plasma scripting snippet (evaluateScript
over the session bus), matching containments to outputs by logical geometry, so we can
render one screen at its native resolution and leave the others untouched.

apply() is the generic driver: it walks the chosen screens, hands each to a caller-
supplied render_png(screen, path) callback, and sets the results. The callback is the
only tool-specific part (year rasterises its SVG; weekly composites its PDF).
"""

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

# org.kde.image FillMode enum
FILL_MODES = {"stretch": 0, "preserveAspectFit": 1, "preserveAspectCrop": 2, "tile": 3, "pad": 6}


@dataclass
class Screen:
    """One connected output: logical geometry (for matching Plasma) and physical pixels."""

    name: str
    x: int  # logical position
    y: int
    lw: int  # logical size (for matching Plasma's screenGeometry)
    lh: int
    pw: int  # physical size (for rendering at native resolution)
    ph: int
    primary: bool = False
    model: str = ""  # friendly name from EDID, e.g. "DELL U3821DW"


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

    def _script(self, assignments, fill):
        """Build the Plasma scripting snippet that matches desktops by geometry and sets images."""
        mode = FILL_MODES.get(fill, 2)
        want = ",".join(f"{{x:{s.x},y:{s.y},w:{s.lw},h:{s.lh},path:'file://{path}'}}" for s, path in assignments)
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

    def apply(self, assignments, fill="preserveAspectCrop"):
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
                "string:" + self._script(assignments, fill),
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


def resolve_screens(backend, spec):
    """spec: 'all' | 'primary' | comma-string | list of output names."""
    screens = backend.list_screens()
    if not spec or spec == "all":
        return screens
    if spec == "primary":
        return [s for s in screens if s.primary] or screens[:1]
    want = spec if isinstance(spec, list) else [s.strip() for s in str(spec).split(",")]
    by_name = {s.name: s for s in screens}
    bad = [w for w in want if w not in by_name]
    if bad:
        raise SystemExit(f"unknown screen(s): {', '.join(bad)}  (have: {', '.join(by_name)})")
    return [by_name[w] for w in want]


def apply(backend, screens, out, render_png, fill="preserveAspectCrop", prefix="wallpaper"):
    """Render each screen via render_png(screen, path) and set the results.

    render_png must write a PNG for `screen` to `path` (sized however the tool wants;
    for a crisp result render at screen.pw x screen.ph). Screens that share a resolution
    reuse one render. Each run writes a fresh `{prefix}-{w}x{h}-{stamp}.png` and prunes the
    tool's older files of that resolution: Plasma's org.kde.image only reloads when the path
    string changes, so a stable filename would leave the cached pixmap in place. `prefix` is
    tool-scoped (e.g. `year-wallpaper`) so both tools' files can share one directory.
    Returns (assignments, info) where info has `requested`/`applied` screen names and the
    detected `desktops` geometries (so a geometry mismatch is visible, not silent).
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = str(int(time.time() * 1000))
    rendered = {}  # (w, h) -> png path
    assignments = []
    for scr in screens:
        res = (scr.pw, scr.ph)
        if res not in rendered:
            for old in out.glob(f"{prefix}-{scr.pw}x{scr.ph}-*.png"):
                old.unlink()
            png = out / f"{prefix}-{scr.pw}x{scr.ph}-{stamp}.png"
            render_png(scr, png)
            rendered[res] = png
        assignments.append((scr, rendered[res]))
    report = backend.apply(assignments, fill)
    by_key = {f"{s.x},{s.y},{s.lw}x{s.lh}": s.name for s, _ in assignments}
    info = {
        "requested": [s.name for s, _ in assignments],
        "applied": [by_key[k] for k in report.get("set", []) if k in by_key],
        "desktops": report.get("desktops", []),
    }
    return assignments, info
