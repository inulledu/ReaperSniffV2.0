import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from reapersniff.ui.main_window import MainWindow
from reapersniff.ui.theme import build_stylesheet
from reapersniff.core.sampler import SamplerThread
from reapersniff.core.health import PingThread

app = QApplication.instance() or QApplication([])
app.setStyleSheet(build_stylesheet())
w = MainWindow()
w.resize(1280, 820)
w.show()

# --- live sampler against real container connections (psutil mode) ---
results = {}
def on_snap(s):
    results['snap'] = s
    w._on_snapshot(s)
def on_ping(p):
    results['ping'] = p
    w._on_ping(p)

samp = SamplerThread(interval=1.0, use_npcap=False)
samp.snapshot.connect(on_snap)
samp.error.connect(lambda e: results.setdefault('err', e))
samp.start()
ping = PingThread(target="8.8.8.8", interval=1.0)
ping.sample.connect(on_ping)
ping.start()

loop = QEventLoop()
QTimer.singleShot(4000, loop.quit)
loop.exec()

samp.stop(); ping.stop()
samp.wait(2000); ping.wait(2000)

snap = results.get('snap')
print("live snapshot:", "OK" if snap else "NONE",
      "| conns=", len(snap.connections) if snap else 0,
      "| procs=", len(snap.processes) if snap else 0,
      "| findings=", len(snap.findings) if snap else 0,
      "| mode=", snap.mode if snap else "-")
print("ping sample:", results.get('ping'))
if 'err' in results: print("sampler note:", results['err'])

w.grab().save("/app/preview.png")
print("saved /app/preview.png")
