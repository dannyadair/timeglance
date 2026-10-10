"""The planners the control panel and scheduler drive, behind one protocol.

A planner is a thin adapter over a renderer (``timeglance.year`` / ``timeglance.weekly``):
it knows where it reads its config and writes its output, and how to produce UI metadata, a
preview, an export and a wallpaper. Add a planner by implementing ``Planner`` and listing it
in ``PLANNERS``; nothing else special-cases planner names.
"""

from pathlib import Path
from typing import Protocol

from timeglance import paths
from timeglance.planners.weekly import WeeklyPlanner
from timeglance.planners.year import YearPlanner


class Planner(Protocol):
    """What the control panel and scheduler need from a planner: identity, where it reads and
    writes, and the render/export/wallpaper operations."""

    name: str
    out_name: str
    template: Path

    @property
    def data(self) -> Path: ...

    @property
    def out(self) -> Path: ...

    def meta(self) -> dict: ...

    def preview(self, p: dict) -> tuple[str, bytes]: ...

    def export(self, p: dict) -> tuple[str, str, bytes]: ...

    def set_wallpaper(self, p: dict) -> dict: ...

    def warnings(self) -> list: ...


PLANNERS = {"year": YearPlanner(), "weekly": WeeklyPlanner()}


def output_path(planner):
    """Path of the file this planner writes, relative to the project root (for the UI)."""
    return str((planner.out / planner.out_name).relative_to(paths.project_dir()))
