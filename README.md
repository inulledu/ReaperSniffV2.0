# ReaperSniff

A polished **Windows desktop dashboard** that combines **P2P traffic detection**,
**live bandwidth monitoring**, and **connection health** in one clean cyan/white/purple
dark interface.

> Built for monitoring **your own machine and network, with your consent.** It inspects
> your own host's connections — it is a personal monitoring/learning tool.

---

## Features

- **Live bandwidth** — total upload/download throughput with filled live graphs, plus
  per-process throughput in deep-capture mode.
- **P2P detection** — three heuristics working together:
  - **Torrent P2P** — known clients + BitTorrent ports + large peer swarms (uTP/DHT).
  - **Game P2P** — known game executables + P2P game netcode on game port ranges.
  - **Generic P2P** — the "many-peers" heuristic (many simultaneous peers across many
    distinct networks on high UDP ports).
  - Each finding shows a category chip, confidence bar, peers, protocol split, the
    reasons it matched, and peer **countries**.
- **Connection health** — ping a game server / any host, with a latency graph, jitter,
  packet loss, min/max, and **lag-spike alerts**.
- **Geo country labels** — remote peers resolved to country via a free key-less IP-geo
  API (no map, just labels), cached locally.
- **Connections table** — every active outbound connection (process, proto, remote IP,
  port, country, state), sortable.

---

## Tech stack

- **Python + PySide6** (Qt GUI) + **pyqtgraph** (live charts)
- **psutil** — default capture (no driver, no admin needed for your own processes)
- **scapy + Npcap** — optional deep capture (real per-process bandwidth + UDP peers)
- **PyInstaller** — packaged into a standalone Windows `.exe`

### Capture modes (hybrid)

| Mode | Setup | What you get |
|------|-------|--------------|
| **psutil** (default) | none | TCP peers, total bandwidth, torrent/game by client + ports |
| **Npcap deep** (optional) | install Npcap + run as admin | real **per-process** bandwidth + full **UDP** peer detection |

---

## Build the .exe (on Windows)

1. Copy this folder to a **Windows** PC with **Python 3.10+** installed.
2. Double-click **`build_exe.bat`** (or run it in a terminal).
3. When it finishes, launch:

   ```
   dist\ReaperSniff\ReaperSniff.exe
   ```

The `.bat` creates a virtualenv, installs everything, and runs PyInstaller using
`reapersniff.spec`.

### Enable deep mode (optional but recommended)

1. Install **Npcap**: https://npcap.com/#download — tick *"Install Npcap in WinPcap
   API-compatible Mode"*.
2. **Run ReaperSniff as Administrator.**
3. Tick **"Npcap deep mode"** before pressing **Start Capture**.

---

## Run from source (any OS, for development)

```bash
pip install -r requirements.txt
python run.py
```

> On Linux/macOS the app runs in psutil mode for development; deep Npcap mode and `.exe`
> packaging are Windows-only.

---

## Project structure

```
reapersniff/
├── core/
│   ├── models.py         # dataclasses (Connection, ProcessStat, Snapshot, ...)
│   ├── util.py           # IP helpers + P2P heuristic knowledge base
│   ├── sampler.py        # background sampling thread (psutil + optional sniffer)
│   ├── sniffer.py        # Npcap/scapy deep-capture engine
│   ├── p2p_detector.py   # torrent / game / generic-P2P scoring
│   ├── geoip.py          # free IP->country lookup (cached, batched)
│   └── health.py         # ping/latency monitor thread
└── ui/
    ├── theme.py          # cyan/white/purple dark QSS
    ├── main_window.py    # dashboard layout + wiring
    └── widgets/          # stat cards, graphs, p2p panel, tables, health panel
run.py                    # launcher
build_exe.bat             # one-click Windows build
reapersniff.spec          # PyInstaller config
smoke_test.py             # headless self-test
```

### Add a custom app icon
Drop an `icon.ico` into `reapersniff/assets/` before building — the spec picks it up
automatically.

---

## Responsible use
ReaperSniff is designed for monitoring traffic **you own and control** — understand your
home network, debug your connection, learn how protocols work, and watch background P2P
activity on your own machine.
