"""Polls the metrics sampler on a timer and publishes each Snapshot."""
from PySide6.QtCore import QObject, QTimer, Signal

from monitors.sampler import MetricsSampler


class SamplingService(QObject):
    """Owns the sampling timer. The interval can be changed while running."""

    snapshot_ready = Signal(object)  # monitors.models.Snapshot

    def __init__(self, sampler: MetricsSampler, interval_ms: int, parent=None):
        super().__init__(parent)
        self._sampler = sampler
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.sample_now)

    def start(self):
        """Start the timer and publish a first snapshot immediately."""
        self.timer.start()
        self.sample_now()

    def set_interval(self, milliseconds: int):
        self.timer.setInterval(milliseconds)

    def sample_now(self):
        self.snapshot_ready.emit(self._sampler.sample())
