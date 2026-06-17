# ReaperSniff — PRD

## Original problem statement
Windows desktop dashboard "ReaperSniff" combining **P2P detection + live bandwidth +
connection health**. Detect P2P from games, torrents, and a general many-peers
heuristic. Ship as a Windows **.exe**. Cyan/white/purple polished dark UI.

## User choices (locked)
- Capture: **Hybrid** — psutil by default, optional Npcap deep mode if installed.
- Geo: **Free IP-geo API** (ip-api.com), country labels only, no map.
- UI: **PySide6**.
- Delivery: **Full source + build_exe.bat + PyInstaller spec** (user compiles .exe on Windows).
- Bandwidth: **Per-process + total** upload/download with live graphs.

## Architecture
- Python + PySide6 + pyqtgraph; psutil (default capture); scapy+Npcap (deep mode); requests (geo).
- `core/`: models, util (heuristic KB), sampler (QThread), sniffer (scapy deep), p2p_detector,
  geoip (QThread, batched+cached), health (ping QThread).
- `ui/`: theme (QSS), main_window, widgets (stat_card, graphs, p2p_panel, connections_table, health_panel).
- Packaging: `run.py`, `build_exe.bat`, `reapersniff.spec`.

## Implemented (2026-06)
- Hybrid capture: psutil connection sampling + optional scapy/Npcap per-process bandwidth & UDP peers.
- P2P detection: Torrent / Game / Generic (many-peers) scoring with confidence + reasons.
- Live bandwidth graph (total up/down), per-process throughput in deep mode.
- Connection health: ping monitor, latency graph, jitter/loss/min/max, lag-spike alerts, configurable target.
- Geo country labels via ip-api.com batch (cached). Connections table with country + state.
- Polished cyan/white/purple dark theme. Tabs: Overview, Connections, How it works, Connection Health.
- Validated headless: smoke_test.py (detector + UI build) and live_check.py (real psutil sampling) pass.

## Notes / limitations
- psutil mode cannot see connectionless UDP peers or per-process bandwidth → Npcap deep mode required for those (documented in UI + README).
- ICMP ping returns LOSS inside this Linux sandbox (no raw socket); works on user's Windows PC.
- .exe must be built on Windows (PyInstaller is platform-specific) — build_exe.bat provided.

## Backlog / next
- P0: User builds + runs .exe on Windows, validate Npcap deep mode end-to-end.
- P1: Bundle offline GeoLite2 option; per-process history/sparklines; CSV export of findings.
- P2: System tray + background alerts; custom app icon (drop reapersniff/assets/icon.ico).
- P2: Whitelist/known-good process list to reduce false positives; adjustable thresholds in UI.
