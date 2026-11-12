"""Bottom-right card. Switches between 'System' (label/value rows) and 'Top processes'."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from config.settings import TOP_PROCESS_COUNT
from ui.components.card import Card
from ui.components.labels import ElidedLabel, make_label
from ui.components.segmented_control import SegmentedControl
from ui.theme import MUTED, TEXT, ui_font
from utils.formatting import format_bytes

_ROW_NAMES = ("RAM", "Swap", "Disk (/)", "Processes", "Uptime")
_BATTERY_ROW_NAME = "Battery"
_ROW_STYLE = ("QFrame { border-bottom: 1px solid rgba(255,255,255,12); }"
              "QLabel { border: none; }")

VIEW_SYSTEM = "system"
VIEW_PROCESSES = "processes"
_TITLES = {VIEW_SYSTEM: "System", VIEW_PROCESSES: "Top processes"}

# Process table column widths (px): CPU and memory are right-aligned fixed columns.
_CPU_COLUMN_WIDTH = 64
_MEMORY_COLUMN_WIDTH = 76


def _row(*widgets_and_stretch, top_bottom_margin=9, style=_ROW_STYLE):
    """A horizontal row with a hairline under it. ``None`` entries become stretch."""
    row = QFrame()
    row.setStyleSheet(style)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, top_bottom_margin, 0, top_bottom_margin)
    for item in widgets_and_stretch:
        if item is None:
            layout.addStretch(1)
        else:
            layout.addWidget(item)
    return row


class SystemPanel(Card):
    view_changed = Signal(str)  # VIEW_SYSTEM or VIEW_PROCESSES

    def __init__(self, show_battery):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)

        self.title_label = make_label(_TITLES[VIEW_SYSTEM], 14, TEXT, QFont.DemiBold)
        self.view_selector = SegmentedControl(
            [("Overview", VIEW_SYSTEM), ("Processes", VIEW_PROCESSES)], VIEW_SYSTEM, size="compact")
        self.view_selector.selected.connect(self.show_view)
        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.view_selector)
        layout.addLayout(header)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_system_page(show_battery))
        self.pages.addWidget(self._build_processes_page())
        layout.addWidget(self.pages, 1)
        self.current_view = VIEW_SYSTEM

    # ---- System page -------------------------------------------------------

    def _build_system_page(self, show_battery):
        page = QWidget()
        rows = QVBoxLayout(page)
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(0)
        self.value_labels = {}
        names = list(_ROW_NAMES)
        if show_battery:
            names.append(_BATTERY_ROW_NAME)
        for name in names:
            value_label = make_label("", 13, TEXT, QFont.Medium)
            self.value_labels[name] = value_label
            rows.addWidget(_row(make_label(name, 13), None, value_label))
        rows.addStretch(1)
        return page

    def set_values(self, ram, swap, disk, processes, uptime, battery=None):
        """Update the rows. ``battery`` is ignored when None or when the row is hidden."""
        self.value_labels["RAM"].setText(ram)
        self.value_labels["Swap"].setText(swap)
        self.value_labels["Disk (/)"].setText(disk)
        self.value_labels["Processes"].setText(processes)
        self.value_labels["Uptime"].setText(uptime)
        if battery is not None and _BATTERY_ROW_NAME in self.value_labels:
            self.value_labels[_BATTERY_ROW_NAME].setText(battery)

    # ---- Processes page ----------------------------------------------------

    def _build_processes_page(self):
        page = QWidget()
        rows = QVBoxLayout(page)
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(0)

        def column(text, width, color=MUTED, size=11, weight=QFont.Medium):
            label = make_label(text, size, color, weight)
            label.setFixedWidth(width)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return label

        heading_name = make_label("PROCESS", 11, MUTED, QFont.Medium)
        rows.addWidget(_row(heading_name, None, column("CPU", _CPU_COLUMN_WIDTH),
                            column("MEMORY", _MEMORY_COLUMN_WIDTH), top_bottom_margin=6))

        self.process_rows = []
        for _ in range(TOP_PROCESS_COUNT):
            name = ElidedLabel(ui_font(13), MUTED)
            cpu = column("", _CPU_COLUMN_WIDTH, TEXT, 13)
            memory = column("", _MEMORY_COLUMN_WIDTH, TEXT, 13)
            self.process_rows.append((name, cpu, memory))
            rows.addWidget(_row(name, cpu, memory, top_bottom_margin=8))
        self.process_rows[0][0].setText("Measuring…")
        rows.addStretch(1)
        return page

    def set_processes(self, processes):
        """``processes``: List[ProcessInfo], highest CPU first."""
        for index, (name, cpu, memory) in enumerate(self.process_rows):
            if index < len(processes):
                process = processes[index]
                name.setText(process.name)
                cpu.setText(f"{process.cpu_percent:.1f}%")
                memory.setText(format_bytes(process.memory_bytes))
            else:
                name.setText("")
                cpu.setText("")
                memory.setText("")

    # ---- Switching ---------------------------------------------------------

    def show_view(self, view):
        self.current_view = view
        self.title_label.setText(_TITLES[view])
        self.pages.setCurrentIndex(0 if view == VIEW_SYSTEM else 1)
        self.view_changed.emit(view)
