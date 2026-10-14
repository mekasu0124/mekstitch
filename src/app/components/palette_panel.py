"""Palette editing panel.

Ported from ``PalettePanel.jsx``. The colour chips are custom-painted
``SwatchButton``s (Fluent has no swatch-grid widget), but everything around them
— labels, text fields, the colour picker — is a Fluent control.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ColorPickerButton,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from ...core.glyphs import contrast_for, symbol_char
from ...core.model import Project, is_valid_hex

SWATCH_COLUMNS = 6
ACCENT = "#4c8dd8"


class SwatchButton(QWidget):
    """A single palette chip: solid colour, symbol glyph and a checked ring."""

    clicked = Signal()

    def __init__(self, hex_value: str, symbol: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("swatch")
        self.setFixedSize(34, 34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hex = hex_value
        self._symbol = symbol
        self._checked = False

    def set_colour(self, hex_value: str, symbol: str) -> None:
        self._hex = hex_value
        self._symbol = symbol
        self.update()

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect().adjusted(2, 2, -2, -2)

            painter.setBrush(QColor(self._hex))
            painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
            painter.drawRoundedRect(rect, 6, 6)

            font = self.font()
            font.setPixelSize(15)
            painter.setFont(font)
            painter.setPen(contrast_for(self._hex))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._symbol)

            if self._checked:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(ACCENT), 2))
                painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)
        finally:
            painter.end()


class PalettePanel(QWidget):
    """Colour list plus an editor for the selected entry."""

    colorSelected = Signal(int)
    colorAdded = Signal(str, str)
    colorUpdated = Signal(int, str, str)
    colorRemoved = Signal(int)
    paletteReset = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._project: Project | None = None
        self._counts: list[int] = []
        self._color_index = 0
        self._swatches: list[SwatchButton] = []
        self._new_hex = "#808080"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        root.addWidget(StrongBodyLabel("Palette"))

        self._grid = QGridLayout()
        self._grid.setSpacing(6)
        root.addLayout(self._grid)

        # -- editor for the selected colour --------------------------------
        self._name_edit = LineEdit()
        self._name_edit.setPlaceholderText("Colour name")
        root.addWidget(self._field_row("Name", self._name_edit))

        self._pick_button = ColorPickerButton(
            QColor("#000000"), "colour", self
        )
        self._pick_button.setFixedWidth(56)
        self._pick_button.colorChanged.connect(self._on_pick_changed)
        self._hex_edit = LineEdit()
        self._hex_edit.setMaxLength(7)
        self._hex_edit.setPlaceholderText("#RRGGBB")
        colour_row = QHBoxLayout()
        colour_row.setSpacing(8)
        colour_row.addWidget(self._pick_button)
        colour_row.addWidget(self._hex_edit, 1)
        root.addWidget(self._field_row("Colour", colour_row, is_layout=True))

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self._update_button = PrimaryPushButton("Update")
        self._update_button.clicked.connect(self._emit_update)
        self._remove_button = PushButton("Remove")
        self._remove_button.clicked.connect(self._emit_remove)
        self._reset_button = PushButton("Reset")
        self._reset_button.clicked.connect(self.paletteReset.emit)
        for button in (self._update_button, self._remove_button, self._reset_button):
            buttons.addWidget(button)
        root.addLayout(buttons)

        self._hint = CaptionLabel("")
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)

        # -- add a new colour ----------------------------------------------
        self._new_name = LineEdit()
        self._new_name.setText("New colour")
        self._new_pick = ColorPickerButton(QColor(self._new_hex), "new colour", self)
        self._new_pick.setFixedWidth(56)
        self._new_pick.colorChanged.connect(self._on_new_pick_changed)
        add_button = PrimaryPushButton("Add")
        add_button.clicked.connect(self._emit_add)
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        add_row.addWidget(self._new_name, 1)
        add_row.addWidget(self._new_pick)
        add_row.addWidget(add_button)
        root.addWidget(self._field_row("New", add_row, is_layout=True))

    # -- helpers -----------------------------------------------------------

    def _field_row(self, label: str, content, is_layout: bool = False) -> QWidget:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lbl = BodyLabel(label)
        lbl.setFixedWidth(56)
        lay.addWidget(lbl)
        if is_layout:
            lay.addLayout(content, 1)
        else:
            lay.addWidget(content, 1)
        return row

    # -- population --------------------------------------------------------

    def refresh(self, project: Project, counts: list[int], color_index: int) -> None:
        index_changed = color_index != self._color_index
        palette_changed = (
            self._project is None
            or [c.hex for c in self._project.palette] != [c.hex for c in project.palette]
            or [c.name for c in self._project.palette] != [c.name for c in project.palette]
        )
        self._project = project
        self._counts = counts
        self._color_index = color_index

        if palette_changed or len(self._swatches) != len(project.palette):
            self._rebuild_swatches(project)

        self._sync_selection(project, color_index)
        self._sync_editor(
            project, color_index, force=palette_changed or index_changed
        )
        self._update_hint(project, color_index)

    def _rebuild_swatches(self, project: Project) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._swatches = []

        for i, color in enumerate(project.palette):
            swatch = SwatchButton(color.hex, symbol_char(i))
            swatch.setToolTip(
                f"{color.name} ({color.hex}) — "
                f"{self._counts[i] if i < len(self._counts) else 0} stitches"
            )
            swatch.installEventFilter(
                ToolTipFilter(swatch, 400, ToolTipPosition.BOTTOM)
            )
            swatch.clicked.connect(
                lambda idx=i: self.colorSelected.emit(idx)
            )
            self._grid.addWidget(swatch, i // SWATCH_COLUMNS, i % SWATCH_COLUMNS)
            self._swatches.append(swatch)

    def _sync_selection(self, project: Project, color_index: int) -> None:
        for i, swatch in enumerate(self._swatches):
            swatch.set_checked(i == color_index)

        has_selection = 0 <= color_index < len(project.palette)
        self._remove_button.setEnabled(len(project.palette) > 1)
        for widget in (
            self._name_edit,
            self._hex_edit,
            self._pick_button,
            self._update_button,
        ):
            widget.setEnabled(has_selection)

    def _sync_editor(
        self, project: Project, color_index: int, force: bool = False
    ) -> None:
        if not (0 <= color_index < len(project.palette)):
            self._name_edit.setText("")
            self._hex_edit.setText("")
            self._pick_button.setColor(QColor("#000000"))
            return
        color = project.palette[color_index]
        # Don't clobber what the user is currently typing.
        if force or not self._name_edit.hasFocus():
            self._name_edit.setText(color.name)
        if force or not self._hex_edit.hasFocus():
            self._hex_edit.setText(color.hex)
        self._pick_button.setColor(QColor(color.hex))

    def _update_hint(self, project: Project, color_index: int) -> None:
        count = self._counts[color_index] if color_index < len(self._counts) else 0
        self._hint.setText(
            f"{count} stitches use this colour. Symbol {symbol_char(color_index)}"
        )

    # -- actions -----------------------------------------------------------

    def _on_pick_changed(self, color: QColor) -> None:
        if self._project is None:
            return
        value = color.name()
        self._hex_edit.setText(value)
        self.colorUpdated.emit(self._color_index, self._name_edit.text(), value)

    def _on_new_pick_changed(self, color: QColor) -> None:
        self._new_hex = color.name()

    def _emit_update(self) -> None:
        if self._project is None:
            return
        name = self._name_edit.text()
        hex_value = self._hex_edit.text()
        if not is_valid_hex(hex_value):
            if 0 <= self._color_index < len(self._project.palette):
                hex_value = self._project.palette[self._color_index].hex
            else:
                hex_value = "#808080"
            self._hex_edit.setText(hex_value)
        self.colorUpdated.emit(self._color_index, name, hex_value)

    def _emit_remove(self) -> None:
        self.colorRemoved.emit(self._color_index)

    def _emit_add(self) -> None:
        self.colorAdded.emit(self._new_name.text() or "New colour", self._new_hex)
        # Select the colour we just appended so the editor targets it right away.
        if self._project is not None and self._project.palette:
            self.colorSelected.emit(len(self._project.palette) - 1)
