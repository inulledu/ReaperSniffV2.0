from __future__ import annotations

from .models import ProcessStat, P2PFinding
from .util import TORRENT_APPS, GAME_APPS

# Minimum score for a process to be surfaced as P2P.
THRESHOLD = 45


def _name_hit(name: str, table) -> bool:
    n = (name or "").lower()
    return any(k in n for k in table)


def classify_process(ps: ProcessStat) -> P2PFinding | None:
    """Score a single process against torrent / game / generic-P2P heuristics."""
    name = ps.name or "?"
    total = ps.tcp + ps.udp
    if total == 0 and ps.peers == 0:
        return None

    udp_ratio = ps.udp / total if total else 0.0
    high_ratio = ps.high_ports / total if total else 0.0
    diversity = ps.distinct_prefixes
    peers = ps.peers

    is_torrent_app = _name_hit(name, TORRENT_APPS)
    is_game_app = _name_hit(name, GAME_APPS)

    # ---- Torrent / BitTorrent score ----
    t = 0
    t_reasons = []
    if is_torrent_app:
        t += 60
        t_reasons.append("known torrent client")
    if ps.bt_hits > 0:
        t += 25
        t_reasons.append(f"BitTorrent ports ({ps.bt_hits})")
    if peers >= 40:
        t += 28
        t_reasons.append(f"swarm of {peers} peers")
    elif peers >= 15:
        t += 14
    if diversity >= 12:
        t += 16
        t_reasons.append(f"{diversity} distinct networks")
    if udp_ratio > 0.5 and peers >= 20:
        t += 10
        t_reasons.append("UDP-heavy swarm (uTP/DHT)")

    # ---- Game P2P score ----
    g = 0
    g_reasons = []
    if is_game_app:
        g += 55
        g_reasons.append("known game process")
    if ps.game_hits > 0:
        g += 28
        g_reasons.append(f"game ports ({ps.game_hits})")
    if 2 <= peers <= 40 and udp_ratio > 0.45:
        g += 22
        g_reasons.append(f"{peers} UDP peers (P2P netcode)")
    if ps.game_hits > 0 and ps.udp > 0:
        g += 10

    # ---- Generic many-peers score ----
    gen = 0
    gen_reasons = []
    if peers >= 25:
        gen += 35
        gen_reasons.append(f"{peers} simultaneous peers")
    if diversity >= 14:
        gen += 25
        gen_reasons.append(f"{diversity} distinct networks")
    if udp_ratio > 0.6:
        gen += 20
        gen_reasons.append("predominantly UDP")
    if high_ratio > 0.8:
        gen += 10
        gen_reasons.append("ephemeral high ports")
    if peers >= 60:
        gen += 15

    best = max(t, g, gen)
    if best < THRESHOLD:
        return None

    if best == t:
        category, reasons = "Torrent P2P", t_reasons
    elif best == g:
        category, reasons = "Game P2P", g_reasons
    else:
        # Promote to Torrent if clear BitTorrent indicators are present.
        if ps.bt_hits > 0 or is_torrent_app:
            category, reasons = "Torrent P2P", gen_reasons + ["BitTorrent indicators"]
        else:
            category, reasons = "Generic P2P", gen_reasons

    return P2PFinding(
        pid=ps.pid,
        name=name,
        category=category,
        confidence=min(99, int(best)),
        peers=peers,
        udp=ps.udp,
        tcp=ps.tcp,
        reasons=reasons or ["heuristic match"],
        remote_ips=list(ps.remote_ips)[:8],
    )


def classify_processes(processes) -> list:
    findings = []
    for ps in processes:
        f = classify_process(ps)
        if f is not None:
            findings.append(f)
    findings.sort(key=lambda f: f.confidence, reverse=True)
    return findings
