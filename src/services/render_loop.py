"""Frame clock that drives the animations, independent of the sampling interval."""
import time

from PySide6.QtCore import QObject, Qt, QTimer, Signal


class RenderLoop(QObject):
    """Emits ``frame(now, dt)`` on every tick (``now`` is time.monotonic())."""

    frame = Signal(float, float)

    def __init__(self, interval_ms: int, parent=None):
        super().__init__(parent)
        self._last_frame_time = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.tick)

    def start(self):
        self._last_frame_time = time.monotonic()
        self.timer.start()

    def tick(self):
        now = time.monotonic()
        dt = max(now - self._last_frame_time, 1e-3)
        self._last_frame_time = now
        self.frame.emit(now, dt)
