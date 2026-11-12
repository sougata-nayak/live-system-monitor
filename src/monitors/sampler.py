"""Live metric sampling. Wraps psutil; knows nothing about Qt or display formatting."""
import time
from typing import Callable, Optional, TypeVar

import psutil

from monitors.models import BatteryReading, ByteRates, Snapshot

T = TypeVar("T")


def _safe_call(read: Callable[[], T], fallback: T) -> T:
    """Call a psutil reader; return ``fallback`` if it fails, so one bad reading
    doesn't drop the whole sample."""
    try:
        return read()
    except Exception:
        return fallback


def _rate(current: float, previous: float, elapsed: float) -> float:
    """Per-second rate, never negative (counters can drop, e.g. when an interface goes away)."""
    return max(0.0, (current - previous) / elapsed)


class MetricsSampler:
    """Takes Snapshots. Keeps the previous counters so it can derive per-second rates."""

    def __init__(self, read_battery: bool):
        self._read_battery = read_battery
        self._last_net = _safe_call(psutil.net_io_counters, None)
        self._last_disk = _safe_call(psutil.disk_io_counters, None)
        self._last_time: Optional[float] = None
        # Last good values, reused if a reading fails.
        self._last_disk_usage = None
        self._last_process_count = 0
        psutil.cpu_percent(percpu=True)  # prime

    def sample(self) -> Snapshot:
        now = time.monotonic()
        elapsed = (now - self._last_time) if self._last_time else None
        self._last_time = now

        per_core = psutil.cpu_percent(percpu=True)
        cpu_percent = sum(per_core) / len(per_core)
        freq = _safe_call(psutil.cpu_freq, None)
        freq_mhz = freq.current if freq and freq.current else None

        memory, swap = psutil.virtual_memory(), psutil.swap_memory()

        net = _safe_call(psutil.net_io_counters, None)
        disk = _safe_call(psutil.disk_io_counters, None)
        network_rates = None
        disk_io_rates = None
        if elapsed:
            if net and self._last_net:
                network_rates = ByteRates(
                    _rate(net.bytes_recv, self._last_net.bytes_recv, elapsed),
                    _rate(net.bytes_sent, self._last_net.bytes_sent, elapsed))
            if disk and self._last_disk:
                disk_io_rates = ByteRates(
                    _rate(disk.read_bytes, self._last_disk.read_bytes, elapsed),
                    _rate(disk.write_bytes, self._last_disk.write_bytes, elapsed))
        self._last_net, self._last_disk = net, disk

        disk_usage = _safe_call(lambda: psutil.disk_usage("/"), self._last_disk_usage)
        self._last_disk_usage = disk_usage
        process_count = _safe_call(lambda: len(psutil.pids()), self._last_process_count)
        self._last_process_count = process_count
        uptime = int(time.time() - psutil.boot_time())

        battery = None
        if self._read_battery:
            reading = _safe_call(psutil.sensors_battery, None)
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
            disk_used=disk_usage.used if disk_usage else 0,
            disk_total=disk_usage.total if disk_usage else 0,
            disk_percent=disk_usage.percent if disk_usage else 0.0,
            process_count=process_count,
            uptime_seconds=uptime,
            battery=battery,
        )
