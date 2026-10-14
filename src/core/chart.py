"""Renders a project to a printable chart image / yarn list.

Ported from `src-tauri/src/export.rs`. Symbols are drawn procedurally (see
`core.glyphs`) rather than with a font, so the export has no font dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen

from .glyphs import contrast_for, draw_glyph
from .model import CraftMode, Project

EMPTY = QColor(255, 255, 255)
GRID = QColor(190, 190, 190)
MAJOR = QColor(70, 70, 70)


@dataclass
class ExportOptions:
    """Rendering knobs for the printed chart."""

    cell_size: int = 16
    show_grid: bool = True
    show_symbols: bool = True
    major_every: int = 10
    major_rows_every: int = 10


def render_chart(project: Project, opts: ExportOptions) -> QImage:
    """Render the chart. The image is `width*cell_size` by `height*cell_size`."""
    cs = max(2, min(256, int(opts.cell_size)))
    width_px = max(1, project.width * cs)
    height_px = max(1, project.height * cs)

    img = QImage(width_px, height_px, QImage.Format.Format_RGB32)
    img.fill(EMPTY)

    block = project.block_size if project.mode == CraftMode.CROCHET_C2C else 0
    block = max(1, block) if block else 0

    painter = QPainter(img)
    try:
        palette = project.palette
        for y in range(project.height):
            row = y * project.width
            for x in range(project.width):
                color = project.cells[row + x]
                if color < 0 or color >= len(palette):
                    continue
                yarn = palette[color]
                fill = QColor(*yarn.rgb())
                painter.fillRect(x * cs, y * cs, cs, cs, fill)
                if opts.show_symbols:
                    draw_glyph(
                        painter, x * cs, y * cs, cs, contrast_for(yarn.hex), color
                    )

        if opts.show_grid:
            _draw_grid(painter, project, cs, opts, block, width_px, height_px)
    finally:
        painter.end()

    return img


def _draw_grid(
    painter: QPainter,
    project: Project,
    cs: int,
    opts: ExportOptions,
    block: int,
    w: int,
    h: int,
) -> None:
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for x in range(project.width + 1):
        px = min(x * cs, w - 1)
        major = (opts.major_every > 0 and x % opts.major_every == 0) or (
            block > 0 and x % block == 0
        )
        color = MAJOR if (x == 0 or x == project.width or major) else GRID
        pen = QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(px, 0, px, h)

    for y in range(project.height + 1):
        py = min(y * cs, h - 1)
        major = (opts.major_rows_every > 0 and y % opts.major_rows_every == 0) or (
            block > 0 and y % block == 0
        )
        color = MAJOR if (y == 0 or y == project.height or major) else GRID
        pen = QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(0, py, w, py)


def legend_text(project: Project) -> str:
    """A plain-text floss/yarn list: colour, symbol index, stitch count."""
    counts = project.color_counts()
    lines = [project.name]
    lines.append(f"{project.width} x {project.height} cells  |  {project.mode.value}")
    lines.append("")
    lines.append("symbol\tcolour\thex\tstitches")
    for i, c in enumerate(project.palette):
        count = counts[i] if i < len(counts) else 0
        lines.append(f"{i % 8}\t{c.name}\t{c.hex}\t{count}")
    return "\n".join(lines) + "\n"


__all__ = ["ExportOptions", "render_chart", "legend_text", "EMPTY", "GRID", "MAJOR"]
