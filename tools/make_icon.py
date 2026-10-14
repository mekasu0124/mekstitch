"""Generate the app icon (a simple cross-stitch chart tile) as a PNG.

Run once to (re)create ``src/assets/mekstitch.png``::

    uv run --project . python tools/make_icon.py
"""

import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

SIZE = 256


def draw(path: str) -> None:
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Rounded tile.
        tile = QRectF(8, 8, SIZE - 16, SIZE - 16)
        painter.setBrush(QColor("#6A2C70"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(tile, 48, 48)

        # A 3x3 mini grid of "stitches".
        colours = [
            "#E31C25", "#FFB500", "#7BC043",
            "#1F8AC0", "#FFFFFF", "#A05EB5",
            "#E8A87C", "#C9C9C9", "#17497E",
        ]
        cell = (SIZE - 96) / 3
        origin = 48.0
        for i, hex_value in enumerate(colours):
            row, col = divmod(i, 3)
            rect = QRectF(origin + col * cell, origin + row * cell, cell, cell)
            painter.setBrush(QColor(hex_value))
            painter.setPen(QPen(QColor(255, 255, 255, 60), 2))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)

        # A cross-stitch "X" marker over the centre cell.
        painter.setPen(
            QPen(
                QColor(20, 20, 20, 210),
                8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        cx = origin + cell * 1.5
        cy = origin + cell * 1.5
        d = cell * 0.28
        painter.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
        painter.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
    finally:
        painter.end()

    if not img.save(path):
        raise SystemExit(f"could not write {path}")
    print("wrote", path)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # noqa: F841 - QImage needs a QGuiApplication
    draw(sys.argv[1] if len(sys.argv) > 1 else "src/assets/mekstitch.png")
