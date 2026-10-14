"""Application entry point.

The `mekstitch` console script declared in `pyproject.toml` points at
`src.main:main`.

The shape mirrors Momentum's `src/main.py`: build the ``QApplication``, create
the ``Logic`` session, hand both to the ``FluentWindow`` and run the event loop.

This lives under `src/` alongside `src/app` and `src/core` rather than at the
repository root, so it can never be confused with an unrelated top-level
`main.py`.
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from .app.app import MainWindow
from .config import Config
from .core.logic import Logic


def main() -> int:
    """Create the QApplication, show the window and run the event loop."""
    load_dotenv()

    app = QApplication(sys.argv)
    app.setApplicationName(Config.APP_NAME)
    app.setApplicationVersion(Config.APP_VERSION)
    app.setOrganizationName("mekstitch")

    logic = Logic(Config.APP_DIR)

    window = MainWindow(logic, Config.APP_STYLES)
    window.setWindowTitle(Config.APP_NAME)
    if Config.APP_ICON.exists():
        window.setWindowIcon(QPixmap(str(Config.APP_ICON)))
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
