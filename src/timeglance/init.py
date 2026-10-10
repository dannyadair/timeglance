"""Scaffold working configs from the packaged templates.

`timeglance-init` writes `year/config.yaml` and `weekly/config.yaml` into the project
directory (the current directory) from the bundled `config.yaml.in` templates, so the
first run - and Docker's bind-mounts, which expect the files to exist - has something
to read. Existing configs are left untouched.
"""

import shutil

from timeglance import paths
from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild


def main():
    """Copy each planner's bundled template into the project, skipping ones that exist."""
    for planner, template in (("year", ybuild.TEMPLATE), ("weekly", wbuild.TEMPLATE)):
        dest = paths.planner_config(planner)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            print(f"{dest} already exists - leaving it")
        else:
            shutil.copy(template, dest)
            print(f"wrote {dest}")


if __name__ == "__main__":
    main()
