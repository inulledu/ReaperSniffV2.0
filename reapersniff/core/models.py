from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Connection:
    pid: Optional[int]
    name: str
    proto: str            # 'TCP' | 'UDP'
    lport: int
    rip: str
    rport: int
    status: str


@dataclass
class ProcessStat:
    pid: Optional[int]
    name: str
    peers: int
    tcp: int
    udp: int
    established: int
    up_rate: float        # bytes/sec (Npcap mode only)
    down_rate: float      # bytes/sec (Npcap mode only)
    remote_ips: set = field(default_factory=set)
    high_ports: int = 0
    bt_hits: int = 0
    game_hits: int = 0
    distinct_prefixes: int = 0


@dataclass
class P2PFinding:
    pid: Optional[int]
    name: str
    category: str         # 'Torrent P2P' | 'Game P2P' | 'Generic P2P'
    confidence: int       # 0..99
    peers: int
    udp: int
    tcp: int
    reasons: list = field(default_factory=list)
    remote_ips: list = field(default_factory=list)


@dataclass
class Snapshot:
    ts: float
    up_rate: float
    down_rate: float
    total_up: int
    total_down: int
    connections: list
    processes: list
    findings: list
    mode: str             # 'psutil' | 'Npcap'


@dataclass
class HealthSample:
    ts: float
    latency: Optional[float]   # ms, or None for timeout/loss
    target: str
