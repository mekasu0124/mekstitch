"""Undo/redo history plus the live project.

Ported from `src-tauri/src/state.rs`. Undo is deliberately simple: every
mutating operation snapshots the project first. Charts are small, so this is
plenty fast and removes a whole class of bugs a diff approach would introduce.
"""

from __future__ import annotations

import copy
from typing import Callable

from .model import CraftMode, Project

MAX_HISTORY = 200


class History:
    """Owns the open project and its snapshot-based undo/redo stacks."""

    def __init__(self, project: Project | None = None) -> None:
        self._project = project or Project.create(
            "Untitled", 60, 60, CraftMode.CROSS_STITCH
        )
        self._undo: list[Project] = []
        self._redo: list[Project] = []

    # -- access ------------------------------------------------------------

    @property
    def project(self) -> Project:
        return self._project

    def checkpoint(self) -> None:
        """Snapshot the current project and clear redo. Call *before* mutating."""
        self._undo.append(copy.deepcopy(self._project))
        if len(self._undo) > MAX_HISTORY:
            self._undo.pop(0)
        self._redo.clear()

    def replace(self, project: Project) -> None:
        """Replace the project wholesale (open/new), resetting history."""
        self._project = project
        self._undo.clear()
        self._redo.clear()

    def mutate(self, fn: Callable[[Project], None]) -> Project:
        """Mutate the live project, snapshotting first."""
        self.checkpoint()
        fn(self._project)
        return self._project

    def undo(self) -> Project:
        if self._undo:
            self._redo.append(copy.deepcopy(self._project))
            self._project = self._undo.pop()
        return self._project

    def redo(self) -> Project:
        if self._redo:
            self._undo.append(copy.deepcopy(self._project))
            self._project = self._redo.pop()
        return self._project

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)
