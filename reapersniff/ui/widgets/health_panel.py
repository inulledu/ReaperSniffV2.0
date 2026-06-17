from __future__ import annotations

from collections import deque
from statistics import mean, pstdev

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor

from ..theme import AMBER, BORDER, CYAN, GREEN, MUTED, RED, WHITE
from .graphs import LatencyGraph


def _stat(label):
    box = QFrame()
    box.setObjectName("card")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)
    t = QLabel(label.upper())
    t.setObjectName("cardTitle")
    v = QLabel("--")
    v.setStyleSheet("font-size:18px; font-weight:800; font-family:Consolas,monospace;")
    lay.addWidget(t)
    lay.addWidget(v)
    return box, v


class HealthPanel(QWidget):
    """Latency graph + jitter/loss stats + spike alert log + target control."""

    target_changed = Signal(str)

    def __init__(self, threshold: float = 80.0, parent=None):
        super().__init__(parent)
        self.threshold = threshold
        self.samples = deque(maxlen=120)   # latency values (None=loss)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # target control row
        ctrl = QHBoxLayout()
        lbl = QLabel("Target")
        lbl.setStyleSheet(f"color:{MUTED}; font-weight:700;")
        self.target_edit = QLineEdit("8.8.8.8")
        self.target_edit.setPlaceholderText("game server IP or hostname")
        self.target_edit.setFixedWidth(260)
        apply_btn = QPushButton("Set Target")
        apply_btn.clicked.connect(self._apply)
        ctrl.addWidget(lbl)
        ctrl.addWidget(self.target_edit)
        ctrl.addWidget(apply_btn)
        ctrl.addStretch(1)
        thr_lbl = QLabel(f"Spike threshold: {int(self.threshold)} ms")
        thr_lbl.setStyleSheet(f"color:{AMBER}; font-weight:700;")
        self.thr_lbl = thr_lbl
        ctrl.addWidget(thr_lbl)
        root.addLayout(ctrl)

        # graph
        self.graph = LatencyGraph(threshold=self.threshold)
        self.graph.setMinimumHeight(220)
        root.addWidget(self.graph, 2)

        # stat cards
        stats = QHBoxLayout()
        stats.setSpacing(10)
        self.box_cur, self.v_cur = _stat("Current")
        self.box_avg, self.v_avg = _stat("Average")
        self.box_jit, self.v_jit = _stat("Jitter")
        self.box_loss, self.v_loss = _stat("Loss")
        self.box_min, self.v_min = _stat("Min")
        self.box_max, self.v_max = _stat("Max")
        for b in (self.box_cur, self.box_avg, self.box_jit, self.box_loss,
                  self.box_min, self.box_max):
            stats.addWidget(b)
        root.addLayout(stats)

        # alerts
        al = QLabel("LAG SPIKE ALERTS")
        al.setObjectName("cardTitle")
        root.addWidget(al)
        self.alerts = QListWidget()
        self.alerts.setMinimumHeight(120)
        root.addWidget(self.alerts, 1)

    def _apply(self):
        self.target_changed.emit(self.target_edit.text())
        self._alert(f"Target changed to {self.target_edit.text().strip()}", MUTED)

    def add_sample(self, sample):
        lat = sample.latency
        self.samples.append(lat)
        self.graph.push(lat)

        valid = [v for v in self.samples if v is not None]
        loss = 100.0 * (1 - len(valid) / len(self.samples)) if self.samples else 0.0
        avg = mean(valid) if valid else 0.0
        jit = pstdev(valid) if len(valid) > 1 else 0.0

        self.v_cur.setText("LOSS" if lat is None else f"{lat:.0f} ms")
        self.v_cur.setStyleSheet(self._color_for(lat))
        self.v_avg.setText(f"{avg:.0f} ms")
        self.v_jit.setText(f"{jit:.0f} ms")
        self.v_loss.setText(f"{loss:.0f}%")
        self.v_min.setText(f"{min(valid):.0f} ms" if valid else "--")
        self.v_max.setText(f"{max(valid):.0f} ms" if valid else "--")

        # spike / loss alerts
        if lat is None:
            self._alert(f"Packet loss to {sample.target}", RED)
        elif lat > self.threshold or (avg and lat > avg + 2 * jit and lat > 50):
            self._alert(f"Lag spike: {lat:.0f} ms to {sample.target}", AMBER)

    def _color_for(self, lat):
        if lat is None:
            return f"font-size:18px; font-weight:800; color:{RED}; font-family:Consolas,monospace;"
        if lat > self.threshold:
            return f"font-size:18px; font-weight:800; color:{AMBER}; font-family:Consolas,monospace;"
        return f"font-size:18px; font-weight:800; color:{GREEN}; font-family:Consolas,monospace;"

    def _alert(self, text, color):
        from time import strftime
        item = QListWidgetItem(f"[{strftime('%H:%M:%S')}]  {text}")
        item.setForeground(QColor(color))
        self.alerts.insertItem(0, item)
        while self.alerts.count() > 100:
            self.alerts.takeItem(self.alerts.count() - 1)
