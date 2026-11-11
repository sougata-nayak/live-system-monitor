"""Live System Monitor - PySide6 + psutil + pyqtgraph."""
import math
import platform
import sys
import time
from collections import deque

import numpy as np
import psutil
import pyqtgraph as pg
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontDatabase, QLinearGradient, QPainter, QPainterPath, QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

HISTORY = 60  # seconds of history shown

# ---- Design tokens ---------------------------------------------------------
BG = "#090B0F"
CARD = "#12151C"
TEXT = "#E8EAF0"
MUTED = "#8B93A5"
BLUE, VIOLET, AMBER = "#5EA8FF", "#B28CFF", "#FFB454"
TEAL, ORANGE = "#3DDBB0", "#FF9A5C"
YELLOW, PINK = "#FFD166", "#FF6B8A"
FONT_FAMILIES = ["Inter", "Segoe UI", "Roboto", "Arial"]  # non-macOS preference order
_FAMILY = None


def rgba(hex_color, alpha):
    c = QColor(hex_color)
    c.setAlpha(alpha)
    return c


# ---- Helpers ---------------------------------------------------------------
def split_bytes(n: float):
    """Return ('1.2', 'MB') for a byte count."""
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while abs(n) >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return (f"{n:.0f}" if n >= 100 or i == 0 else f"{n:.1f}"), units[i]


def fmt_bytes(n: float) -> str:
    v, u = split_bytes(n)
    return f"{v} {u}"


def ease_factor(dt: float, tau: float) -> float:
    """Frame-rate independent exponential smoothing factor."""
    return 1.0 - math.exp(-dt / tau)


def ui_font(size, weight=QFont.Normal):
    """macOS: the system font (San Francisco). Elsewhere: first installed family."""
    global _FAMILY
    if _FAMILY is None:
        system = QFontDatabase.systemFont(QFontDatabase.GeneralFont).family()
        if sys.platform == "darwin":
            _FAMILY = system
        else:
            installed = set(QFontDatabase.families())
            _FAMILY = next((f for f in FONT_FAMILIES if f in installed), system)
    f = QFont(_FAMILY)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


# ---- Axes ------------------------------------------------------------------
def style_axis(axis):
    axis.setPen(pg.mkPen(None))
    axis.setTextPen(pg.mkPen(MUTED))
    axis.setStyle(tickLength=0, tickTextOffset=8, tickFont=ui_font(13))


class UnitAxis(pg.AxisItem):
    """Left axis with human-friendly labels: '50%' or '256 KB/s'."""

    UNITS = ("B", "KB", "MB", "GB", "TB")

    def __init__(self, kind="percent"):
        super().__init__("left")
        self.kind = kind
        self.setWidth(78)  # fixed width so the plot doesn't jitter as labels change
        self.enableAutoSIPrefix(False)
        style_axis(self)

    def _unit(self, value):
        i = 0
        while abs(value) >= 1024 and i < len(self.UNITS) - 1:
            value /= 1024
            i += 1
        return 1024 ** i, self.UNITS[i]

    def tickValues(self, minVal, maxVal, size):
        if self.kind == "percent":
            return [(25, [0, 25, 50, 75, 100])]
        div, _ = self._unit(maxVal)
        want = max(2, int(size / 45))
        raw = (maxVal - minVal) / div / want
        mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
        step = next((m * mag for m in (1, 2, 5, 10) if m * mag >= raw), 10 * mag) * div
        n = int(maxVal // step)
        return [(step, [i * step for i in range(n + 1)])]

    def tickStrings(self, values, scale, spacing):
        if self.kind == "percent":
            return [f"{v:g}%" for v in values]
        div, unit = self._unit(max((abs(v) for v in values), default=0))
        step = spacing / div
        decimals = 0 if step >= 1 else (1 if step >= 0.1 else 2)
        return [f"{v / div:.{decimals}f} {unit}/s" for v in values]


class TimeAxis(pg.AxisItem):
    """Bottom axis: '60s ago · 30s · now'."""

    def __init__(self):
        super().__init__("bottom")
        style_axis(self)

    def boundingRect(self):
        # pyqtgraph drops labels that stick out of this rect; edge labels
        # ('60s ago', 'now') are centered on the plot's edges, so allow overhang.
        return super().boundingRect().adjusted(-40, 0, 40, 0)

    def tickValues(self, minVal, maxVal, size):
        return [(30, [-HISTORY, -HISTORY / 2, 0])]

    def tickStrings(self, values, scale, spacing):
        return [f"{int(-v)}s ago" if v <= -HISTORY else ("now" if v == 0 else f"{int(-v)}s")
                for v in values]


# ---- Cards -----------------------------------------------------------------
class Card(QFrame):
    """Rounded surface with a hairline border and an optional accent strip."""

    def __init__(self, accent=None):
        super().__init__()
        self.accent = accent
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setStyleSheet("QLabel { background: transparent; }")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 16, 16)
        p.fillPath(path, QColor(CARD))
        if self.accent:
            p.save()
            p.setClipPath(path)
            p.fillRect(QRectF(r.left(), r.top(), r.width(), 2), QColor(self.accent))
            p.restore()
        p.setPen(QPen(QColor(255, 255, 255, 16), 1))
        p.drawPath(path)


