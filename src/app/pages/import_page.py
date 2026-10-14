"""Image import page: map a photo onto the grid or rebuild the palette.

The heavy lifting (`import_image`, `palette_from_image`) runs on a worker thread
through ``AsyncHelper`` so the window never freezes on a large photo — the same
off-thread pattern Momentum uses for its database work.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    CaptionLabel,
    FluentIcon as fi,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
)

from ...core.images import supported_image_extensions
from ..components.base_page import BasePage
from ..components.fields import NumberField, SelectField, switch_row

IMAGE_FILTER = (
    "Images ("
    + " ".join(f"*.{ext}" for ext in supported_image_extensions())
    + ");;All files (*)"
)

RESAMPLE_OPTIONS = [
    ("nearest", "Nearest (pixel art)"),
    ("triangle", "Triangle"),
    ("catmullRom", "Catmull-Rom"),
    ("lanczos3", "Lanczos3"),
]


class ImportPage(BasePage):
    """Choose an image and either quantise it onto the grid or into the palette."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ImportPage")
        self._path: str | None = None
        self._busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        root.addWidget(SubtitleLabel("Import an image"))
        root.addWidget(
            CaptionLabel(
                "“Import into grid” maps the photo onto the current palette. "
                "“Build palette” quantises the photo and replaces the palette."
            )
        )

        self._path_edit = LineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("No image chosen")
        choose = PushButton("Choose image", icon=fi.PHOTO)
        choose.clicked.connect(self._choose_image)
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        path_row.addWidget(self._path_edit, 1)
        path_row.addWidget(choose)
        root.addLayout(path_row)

        project = self.logic.project
        self._width_field = NumberField("Width", project.width, lambda _v: None,
                                        minimum=1, maximum=4000)
        self._height_field = NumberField("Height", project.height, lambda _v: None,
                                         minimum=1, maximum=4000)
        root.addWidget(self._width_field)
        root.addWidget(self._height_field)

        self._filter_field = SelectField(
            "Resample", RESAMPLE_OPTIONS, "triangle", lambda _v: None
        )
        root.addWidget(self._filter_field)

        self._dither_switch = SwitchButton()
        self._dither_switch.setChecked(True)
        self._dither_switch.setOnText("On")
        self._dither_switch.setOffText("Off")
        root.addWidget(switch_row("Floyd–Steinberg dithering", self._dither_switch))

        self._transparent_switch = SwitchButton()
        self._transparent_switch.setChecked(True)
        self._transparent_switch.setOnText("On")
        self._transparent_switch.setOffText("Off")
        root.addWidget(
            switch_row("Transparent pixels become empty stitches", self._transparent_switch)
        )

        self._import_button = PrimaryPushButton("Import into grid", icon=fi.DOWNLOAD)
        self._import_button.clicked.connect(self._do_import)
        root.addWidget(self._import_button)

        root.addWidget(StrongBodyLabel("Build palette from image"))

        self._colors_field = NumberField("Colours", 24, lambda _v: None,
                                         minimum=2, maximum=256)
        root.addWidget(self._colors_field)

        self._build_button = PushButton("Build palette", icon=fi.PALETTE)
        self._build_button.clicked.connect(self._do_build_palette)
        build_row = QHBoxLayout()
        build_row.addWidget(self._build_button)
        build_row.addStretch(1)
        root.addLayout(build_row)

        root.addStretch(1)

        window = self.window()
        if hasattr(window, "projectChanged"):
            window.projectChanged.connect(self._on_project_changed)

    # -- helpers -----------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for widget in (self._import_button, self._build_button):
            widget.setEnabled(not busy)

    def _on_project_changed(self) -> None:
        # Reseed the target size from the project; `set_value` leaves the field
        # alone while the user is typing in it.
        project = self.logic.project
        self._width_field.set_value(project.width)
        self._height_field.set_value(project.height)

    # -- actions -----------------------------------------------------------

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an image", "", IMAGE_FILTER
        )
        if path:
            self._path = path
            self._path_edit.setText(path)

    def _do_import(self) -> None:
        if not self._check_ready():
            return
        self._set_busy(True)
        self.handle_error_success("Importing image…")
        worker = self.async_helper.run_async(
            self.logic.chart.import_into_grid,
            self._path,
            self._width_field.value(),
            self._height_field.value(),
            self._filter_field.value(),
            self._dither_switch.isChecked(),
            self._transparent_switch.isChecked(),
        )
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

    def _do_build_palette(self) -> None:
        if not self._check_ready():
            return
        self._set_busy(True)
        self.handle_error_success("Building palette…")
        worker = self.async_helper.run_async(
            self.logic.chart.build_palette_from_image,
            self._path,
            self._colors_field.value(),
        )
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

    def _check_ready(self) -> bool:
        if self._busy:
            return False
        if not self._path:
            self.handle_error_success(
                "No image chosen", is_error=True, detail="Pick an image first."
            )
            return False
        return True

    def _on_finished(self, result) -> None:
        self._set_busy(False)
        ok, message = result
        if ok:
            self.report(result)
        else:
            self.handle_error_success(message, is_error=True)
        self._notify_changed()

    def _on_error(self, detail: str) -> None:
        self._set_busy(False)
        self.handle_error_success("Import failed", is_error=True, detail=detail)

    def _notify_changed(self) -> None:
        window = self.window()
        if hasattr(window, "notify_project_changed"):
            window.notify_project_changed()
