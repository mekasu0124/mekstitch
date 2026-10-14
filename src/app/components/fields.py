"""Labelled form rows built on Fluent controls.

Mirrors the `Fields.jsx` helpers from the old front-end: fields keep a draft
value while the user types and only commit on Enter / focus-out, so we never
fire a mutation on every keystroke. The controls themselves are the Fluent
Widgets variants (`LineEdit`, `SpinBox`, `DoubleSpinBox`, `ComboBox`).
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, ComboBox, DoubleSpinBox, LineEdit, SpinBox

LABEL_WIDTH = 92


class Field(QWidget):
    """A ``label | control`` row on a fixed label gutter."""

    def __init__(self, label: str, control: QWidget, parent: QWidget | None = None):
        super().__init__(parent)
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.setColumnMinimumWidth(0, LABEL_WIDTH)
        grid.setColumnStretch(1, 1)

        lbl = BodyLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(lbl, 0, 0)
        grid.addWidget(control, 0, 1)


def hbox(*widgets: QWidget, spacing: int = 6) -> QWidget:
    """Pack widgets horizontally into a plain container."""
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for widget in widgets:
        lay.addWidget(widget)
    return box


def switch_row(label: str, switch, parent: QWidget | None = None) -> QWidget:
    """A ``label … switch`` row (label left, control right)."""
    row = QWidget(parent)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    lay.addWidget(BodyLabel(label))
    lay.addStretch(1)
    lay.addWidget(switch)
    return row


class NumberField(Field):
    """Integer field that commits on Enter/blur (not on every keystroke)."""

    def __init__(
        self,
        label: str,
        value: int,
        on_commit: Callable[[int], None],
        minimum: int = 1,
        maximum: int = 9999,
        step: int = 1,
        parent: QWidget | None = None,
    ):
        self._on_commit = on_commit
        self._spin = SpinBox()
        self._spin.setRange(minimum, maximum)
        self._spin.setSingleStep(step)
        self._spin.setValue(int(value))
        self._spin.setKeyboardTracking(False)
        self._spin.valueChanged.connect(self._on_commit)
        super().__init__(label, self._spin, parent)

    def set_value(self, value: int) -> None:
        if self._spin.hasFocus():
            return
        blocked = self._spin.blockSignals(True)
        self._spin.setValue(int(value))
        self._spin.blockSignals(blocked)

    def value(self) -> int:
        return self._spin.value()


class FloatField(Field):
    """Float field that commits on Enter/blur."""

    def __init__(
        self,
        label: str,
        value: float,
        on_commit: Callable[[float], None],
        minimum: float = 0.25,
        maximum: float = 100.0,
        step: float = 0.25,
        decimals: int = 2,
        parent: QWidget | None = None,
    ):
        self._on_commit = on_commit
        self._spin = DoubleSpinBox()
        self._spin.setRange(minimum, maximum)
        self._spin.setSingleStep(step)
        self._spin.setDecimals(decimals)
        self._spin.setValue(float(value))
        self._spin.setKeyboardTracking(False)
        self._spin.valueChanged.connect(self._on_commit)
        super().__init__(label, self._spin, parent)

    def set_value(self, value: float) -> None:
        if self._spin.hasFocus():
            return
        blocked = self._spin.blockSignals(True)
        self._spin.setValue(float(value))
        self._spin.blockSignals(blocked)

    def value(self) -> float:
        return self._spin.value()


class TextField(Field):
    """Text field that commits on Enter/focus-out when the value changed."""

    def __init__(
        self,
        label: str,
        value: str,
        on_commit: Callable[[str], None],
        parent: QWidget | None = None,
    ):
        self._on_commit = on_commit
        self._value = value
        self._edit = LineEdit()
        self._edit.setText(value)
        self._edit.editingFinished.connect(self._commit)
        super().__init__(label, self._edit, parent)

    def set_value(self, value: str) -> None:
        if self._edit.hasFocus():
            return
        self._value = value
        self._edit.setText(value)

    def _commit(self) -> None:
        text = self._edit.text()
        if text != self._value:
            self._value = text
            self._on_commit(text)


class SelectField(Field):
    """A labelled combo box. ``options`` is a list of ``(value, label)`` pairs."""

    def __init__(
        self,
        label: str,
        options: list[tuple[str, str]],
        value: str,
        on_commit: Callable[[str], None],
        parent: QWidget | None = None,
    ):
        self._on_commit = on_commit
        self._combo = ComboBox()
        for opt_value, opt_label in options:
            # Fluent's ComboBox signature is (text, icon, userData); pass
            # userData by keyword so the value isn't mistaken for an icon.
            self._combo.addItem(opt_label, userData=opt_value)
        self._select(value)
        self._combo.currentIndexChanged.connect(self._commit_index)
        super().__init__(label, self._combo, parent)

    def _select(self, value: str) -> None:
        index = self._combo.findData(value)
        blocked = self._combo.blockSignals(True)
        self._combo.setCurrentIndex(max(0, index))
        self._combo.blockSignals(blocked)

    def set_value(self, value: str) -> None:
        self._select(value)

    def value(self) -> str:
        return self._combo.currentData()

    def _commit_index(self, index: int) -> None:
        self._on_commit(self._combo.itemData(index))