def label(text="", size=12, color=MUTED, weight=QFont.Normal):
    lb = QLabel(text)
    lb.setFont(ui_font(size, weight))
    lb.setStyleSheet(f"color:{color}; background:transparent;")
    return lb


class KpiTile(Card):
    def __init__(self, title, accent):
        super().__init__(accent)
        self.value = label("–", 34, TEXT, QFont.DemiBold)
        self.unit = label("", 15, MUTED, QFont.Medium)
        self.sub = label("", 12, MUTED)
        top = label(title.upper(), 11, MUTED, QFont.Medium)
        top.setFont(self._spaced(top.font()))
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self.value, 0, Qt.AlignBottom)
        row.addWidget(self.unit, 0, Qt.AlignBottom)
        row.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(4)
        lay.addWidget(top)
        lay.addLayout(row)
        lay.addWidget(self.sub)

    @staticmethod
    def _spaced(font):
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        return font

    def set(self, value, unit, sub):
        self.value.setText(value)
        self.unit.setText(unit)
        self.sub.setText(sub)


class Chart(Card):
    """A card with a scrolling line chart that eases toward new values.

    push() records a new sample; frame() is called every render tick and
    redraws with the time axis sliding smoothly and the newest point and
    Y-scale animating toward their targets.
    """

    VALUE_TAU = 0.25   # seconds: how quickly the newest point eases to a new sample
    SCALE_TAU = 0.6    # seconds: how quickly the auto Y-scale eases

    def __init__(self, title, series, y_range=None, fmt=None, min_top=1.0,
                 axis="percent"):
        super().__init__()
        self.fmt = fmt or (lambda v: f"{v:.0f}%")
        self.names = [n for n, _ in series]
        self.colors = dict(series)
        self.fixed_y = y_range is not None
        self.min_top = min_top
        self.y_top = y_range[1] if y_range else min_top

        self.pts = {n: deque() for n in self.names}   # committed (t, v)
        self.latest = {n: None for n in self.names}   # most recent (t, v)
        self.disp = {n: None for n in self.names}     # eased head value

        self.legend = label("", 14, MUTED)
        self.legend.setTextFormat(Qt.RichText)
        head = QHBoxLayout()
        head.addWidget(label(title, 17, TEXT, QFont.DemiBold))
        head.addStretch(1)
        head.addWidget(self.legend)

        self.plot = pg.PlotWidget(axisItems={"left": UnitAxis(axis), "bottom": TimeAxis()})
        self.plot.setBackground(None)
        self.plot.setMouseEnabled(False, False)
        self.plot.hideButtons()
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=False, y=True, alpha=0.08)
        # Slightly padded ranges so the edge tick labels ('0%', '100%', 'now') draw.
        self.plot.setXRange(-HISTORY - 1, 1, padding=0)
        self._set_y(self.y_top)
        self.plot.setMinimumHeight(130)
        self.plot.setStyleSheet("background: transparent; border: none;")
        self.plot.plotItem.layout.setContentsMargins(0, 4, 14, 0)

        self.curves = {}
        for i, (name, color) in enumerate(series):
            kw = {}
            if i == 0:  # soft gradient under the primary series
                grad = QLinearGradient(0, 0, 0, 1)
                grad.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
                grad.setColorAt(0, rgba(color, 90))
                grad.setColorAt(1, rgba(color, 0))
                kw = dict(fillLevel=0, brush=QBrush(grad))
            self.curves[name] = self.plot.plot(
                [], [], pen=pg.mkPen(color, width=2), **kw)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 14, 10)
        lay.setSpacing(8)
        lay.addLayout(head)
        lay.addWidget(self.plot, 1)
        self._update_legend({})

    def _set_y(self, top):
        self.plot.setYRange(-top * 0.05, top * 1.05, padding=0)

    def _update_legend(self, values):
        chips = []
        for n in self.names:
            val = f" <span style='color:{TEXT}'>{self.fmt(values[n])}</span>" if n in values else ""
            chips.append(f"<span style='color:{self.colors[n]}'>●</span>&nbsp;{n}{val}")
        self.legend.setText("&nbsp;&nbsp;&nbsp;".join(chips))

    def push(self, **values):
        now = time.monotonic()
        for name, v in values.items():
            prev = self.latest[name]
            if prev is not None:
                self.pts[name].append(prev)
            self.latest[name] = (now, v)
            if self.disp[name] is None:
                self.disp[name] = v
            pts = self.pts[name]
            while pts and pts[0][0] < now - HISTORY - 5:
                pts.popleft()
        self._update_legend(values)

    def frame(self, now, dt):
        k = ease_factor(dt, self.VALUE_TAU)
        peak = 0.0
        for name, curve in self.curves.items():
            latest = self.latest[name]
            if latest is None:
                continue
            self.disp[name] += (latest[1] - self.disp[name]) * k
            xs = [t - now for t, _ in self.pts[name]]
            ys = [v for _, v in self.pts[name]]
            xs.append(0.0)
            ys.append(self.disp[name])
            curve.setData(xs, ys)
            visible = [y for x, y in zip(xs, ys) if x >= -HISTORY - 1]
            if visible:
                peak = max(peak, max(visible))
        if not self.fixed_y:
            target = max(self.min_top, peak * 1.2)
            self.y_top += (target - self.y_top) * ease_factor(dt, self.SCALE_TAU)
            self._set_y(self.y_top)


