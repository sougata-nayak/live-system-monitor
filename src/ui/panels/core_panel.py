"""'CPU per core' card."""
import numpy as np
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ui.charts.core_bars import CoreBars
from ui.components.card import Card
from ui.components.labels import make_label
from ui.theme import TEXT


class CorePanel(Card):
    def __init__(self, core_count):
        super().__init__()
        self.bars = CoreBars(core_count)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        header = QHBoxLayout()
        header.addWidget(make_label("CPU per core", 17, TEXT, QFont.DemiBold))
        header.addStretch(1)
        header.addWidget(make_label(f"{core_count} logical cores", 14))
        layout.addLayout(header)
        layout.addWidget(self.bars, 1)

    def set_target_loads(self, per_core_percent):
        self.bars.target_loads = np.array(per_core_percent)

    def advance_frame(self, dt):
        self.bars.advance_frame(dt)
