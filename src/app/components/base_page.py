"""Shared base for the pages inside the Fluent window.

Every page reaches the session through the window's ``logic`` object and reports
outcomes with Fluent ``InfoBar`` toasts, mirroring the
``handle_error_success`` helper in Momentum's dashboard page.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

TOAST_MS = 3000


class BasePage(QWidget):
    """A page that owns a reference to the app's ``Logic`` session."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.logic = getattr(parent, "logic", None)
        self.async_helper = getattr(parent, "async_helper", None)

    # -- feedback ----------------------------------------------------------

    def handle_error_success(
        self, msg: str, is_error: bool | None = None, detail: str = ""
    ) -> None:
        """Toast ``msg``. ``is_error`` None = info, True = error, False = success."""
        parent = self.window()

        if is_error is None:
            InfoBar.info(
                title=msg,
                content=detail,
                isClosable=True,
                duration=TOAST_MS,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )
        elif is_error:
            InfoBar.error(
                title=msg,
                content=detail,
                isClosable=True,
                duration=TOAST_MS + 2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )
        else:
            InfoBar.success(
                title=msg,
                content=detail,
                isClosable=True,
                duration=TOAST_MS,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )

    def report(self, result: tuple[bool, str]) -> bool:
        """Show the ``(ok, message)`` tuple returned by ``Logic`` operations."""
        ok, message = result
        self.handle_error_success(message, is_error=not ok)
        return ok