class CoreBars(QWidget):
    """Two-column list of per-core load bars with eased fills."""

    def __init__(self, n):
        super().__init__()
        self.n = n
        self.target = np.zeros(n)
        self.disp = np.zeros(n)
        self.setMinimumHeight(max(60, ((n + 1) // 2) * 26))

    def step(self, dt):
        self.disp += (self.target - self.disp) * ease_factor(dt, 0.2)
        self.update()

    @staticmethod
    def color_for(v):
        return PINK if v > 75 else (AMBER if v > 50 else BLUE)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rows = (self.n + 1) // 2
        gap_x, row_h = 24, min(30, self.height() / max(rows, 1))
        col_w = (self.width() - gap_x) / 2
        y0 = (self.height() - rows * row_h) / 2
        for i in range(self.n):
            col, row = divmod(i, rows)
            x = col * (col_w + gap_x)
            y = y0 + row * row_h
            v = float(self.disp[i])
            p.setFont(ui_font(13))
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(x, y, 24, row_h), Qt.AlignVCenter | Qt.AlignLeft, str(i))
            bar = QRectF(x + 30, y + row_h / 2 - 4, col_w - 30 - 52, 8)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 15))
            p.drawRoundedRect(bar, 4, 4)
            fill = QRectF(bar.left(), bar.top(), max(bar.width() * v / 100, 0), bar.height())
            if fill.width() > 0:
                p.setBrush(QColor(self.color_for(v)))
                p.drawRoundedRect(fill, 4, 4)
            p.setPen(QColor(TEXT))
            p.drawText(QRectF(bar.right() + 6, y, 46, row_h),
                       Qt.AlignVCenter | Qt.AlignRight, f"{v:.0f}%")


