from __future__ import annotations

import ipaddress


def is_public_ip(ip: str) -> bool:
    """True only for globally-routable addresses (excludes LAN/loopback/etc)."""
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def prefix16(ip: str) -> str:
    """Coarse network prefix used to measure peer diversity."""
    try:
        if ":" in ip:
            return ":".join(ip.split(":")[:2])
        return ".".join(ip.split(".")[:2])
    except Exception:
        return ip


# ---- P2P heuristic knowledge base ---------------------------------------

# Common BitTorrent listen / tracker / DHT ports.
BT_PORTS = set(range(6881, 6890)) | {6969, 51413, 1337, 25401}

# Port ranges frequently used by peer-to-peer game netcode (mostly UDP).
GAME_PORT_RANGES = [
    (27000, 27100),   # Steam / Source
    (3074, 3079),     # Xbox Live / CoD
    (3478, 3480),     # STUN / PSN
    (3658, 3659),     # EA
    (5055, 5058),     # Photon (Unity games)
    (6250, 6250),     # CoD
    (7000, 8100),     # Riot / misc
    (9000, 9100),     # Epic / Fortnite
    (7777, 7788),     # Unreal / misc
    (4379, 4380),     # Steam
    (4500, 4500),     # IPSec / game NAT traversal
    (12000, 12100),   # misc game relays
]


def in_game_port(p: int) -> bool:
    return any(a <= p <= b for a, b in GAME_PORT_RANGES)


# Process executable name fragments (lower-case) that strongly imply a category.
TORRENT_APPS = [
    "qbittorrent", "utorrent", "\u00b5torrent", "bittorrent", "transmission",
    "deluge", "vuze", "tixati", "bitcomet", "frostwire", "aria2", "libtorrent",
    "picotorrent", "webtorrent",
]

GAME_APPS = [
    "valorant", "riotclient", "league of legends", "leagueclient", "csgo",
    "cs2", "dota2", "fortnite", "fortniteclient", "overwatch", "rocketleague",
    "warzone", "modernwarfare", "callofduty", "cod", "apex", "r5apex",
    "pubg", "tslgame", "destiny2", "gta5", "fivem", "rainbowsix", "siege",
    "warframe", "minecraft", "javaw", "genshinimpact", "halo", "battlefield",
    "fall guys", "fallguys", "amongus", "terraria", "deeprock",
]


def human_rate(bps: float) -> str:
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    v = float(bps)
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.1f} {units[i]}"


def human_bytes(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.1f} {units[i]}"
