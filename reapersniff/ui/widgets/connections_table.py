from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem,
)

from ..theme import CYAN, PURPLE, MUTED, GREEN, WHITE

_COLS = ["Process", "PID", "Proto", "Local", "Remote IP", "R.Port", "Country", "State"]


class ConnectionsTable(QTableWidget):
    """Sortable table of active outbound connections with geo country."""

    def __init__(self, country_lookup, parent=None):
        super().__init__(0, len(_COLS), parent)
        self.country_lookup = country_lookup
        self.setHorizontalHeaderLabels(_COLS)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(_COLS)):
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)

    def update_rows(self, connections):
        # De-duplicate identical TCP/UDP tuples; cap rows for performance.
        seen = set()
        rows = []
        for c in connections:
            key = (c.pid, c.proto, c.rip, c.rport)
            if key in seen:
                continue
            seen.add(key)
            rows.append(c)
        rows = rows[:400]

        self.setSortingEnabled(False)
        self.setRowCount(len(rows))
        for r, c in enumerate(rows):
            proto_color = CYAN if c.proto == "TCP" else PURPLE
            cells = [
                (c.name, WHITE), (str(c.pid), MUTED), (c.proto, proto_color),
                (str(c.lport), MUTED), (c.rip, WHITE), (str(c.rport), MUTED),
                (self.country_lookup(c.rip) or "…", MUTED),
                (c.status, GREEN if c.status == "ESTABLISHED" else MUTED),
            ]
            for col, (text, color) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                if col in (1, 3, 5):
                    item.setData(Qt.DisplayRole, int(text) if text.isdigit() else text)
                self.setItem(r, col, item)
        self.setSortingEnabled(True)
