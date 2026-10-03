"""Config precedence (defaults < YAML < CLI) and the reset-to-template backup."""

from argparse import Namespace

import pytest
import yaml

from timeglance.common.serve import read_config, reset_config, write_config
from timeglance.year import build as ybuild
from timeglance.year import render as yrender

LAYERS = [{"id": "a", "label": "A", "color": "#111"}, {"id": "b", "label": "B", "color": "#222"}]


def test_defaults_applied_when_yaml_silent():
    """A config that omits layout/theme fields falls back to the built-in defaults."""
    cfg = yrender.parse({"layers": LAYERS, "events": []})
    assert (cfg.layout, cfg.week_align, cfg.theme, cfg.week_start) == ("vertical", True, "light", "Mon")


def test_yaml_overrides_defaults():
    """Values set in YAML take precedence over the built-in defaults."""
    raw = {"layers": LAYERS, "events": [], "layout": "horizontal", "week_align": False, "week_start": "Sun"}
    cfg = yrender.parse(raw)
    assert (cfg.layout, cfg.week_align, cfg.week_start) == ("horizontal", False, "Sun")


def test_cli_overrides_yaml():
    """Explicit CLI flags override the YAML values."""
    raw = {"layers": [dict(lyr, visible=True) for lyr in LAYERS], "week_start": "Mon"}
    args = Namespace(week_start="Sun", week_align=False, size="3440x1440", only=None, hide=[])
    ybuild.apply_cli(raw, args)
    assert raw["week_start"] == "Sun"
    assert raw["week_align"] is False
    assert raw["size"] == "3440x1440"


def test_cli_absent_flags_leave_yaml_untouched():
    """Unset CLI flags leave the YAML (and thus the defaults) untouched."""
    raw = {"layers": [dict(lyr, visible=True) for lyr in LAYERS]}
    args = Namespace(week_start=None, week_align=None, size=None, only=None, hide=[])
    ybuild.apply_cli(raw, args)
    assert "week_start" not in raw and "week_align" not in raw and "size" not in raw


def test_cli_only_and_hide_toggle_layer_visibility():
    """``--only`` and ``--hide`` flip the right layers' visibility."""
    raw = {"layers": [dict(lyr, visible=True) for lyr in LAYERS]}
    ybuild.apply_cli(raw, Namespace(week_start=None, week_align=None, size=None, only="a", hide=[]))
    assert {lyr["id"]: lyr["visible"] for lyr in raw["layers"]} == {"a": True, "b": False}

    raw = {"layers": [dict(lyr, visible=True) for lyr in LAYERS]}
    ybuild.apply_cli(raw, Namespace(week_start=None, week_align=None, size=None, only=None, hide=["b"]))
    assert {lyr["id"]: lyr["visible"] for lyr in raw["layers"]} == {"a": True, "b": False}


def test_resolve_list_and_pick():
    """resolve_list and _pick apply CLI > YAML > fallback and validate against allowed values."""
    assert ybuild.resolve_list(None, None, ["x", "y"]) == ["x", "y"]
    assert ybuild.resolve_list("x", None, ["x", "y"]) == ["x"]
    assert ybuild.resolve_list(None, "y,x", ["x", "y"]) == ["y", "x"]
    with pytest.raises(SystemExit):
        ybuild.resolve_list("bad", None, ["x", "y"])

    assert ybuild._pick("dark", "light", "light", ["light", "dark"], "theme") == "dark"
    assert ybuild._pick(None, "dark", "light", ["light", "dark"], "theme") == "dark"
    assert ybuild._pick(None, None, "light", ["light", "dark"], "theme") == "light"
    assert ybuild._pick("a,b", "dark", "light", ["light", "dark"], "theme") == "dark"  # multi-CLI ignored


# ---- reset-to-template backup ----


class FakeTool:
    """Minimal tool stub with a working-config path and a template, for config tests."""

    def __init__(self, tmp):
        """Set up data/template paths under ``tmp`` and seed the template file."""
        self.data = tmp / "config.yaml"
        self.template = tmp / "config.yaml.in"
        self.template.write_text("template: 1\n")


def test_read_config_falls_back_to_template(tmp_path):
    """read_config returns the template, flagged as such, when no working config exists."""
    tool = FakeTool(tmp_path)
    rc = read_config(tool)
    assert rc == {"yaml": "template: 1\n", "from_template": True, "path": "config.yaml"}


def test_reset_without_existing_data_makes_no_backup(tmp_path):
    """Resetting when no working config exists writes the template and makes no backup."""
    tool = FakeTool(tmp_path)
    assert reset_config(tool) is None
    assert tool.data.read_text() == "template: 1\n"
    assert read_config(tool)["from_template"] is False


def test_reset_backs_up_existing_data(tmp_path):
    """Resetting over an existing config backs it up before overwriting with the template."""
    tool = FakeTool(tmp_path)
    tool.data.write_text("user: 2\n")
    backup = reset_config(tool)
    assert backup and backup.endswith(".bak")
    assert tool.data.read_text() == "template: 1\n"
    assert tool.data.with_name(backup).read_text() == "user: 2\n"


def test_write_config_validates_yaml(tmp_path):
    """write_config persists valid YAML and raises on malformed YAML."""
    tool = FakeTool(tmp_path)
    write_config(tool, "a: 1\n")
    assert tool.data.read_text() == "a: 1\n"
    with pytest.raises(yaml.YAMLError):
        write_config(tool, "a: [unclosed\n")
