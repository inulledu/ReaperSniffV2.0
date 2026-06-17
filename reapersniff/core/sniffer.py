from __future__ import annotations

import threading
import time
from collections import defaultdict

from .util import is_public_ip

try:
    from scapy.all import AsyncSniffer, IP, IPv6, TCP, UDP
    import psutil
    SCAPY_OK = True
except Exception:  # pragma: no cover - scapy/Npcap not present
    SCAPY_OK = False


class ScapySniffer:
    """Deep-capture engine (Npcap mode).

    Sniffs packets, attributes bytes + remote peers to the owning process by
    mapping the local port to a PID via the OS socket table. Provides real
    per-process bandwidth and full UDP peer visibility that psutil cannot.
    """

    def __init__(self):
        if not SCAPY_OK:
            raise RuntimeError("scapy / Npcap not available on this system")
        self._stop = False
        self.lock = threading.Lock()
        self.portmap = {}                       # (proto, local_port) -> pid
        self.bw = defaultdict(lambda: [0.0, 0.0])   # pid -> [up_bytes, down_bytes]
        self.peers = defaultdict(set)           # pid -> {(proto, ip, port)}
        self.local_ips = self._local_ips()
        self._last = time.time()
        self._sniffer = None
        self._mapthread = None

    # -- setup -----------------------------------------------------------
    def _local_ips(self):
        ips = set()
        try:
            for addrs in psutil.net_if_addrs().values():
                for a in addrs:
                    if a.address:
                        ips.add(a.address.split("%")[0])
        except Exception:
            pass
        return ips

    def _refresh_portmap(self):
        m = {}
        try:
            for c in psutil.net_connections(kind="inet"):
                if not c.laddr or c.pid is None:
                    continue
                proto = "TCP" if c.type == 1 else "UDP"
                m[(proto, c.laddr.port)] = c.pid
        except Exception:
            pass
        self.portmap = m

    # -- lifecycle -------------------------------------------------------
    def start(self):
        self._refresh_portmap()
        self._last = time.time()
        self._sniffer = AsyncSniffer(prn=self._on_packet, store=False)
        self._sniffer.start()
        self._mapthread = threading.Thread(target=self._map_loop, daemon=True)
        self._mapthread.start()

    def _map_loop(self):
        while not self._stop:
            self._refresh_portmap()
            time.sleep(2)

    def stop(self):
        self._stop = True
        try:
            if self._sniffer:
                self._sniffer.stop()
        except Exception:
            pass

    # -- packet handler --------------------------------------------------
    def _on_packet(self, pkt):
        try:
            if IP in pkt:
                src, dst = pkt[IP].src, pkt[IP].dst
            elif IPv6 in pkt:
                src, dst = pkt[IPv6].src, pkt[IPv6].dst
            else:
                return
            if TCP in pkt:
                proto, sport, dport = "TCP", pkt[TCP].sport, pkt[TCP].dport
            elif UDP in pkt:
                proto, sport, dport = "UDP", pkt[UDP].sport, pkt[UDP].dport
            else:
                return

            length = len(pkt)
            if src in self.local_ips:
                local_port, rip, rport, up = sport, dst, dport, True
            elif dst in self.local_ips:
                local_port, rip, rport, up = dport, src, sport, False
            else:
                return

            pid = self.portmap.get((proto, local_port))
            if pid is None:
                return
            with self.lock:
                self.bw[pid][0 if up else 1] += length
                if is_public_ip(rip):
                    self.peers[pid].add((proto, rip, rport))
        except Exception:
            pass

    # -- drains (called from sampler) ------------------------------------
    def drain_bandwidth(self):
        with self.lock:
            now = time.time()
            dt = max(1e-6, now - self._last)
            self._last = now
            out = {pid: (u / dt, d / dt) for pid, (u, d) in self.bw.items()}
            self.bw.clear()
            return out

    def drain_peers(self):
        with self.lock:
            out = {pid: set(s) for pid, s in self.peers.items()}
            self.peers.clear()
            return out
