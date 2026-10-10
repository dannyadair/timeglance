"""The tray's XDG autostart entry (Start at login)."""

from timeglance import autostart


def test_enable_writes_desktop_entry(tmp_path, monkeypatch):
    """enable() writes a launching .desktop under XDG_CONFIG_HOME/autostart."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert autostart.enabled() is False
    autostart.enable()
    entry = tmp_path / "autostart" / autostart.DESKTOP
    assert entry.exists()
    text = entry.read_text()
    assert "Type=Application" in text
    assert text.rstrip().count("timeglance") and "tray" in text
    assert autostart.enabled() is True


def test_disable_removes_entry(tmp_path, monkeypatch):
    """disable() removes the entry (and is a no-op when it's already gone)."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    autostart.enable()
    autostart.disable()
    assert not (tmp_path / "autostart" / autostart.DESKTOP).exists()
    autostart.disable()
