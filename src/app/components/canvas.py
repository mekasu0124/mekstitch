"""The chart editor canvas.

Ported from `src/components/StitchCanvas.jsx`. A `QWidget` painted directly with
`QPainter`, sized `project.width*zoom` by `project.height*zoom`, and hosted inside
a Fluent `ScrollArea` by the editor page.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ...core.glyphs import contrast_for, draw_glyph
from ...core.model import CraftMode, Project

GRID_COLOR = QColor(150, 150, 150, 89)
MAJOR_COLOR = QColor(60, 60, 60, 191)


def line_cells(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    """Bresenham line between two cells, inclusive of both ends."""
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    out: list[tuple[int, int]] = []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return out


def rect_cells(
    a: tuple[int, int], b: tuple[int, int], filled: bool
) -> list[tuple[int, int]]:
    """Rectangle outline between two cells; ``filled`` returns the solid block."""
    x0, x1 = sorted((a[0], b[0]))
    y0, y1 = sorted((a[1], b[1]))
    out: list[tuple[int, int]] = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            edge = x == x0 or x == x1 or y == y0 or y == y1
            if filled or edge:
                out.append((x, y))
    return out


class StitchCanvas(QWidget):
    """The painted grid with the drawing tools."""

    cellsCommitted = Signal(list)  # list[(x, y, color)]
    floodFillRequested = Signal(int, int)
    colorPicked = Signal(int)
    hovered = Signal(int, int)  # -1, -1 when off-grid

    def __init__(self, project: Project, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("canvasSurface")
        self._project = project
        self._zoom = 14
        self._tool = "pencil"
        self._color_index = 0
        self._show_grid = True
        self._show_symbols = False
        self._major_every = 10
        self._major_rows_every = 10

        self._overlay: list[tuple[int, int, int]] = []
        self._drag: dict | None = None
        self._stroke: dict[int, tuple[int, int, int]] = {}

        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._resize_to_project()

    # -- configuration -----------------------------------------------------

    def set_project(self, project: Project) -> None:
        self._project = project
        self._overlay = []
        self._resize_to_project()
        self.update()

    def set_zoom(self, zoom: int) -> None:
        self._zoom = max(1, int(zoom))
        self._resize_to_project()
        self.update()

    def set_tool(self, tool: str) -> None:
        self._tool = tool

    def set_color_index(self, index: int) -> None:
        self._color_index = index

    def set_show_grid(self, value: bool) -> None:
        self._show_grid = value
        self.update()

    def set_show_symbols(self, value: bool) -> None:
        self._show_symbols = value
        self.update()

    def set_major_lines(self, every: int, rows_every: int) -> None:
        self._major_every = every
        self._major_rows_every = rows_every
        self.update()

    def refresh(self) -> None:
        self._resize_to_project()
        self.update()

    def _resize_to_project(self) -> None:
        w = max(1, self._project.width * self._zoom)
        h = max(1, self._project.height * self._zoom)
        self.setFixedSize(w, h)

    # -- painting ----------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        project = self._project
        zoom = self._zoom
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), QColor(255, 255, 255))

            overlay: dict[int, int] = {
                y * project.width + x: color for x, y, color in self._overlay
            }
            palette = project.palette
            cells = project.cells
            n_palette = len(palette)

            for y in range(project.height):
                row = y * project.width
                for x in range(project.width):
                    idx = row + x
                    color = overlay.get(idx, cells[idx])
                    if color < 0 or color >= n_palette:
                        continue
                    painter.fillRect(
                        x * zoom, y * zoom, zoom, zoom, QColor(*palette[color].rgb())
                    )

            if self._show_grid:
                self._paint_grid(painter)

            if self._show_symbols:
                for y in range(project.height):
                    row = y * project.width
                    for x in range(project.width):
                        idx = row + x
                        color = overlay.get(idx, cells[idx])
                        if color < 0 or color >= n_palette:
                            continue
                        draw_glyph(
                            painter,
                            x * zoom,
                            y * zoom,
                            zoom,
                            contrast_for(palette[color].hex),
                            color,
                        )
        finally:
            painter.end()

    def _paint_grid(self, painter: QPainter) -> None:
        project = self._project
        zoom = self._zoom
        w = self.width()
        h = self.height()
        block = (
            max(1, project.block_size)
            if project.mode == CraftMode.CROCHET_C2C
            else 0
        )

        painter.setBrush(Qt.BrushStyle.NoBrush)
        for x in range(project.width + 1):
            major = (self._major_every > 0 and x % self._major_every == 0) or (
                block > 0 and x % block == 0
            )
            pen = QPen(MAJOR_COLOR if major else GRID_COLOR)
            pen.setWidth(1)
            painter.setPen(pen)
            px = min(x * zoom, w - 1)
            painter.drawLine(px, 0, px, h - 1)

        for y in range(project.height + 1):
            major = (
                self._major_rows_every > 0 and y % self._major_rows_every == 0
            ) or (block > 0 and y % block == 0)
            pen = QPen(MAJOR_COLOR if major else GRID_COLOR)
            pen.setWidth(1)
            painter.setPen(pen)
            py = min(y * zoom, h - 1)
            painter.drawLine(0, py, w - 1, py)

    # -- input -------------------------------------------------------------

    def _cell_at(self, pos: QPoint) -> tuple[int, int] | None:
        x = pos.x() // self._zoom
        y = pos.y() // self._zoom
        if not self._project.in_bounds(x, y):
            return None
        return x, y

    def _paint_color(self) -> int:
        return -1 if self._tool == "eraser" else self._color_index

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        cell = self._cell_at(event.position().toPoint())
        if cell is None:
            return

        x, y = cell
        idx = y * self._project.width + x

        if self._tool == "picker":
            color = self._project.cells[idx]
            if color >= 0:
                self.colorPicked.emit(color)
            return
        if self._tool == "fill":
            self.floodFillRequested.emit(x, y)
            return

        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        self._drag = {"start": cell, "last": cell, "tool": self._tool, "shift": shift}

        if self._tool in ("pencil", "eraser"):
            self._stroke = {idx: (x, y, self._paint_color())}
            self._overlay = list(self._stroke.values())
        else:
            self._overlay = [(x, y, self._paint_color())]
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        cell = self._cell_at(event.position().toPoint())
        self.hovered.emit(*(cell if cell else (-1, -1)))

        drag = self._drag
        if drag is None or cell is None:
            return
        drag["last"] = cell
        x, y = cell

        if drag["tool"] in ("pencil", "eraser"):
            idx = y * self._project.width + x
            if idx not in self._stroke:
                self._stroke[idx] = (x, y, self._paint_color())
                self._overlay = list(self._stroke.values())
                self.update()
            return

        filled = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        drag["shift"] = filled
        if drag["tool"] == "line":
            cells = line_cells(drag["start"], cell)
        else:
            cells = rect_cells(drag["start"], cell, filled)
        self._overlay = [(cx, cy, self._paint_color()) for cx, cy in cells]
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        drag = self._drag
        if drag is None:
            return

        if drag["tool"] in ("pencil", "eraser"):
            edits = list(self._stroke.values())
            self._stroke = {}
            self._overlay = []
            if edits:
                self.cellsCommitted.emit(edits)
        else:
            if drag["tool"] == "line":
                cells = line_cells(drag["start"], drag["last"])
            else:
                cells = rect_cells(drag["start"], drag["last"], drag["shift"])
            self._overlay = []
            self.cellsCommitted.emit(
                [(cx, cy, self._paint_color()) for cx, cy in cells]
            )

        self._drag = None
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hovered.emit(-1, -1)
