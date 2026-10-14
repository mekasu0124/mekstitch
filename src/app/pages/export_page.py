"""Export page: chart PNG settings, yarn list and a live preview."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    FluentIcon as fi,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
)

from ...core.chart import ExportOptions, render_chart
from ..components.base_page import BasePage
from ..components.fields import NumberField, switch_row

PREVIEW_WIDTH = 400
PREVIEW_MAX_CELLS = 250_000


class ExportPage(BasePage):
    """Render the chart to a PNG and the palette to a plain-text yarn list."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ExportPage")
        self._settings = {
            "cellSize": 16,
            "showGrid": True,
            "showSymbols": True,
            "majorEvery": 10,
            "majorRowsEvery": 10,
        }

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        root.addWidget(SubtitleLabel("Export"))
        root.addWidget(
            CaptionLabel(
                "A printable chart with grid lines and matching symbols, "
                "plus a plain-text yarn list."
            )
        )

        self._cell_field = NumberField(
            "Cell size (px)", self._settings["cellSize"], self._set_cell,
            minimum=4, maximum=64,
        )
        root.addWidget(self._cell_field)

        self._major_field = NumberField(
            "Major line every", self._settings["majorEvery"], self._set_major,
            minimum=0, maximum=100,
        )
        root.addWidget(self._major_field)

        self._grid_switch = SwitchButton()
        self._grid_switch.setChecked(True)
        self._grid_switch.setOnText("On")
        self._grid_switch.setOffText("Off")
        self._grid_switch.checkedChanged.connect(
            lambda v: self._set("showGrid", v)
        )
        root.addWidget(switch_row("Grid lines", self._grid_switch))

        self._symbols_switch = SwitchButton()
        self._symbols_switch.setChecked(True)
        self._symbols_switch.setOnText("On")
        self._symbols_switch.setOffText("Off")
        self._symbols_switch.checkedChanged.connect(
            lambda v: self._set("showSymbols", v)
        )
        root.addWidget(switch_row("Symbols", self._symbols_switch))

        root.addWidget(StrongBodyLabel("Preview"))
        self._preview = QLabel()
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumHeight(220)
        self._preview.setWordWrap(True)
        root.addWidget(self._preview)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        png_button = PrimaryPushButton("Export PNG chart", icon=fi.IMAGE_EXPORT)
        png_button.clicked.connect(self._export_chart)
        legend_button = PushButton("Export yarn list", icon=fi.DOCUMENT)
        legend_button.clicked.connect(self._export_legend)
        buttons.addWidget(png_button)
        buttons.addWidget(legend_button)
        buttons.addStretch(1)
        root.addLayout(buttons)

        root.addStretch(1)

        window = self.window()
        if hasattr(window, "projectChanged"):
            window.projectChanged.connect(self._update_preview)

        self._update_preview()

    # -- settings ----------------------------------------------------------

    def export_settings(self) -> dict:
        return dict(self._settings)

    def _set(self, key: str, value) -> None:
        self._settings[key] = value
        self._update_preview()

    def _set_cell(self, value: int) -> None:
        self._set("cellSize", value)

    def _set_major(self, value: int) -> None:
        self._settings["majorEvery"] = value
        self._settings["majorRowsEvery"] = value
        self._update_preview()

    def _options(self, cell_size: int | None = None) -> ExportOptions:
        return ExportOptions(
            cell_size=cell_size or self._settings["cellSize"],
            show_grid=self._settings["showGrid"],
            show_symbols=self._settings["showSymbols"],
            major_every=self._settings["majorEvery"],
            major_rows_every=self._settings["majorRowsEvery"],
        )

    # -- preview -----------------------------------------------------------

    def _update_preview(self) -> None:
        project = self.logic.project
        if project.width * project.height > PREVIEW_MAX_CELLS:
            self._preview.setPixmap(QPixmap())
            self._preview.setText("Preview disabled for very large charts.")
            return

        preview_cell = max(4, min(self._settings["cellSize"], 20))
        image = render_chart(project, self._options(preview_cell))
        pixmap = QPixmap.fromImage(image).scaled(
            PREVIEW_WIDTH,
            PREVIEW_WIDTH,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview.setText("")
        self._preview.setPixmap(pixmap)

    # -- actions -----------------------------------------------------------

    def _export_chart(self) -> None:
        suggested = f"{self.logic.suggested_name()}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export chart", suggested, "PNG image (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        self.report(self.logic.chart.export_chart(self.export_settings(), path))

    def _export_legend(self) -> None:
        suggested = f"{self.logic.suggested_name()}-legend.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export yarn list", suggested, "Text (*.txt)"
        )
        if path:
            self.report(self.logic.chart.export_legend(path))
