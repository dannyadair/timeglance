"""The tray controller's schedule/port edits (the pystray UI itself can't be tested headless)."""

import pytest

pytest.importorskip("pystray")

from timeglance import tray  # noqa: E402
from timeglance.common import schedule, settings  # noqa: E402


def test_toggle_planner_edits_schedule(tmp_path, monkeypatch):
    """Toggling a planner adds then removes it from schedule.yaml's planners list."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    t = tray.Tray()
    t.toggle_planner("weekly")
    assert "weekly" in schedule.Schedule.load().cfg["planners"]
    t.toggle_planner("weekly")
    assert "weekly" not in schedule.Schedule.load().cfg["planners"]


def test_toggle_wallpaper_flips_block(tmp_path, monkeypatch):
    """Toggling wallpaper flips the planner block's wallpaper flag on disk."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    t = tray.Tray()
    t.toggle_wallpaper("year")
    assert schedule.Schedule.load().planner_block("year")["wallpaper"] is False


def test_set_time_persists_and_reinstalls_when_enabled(tmp_path, monkeypatch):
    """set_time writes the new time and rewrites the timer only while it's enabled."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    installed = []
    monkeypatch.setattr(tray.service, "enabled", lambda: True)
    monkeypatch.setattr(tray.service, "install", lambda: installed.append(True))
    t = tray.Tray()
    t.set_time("21:00")
    assert schedule.Schedule.load().cfg["time"] == "21:00"
    assert installed == [True]


def test_set_port_persists(tmp_path, monkeypatch):
    """set_port persists the port; with no server running nothing is restarted."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    t = tray.Tray()
    t.set_port(8888)
    assert settings.get_port() == 8888


def test_autostart_toggle(tmp_path, monkeypatch):
    """The tray's Start-at-login toggle writes then removes the autostart entry."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    class Icon:
        def update_menu(self):
            pass

    t = tray.Tray()
    t._toggle_autostart(Icon())
    assert (tmp_path / "autostart" / tray.autostart.DESKTOP).exists()
    t._toggle_autostart(Icon())
    assert not (tmp_path / "autostart" / tray.autostart.DESKTOP).exists()


def test_menu_builds(tmp_path, monkeypatch):
    """The menu assembles without a display (callables aren't evaluated until shown)."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    assert len(tray.Tray().menu().items) > 0
