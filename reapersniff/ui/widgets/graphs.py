from __future__ import annotations

from collections import deque

import pyqtgraph as pg
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..theme import BG_2, CYAN, PURPLE, MUTED, AMBER

pg.setConfigOptions(antialias=True)


def _pen(color, width=2):
    return pg.mkPen(color, width=width)


class BandwidthGraph(QWidget):
    """Live download/upload throughput (KB/s) with filled area curves."""

    def __init__(self, points: int = 90, parent=None):
        super().__init__(parent)
        self.n = points
        self.down = deque([0.0] * points, maxlen=points)
        self.up = deque([0.0] * points, maxlen=points)
        self.x = list(range(-points + 1, 1))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget()
        self.plot.setBackground(QColor(BG_2))
        self.plot.showGrid(x=False, y=True, alpha=0.12)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.plot.getAxis("bottom").setStyle(showValues=False)
        self.plot.getAxis("left").setTextPen(MUTED)
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.setLabel("left", "KB/s", color=MUTED)
        self.plot.addLegend(offset=(10, 8), labelTextColor=MUTED, brush=None, pen=None)

        self.down_curve = self.plot.plot(
            self.x, list(self.down), pen=_pen(CYAN),
            fillLevel=0, brush=pg.mkBrush(QColor(34, 211, 238, 45)), name="Download")
        self.up_curve = self.plot.plot(
            self.x, list(self.up), pen=_pen(PURPLE),
            fillLevel=0, brush=pg.mkBrush(QColor(168, 85, 247, 45)), name="Upload")
        lay.addWidget(self.plot)

    def push(self, down_bps: float, up_bps: float):
        self.down.append(down_bps / 1024.0)
        self.up.append(up_bps / 1024.0)
        self.down_curve.setData(self.x, list(self.down))
        self.up_curve.setData(self.x, list(self.up))


class LatencyGraph(QWidget):
    """Live latency (ms) with a configurable spike threshold line."""

    def __init__(self, points: int = 120, threshold: float = 80.0, parent=None):
        super().__init__(parent)
        self.n = points
        self.vals = deque([0.0] * points, maxlen=points)
        self.x = list(range(-points + 1, 1))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget()
        self.plot.setBackground(QColor(BG_2))
        self.plot.showGrid(x=False, y=True, alpha=0.12)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.plot.getAxis("bottom").setStyle(showValues=False)
        self.plot.getAxis("left").setTextPen(MUTED)
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.setLabel("left", "ms", color=MUTED)

        self.curve = self.plot.plot(
            self.x, list(self.vals), pen=_pen(CYAN),
            fillLevel=0, brush=pg.mkBrush(QColor(34, 211, 238, 35)))
        self.threshold_line = pg.InfiniteLine(
            pos=threshold, angle=0,
            pen=pg.mkPen(AMBER, width=1, style=pg.QtCore.Qt.DashLine))
        self.plot.addItem(self.threshold_line)
        lay.addWidget(self.plot)

    def set_threshold(self, value: float):
        self.threshold_line.setPos(value)

    def push(self, latency):
        self.vals.append(float(latency) if latency is not None else 0.0)
        self.curve.setData(self.x, list(self.vals))
