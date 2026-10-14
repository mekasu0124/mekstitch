"""Procedural chart symbols.

These mirror `src-tauri/src/export.rs::draw_glyph` (and the old front-end
`src/glyphs.js`) so the on-screen chart and the exported PNG agree on which
symbol belongs to which colour. Each palette index maps to one of eight glyphs.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from .model import parse_hex

GLYPH_COUNT = 8

# Unicode stand-ins used for the little swatches in the palette panel.
SYMBOL_CHARS = ["●", "✕", "＋", "▢", "△", "•", "╱", "—"]


def symbol_char(index: int) -> str:
    return SYMBOL_CHARS[index % GLYPH_COUNT]


def luminance(r: int, g: int, b: int) -> float:
    """Perceived luminance, used to pick a contrasting symbol colour."""
    return 0.299 * r + 0.587 * g + 0.114 * b


def contrast_for(hex_str: str) -> QColor:
    """Black or white, whichever reads better on `hex_str`."""
    rgb = parse_hex(hex_str)
    if rgb is None:
        return QColor(0, 0, 0)
    return QColor(0, 0, 0) if luminance(*rgb) > 140 else QColor(255, 255, 255)


def draw_glyph(
    painter: QPainter,
    ox: float,
    oy: float,
    size: float,
    color: QColor,
    index: int,
) -> None:
    """Draw one symbol into a cell whose top-left corner is at `(ox, oy)`."""
    if size < 6:
        return
    pad = max(1, int(size / 5))
    x0 = ox + pad
    y0 = oy + pad
    s = size - pad * 2
    mid = s / 2.0
    lw = max(1.0, round(size / 10.0))

    painter.save()
    pen = QPen(color)
    pen.setWidthF(lw)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    variant = index % GLYPH_COUNT
    if variant == 0:  # circle outline
        r = max(1.0, s / 2.0 - lw / 2.0)
        painter.drawEllipse(QPointF(x0 + mid, y0 + mid), r, r)
    elif variant == 1:  # X
        painter.drawLine(QPointF(x0, y0), QPointF(x0 + s, y0 + s))
        painter.drawLine(QPointF(x0 + s, y0), QPointF(x0, y0 + s))
    elif variant == 2:  # plus
        painter.drawLine(QPointF(x0 + mid, y0), QPointF(x0 + mid, y0 + s))
        painter.drawLine(QPointF(x0, y0 + mid), QPointF(x0 + s, y0 + mid))
    elif variant == 3:  # square outline
        painter.drawRect(QRectF(x0, y0, s, s))
    elif variant == 4:  # triangle
        painter.drawPolygon(
            [
                QPointF(x0 + mid, y0),
                QPointF(x0 + s, y0 + s),
                QPointF(x0, y0 + s),
            ]
        )
    elif variant == 5:  # filled dot
        painter.setBrush(color)
        r = max(1.0, s / 6.0)
        painter.drawEllipse(QPointF(x0 + mid, y0 + mid), r, r)
    elif variant == 6:  # forward slash
        painter.drawLine(QPointF(x0 + s, y0), QPointF(x0, y0 + s))
    else:  # horizontal bar
        painter.drawLine(QPointF(x0, y0 + mid), QPointF(x0 + s, y0 + mid))

    painter.restore()
