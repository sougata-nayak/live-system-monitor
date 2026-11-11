"""Live metric sampling. Wraps psutil; knows nothing about Qt or display formatting."""
import time
from typing import Optional

import psutil

from monitors.models import BatteryReading, ByteRates, Snapshot


class MetricsSampler:
    """Takes Snapshots. Keeps the previous counters so it can derive per-second rates."""

    def __init__(self, read_battery: bool):
        self._read_battery = read_battery
        self._last_net = psutil.net_io_counters()
        self._last_disk = psutil.disk_io_counters()
        self._last_time: Optional[float] = None
        psutil.cpu_percent(percpu=True)  # prime

    def sample(self) -> Snapshot:
        now = time.monotonic()
        elapsed = (now - self._last_time) if self._last_time else None
        self._last_time = now

        per_core = psutil.cpu_percent(percpu=True)
        cpu_percent = sum(per_core) / len(per_core)
        try:
            freq = psutil.cpu_freq()
            freq_mhz = freq.current if freq and freq.current else None
        except Exception:
            freq_mhz = None

        memory, swap = psutil.virtual_memory(), psutil.swap_memory()

        net = psutil.net_io_counters()
        disk = psutil.disk_io_counters()
        network_rates = None
        disk_io_rates = None
        if elapsed:
            network_rates = ByteRates(
                (net.bytes_recv - self._last_net.bytes_recv) / elapsed,
                (net.bytes_sent - self._last_net.bytes_sent) / elapsed)
            if disk:
                disk_io_rates = ByteRates(
                    (disk.read_bytes - self._last_disk.read_bytes) / elapsed,
                    (disk.write_bytes - self._last_disk.write_bytes) / elapsed)
        self._last_net, self._last_disk = net, disk

        disk_usage = psutil.disk_usage("/")
        uptime = int(time.time() - psutil.boot_time())

        battery = None
        if self._read_battery:
            reading = psutil.sensors_battery()
            if reading:
                battery = BatteryReading(reading.percent, reading.power_plugged)

        return Snapshot(
            per_core_percent=per_core,
            cpu_percent=cpu_percent,
            cpu_freq_mhz=freq_mhz,
            memory_used=memory.used,
            memory_total=memory.total,
            memory_percent=memory.percent,
            swap_used=swap.used,
            swap_total=swap.total,
            swap_percent=swap.percent,
            network_rates=network_rates,
            disk_io_rates=disk_io_rates,
            disk_used=disk_usage.used,
            disk_total=disk_usage.total,
            disk_percent=disk_usage.percent,
            process_count=len(psutil.pids()),
            uptime_seconds=uptime,
            battery=battery,
        )
