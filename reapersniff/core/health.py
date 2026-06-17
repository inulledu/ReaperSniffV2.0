from __future__ import annotations

import platform
import re
import subprocess
import time

from PySide6.QtCore import QThread, Signal

from .models import HealthSample

_TIME_RE = re.compile(r"time[=<]\s*([\d.]+)\s*ms", re.IGNORECASE)


class PingThread(QThread):
    """Pings a target on an interval and emits latency samples (ms or None)."""

    sample = Signal(object)   # HealthSample

    def __init__(self, target: str = "8.8.8.8", interval: float = 1.0):
        super().__init__()
        self.target = target
        self.interval = interval
        self._stop = False

    def set_target(self, target: str):
        self.target = target.strip() or "8.8.8.8"

    def stop(self):
        self._stop = True

    def run(self):
        is_win = platform.system().lower() == "windows"
        while not self._stop:
            lat = self._ping_once(is_win)
            self.sample.emit(HealthSample(time.time(), lat, self.target))
            waited = 0.0
            while waited < self.interval and not self._stop:
                time.sleep(0.1)
                waited += 0.1

    def _ping_once(self, is_win: bool):
        try:
            if is_win:
                cmd = ["ping", "-n", "1", "-w", "1500", self.target]
                # Prevent a console window from flashing on every ping (Windows).
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            else:
                cmd = ["ping", "-c", "1", "-W", "2", self.target]
                flags = 0
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=4,
                creationflags=flags,
            )
            if out.returncode != 0:
                return None
            m = _TIME_RE.search(out.stdout)
            return float(m.group(1)) if m else None
        except Exception:
            return None
