"""Scaffold working configs from the packaged templates.

`timeglance init` writes `year/config.yaml` and `weekly/config.yaml` into the config
directory (`~/.config/timeglance/` by default, or under `TIMEGLANCE_HOME`) from the bundled
`config.yaml.in` templates, so the first run - and Docker's bind-mounts, which expect the
files to exist - has something to read. Existing configs are left untouched.
"""

import shutil

from timeglance import paths
from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild


def ensure():
    """Scaffold any missing planner configs from the bundled templates; return the paths written."""
    written = []
    for planner, template in (("year", ybuild.TEMPLATE), ("weekly", wbuild.TEMPLATE)):
        dest = paths.planner_config(planner)
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(template, dest)
        written.append(dest)
    return written


def main():
    """Copy each planner's bundled template into the config dir, skipping ones that exist."""
    written = ensure()
    for planner in ("year", "weekly"):
        dest = paths.planner_config(planner)
        print(f"wrote {dest}" if dest in written else f"{dest} already exists - not written")


if __name__ == "__main__":
    main()
