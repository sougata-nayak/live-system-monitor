"""Plain data types produced by the monitors. No psutil, no Qt."""
from dataclasses import dataclass
from typing import List, NamedTuple, Optional


class SystemInfo(NamedTuple):
    logical_cores: int
    physical_cores: int
    os_name: str


class ByteRates(NamedTuple):
    """Two byte-per-second rates, e.g. (download, upload) or (read, write)."""
    first: float
    second: float


class BatteryReading(NamedTuple):
    percent: float
    plugged_in: bool


@dataclass(frozen=True)
class Snapshot:
    """One sampling of the machine. Rates are None when they can't be computed."""
    per_core_percent: List[float]
    cpu_percent: float
    cpu_freq_mhz: Optional[float]
    memory_used: int
    memory_total: int
    memory_percent: float
    swap_used: int
    swap_total: int
    swap_percent: float
    network_rates: Optional[ByteRates]      # (download, upload)
    disk_io_rates: Optional[ByteRates]      # (read, write)
    disk_used: int
    disk_total: int
    disk_percent: float
    process_count: int
    uptime_seconds: int
    battery: Optional[BatteryReading]
