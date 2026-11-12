"""Scrolling line chart card."""
import time
from collections import deque

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont, QLinearGradient
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from config.settings import (
    HISTORY_RETENTION_MARGIN_SECONDS,
    HISTORY_SECONDS,
    SCALE_EASE_SECONDS,
    VALUE_EASE_SECONDS,
)
from ui.charts.axes import AxisKind, TimeAxis, UnitAxis
from ui.components.card import Card
from ui.components.labels import make_label
from ui.theme import MUTED, TEXT, with_alpha
from utils.animation import ease_factor
from utils.formatting import format_percent


class LineChart(Card):
    """A card with a scrolling line chart that eases toward new values.

    push_sample() records a new sample; advance_frame() is called every render
    tick and redraws with the time axis sliding smoothly and the newest point
    and Y-scale animating toward their targets.

    ``series`` is a list of (name, color). Samples are pushed as {name: value}.
    """

    def __init__(self, title, series, y_range=None, format_value=None, min_y_top=1.0,
                 axis_kind=AxisKind.PERCENT):
        super().__init__()
        self.format_value = format_value or format_percent
        self.series_names = [name for name, _ in series]
        self.series_colors = dict(series)
        self.has_fixed_y_range = y_range is not None
        self.min_y_top = min_y_top
        self.y_top = y_range[1] if y_range else min_y_top

        self.committed_points = {name: deque() for name in self.series_names}  # (t, v)
        self.latest_sample = {name: None for name in self.series_names}        # (t, v)
        self.displayed_value = {name: None for name in self.series_names}      # eased head
        # committed_points as arrays, rebuilt once per sample instead of once per frame.
        self._point_times = {name: np.empty(0) for name in self.series_names}
        self._point_values = {name: np.empty(0) for name in self.series_names}

        self.legend_label = make_label("", 14, MUTED)
        self.legend_label.setTextFormat(Qt.RichText)
        header = QHBoxLayout()
        header.addWidget(make_label(title, 17, TEXT, QFont.DemiBold))
        header.addStretch(1)
        header.addWidget(self.legend_label)

        self.plot = pg.PlotWidget(axisItems={"left": UnitAxis(axis_kind), "bottom": TimeAxis()})
        self.plot.setBackground(None)
        self.plot.setMouseEnabled(False, False)
        self.plot.hideButtons()
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=False, y=True, alpha=0.08)
        # Slightly padded ranges so the edge tick labels ('0%', '100%', 'now') draw.
        self.plot.setXRange(-HISTORY_SECONDS - 1, 1, padding=0)
        self._set_y_range(self.y_top)
        self.plot.setMinimumHeight(130)
        self.plot.setStyleSheet("background: transparent; border: none;")
        self.plot.plotItem.layout.setContentsMargins(0, 4, 14, 0)

        self.curves = {}
        for index, (name, color) in enumerate(series):
            fill_options = {}
            if index == 0:  # soft gradient under the primary series
                gradient = QLinearGradient(0, 0, 0, 1)
                gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
                gradient.setColorAt(0, with_alpha(color, 90))
                gradient.setColorAt(1, with_alpha(color, 0))
                fill_options = dict(fillLevel=0, brush=QBrush(gradient))
            self.curves[name] = self.plot.plot(
                [], [], pen=pg.mkPen(color, width=2), **fill_options)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 14, 10)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addWidget(self.plot, 1)
        self._update_legend({})

    def _set_y_range(self, top):
        self.plot.setYRange(-top * 0.05, top * 1.05, padding=0)

    def _update_legend(self, values):
        chips = []
        for name in self.series_names:
            value_html = (f" <span style='color:{TEXT}'>{self.format_value(values[name])}</span>"
                          if name in values else "")
            chips.append(f"<span style='color:{self.series_colors[name]}'>●</span>&nbsp;{name}{value_html}")
        self.legend_label.setText("&nbsp;&nbsp;&nbsp;".join(chips))

    def push_sample(self, values):
        """Record a new sample. ``values`` maps series name to value."""
        now = time.monotonic()
        for name, value in values.items():
            previous = self.latest_sample[name]
            if previous is not None:
                self.committed_points[name].append(previous)
            self.latest_sample[name] = (now, value)
            if self.displayed_value[name] is None:
                self.displayed_value[name] = value
            points = self.committed_points[name]
            while points and points[0][0] < now - HISTORY_SECONDS - HISTORY_RETENTION_MARGIN_SECONDS:
                points.popleft()
            self._point_times[name] = np.fromiter((t for t, _ in points), float, len(points))
            self._point_values[name] = np.fromiter((v for _, v in points), float, len(points))
        self._update_legend(values)

    def advance_frame(self, now, dt):
        ease = ease_factor(dt, VALUE_EASE_SECONDS)
        peak = 0.0
        for name, curve in self.curves.items():
            latest = self.latest_sample[name]
            if latest is None:
                continue
            self.displayed_value[name] += (latest[1] - self.displayed_value[name]) * ease
            xs = np.append(self._point_times[name] - now, 0.0)
            ys = np.append(self._point_values[name], self.displayed_value[name])
            curve.setData(xs, ys)
            visible = ys[xs >= -HISTORY_SECONDS - 1]
            if visible.size:
                peak = max(peak, float(visible.max()))
        if not self.has_fixed_y_range:
            target = max(self.min_y_top, peak * 1.2)
            self.y_top += (target - self.y_top) * ease_factor(dt, SCALE_EASE_SECONDS)
            self._set_y_range(self.y_top)
