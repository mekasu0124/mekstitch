"""The application window.

Follows Momentum's `src/app/app.py`: a ``FluentWindow`` that owns the session
handles (``logic``, ``async_helper``), registers each page as a navigation
sub-interface, and applies the theme + local stylesheet.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIcon as fi,
    FluentWindow,
    NavigationItemPosition,
    Theme,
    setTheme,
    setThemeColor,
)

from .pages.about import AboutPage
from .pages.chart import ChartPage
from .pages.export_page import ExportPage
from .pages.import_page import ImportPage
from .utils.async_helper import AsyncHelper

THEME_COLOR = "#4c8dd8"


class MainWindow(FluentWindow):
    """mekstitch's single top-level window."""

    projectChanged = Signal()

    def __init__(self, logic, app_styles):
        super().__init__()

        self.logic = logic
        self.app_styles = app_styles
        self.async_helper = AsyncHelper()

        self.chart_page = ChartPage(self)
        self.import_page = ImportPage(self)
        self.export_page = ExportPage(self)
        self.about_page = AboutPage(self)

        self.init_navigation()
        self.apply_theme()
        self.apply_style()
        self.install_shortcuts()

        self.resize(1280, 840)
        self.setMinimumSize(980, 640)

    # -- setup -------------------------------------------------------------

    def init_navigation(self) -> None:
        self.addSubInterface(self.chart_page, fi.PENCIL_INK, "Chart")
        self.addSubInterface(self.import_page, fi.PHOTO, "Image")
        self.addSubInterface(self.export_page, fi.SAVE, "Export")
        self.addSubInterface(
            self.about_page, fi.INFO, "About", NavigationItemPosition.BOTTOM
        )

    def apply_theme(self) -> None:
        setTheme(Theme.AUTO)
        setThemeColor(THEME_COLOR)

    def apply_style(self) -> None:
        try:
            with open(self.app_styles, "r", encoding="utf-8") as styles:
                self.setStyleSheet(styles.read())
        except OSError:
            print("WARNING: styles file not found. skipping")
            self.setStyleSheet("")

    def install_shortcuts(self) -> None:
        page = self.chart_page
        bindings = (
            (QKeySequence.StandardKey.Undo, page.undo),
            (QKeySequence.StandardKey.Redo, page.redo),
            (QKeySequence.StandardKey.Save, page.save),
            (QKeySequence.StandardKey.Open, page.open_project),
            (QKeySequence.StandardKey.New, page._open_new_dialog),
        )
        for sequence, slot in bindings:
            QShortcut(sequence, self, activated=slot)

    # -- cross-page notification ------------------------------------------

    def notify_project_changed(self) -> None:
        """Tell every page the shared project was replaced by another page."""
        self.projectChanged.emit()
        self.chart_page.refresh()

    # -- events ------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        event.accept()
