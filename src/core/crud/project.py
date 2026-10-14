"""CRUD-style operations over the live chart.

Follows the Momentum layout (`core/crud/task.py`): every method is a small,
UI-agnostic unit of work that returns a ``(ok, message)`` tuple so the widgets
never have to catch exceptions themselves.

The live project is owned by `core.history.History`; these methods mutate it
through ``History.mutate`` so undo/redo stays consistent, and they never touch
any Qt widget.
"""

from __future__ import annotations

from typing import Tuple

from ..chart import ExportOptions, legend_text, render_chart
from ..history import History
from ..images import import_image, palette_from_image
from ..model import CraftMode, Gauge, Project, YarnColor, default_palette
from ..project_file import load_project, save_project

# (ok, message) — the shape every public method returns.
Result = Tuple[bool, str]


class ProjectLogic:
    """Everything the UI can do to the open chart."""

    def __init__(self, parent: "Logic" = None):
        self.parent = parent

    # -- internals ---------------------------------------------------------

    @property
    def history(self) -> History:
        return self.parent.history

    @property
    def current(self) -> Project:
        """The live project (convenience passthrough)."""
        return self.parent.history.project

    def _run(self, label: str, fn) -> Result:
        """Run a mutation, turning any exception into a failure result."""
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - surfaced to the user verbatim
            return False, f"{label}: {exc}"
        return True, label

    # -- lifecycle ---------------------------------------------------------

    def new_project(self, width: int, height: int, mode: str) -> Result:
        def action() -> None:
            project = Project.create("Untitled", width, height, CraftMode(mode))
            self.history.replace(project)
            self.parent.current_path = None

        return self._run(f"New {width}×{height} chart", action)

    def open_project(self, path: str) -> Result:
        def action() -> None:
            self.history.replace(load_project(path))
            self.parent.current_path = path

        return self._run("Opened chart", action)

    def save_project(self, path: str) -> Result:
        def action() -> None:
            save_project(self.history.project, path)
            self.parent.current_path = path

        return self._run("Saved chart", action)

    # -- history -----------------------------------------------------------

    def undo(self) -> Result:
        if not self.history.can_undo:
            return False, "Nothing to undo"
        self.history.undo()
        return True, "Undo"

    def redo(self) -> Result:
        if not self.history.can_redo:
            return False, "Nothing to redo"
        self.history.redo()
        return True, "Redo"

    @property
    def can_undo(self) -> bool:
        return self.history.can_undo

    @property
    def can_redo(self) -> bool:
        return self.history.can_redo

    # -- drawing -----------------------------------------------------------

    def paint(self, edits: list) -> Result:
        if not edits:
            return False, "Nothing painted"

        def action() -> None:
            def apply(project: Project) -> None:
                for x, y, color in edits:
                    if project.in_bounds(x, y):
                        project.cells[project.idx(x, y)] = color

            self.history.mutate(apply)

        return self._run(f"Painted {len(edits)}", action)

    def flood_fill(self, x: int, y: int, color: int) -> Result:
        def action() -> None:
            self.history.mutate(lambda p: p.flood_fill(x, y, color))

        return self._run("Filled region", action)

    # -- project properties ------------------------------------------------

    def set_name(self, name: str) -> Result:
        def action() -> None:
            self.history.mutate(lambda p: setattr(p, "name", name))

        return self._run("Renamed chart", action)

    def set_mode(self, mode: str) -> Result:
        def action() -> None:
            self.history.mutate(lambda p: setattr(p, "mode", CraftMode(mode)))

        return self._run("Craft changed", action)

    def set_block_size(self, size: int) -> Result:
        def action() -> None:
            self.history.mutate(
                lambda p: setattr(p, "block_size", max(1, min(64, int(size))))
            )

        return self._run(f"Block size {size}", action)

    def set_gauge(self, stitches: float, rows: float, unit: str) -> Result:
        def action() -> None:
            def apply(project: Project) -> None:
                project.gauge = Gauge(
                    max(0.01, float(stitches)),
                    max(0.01, float(rows)),
                    unit,
                )

            self.history.mutate(apply)

        return self._run("Gauge updated", action)

    def resize(self, width: int, height: int) -> Result:
        def action() -> None:
            self.history.mutate(lambda p: p.resize(width, height))

        return self._run(f"Resized to {width}×{height}", action)

    # -- palette -----------------------------------------------------------

    def add_color(self, name: str, hex_value: str) -> Result:
        def action() -> None:
            self.history.mutate(
                lambda p: p.palette.append(YarnColor(name, hex_value))
            )

        return self._run("Colour added", action)

    def update_color(self, index: int, name: str, hex_value: str) -> Result:
        def action() -> None:
            def apply(project: Project) -> None:
                if 0 <= index < len(project.palette):
                    project.palette[index].name = name
                    project.palette[index].hex = hex_value

            self.history.mutate(apply)

        return self._run("Colour updated", action)

    def remove_color(self, index: int, remap_to: int | None = None) -> Result:
        def action() -> None:
            def apply(project: Project) -> None:
                if index >= len(project.palette):
                    return
                project.palette.pop(index)
                removed = index
                remap = (
                    remap_to
                    if remap_to is not None and 0 <= remap_to < len(project.palette)
                    else None
                )
                for i, cell in enumerate(project.cells):
                    if cell < 0:
                        continue
                    if cell == removed:
                        project.cells[i] = remap if remap is not None else -1
                    elif cell > removed:
                        project.cells[i] = cell - 1

            self.history.mutate(apply)

        return self._run("Colour removed", action)

    def reset_palette(self) -> Result:
        def action() -> None:
            self.history.mutate(lambda p: setattr(p, "palette", default_palette()))

        return self._run("Palette reset", action)

    # -- image import ------------------------------------------------------

    def import_into_grid(
        self,
        path: str,
        width: int,
        height: int,
        filter_name: str,
        dither: bool,
        transparent: bool,
    ) -> Result:
        def action() -> None:
            def apply(project: Project) -> None:
                import_image(
                    project, path, width, height, filter_name, dither, transparent
                )

            self.history.mutate(apply)

        return self._run("Imported image", action)

    def build_palette_from_image(self, path: str, num_colors: int) -> Result:
        def action() -> None:
            def apply(project: Project) -> None:
                palette_from_image(project, path, num_colors)

            self.history.mutate(apply)

        return self._run("Palette built from image", action)

    # -- export ------------------------------------------------------------

    def export_chart(self, settings: dict, path: str) -> Result:
        def action() -> None:
            options = ExportOptions(
                cell_size=settings["cellSize"],
                show_grid=settings["showGrid"],
                show_symbols=settings["showSymbols"],
                major_every=settings["majorEvery"],
                major_rows_every=settings["majorRowsEvery"],
            )
            image = render_chart(self.history.project, options)
            if not image.save(path):
                raise OSError(f"could not write {path}")

        return self._run("Exported chart", action)

    def export_legend(self, path: str) -> Result:
        def action() -> None:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(legend_text(self.history.project))

        return self._run("Exported yarn list", action)
