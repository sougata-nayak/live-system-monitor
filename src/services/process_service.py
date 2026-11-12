"""Scans processes in small time slices on the UI thread and publishes the top ones.

Why not a background thread: reading all processes takes ~30 ms of Python and psutil
work, and a worker thread still competes with the UI thread for Python's GIL (PySide
releases and re-takes it on every Qt call). Measured with a thread, the slowest 1% of
frames went from 18 ms to 39 ms. Slicing the scan keeps every frame within budget.
"""
import time
from typing import Iterator, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from monitors.models import ProcessInfo
from monitors.processes import iter_processes, top_processes

SLICE_BUDGET_SECONDS = 0.003   # work per slice; a frame is ~16 ms
SLICE_INTERVAL_MS = 8          # gap between slices so frames get drawn in between
PRIME_DELAY_MS = 500           # first scan only primes CPU counters; real scan follows


class ProcessService(QObject):
    processes_ready = Signal(object)  # List[monitors.models.ProcessInfo]

    def __init__(self, limit: int, parent=None):
        super().__init__(parent)
        self._limit = limit
        self._primed = False
        self._busy = False   # True from request() until the result is published
        self._scan: Optional[Iterator[ProcessInfo]] = None
        self._collected: List[ProcessInfo] = []
        self._slice_timer = QTimer(self)
        self._slice_timer.setInterval(SLICE_INTERVAL_MS)
        self._slice_timer.timeout.connect(self._scan_slice)

    def request(self):
        """Start a scan unless one is already in progress."""
        if self._busy:
            return
        self._busy = True
        self._start_scan()

    def _start_scan(self):
        self._scan = iter_processes()
        self._collected = []
        self._slice_timer.start()

    def _scan_slice(self):
        deadline = time.perf_counter() + SLICE_BUDGET_SECONDS
        try:
            while time.perf_counter() < deadline:
                self._collected.append(next(self._scan))
            return  # out of time; continue on the next slice
        except StopIteration:
            pass
        except Exception:  # psutil failure mid-scan: publish what we have
            pass
        self._slice_timer.stop()
        self._scan = None
        if not self._primed:
            self._primed = True
            QTimer.singleShot(PRIME_DELAY_MS, self, self._start_scan)
            return
        self._busy = False
        self.processes_ready.emit(top_processes(self._collected, self._limit))

    def shutdown(self):
        self._slice_timer.stop()
