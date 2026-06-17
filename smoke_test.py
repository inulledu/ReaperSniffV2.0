"""Headless smoke test: builds the full app + exercises core logic without a display.

Run:  QT_QPA_PLATFORM=offscreen python smoke_test.py
"""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from reapersniff.core.models import ProcessStat, Connection, HealthSample
from reapersniff.core.p2p_detector import classify_processes
from reapersniff.core.util import is_public_ip, in_game_port, human_rate


def test_detector():
    torrent = ProcessStat(
        pid=101, name="qbittorrent.exe", peers=55, tcp=20, udp=40, established=18,
        up_rate=0, down_rate=0, remote_ips={f"5.5.5.{i}" for i in range(55)},
        high_ports=58, bt_hits=6, game_hits=0, distinct_prefixes=30)
    game = ProcessStat(
        pid=202, name="VALORANT.exe", peers=8, tcp=1, udp=9, established=2,
        up_rate=0, down_rate=0, remote_ips={f"104.16.0.{i}" for i in range(8)},
        high_ports=9, bt_hits=0, game_hits=4, distinct_prefixes=6)
    generic = ProcessStat(
        pid=303, name="mystery.exe", peers=40, tcp=2, udp=45, established=5,
        up_rate=0, down_rate=0, remote_ips={f"77.{i}.0.1" for i in range(40)},
        high_ports=46, bt_hits=0, game_hits=0, distinct_prefixes=40)
    normal = ProcessStat(
        pid=404, name="chrome.exe", peers=3, tcp=6, udp=0, established=6,
        up_rate=0, down_rate=0, remote_ips={"142.250.1.1"},
        high_ports=2, bt_hits=0, game_hits=0, distinct_prefixes=2)

    findings = classify_processes([torrent, game, generic, normal])
    cats = {f.name: f.category for f in findings}
    assert cats.get("qbittorrent.exe") == "Torrent P2P", cats
    assert cats.get("VALORANT.exe") == "Game P2P", cats
    assert cats.get("mystery.exe") == "Generic P2P", cats
    assert "chrome.exe" not in cats, "normal app must not be flagged"
    print("detector OK ->", [(f.name, f.category, f.confidence) for f in findings])


def test_util():
    assert is_public_ip("8.8.8.8") is True
    assert is_public_ip("192.168.1.5") is False
    assert in_game_port(27015) is True
    assert human_rate(1536) == "1.5 KB/s"
    print("util OK")


def test_app_builds():
    from PySide6.QtWidgets import QApplication
    from reapersniff.ui.main_window import MainWindow
    from reapersniff.ui.theme import build_stylesheet

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(build_stylesheet())
    w = MainWindow()
    w.show()

    # feed a synthetic snapshot through the UI path
    from reapersniff.core.models import Snapshot
    conns = [Connection(101, "qbittorrent.exe", "TCP", 6881, "5.5.5.5", 6881, "ESTABLISHED")]
    procs = [ProcessStat(101, "qbittorrent.exe", 55, 20, 40, 18, 0, 0,
                         {"5.5.5.5"}, 58, 6, 0, 30)]
    findings = classify_processes(procs)
    snap = Snapshot(0, 2048, 1024, 99999, 88888, conns, procs, findings, "psutil")
    w._on_snapshot(snap)
    w._on_ping(HealthSample(0, 42.0, "8.8.8.8"))
    w._on_ping(HealthSample(0, None, "8.8.8.8"))
    w._on_ping(HealthSample(0, 250.0, "8.8.8.8"))
    app.processEvents()
    print("app builds + renders OK")


if __name__ == "__main__":
    test_util()
    test_detector()
    test_app_builds()
    print("\nALL SMOKE TESTS PASSED")
