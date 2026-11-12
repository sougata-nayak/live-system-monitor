"""Segmented control for the sampling interval."""
from PySide6.QtCore import Signal

from config.settings import DEFAULT_SAMPLE_INTERVAL_MS, SAMPLE_INTERVAL_OPTIONS
from ui.components.segmented_control import SegmentedControl


class IntervalSelector(SegmentedControl):
    """Emits the chosen interval in milliseconds."""

    interval_selected = Signal(int)

    def __init__(self):
        super().__init__(SAMPLE_INTERVAL_OPTIONS, DEFAULT_SAMPLE_INTERVAL_MS)
        self.selected.connect(self.interval_selected.emit)
