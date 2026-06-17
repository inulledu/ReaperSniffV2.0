from __future__ import annotations

import threading
import time

import requests
from PySide6.QtCore import QThread, Signal

# Free, key-less IP geolocation (HTTP batch endpoint, up to 100 IPs/request).
ENDPOINT = "http://ip-api.com/batch?fields=status,country,countryCode,query"


class GeoThread(QThread):
    """Resolves public IPs -> country in the background, with caching."""

    resolved = Signal(dict)   # {ip: {"country": str, "cc": str}}

    def __init__(self):
        super().__init__()
        self._stop = False
        self.cache = {}
        self.pending = set()
        self.lock = threading.Lock()

    def enqueue(self, ips):
        with self.lock:
            for ip in ips:
                if ip not in self.cache:
                    self.pending.add(ip)

    def stop(self):
        self._stop = True

    def run(self):
        while not self._stop:
            time.sleep(1.2)
            with self.lock:
                batch = list(self.pending)[:100]
                self.pending.difference_update(batch)
            if not batch:
                continue
            try:
                r = requests.post(ENDPOINT, json=batch, timeout=8)
                data = r.json()
                out = {}
                for item in data:
                    ip = item.get("query")
                    if not ip:
                        continue
                    if item.get("status") == "success":
                        out[ip] = {
                            "country": item.get("country", "Unknown"),
                            "cc": item.get("countryCode", ""),
                        }
                    else:
                        out[ip] = {"country": "Unknown", "cc": ""}
                with self.lock:
                    self.cache.update(out)
                self.resolved.emit(out)
            except Exception:
                # Re-queue and back off on network/rate-limit errors.
                with self.lock:
                    self.pending.update(batch)
                time.sleep(4)
