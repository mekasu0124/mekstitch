"""The chart editor page: canvas, tools, project properties and palette.

This is the Fluent re-housing of the old `TopBar` + `ToolRail` + `SidePanel` +
`PalettePanel` + `StatusBar` cluster: a toolbar of Fluent buttons, the painted
canvas (a custom widget) inside a Fluent scroll area, a right-hand column of
labelled Fluent fields, and a readout strip at the bottom.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as fi,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    ScrollArea,
    StrongBodyLabel,
    SwitchButton,
    TransparentToolButton,
)

from ...core.model import MODE_META, CraftMode
from ..components.base_page import BasePage
from ..components.canvas import StitchCanvas
from ..components.fields import (
    FloatField,
    NumberField,
    SelectField,
    TextField,
    switch_row,
)
from ..components.new_chart_dialog import NewChartDialog
from ..components.palette_panel import PalettePanel
from ..components.readout import Readout
from ..components.toolrail import ToolRail

PROJECT_FILTER = "mekstitch chart (*.wsjson *.json);;All files (*)"
COLUMN_WIDTH = 344


def _section(title: str, rows: list[QWidget]) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    lay.addWidget(StrongBodyLabel(title))
    for row in rows:
        lay.addWidget(row)
    return box


class ChartPage(BasePage):
    """The main editing surface."""

    MIN_ZOOM = 2
    MAX_ZOOM = 64

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ChartPage")

        self._zoom = 14
        self._tool = "pencil"
        self._color_index = 0
        self._show_grid = True
        self._show_symbols = False
        self._cursor: tuple[int, int] | None = None
        self._message = "Ready"
        self._blocked = False

        self._build_ui()
        self._wire()
        self.refresh()

    # -- construction ------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.toolrail = ToolRail()
        body_layout.addWidget(self.toolrail)

        self.canvas = StitchCanvas(self.logic.project)
        self.canvas_scroll = ScrollArea()
        self.canvas_scroll.setObjectName("canvasViewport")
        self.canvas_scroll.setWidget(self.canvas)
        self.canvas_scroll.setWidgetResizable(False)
        self.canvas_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_scroll.enableTransparentBackground()
        body_layout.addWidget(self.canvas_scroll, 1)

        body_layout.addWidget(self._build_column())

        root.addWidget(body, 1)

        self.readout = Readout()
        root.addWidget(self.readout)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(8)

        self._new_button = PushButton("New", icon=fi.ADD)
        self._new_button.clicked.connect(self._open_new_dialog)
        self._open_button = PushButton("Open", icon=fi.FOLDER)
        self._open_button.clicked.connect(self.open_project)
        self._save_button = PrimaryPushButton("Save", icon=fi.SAVE)
        self._save_button.clicked.connect(self.save)
        self._save_as_button = PushButton("Save As", icon=fi.SAVE_AS)
        self._save_as_button.clicked.connect(self.save_as)
        for button in (
            self._new_button,
            self._open_button,
            self._save_button,
            self._save_as_button,
        ):
            lay.addWidget(button)

        self._undo_button = PushButton("Undo")
        self._undo_button.setToolTip("Undo (Ctrl+Z)")
        self._undo_button.clicked.connect(self.undo)
        self._redo_button = PushButton("Redo")
        self._redo_button.setToolTip("Redo (Ctrl+Shift+Z)")
        self._redo_button.clicked.connect(self.redo)
        lay.addWidget(self._undo_button)
        lay.addWidget(self._redo_button)

        zoom_out = TransparentToolButton(fi.ZOOM_OUT)
        zoom_out.setToolTip("Zoom out")
        zoom_out.clicked.connect(lambda: self._nudge_zoom(-2))
        self._zoom_label = BodyLabel(f"{self._zoom}px")
        self._zoom_label.setMinimumWidth(44)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_in = TransparentToolButton(fi.ZOOM_IN)
        zoom_in.setToolTip("Zoom in")
        zoom_in.clicked.connect(lambda: self._nudge_zoom(2))
        for widget in (zoom_out, self._zoom_label, zoom_in):
            lay.addWidget(widget)

        lay.addStretch(1)

        self._title_label = StrongBodyLabel("Untitled")
        lay.addWidget(self._title_label)
        return bar

    def _build_column(self) -> QWidget:
        project = self.logic.project

        self._name_field = TextField("Name", project.name, self._on_name)
        self._width_field = NumberField(
            "Width",
            project.width,
            lambda v: self._apply(self.logic.chart.resize(v, self.logic.project.height)),
            minimum=1,
            maximum=2000,
        )
        self._height_field = NumberField(
            "Height",
            project.height,
            lambda v: self._apply(self.logic.chart.resize(self.logic.project.width, v)),
            minimum=1,
            maximum=2000,
        )

        # Craft radios.
        mode_box = QWidget()
        mode_lay = QVBoxLayout(mode_box)
        mode_lay.setContentsMargins(0, 0, 0, 0)
        mode_lay.setSpacing(6)
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_buttons: dict[str, RadioButton] = {}
        for meta in MODE_META:
            mode: CraftMode = meta["id"]
            radio = RadioButton(meta["label"])
            radio.setCursor(Qt.CursorShape.PointingHandCursor)
            radio.toggled.connect(
                lambda checked, m=mode: checked and self._on_mode(m.value)
            )
            self._mode_group.addButton(radio)
            self._mode_buttons[mode.value] = radio
            mode_lay.addWidget(radio)

        self._mode_note = CaptionLabel("")
        self._mode_note.setWordWrap(True)
        self._block_field = NumberField(
            "Block size",
            project.block_size,
            self._on_block_size,
            minimum=1,
            maximum=20,
        )

        self._stitch_field = FloatField(
            "Stitches",
            project.gauge.stitches_per_unit,
            lambda _v: self._emit_gauge(),
            minimum=0.25,
            maximum=100.0,
            step=0.25,
        )
        self._row_field = FloatField(
            "Rows",
            project.gauge.rows_per_unit,
            lambda _v: self._emit_gauge(),
            minimum=0.25,
            maximum=100.0,
            step=0.25,
        )
        self._unit_field = SelectField(
            "Unit",
            [("in", "Inches"), ("cm", "Centimetres")],
            project.gauge.unit,
            lambda _v: self._emit_gauge(),
        )
        self._gauge_hint = CaptionLabel("—")
        self._gauge_hint.setWordWrap(True)

        self._grid_switch = SwitchButton()
        self._grid_switch.setChecked(True)
        self._grid_switch.setOnText("On")
        self._grid_switch.setOffText("Off")
        self._grid_switch.checkedChanged.connect(self._on_grid)
        self._symbols_switch = SwitchButton()
        self._symbols_switch.setOnText("On")
        self._symbols_switch.setOffText("Off")
        self._symbols_switch.checkedChanged.connect(self._on_symbols)

        self.palette = PalettePanel()

        column = QWidget()
        column.setObjectName("editorColumn")
        col_lay = QVBoxLayout(column)
        col_lay.setContentsMargins(14, 14, 14, 14)
        col_lay.setSpacing(20)
        col_lay.addWidget(
            _section("Project", [self._name_field, self._width_field, self._height_field])
        )
        col_lay.addWidget(
            _section("Craft", [mode_box, self._mode_note, self._block_field])
        )
        col_lay.addWidget(
            _section(
                "Gauge",
                [self._stitch_field, self._row_field, self._unit_field, self._gauge_hint],
            )
        )
        col_lay.addWidget(
            _section(
                "View",
                [
                    switch_row("Grid lines", self._grid_switch),
                    switch_row("Symbols", self._symbols_switch),
                ],
            )
        )
        col_lay.addWidget(_section("Palette", [self.palette]))
        col_lay.addStretch(1)

        scroll = ScrollArea()
        scroll.setWidget(column)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(COLUMN_WIDTH)
        scroll.enableTransparentBackground()
        return scroll

    def _wire(self) -> None:
        self.toolrail.toolChanged.connect(self.set_tool)

        self.canvas.cellsCommitted.connect(self._on_cells_committed)
        self.canvas.floodFillRequested.connect(self._on_flood_fill)
        self.canvas.colorPicked.connect(self.set_color_index)
        self.canvas.hovered.connect(self._on_hover)

        self.palette.colorSelected.connect(self.set_color_index)
        self.palette.colorAdded.connect(
            lambda name, hexv: self._apply(self.logic.chart.add_color(name, hexv))
        )
        self.palette.colorUpdated.connect(
            lambda i, name, hexv: self._apply(
                self.logic.chart.update_color(i, name, hexv)
            )
        )
        self.palette.colorRemoved.connect(
            lambda i: self._apply(self.logic.chart.remove_color(i))
        )
        self.palette.paletteReset.connect(
            lambda: self._apply(self.logic.chart.reset_palette())
        )

    # -- helpers -----------------------------------------------------------

    def _apply(self, result: tuple[bool, str]) -> None:
        ok, message = result
        self._message = message
        if not ok:
            self.handle_error_success(message, is_error=True)
        self.refresh()

    def _stats(self) -> dict:
        project = self.logic.project
        width, height = project.finished_size()
        return {
            "finishedWidth": width,
            "finishedHeight": height,
            "unit": project.gauge.unit,
            "colorCounts": project.color_counts(),
        }

    def _accent(self) -> str:
        project = self.logic.project
        if 0 <= self._color_index < len(project.palette):
            return project.palette[self._color_index].hex
        return "#4c8dd8"

    # -- refresh -----------------------------------------------------------

    def refresh(self) -> None:
        project = self.logic.project
        stats = self._stats()

        self.canvas.set_project(project)
        self.canvas.set_zoom(self._zoom)
        self.canvas.set_tool(self._tool)
        self.canvas.set_color_index(self._color_index)
        self.canvas.set_show_grid(self._show_grid)
        self.canvas.set_show_symbols(self._show_symbols)
        self.canvas.set_major_lines(10, 10)

        self._title_label.setText(project.name)
        self._zoom_label.setText(f"{self._zoom}px")

        self._blocked = True
        try:
            self._name_field.set_value(project.name)
            self._width_field.set_value(project.width)
            self._height_field.set_value(project.height)
            self._stitch_field.set_value(project.gauge.stitches_per_unit)
            self._row_field.set_value(project.gauge.rows_per_unit)
            self._unit_field.set_value(project.gauge.unit)
            self._block_field.set_value(project.block_size)
            for mode_id, radio in self._mode_buttons.items():
                radio.setChecked(mode_id == project.mode.value)

            meta = next((m for m in MODE_META if m["id"] == project.mode), None)
            self._mode_note.setText(meta["note"] if meta else "")
            is_c2c = project.mode == CraftMode.CROCHET_C2C
            self._block_field.setVisible(is_c2c)

            self._gauge_hint.setText(
                f"Finished ≈ {stats['finishedWidth']:.1f} × "
                f"{stats['finishedHeight']:.1f} {stats['unit']}"
            )
        finally:
            self._blocked = False

        self.palette.refresh(project, stats["colorCounts"], self._color_index)
        self.readout.refresh(
            project,
            stats,
            self._zoom,
            self._cursor,
            self._message,
            self._accent(),
        )
        self._sync_history_buttons()

    def _sync_history_buttons(self) -> None:
        self._undo_button.setEnabled(self.logic.chart.can_undo)
        self._redo_button.setEnabled(self.logic.chart.can_redo)

    # -- view state --------------------------------------------------------

    def _nudge_zoom(self, delta: int) -> None:
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self._zoom + delta))
        self.refresh()

    def set_tool(self, tool: str) -> None:
        self._tool = tool
        self.toolrail.set_tool(tool)
        self.canvas.set_tool(tool)

    def set_color_index(self, index: int) -> None:
        self._color_index = index
        self.refresh()

    def _on_grid(self, value: bool) -> None:
        self._show_grid = value
        self.canvas.set_show_grid(value)

    def _on_symbols(self, value: bool) -> None:
        self._show_symbols = value
        self.canvas.set_show_symbols(value)

    def _on_hover(self, x: int, y: int) -> None:
        self._cursor = None if x < 0 else (x, y)
        self.readout.refresh(
            self.logic.project,
            self._stats(),
            self._zoom,
            self._cursor,
            self._message,
            self._accent(),
        )

    # -- actions -----------------------------------------------------------

    def _open_new_dialog(self) -> None:
        dialog = NewChartDialog(self.logic.project.mode, self.window())
        if dialog.exec():
            width, height, mode = dialog.values()
            self._apply(self.logic.chart.new_project(width, height, mode))

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open chart", "", PROJECT_FILTER
        )
        if path:
            self._apply(self.logic.chart.open_project(path))

    def save(self) -> None:
        if self.logic.has_path():
            self._apply(self.logic.chart.save_project(self.logic.current_path))
        else:
            self.save_as()

    def save_as(self) -> None:
        suggested = f"{self.logic.suggested_name()}.wsjson"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save chart", suggested, PROJECT_FILTER
        )
        if path:
            self._apply(self.logic.chart.save_project(path))

    def undo(self) -> None:
        self._apply(self.logic.chart.undo())

    def redo(self) -> None:
        self._apply(self.logic.chart.redo())

    # -- drawing -----------------------------------------------------------

    def _on_cells_committed(self, edits: list) -> None:
        if edits:
            self._apply(self.logic.chart.paint(edits))

    def _on_flood_fill(self, x: int, y: int) -> None:
        color = -1 if self._tool == "eraser" else self._color_index
        self._apply(self.logic.chart.flood_fill(x, y, color))

    # -- project properties ------------------------------------------------

    def _on_name(self, name: str) -> None:
        self._apply(self.logic.chart.set_name(name))

    def _on_mode(self, mode_id: str) -> None:
        if self._blocked:
            return
        self._apply(self.logic.chart.set_mode(mode_id))

    def _on_block_size(self, size: int) -> None:
        if self._blocked:
            return
        self._apply(self.logic.chart.set_block_size(size))

    def _emit_gauge(self) -> None:
        if self._blocked:
            return
        self._apply(
            self.logic.chart.set_gauge(
                self._stitch_field.value(),
                self._row_field.value(),
                self._unit_field.value(),
            )
        )