class LiveBadge(QWidget):
    """Pill with a softly pulsing dot."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(66, 28)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(rgba(TEAL, 26))
        p.setPen(QPen(rgba(TEAL, 64), 1))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        pulse = 0.5 + 0.5 * math.sin(time.monotonic() * 3)
        c = QPointF(15, r.center().y())
        glow = QRadialGradient(c, 9)
        glow.setColorAt(0, rgba(TEAL, int(120 * pulse)))
        glow.setColorAt(1, rgba(TEAL, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(c, 9, 9)
        p.setBrush(QColor(TEAL))
        p.drawEllipse(c, 3.5, 3.5)
        p.setPen(QColor(TEAL))
        p.setFont(ui_font(12, QFont.Medium))
        p.drawText(QRectF(26, 0, 38, r.height()), Qt.AlignVCenter | Qt.AlignLeft, "Live")


class LogoMark(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(36, 36)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 36, 36)
        g.setColorAt(0, QColor(BLUE))
        g.setColorAt(1, QColor(VIOLET))
        p.setBrush(g)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(0, 0, 36, 36), 10, 10)
        pen = QPen(QColor("#0A0C12"), 2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        pts = [(9, 19), (14, 19), (17, 12), (21, 25), (24, 17), (28, 17)]
        p.drawPolyline([QPointF(x, y) for x, y in pts])


class Root(QWidget):
    """Window background with two soft color glows."""

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        for cx, cy, color, rad, a in ((0.15, -0.05, BLUE, 700, 30), (1.0, 0.0, VIOLET, 650, 24)):
            g = QRadialGradient(QPointF(self.width() * cx, self.height() * cy), rad)
            g.setColorAt(0, rgba(color, a))
            g.setColorAt(1, rgba(color, 0))
            p.fillRect(self.rect(), g)


# ---- Main window -----------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.resize(1360, 900)
        self.setMinimumSize(1040, 700)
        self.setFont(ui_font(13))
        self.root = Root()

        self.ncores = psutil.cpu_count(logical=True)
        phys = psutil.cpu_count(logical=False) or self.ncores
        osname = "macOS" if sys.platform == "darwin" else platform.system()

        # --- Header
        title = QVBoxLayout()
        title.setSpacing(2)
        title.addWidget(label("System Monitor", 18, TEXT, QFont.DemiBold))
        title.addWidget(label(f"{osname} · {self.ncores} logical cores · {phys} physical", 12))
        brand = QHBoxLayout()
        brand.setSpacing(14)
        brand.addWidget(LogoMark())
        brand.addLayout(title)

        self.badge = LiveBadge()
        seg = QFrame()
        seg.setStyleSheet(
            "QFrame#seg { background:#12151C; border:1px solid rgba(255,255,255,18);"
            " border-radius:11px; }"
            "QPushButton { color:#8B93A5; background:transparent; border:none;"
            " border-radius:8px; padding:6px 14px; font-size:12px; font-weight:500; }"
            "QPushButton:hover { color:#E8EAF0; }"
            "QPushButton:checked { color:#E8EAF0; background:#232837; }")
        seg.setObjectName("seg")
        seg_lay = QHBoxLayout(seg)
        seg_lay.setContentsMargins(3, 3, 3, 3)
        seg_lay.setSpacing(2)
        self.group = QButtonGroup(self)
        for i, (text, ms) in enumerate((("0.5 s", 500), ("1 s", 1000), ("2 s", 2000), ("5 s", 5000))):
            b = QPushButton(text)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setChecked(ms == 1000)
            b.clicked.connect(lambda _=False, ms=ms: self.timer.setInterval(ms))
            self.group.addButton(b, i)
            seg_lay.addWidget(b)
        header = QHBoxLayout()
        header.addLayout(brand)
        header.addStretch(1)
        header.addWidget(self.badge)
        header.addSpacing(8)
        header.addWidget(seg)

        # --- KPI tiles
        self.k_cpu = KpiTile("CPU", BLUE)
        self.k_mem = KpiTile("Memory", VIOLET)
        self.k_net = KpiTile("Network", TEAL)
        self.k_disk = KpiTile("Disk I/O", YELLOW)
        kpis = QHBoxLayout()
        kpis.setSpacing(16)
        for k in (self.k_cpu, self.k_mem, self.k_net, self.k_disk):
            kpis.addWidget(k, 1)

        # --- Charts
        rate = lambda v: fmt_bytes(v) + "/s"
        self.cpu_total = Chart("CPU usage", [("Total", BLUE)], (0, 100))
        self.mem = Chart("Memory", [("RAM", VIOLET), ("Swap", AMBER)], (0, 100))
        self.net = Chart("Network", [("Download", TEAL), ("Upload", ORANGE)],
                         fmt=rate, min_top=10 * 1024, axis="bytes")
        self.disk = Chart("Disk I/O", [("Read", YELLOW), ("Write", PINK)],
                          fmt=rate, min_top=100 * 1024, axis="bytes")

        self.cores = CoreBars(self.ncores)
        core_card = Card()
        cl = QVBoxLayout(core_card)
        cl.setContentsMargins(20, 16, 20, 12)
        ch = QHBoxLayout()
        ch.addWidget(label("CPU per core", 17, TEXT, QFont.DemiBold))
        ch.addStretch(1)
        ch.addWidget(label(f"{self.ncores} logical cores", 14))
        cl.addLayout(ch)
        cl.addWidget(self.cores, 1)

        sys_card = Card()
        sl = QVBoxLayout(sys_card)
        sl.setContentsMargins(20, 16, 20, 12)
        sl.addWidget(label("System", 14, TEXT, QFont.DemiBold))
        self.sys_vals = {}
        rows = QVBoxLayout()
        rows.setSpacing(0)
        names = ["RAM", "Swap", "Disk (/)", "Processes", "Uptime"]
        if hasattr(psutil, "sensors_battery") and psutil.sensors_battery():
            names.append("Battery")
        for n in names:
            row = QFrame()
            row.setStyleSheet("QFrame { border-bottom: 1px solid rgba(255,255,255,12); }"
                              "QLabel { border: none; }")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 9, 0, 9)
            rl.addWidget(label(n, 13))
            rl.addStretch(1)
            v = label("", 13, TEXT, QFont.Medium)
            self.sys_vals[n] = v
            rl.addWidget(v)
            rows.addWidget(row)
        rows.addStretch(1)
        sl.addLayout(rows, 1)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        for r in range(2):
            grid.setRowStretch(r, 1)
        grid.addWidget(self.cpu_total, 0, 0)
        grid.addWidget(self.mem, 0, 1)
        grid.addWidget(self.net, 0, 2)
        grid.addWidget(self.disk, 1, 0)
        grid.addWidget(core_card, 1, 1)
        grid.addWidget(sys_card, 1, 2)

        body = QVBoxLayout(self.root)
        body.setContentsMargins(32, 28, 32, 32)
        body.setSpacing(22)
        body.addLayout(header)
        body.addLayout(kpis)
        body.addLayout(grid, 1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.root)

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

        # Render loop: ~60 fps, independent of the sampling interval.
        self._last_frame = time.monotonic()
        self.render_timer = QTimer(self)
        self.render_timer.setTimerType(Qt.PreciseTimer)
        self.render_timer.setInterval(16)
        self.render_timer.timeout.connect(self.render)
        self.render_timer.start()

    def render(self):
        now = time.monotonic()
        dt = max(now - self._last_frame, 1e-3)
        self._last_frame = now
        for chart in (self.cpu_total, self.mem, self.net, self.disk):
            chart.frame(now, dt)
        self.cores.step(dt)
        self.badge.update()

    def tick(self):
        now = time.monotonic()
        dt = (now - self._last_t) if self._last_t else None
        self._last_t = now

        per_core = psutil.cpu_percent(percpu=True)
        total = sum(per_core) / len(per_core)
        self.cpu_total.push(Total=total)
        self.cores.target = np.array(per_core)
        try:
            freq = psutil.cpu_freq()
            freq_txt = f" · {freq.current / 1000:.1f} GHz" if freq and freq.current else ""
        except Exception:
            freq_txt = ""
        self.k_cpu.set(f"{total:.0f}", "%", f"{self.ncores} cores{freq_txt}")

        vm, sw = psutil.virtual_memory(), psutil.swap_memory()
        self.mem.push(RAM=vm.percent, Swap=sw.percent)
        used, used_u = split_bytes(vm.used)
        self.k_mem.set(used, used_u, f"of {fmt_bytes(vm.total)} · {vm.percent:.0f}% used")

        net = psutil.net_io_counters()
        disk = psutil.disk_io_counters()
        if dt:
            down = (net.bytes_recv - self._last_net.bytes_recv) / dt
            up = (net.bytes_sent - self._last_net.bytes_sent) / dt
            self.net.push(Download=down, Upload=up)
            v, u = split_bytes(down)
            self.k_net.set(v, u + "/s", f"↑ {fmt_bytes(up)}/s upload")
            if disk:
                rd = (disk.read_bytes - self._last_disk.read_bytes) / dt
                wr = (disk.write_bytes - self._last_disk.write_bytes) / dt
                self.disk.push(Read=rd, Write=wr)
                v, u = split_bytes(rd + wr)
                self.k_disk.set(v, u + "/s", f"Read {fmt_bytes(rd)}/s · Write {fmt_bytes(wr)}/s")
        self._last_net, self._last_disk = net, disk

        du = psutil.disk_usage("/")
        uptime = int(time.time() - psutil.boot_time())
        d, rem = divmod(uptime, 86400)
        h, rem = divmod(rem, 3600)
        vals = {
            "RAM": f"{fmt_bytes(vm.used)} / {fmt_bytes(vm.total)}",
            "Swap": f"{fmt_bytes(sw.used)} / {fmt_bytes(sw.total)}",
            "Disk (/)": f"{fmt_bytes(du.used)} / {fmt_bytes(du.total)} ({du.percent:.0f}%)",
            "Processes": str(len(psutil.pids())),
            "Uptime": f"{d}d {h}h {rem // 60}m",
        }
        if "Battery" in self.sys_vals:
            bat = psutil.sensors_battery()
            if bat:
                state = "charging" if bat.power_plugged else "on battery"
                vals["Battery"] = f"{bat.percent:.0f}% · {state}"
        for k, v in vals.items():
            self.sys_vals[k].setText(v)


def main():
    app = QApplication(sys.argv)
    app.setFont(ui_font(13))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
