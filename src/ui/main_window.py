"""Main window: lays out the panels and connects the services to them."""
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from config.settings import (
    APP_NAME, DEFAULT_SAMPLE_INTERVAL_MS, RENDER_INTERVAL_MS, SECTION_SPACING, WINDOW_MIN_SIZE,
    WINDOW_SIZE,
)
from monitors.models import Snapshot
from monitors.sampler import MetricsSampler
from monitors.system_info import battery_available, read_system_info
from services.render_loop import RenderLoop
from services.sampling_service import SamplingService
from ui.charts.axes import AxisKind
from ui.charts.line_chart import LineChart
from ui.components.backdrop import Backdrop
from ui.panels.core_panel import CorePanel
from ui.panels.header import Header
from ui.panels.kpi_tile import KpiTile
from ui.panels.system_panel import SystemPanel
from ui.theme import AMBER, BLUE, ORANGE, PINK, TEAL, VIOLET, YELLOW, ui_font
from utils.formatting import format_byte_rate, format_bytes, format_uptime, split_bytes


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)
        self.setFont(ui_font(13))
        self.backdrop = Backdrop()

        info = read_system_info()
        self._logical_cores = info.logical_cores
        show_battery = battery_available()

        self.header = Header(
            f"{info.os_name} · {info.logical_cores} logical cores · {info.physical_cores} physical")

        self.cpu_tile = KpiTile("CPU", BLUE)
        self.memory_tile = KpiTile("Memory", VIOLET)
        self.network_tile = KpiTile("Network", TEAL)
        self.disk_tile = KpiTile("Disk I/O", YELLOW)
        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(16)
        for tile in (self.cpu_tile, self.memory_tile, self.network_tile, self.disk_tile):
            tiles_row.addWidget(tile, 1)

        self.cpu_chart = LineChart("CPU usage", [("Total", BLUE)], y_range=(0, 100))
        self.memory_chart = LineChart("Memory", [("RAM", VIOLET), ("Swap", AMBER)],
                                      y_range=(0, 100))
        self.network_chart = LineChart("Network", [("Download", TEAL), ("Upload", ORANGE)],
                                       format_value=format_byte_rate, min_y_top=10 * 1024,
                                       axis_kind=AxisKind.BYTES)
        self.disk_chart = LineChart("Disk I/O", [("Read", YELLOW), ("Write", PINK)],
                                    format_value=format_byte_rate, min_y_top=100 * 1024,
                                    axis_kind=AxisKind.BYTES)
        self.core_panel = CorePanel(info.logical_cores)
        self.system_panel = SystemPanel(show_battery)
        self.charts = (self.cpu_chart, self.memory_chart, self.network_chart, self.disk_chart)

        grid = QGridLayout()
        grid.setSpacing(16)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        for row in range(2):
            grid.setRowStretch(row, 1)
        grid.addWidget(self.cpu_chart, 0, 0)
        grid.addWidget(self.memory_chart, 0, 1)
        grid.addWidget(self.network_chart, 0, 2)
        grid.addWidget(self.disk_chart, 1, 0)
        grid.addWidget(self.core_panel, 1, 1)
        grid.addWidget(self.system_panel, 1, 2)

        body = QVBoxLayout(self.backdrop)
        body.setContentsMargins(32, 28, 32, 32)
        body.setSpacing(SECTION_SPACING)
        body.addWidget(self.header)
        body.addLayout(tiles_row)
        body.addLayout(grid, 1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.backdrop)

        # Services: sampling publishes Snapshots, the render loop publishes frames.
        self.sampling_service = SamplingService(
            MetricsSampler(read_battery=show_battery), DEFAULT_SAMPLE_INTERVAL_MS, parent=self)
        self.sampling_service.snapshot_ready.connect(self._show_snapshot)
        self.header.interval_selector.interval_selected.connect(self.sampling_service.set_interval)
        self.sampling_service.start()

        self.render_loop = RenderLoop(RENDER_INTERVAL_MS, parent=self)
        self.render_loop.frame.connect(self._advance_frame)
        self.render_loop.start()

    def _advance_frame(self, now, dt):
        for chart in self.charts:
            chart.advance_frame(now, dt)
        self.core_panel.advance_frame(dt)
        self.header.refresh_live_badge()

    def _show_snapshot(self, snapshot: Snapshot):
        self._show_cpu(snapshot)
        self._show_memory(snapshot)
        self._show_network(snapshot)
        self._show_disk_io(snapshot)
        self._show_system(snapshot)

    def _show_cpu(self, s: Snapshot):
        self.cpu_chart.push_sample({"Total": s.cpu_percent})
        self.core_panel.set_target_loads(s.per_core_percent)
        freq_text = f" · {s.cpu_freq_mhz / 1000:.1f} GHz" if s.cpu_freq_mhz else ""
        self.cpu_tile.set_values(
            f"{s.cpu_percent:.0f}", "%", f"{self._logical_cores} cores{freq_text}")

    def _show_memory(self, s: Snapshot):
        self.memory_chart.push_sample({"RAM": s.memory_percent, "Swap": s.swap_percent})
        used, used_unit = split_bytes(s.memory_used)
        self.memory_tile.set_values(
            used, used_unit, f"of {format_bytes(s.memory_total)} · {s.memory_percent:.0f}% used")

    def _show_network(self, s: Snapshot):
        if s.network_rates is None:
            return
        download, upload = s.network_rates
        self.network_chart.push_sample({"Download": download, "Upload": upload})
        value, unit = split_bytes(download)
        self.network_tile.set_values(value, unit + "/s", f"↑ {format_bytes(upload)}/s upload")

    def _show_disk_io(self, s: Snapshot):
        if s.disk_io_rates is None:
            return
        read, write = s.disk_io_rates
        self.disk_chart.push_sample({"Read": read, "Write": write})
        value, unit = split_bytes(read + write)
        self.disk_tile.set_values(
            value, unit + "/s", f"Read {format_bytes(read)}/s · Write {format_bytes(write)}/s")

    def _show_system(self, s: Snapshot):
        battery_text = None
        if s.battery is not None:
            state = "charging" if s.battery.plugged_in else "on battery"
            battery_text = f"{s.battery.percent:.0f}% · {state}"
        self.system_panel.set_values(
            ram=f"{format_bytes(s.memory_used)} / {format_bytes(s.memory_total)}",
            swap=f"{format_bytes(s.swap_used)} / {format_bytes(s.swap_total)}",
            disk=f"{format_bytes(s.disk_used)} / {format_bytes(s.disk_total)} ({s.disk_percent:.0f}%)",
            processes=str(s.process_count),
            uptime=format_uptime(s.uptime_seconds),
            battery=battery_text)
