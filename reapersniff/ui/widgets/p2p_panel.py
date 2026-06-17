from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget,
    QScrollArea,
)

from ..theme import BG_2, BORDER, CAT_COLORS, MUTED, WHITE, CYAN


class FindingCard(QFrame):
    """One detected P2P process with category chip + confidence bar."""

    def __init__(self, finding, country_lookup, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.country_lookup = country_lookup
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        self.name = QLabel()
        self.name.setStyleSheet(f"font-size:14px; font-weight:800; color:{WHITE};")
        self.chip = QLabel()
        self.chip.setObjectName("badge")
        self.chip.setAlignment(Qt.AlignCenter)
        top.addWidget(self.name)
        top.addStretch(1)
        top.addWidget(self.chip)
        lay.addLayout(top)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        lay.addWidget(self.bar)

        self.meta = QLabel()
        self.meta.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        self.meta.setWordWrap(True)
        lay.addWidget(self.meta)

        self.reasons = QLabel()
        self.reasons.setStyleSheet(f"color:{CYAN}; font-size:11px;")
        self.reasons.setWordWrap(True)
        lay.addWidget(self.reasons)

        self.update_finding(finding)

    def update_finding(self, f):
        color = CAT_COLORS.get(f.category, CYAN)
        self.name.setText(f"{f.name}  ·  pid {f.pid}")
        self.chip.setText(f"{f.category}  {f.confidence}%")
        self.chip.setStyleSheet(f"#badge {{ background: {color}26; color: {color}; }}")
        self.bar.setValue(f.confidence)
        self.bar.setStyleSheet(
            f"QProgressBar::chunk {{ border-radius:4px; background:{color}; }}")

        countries = sorted({self.country_lookup(ip) for ip in f.remote_ips} - {""})
        c_txt = ", ".join(countries) if countries else "resolving…"
        self.meta.setText(
            f"{f.peers} peers   ·   {f.tcp} TCP / {f.udp} UDP   ·   {c_txt}")
        self.reasons.setText("• " + "   • ".join(f.reasons))


class P2PPanel(QWidget):
    """Scrollable list of P2P findings (cards), incrementally updated."""

    def __init__(self, country_lookup, parent=None):
        super().__init__(parent)
        self.country_lookup = country_lookup
        self.cards = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self.empty = QLabel("No P2P activity detected yet.\n"
                            "Start capture and let traffic flow.")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setStyleSheet(f"color:{MUTED}; font-size:13px; padding:30px;")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.vbox = QVBoxLayout(self.host)
        self.vbox.setContentsMargins(2, 2, 2, 2)
        self.vbox.setSpacing(10)
        self.vbox.addWidget(self.empty)
        self.vbox.addStretch(1)
        self.scroll.setWidget(self.host)
        outer.addWidget(self.scroll)

    def update_findings(self, findings):
        self.empty.setVisible(len(findings) == 0)
        seen = set()
        for f in findings:
            seen.add(f.pid)
            if f.pid in self.cards:
                self.cards[f.pid].update_finding(f)
            else:
                card = FindingCard(f, self.country_lookup)
                self.cards[f.pid] = card
                self.vbox.insertWidget(self.vbox.count() - 1, card)
        for pid in list(self.cards):
            if pid not in seen:
                w = self.cards.pop(pid)
                w.setParent(None)
                w.deleteLater()
