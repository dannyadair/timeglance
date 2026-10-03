"""Runtime data locations, resolved from the current working directory.

Code and packaged assets (templates, web, the `*.yaml.in` files) live inside the
installed package; the *working* data a user edits and the app writes - each tool's
`config.yaml` and `out/`, plus shared `state/` - live under the project directory,
which defaults to the current working directory (override with `TIMEGLANCE_HOME`).
So you `cd` into your project and run `timeglance`; Docker bind-mounts map the same
`./year`, `./weekly` and `./state` into the container's working directory.
"""

import os
from pathlib import Path


def project_dir():
    """Return the project root (``TIMEGLANCE_HOME`` or the current directory)."""
    return Path(os.environ.get("TIMEGLANCE_HOME", Path.cwd()))


def tool_config(tool):
    """Return the path to ``<tool>/config.yaml`` under the project root."""
    return project_dir() / tool / "config.yaml"


def tool_out(tool):
    """Return the output directory ``<tool>/out`` under the project root."""
    return project_dir() / tool / "out"


def state_dir():
    """Return the shared ``state/`` directory under the project root."""
    return project_dir() / "state"
