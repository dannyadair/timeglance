"""Working-config plumbing shared by every planner: read, validate-and-write, reset-to-template.

Schema-agnostic - it only moves YAML text between a planner's ``config.yaml`` and its packaged
template, so adding a planner needs no changes here.
"""

import datetime as dt

import yaml


def read_config(planner):
    """Read the planner's working config, falling back to its packaged template when absent."""
    path = planner.data if planner.data.exists() else planner.template
    return {"yaml": path.read_text(), "from_template": not planner.data.exists(), "path": planner.data.name}


def write_config(planner, text):
    """Validate ``text`` as YAML and write it to the planner's working config."""
    yaml.safe_load(text)  # validate; raises on bad YAML
    planner.data.write_text(text)


def reset_config(planner):
    """Overwrite the working config with the template, backing up the current file first.
    Returns the backup filename (or None if there was nothing to back up)."""
    backup = None
    if planner.data.exists():
        stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup = planner.data.with_name(f"{planner.data.name}.{stamp}.bak")
        backup.write_text(planner.data.read_text())
    planner.data.write_text(planner.template.read_text())
    return backup.name if backup else None
