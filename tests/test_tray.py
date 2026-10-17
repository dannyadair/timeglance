"""The tray controller's schedule/port edits (the Qt UI itself can't be driven headless, so we
run Qt on the offscreen platform and exercise the controller, not real clicks)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# PySide6 is an optional extra and needs a Qt platform plugin; where either is missing (the dev
# venv without [tray], or a distro that doesn't ship PySide6) skip the whole module.
try:
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])
    from timeglance import autostart, init, tray
    from timeglance.common import schedule, settings
except Exception as e:
    pytest.skip(f"tray unavailable: {e}", allow_module_level=True)


@pytest.fixture
def t(tmp_path, monkeypatch):
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    init.ensure()  # scaffold the planner configs the menu reads for its size labels
    return tray.Tray(_app)


def test_set_port_persists(t):
    """set_port persists the port; with no server running nothing is restarted."""
    t.set_port(8888)
    assert settings.get_port() == 8888


def test_set_time_persists_and_reinstalls_when_enabled(t, monkeypatch):
    """set_time writes the new time and rewrites the timer only while it's installed."""
    installed = []
    monkeypatch.setattr(tray.service, "enabled", lambda: True)
    monkeypatch.setattr(tray.service, "install", lambda *a: installed.append(True))
    t.set_time("21:00")
    assert schedule.Schedule.load().cfg["time"] == "21:00"
    assert installed == [True]


def test_toggle_enabled_flips_dead_switch(t):
    """The dead switch defaults on and toggles on disk, so a running scheduler re-reads it."""
    assert schedule.Schedule.load().enabled is True
    t.toggle_enabled()
    assert schedule.Schedule.load().enabled is False
    t.toggle_enabled()
    assert schedule.Schedule.load().enabled is True


def test_autostart_toggle(t, tmp_path, monkeypatch):
    """The Autostart toggle writes then removes the login-autostart entry."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    t.toggle_autostart()
    assert (tmp_path / "autostart" / autostart.DESKTOP).exists()
    t.toggle_autostart()
    assert not (tmp_path / "autostart" / autostart.DESKTOP).exists()


def test_menu_populates(t):
    """The context menu assembles from live state without a display."""
    t.populate()
    assert len(t.menu.actions()) > 0
