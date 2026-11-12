"""Process reading against a fake psutil."""
from collections import namedtuple

from monitors import processes as processes_module
from monitors.models import ProcessInfo
from monitors.processes import iter_processes, top_processes

Mem = namedtuple("Mem", "rss")


class FakeProcess:
    def __init__(self, pid, name, cpu, rss):
        self.info = {"pid": pid, "name": name, "cpu_percent": cpu,
                     "memory_info": None if rss is None else Mem(rss)}


class FakePsutil:
    def __init__(self, rows):
        self.rows = rows

    def process_iter(self, attrs, ad_value=None):
        return (FakeProcess(*row) for row in self.rows)


def test_iter_processes_skips_unreadable_and_names_by_pid(monkeypatch):
    monkeypatch.setattr(processes_module, "psutil", FakePsutil([
        (1, "a", 1.0, 10),
        (2, "root-owned", None, None),  # access denied
        (3, "", 5.0, 1),
    ]))
    assert list(iter_processes()) == [ProcessInfo(1, "a", 1.0, 10), ProcessInfo(3, "3", 5.0, 1)]


def test_top_processes_sorted_by_cpu_then_memory_and_limited():
    processes = [ProcessInfo(1, "idle", 0.0, 10), ProcessInfo(2, "busy", 80.0, 100),
                 ProcessInfo(3, "medium", 20.0, 50), ProcessInfo(4, "medium-big", 20.0, 500)]
    assert [p.name for p in top_processes(processes, 3)] == ["busy", "medium-big", "medium"]
