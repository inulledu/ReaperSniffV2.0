from __future__ import annotations

import socket
import time
from collections import defaultdict

import psutil
from PySide6.QtCore import QThread, Signal

from .models import Connection, ProcessStat, Snapshot
from .p2p_detector import classify_processes
from .util import is_public_ip, prefix16, BT_PORTS, in_game_port

try:
    from .sniffer import ScapySniffer, SCAPY_OK
except Exception:
    ScapySniffer, SCAPY_OK = None, False


class SamplerThread(QThread):
    """Periodically samples connections + bandwidth and emits a Snapshot."""

    snapshot = Signal(object)
    error = Signal(str)
    mode_changed = Signal(str)

    def __init__(self, interval: float = 2.0, use_npcap: bool = False):
        super().__init__()
        self.interval = interval
        self.use_npcap = use_npcap and SCAPY_OK
        self._stop = False
        self._pname = {}
        self.sniffer = None

    def stop(self):
        self._stop = True

    # -- helpers ---------------------------------------------------------
    def _name(self, pid):
        if pid is None:
            return "system"
        if pid in self._pname:
            return self._pname[pid]
        try:
            n = psutil.Process(pid).name()
        except Exception:
            n = f"pid:{pid}"
        self._pname[pid] = n
        return n

    def _collect(self):
        conns = []
        try:
            raw = psutil.net_connections(kind="inet")
        except Exception as e:
            self.error.emit(f"connection scan failed: {e}")
            return conns
        for c in raw:
            if not c.raddr:
                continue
            proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
            conns.append(Connection(
                pid=c.pid,
                name=self._name(c.pid),
                proto=proto,
                lport=c.laddr.port if c.laddr else 0,
                rip=c.raddr.ip,
                rport=c.raddr.port,
                status=c.status or "",
            ))
        return conns

    def _aggregate(self, conns, sniff_bw):
        agg = defaultdict(lambda: {
            "name": "?", "ips": set(), "pref": set(),
            "udp": 0, "tcp": 0, "est": 0, "high": 0, "bt": 0, "game": 0,
        })
        for c in conns:
            if not c.rip or not is_public_ip(c.rip):
                continue
            d = agg[c.pid]
            d["name"] = c.name
            d["ips"].add(c.rip)
            d["pref"].add(prefix16(c.rip))
            if c.proto == "UDP":
                d["udp"] += 1
            else:
                d["tcp"] += 1
            if c.status == "ESTABLISHED":
                d["est"] += 1
            if c.rport > 1024:
                d["high"] += 1
            if c.rport in BT_PORTS or c.lport in BT_PORTS:
                d["bt"] += 1
            if in_game_port(c.rport) or in_game_port(c.lport):
                d["game"] += 1

        result = []
        for pid, d in agg.items():
            up, down = sniff_bw.get(pid, (0.0, 0.0))
            result.append(ProcessStat(
                pid=pid, name=d["name"], peers=len(d["ips"]),
                tcp=d["tcp"], udp=d["udp"], established=d["est"],
                up_rate=up, down_rate=down, remote_ips=d["ips"],
                high_ports=d["high"], bt_hits=d["bt"], game_hits=d["game"],
                distinct_prefixes=len(d["pref"]),
            ))
        return result

    # -- main loop -------------------------------------------------------
    def run(self):
        try:
            prev = psutil.net_io_counters()
            prevt = time.time()
        except Exception as e:
            self.error.emit(str(e))
            return

        if self.use_npcap and ScapySniffer is not None:
            try:
                self.sniffer = ScapySniffer()
                self.sniffer.start()
            except Exception as e:
                self.error.emit(f"Npcap unavailable, using psutil: {e}")
                self.use_npcap = False
        self.mode_changed.emit("Npcap" if self.use_npcap else "psutil")

        while not self._stop:
            t0 = time.time()
            while time.time() - t0 < self.interval and not self._stop:
                time.sleep(0.1)
            if self._stop:
                break
            try:
                cur = psutil.net_io_counters()
                now = time.time()
                dt = max(1e-6, now - prevt)
                up = (cur.bytes_sent - prev.bytes_sent) / dt
                down = (cur.bytes_recv - prev.bytes_recv) / dt
                prev, prevt = cur, now

                conns = self._collect()
                sniff_bw = {}
                if self.use_npcap and self.sniffer:
                    sniff_bw = self.sniffer.drain_bandwidth()
                    for pid, peerset in self.sniffer.drain_peers().items():
                        nm = self._name(pid)
                        for (proto, ip, port) in peerset:
                            conns.append(Connection(pid, nm, proto, 0, ip, port, "OBS"))

                procs = self._aggregate(conns, sniff_bw)
                findings = classify_processes(procs)
                self.snapshot.emit(Snapshot(
                    ts=now, up_rate=up, down_rate=down,
                    total_up=cur.bytes_sent, total_down=cur.bytes_recv,
                    connections=conns, processes=procs, findings=findings,
                    mode="Npcap" if self.use_npcap else "psutil",
                ))
            except Exception as e:
                self.error.emit(str(e))

        if self.sniffer:
            try:
                self.sniffer.stop()
            except Exception:
                pass
