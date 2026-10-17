"""The schedule's dead switch: automatic runs honour it, Run now bypasses it."""

from timeglance import cli
from timeglance.common import schedule


def test_run_respects_dead_switch(tmp_path, monkeypatch):
    """`timeglance run` (the service/automatic path) renders when enabled and skips when disabled."""
    monkeypatch.setenv("TIMEGLANCE_HOME", str(tmp_path))
    calls = []
    monkeypatch.setattr(schedule.Schedule, "run_once", lambda self, *a, **k: calls.append(True))

    cli.main(["run"])  # enabled by default -> renders
    assert calls == [True]

    s = schedule.Schedule.load()
    s.cfg["enabled"] = False
    s.save()
    cli.main(["run"])  # disabled -> skipped, run_once not called again
    assert calls == [True]
