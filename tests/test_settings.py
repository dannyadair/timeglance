"""The control-panel port persisted in the config dir's settings.yaml."""

from timeglance.common import settings


def test_default_port_without_file(tmp_path, monkeypatch):
    """With no settings.yaml, the port is the built-in default."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    assert settings.get_port() == settings.DEFAULT_PORT


def test_set_port_roundtrips(tmp_path, monkeypatch):
    """set_port writes settings.yaml and get_port reads it back."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    settings.set_port(8080)
    assert (tmp_path / "settings.yaml").exists()
    assert settings.get_port() == 8080
