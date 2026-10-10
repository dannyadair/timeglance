"""The systemd user units `timeglance install` writes, and the install/uninstall calls."""

import types

from timeglance import service


def test_timer_unit_pads_time_and_persists():
    """The timer fires daily at the padded HH:MM and catches up missed runs."""
    unit = service._timer_unit("6:30")
    assert "OnCalendar=*-*-* 06:30:00" in unit
    assert "Persistent=true" in unit
    assert "WantedBy=timers.target" in unit


def test_service_unit_is_oneshot_running_run():
    """The service is a oneshot invoking `timeglance run`."""
    unit = service._service_unit()
    assert "Type=oneshot" in unit
    assert unit.rstrip().endswith(" run")


def test_install_writes_units_and_enables(tmp_path, monkeypatch):
    """install writes both units under XDG_CONFIG_HOME and enables the timer."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(service.shutil, "which", lambda _: "/usr/bin/systemctl")
    calls = []
    monkeypatch.setattr(service.subprocess, "run", lambda cmd, check=True: calls.append(cmd))

    service.install("07:30")

    unit_dir = tmp_path / "systemd" / "user"
    assert (unit_dir / service.SERVICE).exists()
    assert "07:30:00" in (unit_dir / service.TIMER).read_text()
    assert ["systemctl", "--user", "daemon-reload"] in calls
    assert ["systemctl", "--user", "enable", "--now", service.TIMER] in calls


def test_uninstall_disables_and_removes(tmp_path, monkeypatch):
    """uninstall disables the timer and deletes the unit files."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(service.shutil, "which", lambda _: "/usr/bin/systemctl")
    monkeypatch.setattr(service.subprocess, "run", lambda cmd, check=True: None)
    unit_dir = tmp_path / "systemd" / "user"
    unit_dir.mkdir(parents=True)
    (unit_dir / service.SERVICE).write_text("x")
    (unit_dir / service.TIMER).write_text("x")

    service.uninstall()

    assert not (unit_dir / service.SERVICE).exists()
    assert not (unit_dir / service.TIMER).exists()


def test_enabled_reads_is_enabled(monkeypatch):
    """enabled() is True only when `systemctl is-enabled` reports enabled."""
    monkeypatch.setattr(service.shutil, "which", lambda _: "/usr/bin/systemctl")
    monkeypatch.setattr(service.subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout="enabled\n"))
    assert service.enabled() is True
    monkeypatch.setattr(service.subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout="disabled\n"))
    assert service.enabled() is False


def test_enable_installs_when_units_missing(tmp_path, monkeypatch):
    """enable() falls back to a full install when the timer unit isn't on disk yet."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(service.shutil, "which", lambda _: "/usr/bin/systemctl")
    monkeypatch.setattr(service.subprocess, "run", lambda *a, **k: None)
    installed = []
    monkeypatch.setattr(service, "install", lambda: installed.append(True))

    service.enable()

    assert installed == [True]


def test_enable_uses_systemctl_when_installed(tmp_path, monkeypatch):
    """enable() just re-enables when the units already exist."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(service.shutil, "which", lambda _: "/usr/bin/systemctl")
    (tmp_path / "systemd" / "user").mkdir(parents=True)
    (tmp_path / "systemd" / "user" / service.TIMER).write_text("x")
    calls = []
    monkeypatch.setattr(service.subprocess, "run", lambda cmd, check=True: calls.append(cmd))

    service.enable()

    assert ["systemctl", "--user", "enable", "--now", service.TIMER] in calls


def test_disable_stops_timer(monkeypatch):
    """disable() stops and disables the timer without touching the unit files."""
    calls = []
    monkeypatch.setattr(service.subprocess, "run", lambda cmd, check=True: calls.append(cmd))
    service.disable()
    assert ["systemctl", "--user", "disable", "--now", service.TIMER] in calls
