"""'System' card: a list of label/value rows."""
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from ui.components.card import Card
from ui.components.labels import make_label
from ui.theme import TEXT

_ROW_NAMES = ("RAM", "Swap", "Disk (/)", "Processes", "Uptime")
_BATTERY_ROW_NAME = "Battery"


class SystemPanel(Card):
    def __init__(self, show_battery):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.addWidget(make_label("System", 14, TEXT, QFont.DemiBold))

        self.value_labels = {}
        rows = QVBoxLayout()
        rows.setSpacing(0)
        names = list(_ROW_NAMES)
        if show_battery:
            names.append(_BATTERY_ROW_NAME)
        for name in names:
            row = QFrame()
            row.setStyleSheet("QFrame { border-bottom: 1px solid rgba(255,255,255,12); }"
                              "QLabel { border: none; }")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 9, 0, 9)
            row_layout.addWidget(make_label(name, 13))
            row_layout.addStretch(1)
            value_label = make_label("", 13, TEXT, QFont.Medium)
            self.value_labels[name] = value_label
            row_layout.addWidget(value_label)
            rows.addWidget(row)
        rows.addStretch(1)
        layout.addLayout(rows, 1)

    def set_values(self, ram, swap, disk, processes, uptime, battery=None):
        """Update the rows. ``battery`` is ignored when None or when the row is hidden."""
        self.value_labels["RAM"].setText(ram)
        self.value_labels["Swap"].setText(swap)
        self.value_labels["Disk (/)"].setText(disk)
        self.value_labels["Processes"].setText(processes)
        self.value_labels["Uptime"].setText(uptime)
        if battery is not None and _BATTERY_ROW_NAME in self.value_labels:
            self.value_labels[_BATTERY_ROW_NAME].setText(battery)
