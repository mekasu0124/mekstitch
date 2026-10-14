"""Application-wide paths and metadata.

Mirrors `src/config.py` in the Momentum project: a single `Config` class that
every other module imports instead of hard-coding filesystem paths.
"""

from pathlib import Path


class Config:
    APP_DIR = Path(__file__).parent
    APP_NAME = "mekstitch"
    APP_VERSION = "1.0.0"

    APP_ICON = Path(__file__).parent / "assets/mekstitch.png"
    APP_STYLES = Path(__file__).parent / "assets/styles.qss"
