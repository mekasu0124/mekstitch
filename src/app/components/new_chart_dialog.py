"""The "New chart" dialog, built on Fluent's ``MessageBoxBase``."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget
from qfluentwidgets import ComboBox, MessageBoxBase, SpinBox, SubtitleLabel

from ...core.model import MODE_META, CraftMode


class NewChartDialog(MessageBoxBase):
    """Ask for size and craft mode before starting a fresh chart."""

    def __init__(self, current_mode: CraftMode, parent: QWidget | None = None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("New chart", self)
        self.viewLayout.addWidget(self.titleLabel)

        self._width = SpinBox(self)
        self._width.setRange(1, 2000)
        self._width.setValue(60)
        self.viewLayout.addWidget(_row("Width", self._width))

        self._height = SpinBox(self)
        self._height.setRange(1, 2000)
        self._height.setValue(60)
        self.viewLayout.addWidget(_row("Height", self._height))

        self._mode = ComboBox(self)
        for meta in MODE_META:
            self._mode.addItem(meta["label"], meta["id"].value)
        index = self._mode.findData(current_mode.value)
        self._mode.setCurrentIndex(max(0, index))
        self.viewLayout.addWidget(_row("Craft", self._mode))

        self.yesButton.setText("Create")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(360)

    def values(self) -> tuple[int, int, str]:
        return self._width.value(), self._height.value(), self._mode.currentData()


def _row(label: str, control: QWidget) -> QWidget:
    from qfluentwidgets import BodyLabel
    from PySide6.QtWidgets import QHBoxLayout

    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    lbl = BodyLabel(label)
    lbl.setFixedWidth(72)
    lay.addWidget(lbl)
    lay.addWidget(control, 1)
    return row
