"""Hover readout for a LineChart: a vertical guide line, a dot on each series and a
small label with the time and every series' value at the hovered sample."""
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt

from config.settings import HISTORY_SECONDS
from ui.theme import CARD, MUTED, TEXT, ui_font, with_alpha

SeriesData = Dict[str, Tuple[np.ndarray, np.ndarray]]  # name -> (xs, ys); x is seconds relative to now

_LABEL_GAP_PX = 10


def format_time_ago(x: float) -> str:
    return "now" if x > -0.5 else f"{-x:.0f}s ago"


class ChartHover:
    def __init__(self, plot: pg.PlotWidget, series: List[Tuple[str, str]],
                 format_value: Callable[[float], str]):
        self._plot = plot
        self._series = series
        self._format_value = format_value
        self.mouse_x: Optional[float] = None  # hovered x in plot coordinates, None when not hovering

        self._line = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen(with_alpha(TEXT, 90), width=1, style=Qt.DashLine))
        self._dots = pg.ScatterPlotItem(size=9, pen=pg.mkPen(CARD, width=2))
        self._label = pg.TextItem(anchor=(0, 0), border=pg.mkPen(with_alpha(TEXT, 30)),
                                  fill=pg.mkBrush(with_alpha(CARD, 235)))
        self._label.setFont(ui_font(13))
        self._label.textItem.document().setDocumentMargin(7)
        for item in (self._line, self._dots, self._label):
            item.setZValue(100)
            item.setVisible(False)
            plot.addItem(item, ignoreBounds=True)

    def update(self, data: SeriesData):
        """Redraw for the current frame (data scrolls, so this runs every frame while hovering)."""
        primary_xs = data[self._series[0][0]][0] if self._series[0][0] in data else None
        if self.mouse_x is None or primary_xs is None or primary_xs.size == 0:
            self._set_visible(False)
            return
        snap_index = int(np.argmin(np.abs(primary_xs - self.mouse_x)))
        x = float(primary_xs[snap_index])
        if abs(x - self.mouse_x) > 2.5:  # cursor is over a stretch with no data yet
            self._set_visible(False)
            return

        rows, dots = [], []
        for name, color in self._series:
            if name not in data:
                continue
            xs, ys = data[name]
            i = int(np.argmin(np.abs(xs - x)))
            rows.append(f"<span style='color:{color}'>●</span>&nbsp;{name}&nbsp;&nbsp;"
                        f"<b style='color:{TEXT}'>{self._format_value(float(ys[i]))}</b>")
            dots.append({"pos": (float(xs[i]), float(ys[i])), "brush": pg.mkBrush(color)})

        self._label.setHtml(f"<span style='color:{MUTED}'>{format_time_ago(x)}</span><br>"
                            + "<br>".join(rows))
        self._line.setPos(x)
        self._dots.setData(dots)

        # Keep the label inside the plot: right of the line, or left of it near the right edge.
        view_box = self._plot.plotItem.vb
        (_, _), (_, y_top) = view_box.viewRange()
        gap = view_box.viewPixelSize()[0] * _LABEL_GAP_PX
        on_left = x > -HISTORY_SECONDS * 0.4
        self._label.setAnchor((1, 0) if on_left else (0, 0))
        self._label.setPos(x - gap if on_left else x + gap, y_top)
        self._set_visible(True)

    def _set_visible(self, visible: bool):
        for item in (self._line, self._dots, self._label):
            item.setVisible(visible)
