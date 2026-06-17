from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.geoip import GeoThread
from ..core.health import PingThread
from ..core.sampler import SamplerThread
from ..core.sniffer import SCAPY_OK
from ..core.util import human_bytes, human_rate, is_public_ip
from .theme import AMBER, BG_1, BORDER, CYAN, GREEN, MUTED, PURPLE, RED, WHITE
from .widgets.connections_table import ConnectionsTable
from .widgets.graphs import BandwidthGraph
from .widgets.health_panel import HealthPanel
from .widgets.p2p_panel import P2PPanel
from .widgets.stat_card import StatCard

SPIKE_THRESHOLD = 80.0


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReaperSniff — LAN · P2P · Health Monitor")
        self.resize(1280, 820)

        self.geo = {}          # ip -> country string
        self.sampler = None
        self.geo_thread = None
        self.ping_thread = None
        self.capturing = False

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(18, 16, 18, 18)
        body_lay.setSpacing(14)
        body_lay.addLayout(self._build_cards())
        body_lay.addWidget(self._build_tabs(), 1)
        layout.addWidget(body, 1)

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(74)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = QLabel('Reaper<span id="accent" style="color:%s">Sniff</span>' % CYAN)
        title.setObjectName("title")
        title.setTextFormat(Qt.RichText)
        sub = QLabel("Live bandwidth · P2P detection · connection health")
        sub.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(sub)
        lay.addLayout(titles)
        lay.addStretch(1)

        self.mode_badge = QLabel("idle")
        self.mode_badge.setObjectName("badge")
        self.mode_badge.setStyleSheet(f"#badge {{ background:{BORDER}; color:{MUTED}; }}")
        lay.addWidget(self.mode_badge)

        self.npcap_chk = QCheckBox("Npcap deep mode")
        self.npcap_chk.setEnabled(SCAPY_OK)
        self.npcap_chk.setToolTip(
            "Requires Npcap + admin. Enables real per-process bandwidth and "
            "full UDP peer detection." if SCAPY_OK
            else "Install Npcap and the scapy package to enable deep capture.")
        lay.addWidget(self.npcap_chk)

        self.start_btn = QPushButton("Start Capture")
        self.start_btn.clicked.connect(self.toggle_capture)
        lay.addWidget(self.start_btn)
        return header

    def _build_cards(self):
        grid = QGridLayout()
        grid.setSpacing(12)
        self.card_down = StatCard("Download", CYAN)
        self.card_up = StatCard("Upload", PURPLE)
        self.card_conns = StatCard("Connections", WHITE)
        self.card_p2p = StatCard("P2P Processes", AMBER)
        self.card_lat = StatCard("Latency", GREEN)
        self.card_total = StatCard("Session Total", WHITE)
        cards = [self.card_down, self.card_up, self.card_conns,
                 self.card_p2p, self.card_lat, self.card_total]
        for i, c in enumerate(cards):
            grid.addWidget(c, 0, i)
        return grid

    def _build_tabs(self):
        self.tabs = QTabWidget()

        # Overview tab: bandwidth graph + P2P findings
        overview = QWidget()
        ov = QVBoxLayout(overview)
        ov.setContentsMargins(14, 14, 14, 14)
        ov.setSpacing(12)
        bw_title = QLabel("LIVE BANDWIDTH")
        bw_title.setObjectName("cardTitle")
        ov.addWidget(bw_title)
        self.bw_graph = BandwidthGraph()
        self.bw_graph.setMinimumHeight(230)
        ov.addWidget(self.bw_graph, 2)
        p2p_title = QLabel("P2P DETECTION")
        p2p_title.setObjectName("cardTitle")
        ov.addWidget(p2p_title)
        self.p2p_panel = P2PPanel(self._country)
        ov.addWidget(self.p2p_panel, 3)
        self.tabs.addTab(overview, "Overview")

        # Connections tab
        conn_tab = QWidget()
        cl = QVBoxLayout(conn_tab)
        cl.setContentsMargins(14, 14, 14, 14)
        self.conn_table = ConnectionsTable(self._country)
        cl.addWidget(self.conn_table)
        self.tabs.addTab(conn_tab, "Connections")

        # P2P detail tab (reuse panel? need separate widget) -> heuristics info
        p2p_tab = QWidget()
        pl = QVBoxLayout(p2p_tab)
        pl.setContentsMargins(18, 18, 18, 18)
        pl.setSpacing(10)
        info = QLabel(
            "How detection works\n\n"
            "• Torrent P2P — known clients (qBittorrent, Transmission…), "
            "BitTorrent ports (6881-6889 / 51413), large peer swarms across many "
            "distinct networks, UDP-heavy uTP/DHT traffic.\n\n"
            "• Game P2P — known game executables and P2P game netcode: a handful "
            "of UDP peers on game port ranges (Steam 27000-27100, Xbox 3074, "
            "Riot/Photon, etc.).\n\n"
            "• Generic P2P — the many-peers heuristic: any process opening lots of "
            "simultaneous connections to many different networks on high ephemeral "
            "ports, predominantly UDP.\n\n"
            "Tip: enable Npcap deep mode for real per-process throughput and full "
            "UDP peer visibility (psutil cannot see connectionless UDP peers)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{MUTED}; font-size:13px; line-height:160%;")
        pl.addWidget(info)
        pl.addStretch(1)
        self.tabs.addTab(p2p_tab, "How it works")

        # Health tab
        self.health_panel = HealthPanel(threshold=SPIKE_THRESHOLD)
        self.health_panel.target_changed.connect(self._on_target_changed)
        health_tab = QWidget()
        hl = QVBoxLayout(health_tab)
        hl.setContentsMargins(14, 14, 14, 14)
        hl.addWidget(self.health_panel)
        self.tabs.addTab(health_tab, "Connection Health")

        return self.tabs

    # ------------------------------------------------------------- capture
    def toggle_capture(self):
        if self.capturing:
            self._stop_capture()
        else:
            self._start_capture()

    def _start_capture(self):
        self.capturing = True
        self.start_btn.setText("Stop Capture")
        self.start_btn.setObjectName("danger")
        self.start_btn.setStyleSheet("")  # re-evaluate object name styling
        self.style().unpolish(self.start_btn)
        self.style().polish(self.start_btn)
        self.npcap_chk.setEnabled(False)

        self.geo_thread = GeoThread()
        self.geo_thread.resolved.connect(self._on_geo)
        self.geo_thread.start()

        self.sampler = SamplerThread(interval=2.0, use_npcap=self.npcap_chk.isChecked())
        self.sampler.snapshot.connect(self._on_snapshot)
        self.sampler.error.connect(self._on_error)
        self.sampler.mode_changed.connect(self._on_mode)
        self.sampler.start()

        self.ping_thread = PingThread(target=self.health_panel.target_edit.text(),
                                      interval=1.0)
        self.ping_thread.sample.connect(self._on_ping)
        self.ping_thread.start()

    def _stop_capture(self):
        self.capturing = False
        self.start_btn.setText("Start Capture")
        self.start_btn.setObjectName("")
        self.style().unpolish(self.start_btn)
        self.style().polish(self.start_btn)
        self.npcap_chk.setEnabled(SCAPY_OK)
        for th in (self.sampler, self.ping_thread, self.geo_thread):
            if th:
                th.stop()
                th.wait(2000)
        self.sampler = self.ping_thread = self.geo_thread = None
        self.mode_badge.setText("idle")
        self.mode_badge.setStyleSheet(f"#badge {{ background:{BORDER}; color:{MUTED}; }}")

    # --------------------------------------------------------------- slots
    @Slot(object)
    def _on_snapshot(self, snap):
        # enqueue unknown public IPs for geo lookup
        unknown = {c.rip for c in snap.connections
                   if is_public_ip(c.rip) and c.rip not in self.geo}
        if unknown and self.geo_thread:
            self.geo_thread.enqueue(unknown)

        self.bw_graph.push(snap.down_rate, snap.up_rate)
        self.card_down.set_value(human_rate(snap.down_rate))
        self.card_up.set_value(human_rate(snap.up_rate))
        self.card_conns.set_value(str(len(snap.connections)),
                                  f"{len(snap.processes)} processes")
        self.card_p2p.set_value(str(len(snap.findings)),
                                "torrent/game/generic")
        self.card_total.set_value(human_bytes(snap.total_down),
                                  f"↑ {human_bytes(snap.total_up)}")

        self.conn_table.update_rows(snap.connections)
        self.p2p_panel.update_findings(snap.findings)

    @Slot(dict)
    def _on_geo(self, mapping):
        for ip, info in mapping.items():
            self.geo[ip] = info.get("country", "")

    @Slot(object)
    def _on_ping(self, sample):
        self.health_panel.add_sample(sample)
        if sample.latency is None:
            self.card_lat.set_value("LOSS", sample.target)
            self.card_lat.set_accent(RED)
        else:
            self.card_lat.set_value(f"{sample.latency:.0f} ms", sample.target)
            self.card_lat.set_accent(
                GREEN if sample.latency <= SPIKE_THRESHOLD else AMBER)

    @Slot(str)
    def _on_mode(self, mode):
        color = PURPLE if mode == "Npcap" else CYAN
        self.mode_badge.setText(f"capturing · {mode}")
        self.mode_badge.setStyleSheet(f"#badge {{ background:{color}26; color:{color}; }}")

    @Slot(str)
    def _on_error(self, msg):
        self.mode_badge.setText(msg[:60])

    def _on_target_changed(self, target):
        if self.ping_thread:
            self.ping_thread.set_target(target)

    def _country(self, ip):
        if not is_public_ip(ip):
            return "LAN"
        return self.geo.get(ip, "")

    def closeEvent(self, event):
        if self.capturing:
            self._stop_capture()
        super().closeEvent(event)
