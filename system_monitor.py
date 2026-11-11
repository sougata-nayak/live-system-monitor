"""Live System Monitor - PySide6 + psutil + pyqtgraph."""
import sys
from collections import deque

import numpy as np
import psutil
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QVBoxLayout, QWidget,
)

HISTORY = 60  # seconds of history shown
COLORS = {
    "cpu": "#4cc9f0", "mem": "#f72585", "swap": "#ffb703",
    "down": "#06d6a0", "up": "#ef476f", "read": "#8ecae6", "write": "#fb8500",
    "temp": "#e76f51",
}

pg.setConfigOptions(antialias=True, background="#14171c", foreground="#c9d1d9")


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


class Chart(QWidget):
    """A titled line chart with one or more named series and a live readout."""

    def __init__(self, title, series, y_range=None, unit="", fmt=None, fill=True):
        super().__init__()
        self.unit, self.fmt = unit, fmt
        self.x = np.arange(-HISTORY + 1, 1)
        self.data = {name: deque([0.0] * HISTORY, maxlen=HISTORY) for name, _ in series}

        self.title = QLabel(title)
        self.title.setStyleSheet("font-weight:600; font-size:13px; color:#e6edf3;")
        self.readout = QLabel("")
        self.readout.setAlignment(Qt.AlignRight)
        self.readout.setStyleSheet("font-size:12px; color:#8b949e;")
        head = QHBoxLayout()
        head.addWidget(self.title)
        head.addWidget(self.readout, 1)

        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(False, False)
        self.plot.hideButtons()
        self.plot.showGrid(x=False, y=True, alpha=0.15)
        self.plot.setXRange(-HISTORY + 1, 0, padding=0)
        self.plot.getAxis("bottom").setLabel("seconds ago")
        if y_range:
            self.plot.setYRange(*y_range, padding=0)
        else:
            self.plot.enableAutoRange("y", True)
            self.plot.setLimits(yMin=0)
        if len(series) > 1:
            self.plot.addLegend(offset=(10, 5))

        self.curves = {}
        for name, color in series:
            kw = {}
            if fill:
                kw = dict(fillLevel=0, brush=pg.mkBrush(color + "40"))
            self.curves[name] = self.plot.plot(
                self.x, list(self.data[name]), pen=pg.mkPen(color, width=2),
                name=name if len(series) > 1 else None, **kw)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.addLayout(head)
        lay.addWidget(self.plot)
        self.setStyleSheet("Chart { background:#1b1f27; border-radius:8px; }")
        self.setAttribute(Qt.WA_StyledBackground, True)

    def push(self, **values):
        for name, v in values.items():
            self.data[name].append(v)
            self.curves[name].setData(self.x, list(self.data[name]))
        parts = []
        for name, v in values.items():
            txt = self.fmt(v) if self.fmt else f"{v:.1f}{self.unit}"
            parts.append(f"{name}: {txt}" if len(values) > 1 else txt)
        self.readout.setText("   ".join(parts))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live System Monitor")
        self.resize(1200, 800)
        self.setStyleSheet("QMainWindow, QWidget#root { background:#0d1117; }"
                           "QLabel { color:#c9d1d9; }"
                           "QComboBox { color:#c9d1d9; background:#1b1f27; padding:2px 6px; }")

        self.cpu_total = Chart("CPU Usage", [("total", COLORS["cpu"])], (0, 100), "%")
        self.mem = Chart("Memory", [("RAM", COLORS["mem"]), ("Swap", COLORS["swap"])],
                         (0, 100), "%", fill=False)
        self.net = Chart("Network", [("down", COLORS["down"]), ("up", COLORS["up"])],
                         fmt=lambda v: fmt_bytes(v) + "/s", fill=False)
        self.disk = Chart("Disk I/O", [("read", COLORS["read"]), ("write", COLORS["write"])],
                          fmt=lambda v: fmt_bytes(v) + "/s", fill=False)

        # Per-core bars
        self.ncores = psutil.cpu_count(logical=True)
        self.core_plot = pg.PlotWidget()
        self.core_plot.setMouseEnabled(False, False)
        self.core_plot.hideButtons()
        self.core_plot.setYRange(0, 100, padding=0)
        self.core_plot.setXRange(-0.6, self.ncores - 0.4, padding=0)
        self.core_plot.showGrid(y=True, alpha=0.15)
        self.core_plot.getAxis("bottom").setTicks(
            [[(i, str(i)) for i in range(self.ncores)]])
        self.core_bars = pg.BarGraphItem(
            x=np.arange(self.ncores), height=np.zeros(self.ncores), width=0.7,
            brush=COLORS["cpu"])
        self.core_plot.addItem(self.core_bars)
        core_box = QWidget()
        core_box.setObjectName("core")
        core_box.setStyleSheet("#core { background:#1b1f27; border-radius:8px; }")
        core_box.setAttribute(Qt.WA_StyledBackground, True)
        cl = QVBoxLayout(core_box)
        cl.setContentsMargins(10, 8, 10, 8)
        t = QLabel("CPU Per Core")
        t.setStyleSheet("font-weight:600; font-size:13px; color:#e6edf3;")
        cl.addWidget(t)
        cl.addWidget(self.core_plot)

        # Header: summary + refresh interval
        self.summary = QLabel()
        self.summary.setStyleSheet("font-size:12px; color:#8b949e;")
        self.interval = QComboBox()
        for label, ms in (("0.5 s", 500), ("1 s", 1000), ("2 s", 2000), ("5 s", 5000)):
            self.interval.addItem(label, ms)
        self.interval.setCurrentIndex(1)
        self.interval.currentIndexChanged.connect(
            lambda: self.timer.setInterval(self.interval.currentData()))
        head = QHBoxLayout()
        head.addWidget(self.summary, 1)
        head.addWidget(QLabel("Refresh:"))
        head.addWidget(self.interval)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self.cpu_total, 0, 0)
        grid.addWidget(core_box, 0, 1)
        grid.addWidget(self.mem, 1, 0)
        grid.addWidget(self.net, 1, 1)
        grid.addWidget(self.disk, 2, 0)
        extras = self._build_extras()
        grid.addWidget(extras, 2, 1)

        root = QWidget()
        root.setObjectName("root")
        lay = QVBoxLayout(root)
        lay.addLayout(head)
        lay.addLayout(grid, 1)
        self.setCentralWidget(root)

        # Baselines for rate calculations
        self._last_net = psutil.net_io_counters()
        self._last_disk = psutil.disk_io_counters()
        self._last_t = None
        psutil.cpu_percent(percpu=True)  # prime

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.tick()

    def _build_extras(self):
        """Battery / uptime / disk usage panel."""
        box = QWidget()
        box.setObjectName("extras")
        box.setStyleSheet("#extras { background:#1b1f27; border-radius:8px; }")
        box.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 8)
        t = QLabel("System")
        t.setStyleSheet("font-weight:600; font-size:13px; color:#e6edf3;")
        self.info = QLabel()
        self.info.setStyleSheet("font-size:13px; line-height:150%;")
        self.info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay.addWidget(t)
        lay.addWidget(self.info, 1)
        return box

    def tick(self):
        import time
        now = time.monotonic()
        dt = (now - self._last_t) if self._last_t else None
        self._last_t = now

        per_core = psutil.cpu_percent(percpu=True)
        total = sum(per_core) / len(per_core)
        self.cpu_total.push(total=total)
        self.core_bars.setOpts(height=np.array(per_core))

        vm, sw = psutil.virtual_memory(), psutil.swap_memory()
        self.mem.push(RAM=vm.percent, Swap=sw.percent)

        net = psutil.net_io_counters()
        disk = psutil.disk_io_counters()
        if dt:
            self.net.push(down=(net.bytes_recv - self._last_net.bytes_recv) / dt,
                          up=(net.bytes_sent - self._last_net.bytes_sent) / dt)
            if disk:
                self.disk.push(read=(disk.read_bytes - self._last_disk.read_bytes) / dt,
                               write=(disk.write_bytes - self._last_disk.write_bytes) / dt)
        self._last_net, self._last_disk = net, disk

        du = psutil.disk_usage("/")
        uptime = int(time.time() - psutil.boot_time())
        d, rem = divmod(uptime, 86400)
        h, rem = divmod(rem, 3600)
        lines = [
            f"<b>RAM:</b> {fmt_bytes(vm.used)} / {fmt_bytes(vm.total)}",
            f"<b>Swap:</b> {fmt_bytes(sw.used)} / {fmt_bytes(sw.total)}",
            f"<b>Disk (/):</b> {fmt_bytes(du.used)} / {fmt_bytes(du.total)} ({du.percent:.0f}%)",
            f"<b>Processes:</b> {len(psutil.pids())}",
            f"<b>Uptime:</b> {d}d {h}h {rem // 60}m",
        ]
        bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        if bat:
            state = "charging" if bat.power_plugged else "on battery"
            lines.append(f"<b>Battery:</b> {bat.percent:.0f}% ({state})")
        self.info.setText("<br>".join(lines))
        self.summary.setText(
            f"{self.ncores} logical cores · {psutil.cpu_count(logical=False)} physical")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
