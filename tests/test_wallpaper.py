"""Remembered-screens registry and screen resolution (incl. disconnected targets)."""

import datetime as dt
import json

import pytest

from timeglance.common import wallpaper
from timeglance.common.wallpaper import Screen


class FakeBackend:
    """Backend stub returning a fixed screen list."""

    def __init__(self, screens):
        self._screens = screens

    def list_screens(self):
        return self._screens


def _scr(name, pw=1920, ph=1080, primary=False, model=""):
    return Screen(name, 0, 0, pw, ph, pw, ph, primary=primary, model=model)


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    return tmp_path


def test_known_tracks_screens_across_disconnect():
    be = FakeBackend([_scr("eDP-1", primary=True), _scr("DP-8", 3840, 1600, model="DELL")])
    seen = {s["name"]: s for s in wallpaper.known(be)}
    assert seen["eDP-1"]["connected"] and seen["DP-8"]["connected"]
    assert seen["DP-8"]["w"] == 3840 and seen["DP-8"]["model"] == "DELL"

    seen = {s["name"]: s for s in wallpaper.known(FakeBackend([_scr("eDP-1", primary=True)]))}
    assert seen["eDP-1"]["connected"] is True
    assert seen["DP-8"]["connected"] is False and seen["DP-8"]["w"] == 3840


def test_forget_removes_screen():
    wallpaper.known(FakeBackend([_scr("DP-8", 3840, 1600)]))
    wallpaper.forget("DP-8")
    assert wallpaper.known(FakeBackend([])) == []


def test_prune_drops_stale(home):
    wallpaper.known(FakeBackend([_scr("DP-8", 3840, 1600)]))
    reg_path = home / "state" / "screens.json"
    reg = json.loads(reg_path.read_text())
    reg["DP-8"]["last_seen"] = (dt.date.today() - dt.timedelta(days=40)).isoformat()
    reg_path.write_text(json.dumps(reg))
    assert wallpaper.known(FakeBackend([])) == []


def test_resolve_disconnected_from_registry():
    wallpaper.known(FakeBackend([_scr("eDP-1", primary=True), _scr("DP-8", 3840, 1600, model="DELL")]))
    got = wallpaper.resolve_screens(FakeBackend([_scr("eDP-1", primary=True)]), ["eDP-1", "DP-8"])
    assert [s.name for s in got] == ["eDP-1", "DP-8"]
    dp = next(s for s in got if s.name == "DP-8")
    assert dp.connected is False and (dp.pw, dp.ph) == (3840, 1600)


def test_resolve_unknown_raises():
    with pytest.raises(SystemExit):
        wallpaper.resolve_screens(FakeBackend([_scr("eDP-1")]), ["NOPE"])


def test_apply_renders_disconnected_but_defers(tmp_path):
    class RecordBackend(FakeBackend):
        applied = None

        def apply(self, assignments, fill="preserveAspectCrop", bust=""):
            self.applied = [s.name for s, _ in assignments]
            return {"desktops": [], "set": [f"{s.x},{s.y},{s.lw}x{s.lh}" for s, _ in assignments]}

    def render_png(scr, path):
        path.write_bytes(b"PNG")

    be = RecordBackend([])
    connected = _scr("eDP-1")
    disconnected = Screen("DP-8", 0, 0, 0, 0, 3840, 1600, connected=False)
    _, info = wallpaper.apply(be, [connected, disconnected], tmp_path, render_png, prefix="year-wallpaper")

    assert (tmp_path / "year-wallpaper-eDP-1.png").exists()
    assert (tmp_path / "year-wallpaper-DP-8.png").exists()  # rendered despite being disconnected
    assert be.applied == ["eDP-1"]  # only the connected screen is assigned in Plasma
    assert info["applied"] == ["eDP-1"] and info["pending"] == ["DP-8"]
    assert set(info["written"]) == {"eDP-1", "DP-8"}
