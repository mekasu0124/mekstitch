"""The vertical tool picker.

Ported from ``ToolRail`` in the old ``src/components/ToolRail.jsx``, rebuilt on
Fluent ``ToggleToolButton``s with ``FluentIcon`` glyphs so it follows the system
theme instead of the old unicode symbols.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QVBoxLayout, QWidget
from qfluentwidgets import (
    FluentIcon as fi,
    ToggleToolButton,
    ToolTipFilter,
    ToolTipPosition,
)

# (tool id, icon, tooltip)
TOOLS: list[tuple[str, object, str]] = [
    ("pencil", fi.PENCIL_INK, "Pencil — paint single stitches"),
    ("eraser", fi.ERASE_TOOL, "Eraser — clear stitches"),
    ("fill", fi.BACKGROUND_FILL, "Fill — flood fill a region"),
    ("line", fi.ALIGNMENT, "Line — drag to draw a straight line"),
    ("rect", fi.LAYOUT, "Rectangle — drag; hold Shift to fill"),
    ("picker", fi.PALETTE, "Eyedropper — pick a colour from the chart"),
]


class ToolRail(QWidget):
    """Exclusive tool buttons, one per drawing tool."""

    toolChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(56)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, ToggleToolButton] = {}

        for tool_id, icon, title in TOOLS:
            button = ToggleToolButton(icon)
            button.setFixedSize(40, 40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip(title)
            button.installEventFilter(
                ToolTipFilter(button, 400, ToolTipPosition.BOTTOM)
            )
            button.clicked.connect(
                lambda _checked=False, t=tool_id: self.toolChanged.emit(t)
            )
            self._group.addButton(button)
            self._buttons[tool_id] = button
            lay.addWidget(button)

        self._buttons["pencil"].setChecked(True)

    def set_tool(self, tool: str) -> None:
        button = self._buttons.get(tool)
        if button is not None and not button.isChecked():
            blocked = button.blockSignals(True)
            button.setChecked(True)
            button.blockSignals(blocked)
