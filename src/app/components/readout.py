"""The bottom readout strip on the editor page.

Ported from the old `StatusBar` in `src/components/ToolRail.jsx`: a row of small
dimmed labels reporting grid size, block count, finished size, zoom and the
cursor cell, plus a chip previewing the active colour.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ...core.model import CraftMode, Project

ACCENT = "#4c8dd8"


class Readout(QWidget):
    """Readouts for size, blocks/colours, finished size, zoom and cursor."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("readout")
        self.setFixedHeight(30)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 2, 14, 2)
        lay.setSpacing(18)

        self._cells = self._dim_label()
        self._colours = self._dim_label()
        self._finished = self._dim_label()
        self._zoom = self._dim_label()
        self._cursor = self._dim_label()
        for label in (
            self._cells,
            self._colours,
            self._finished,
            self._zoom,
            self._cursor,
        ):
            lay.addWidget(label)

        lay.addStretch(1)

        self._chip = QLabel()
        self._chip.setObjectName("colourChip")
        self._chip.setFixedSize(12, 12)
        lay.addWidget(self._chip)

        self._message = self._dim_label()
        self._message.setText("Ready")
        lay.addWidget(self._message)

    def _dim_label(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("readoutLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return label

    def refresh(
        self,
        project: Project,
        stats,
        zoom: int,
        cursor: tuple[int, int] | None,
        message: str,
        accent: str,
    ) -> None:
        span = project.block_size if project.mode == CraftMode.CROCHET_C2C else 1
        self._cells.setText(f"{project.width} × {project.height} cells")

        if project.mode == CraftMode.CROCHET_C2C:
            self._colours.setText(
                f"{project.width // span} × {project.height // span} "
                f"blocks ({span}×{span})"
            )
        else:
            self._colours.setText(f"{len(project.palette)} colours")

        if stats is not None:
            self._finished.setText(
                f"Finished ≈ {stats['finishedWidth']:.1f} × "
                f"{stats['finishedHeight']:.1f} {stats['unit']}"
            )
        else:
            self._finished.setText("Finished ≈ —")

        self._zoom.setText(f"{zoom}px/cell")
        self._cursor.setText(
            f"x {cursor[0]}, y {cursor[1]}" if cursor else "\u00a0"
        )
        self._chip.setStyleSheet(
            f"background: {accent or ACCENT}; border-radius: 3px;"
        )
        self._message.setText(message)
