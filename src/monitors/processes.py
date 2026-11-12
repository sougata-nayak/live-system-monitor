"""Top processes by CPU.

Reading every process takes ~30 ms in total, too long for one go on the UI thread,
so this exposes a generator that the caller can consume a few processes at a time
(see services/process_service.py).

psutil reports a process's CPU % relative to the previous call on the same Process
object (``process_iter`` caches them between scans). The very first scan is therefore
all zeros and only serves to prime the counters.
"""
from typing import Iterable, Iterator, List

import psutil

from monitors.models import ProcessInfo

_ATTRS = ["pid", "name", "cpu_percent", "memory_info"]


def iter_processes() -> Iterator[ProcessInfo]:
    """Yield every process we are allowed to read. Processes owned by other users or
    the system come back with None (access denied) and are skipped."""
    for process in psutil.process_iter(_ATTRS, ad_value=None):
        info = process.info
        if info["cpu_percent"] is None or info["memory_info"] is None:
            continue
        yield ProcessInfo(info["pid"], info["name"] or str(info["pid"]),
                          info["cpu_percent"], info["memory_info"].rss)


def top_processes(processes: Iterable[ProcessInfo], limit: int) -> List[ProcessInfo]:
    """Highest CPU first; memory breaks ties."""
    return sorted(processes, key=lambda p: (p.cpu_percent, p.memory_bytes), reverse=True)[:limit]
