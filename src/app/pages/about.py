"""About page: version, stack and links."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    HyperlinkButton,
    SubtitleLabel,
    TitleLabel,
)

from ...config import Config

REPO_URL = "https://github.com/mekasu0124/mekstitch"


class AboutPage(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AboutPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        root.addWidget(TitleLabel(Config.APP_NAME))
        root.addWidget(CaptionLabel(f"Version {Config.APP_VERSION}"))

        root.addWidget(
            BodyLabel(
                "A chart designer for counted-thread crafts — cross stitch, "
                "crochet, corner-to-corner, Tunisian and knitting colourwork."
            )
        )

        card = CardWidget()
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 16, 16, 16)
        card_lay.setSpacing(6)
        card_lay.addWidget(SubtitleLabel("Built with"))
        for line in (
            "PySide6 (Qt for Python)",
            "PySide6-Fluent-Widgets",
            "python-dotenv",
        ):
            card_lay.addWidget(BodyLabel(f"• {line}"))
        root.addWidget(card)

        root.addWidget(HyperlinkButton(REPO_URL, "Source on GitHub", self))
        root.addStretch(1)
