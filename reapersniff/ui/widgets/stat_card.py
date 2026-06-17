from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ..theme import CYAN


class StatCard(QFrame):
    """Compact metric card: title, big value, small subtext, accent colour."""

    def __init__(self, title: str, accent: str = CYAN, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.accent = accent
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        self.title = QLabel(title.upper())
        self.title.setObjectName("cardTitle")

        self.value = QLabel("--")
        self.value.setObjectName("cardValue")
        self.value.setStyleSheet(f"color: {accent};")

        self.sub = QLabel("")
        self.sub.setObjectName("cardSub")

        lay.addWidget(self.title)
        lay.addWidget(self.value)
        lay.addWidget(self.sub)
        lay.addStretch(1)

    def set_value(self, value: str, sub: str = ""):
        self.value.setText(value)
        self.sub.setText(sub)

    def set_accent(self, color: str):
        self.accent = color
        self.value.setStyleSheet(f"color: {color};")
