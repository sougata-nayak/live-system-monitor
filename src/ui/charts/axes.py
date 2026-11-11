"""pyqtgraph axes with human-friendly labels."""
import math
from enum import Enum

import pyqtgraph as pg

from config.settings import HISTORY_SECONDS
from ui.theme import MUTED, ui_font


class AxisKind(Enum):
    PERCENT = "percent"
    BYTES = "bytes"


def style_axis(axis):
    axis.setPen(pg.mkPen(None))
    axis.setTextPen(pg.mkPen(MUTED))
    axis.setStyle(tickLength=0, tickTextOffset=8, tickFont=ui_font(13))


class UnitAxis(pg.AxisItem):
    """Left axis with human-friendly labels: '50%' or '256 KB/s'."""

    UNITS = ("B", "KB", "MB", "GB", "TB")

    def __init__(self, kind=AxisKind.PERCENT):
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
        if self.kind is AxisKind.PERCENT:
            return [(25, [0, 25, 50, 75, 100])]
        div, _ = self._unit(maxVal)
        want = max(2, int(size / 45))
        raw = (maxVal - minVal) / div / want
        mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
        step = next((m * mag for m in (1, 2, 5, 10) if m * mag >= raw), 10 * mag) * div
        n = int(maxVal // step)
        return [(step, [i * step for i in range(n + 1)])]

    def tickStrings(self, values, scale, spacing):
        if self.kind is AxisKind.PERCENT:
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
        return [(30, [-HISTORY_SECONDS, -HISTORY_SECONDS / 2, 0])]

    def tickStrings(self, values, scale, spacing):
        return [f"{int(-v)}s ago" if v <= -HISTORY_SECONDS else ("now" if v == 0 else f"{int(-v)}s")
                for v in values]
