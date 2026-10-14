"""The single entry point the GUI talks to.

Modelled on `src/core/logic.py` in the Momentum project: the window receives one
``Logic`` instance and reaches the rest of the app through it, rather than
importing the model modules directly. It owns the session (the live project plus
its undo history) and the CRUD helpers that operate on it.
"""

from __future__ import annotations

from pathlib import Path

from .crud.project import ProjectLogic
from .history import History
from .model import Project


class Logic:
    def __init__(self, app_dir: Path):
        self.app_dir = Path(app_dir)

        self.history = History()
        self.current_path: str | None = None

        self.chart = ProjectLogic(self)

    # -- convenience -------------------------------------------------------

    @property
    def project(self) -> Project:
        """The live project being edited."""
        return self.history.project

    def has_path(self) -> bool:
        return bool(self.current_path)

    def suggested_name(self) -> str:
        return self.project.name or "chart"
