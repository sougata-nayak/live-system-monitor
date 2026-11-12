"""MetricsSampler against a fake psutil, so results are deterministic."""
from collections import namedtuple

import pytest

from monitors import sampler as sampler_module
from monitors.sampler import MetricsSampler

Net = namedtuple("Net", "bytes_sent bytes_recv")
Disk = namedtuple("Disk", "read_bytes write_bytes")
Mem = namedtuple("Mem", "total used percent")
Usage = namedtuple("Usage", "total used percent")
Freq = namedtuple("Freq", "current min max")
Battery = namedtuple("Battery", "percent secsleft power_plugged")


class FakePsutil:
    def __init__(self):
        self.net = Net(1000, 5000)
        self.disk = Disk(10_000, 20_000)
        self.fail = set()

    def _maybe_fail(self, name):
        if name in self.fail:
            raise OSError(name)

    def cpu_percent(self, percpu=False):
        return [10.0, 30.0]

    def cpu_freq(self):
        self._maybe_fail("cpu_freq")
        return Freq(3200.0, 0, 0)

    def virtual_memory(self):
        return Mem(16 * 1024 ** 3, 8 * 1024 ** 3, 50.0)

    def swap_memory(self):
        return Mem(4 * 1024 ** 3, 1024 ** 3, 25.0)

    def net_io_counters(self):
        return self.net

    def disk_io_counters(self):
        return self.disk

    def disk_usage(self, path):
        self._maybe_fail("disk_usage")
        return Usage(500, 100, 20.0)

    def pids(self):
        self._maybe_fail("pids")
        return list(range(42))

    def boot_time(self):
        return 0.0

    def sensors_battery(self):
        self._maybe_fail("battery")
        return Battery(80.0, 3600, True)


@pytest.fixture
def env(monkeypatch):
    fake = FakePsutil()
    clock = [100.0]
    monkeypatch.setattr(sampler_module, "psutil", fake)
    monkeypatch.setattr(sampler_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(sampler_module.time, "time", lambda: 1000.0)
    return fake, clock


def test_first_sample_has_no_rates(env):
    s = MetricsSampler(read_battery=True).sample()
    assert s.network_rates is None and s.disk_io_rates is None
    assert s.cpu_percent == 20.0
    assert s.cpu_freq_mhz == 3200.0
    assert s.process_count == 42
    assert s.uptime_seconds == 1000
    assert s.battery.percent == 80.0 and s.battery.plugged_in


def test_rates_are_per_second(env):
    fake, clock = env
    sampler = MetricsSampler(read_battery=False)
    sampler.sample()
    clock[0] += 2.0
    fake.net = Net(1000 + 400, 5000 + 2000)
    fake.disk = Disk(10_000 + 600, 20_000 + 200)
    s = sampler.sample()
    assert s.network_rates == (1000.0, 200.0)  # (download, upload)
    assert s.disk_io_rates == (300.0, 100.0)    # (read, write)
    assert s.battery is None


def test_rates_never_negative(env):
    fake, clock = env
    sampler = MetricsSampler(read_battery=False)
    sampler.sample()
    clock[0] += 1.0
    fake.net = Net(0, 0)  # counters dropped (e.g. an interface went away)
    fake.disk = Disk(0, 0)
    s = sampler.sample()
    assert s.network_rates == (0.0, 0.0)
    assert s.disk_io_rates == (0.0, 0.0)


def test_disk_counters_missing_at_start(env):
    fake, clock = env
    fake.disk = None
    sampler = MetricsSampler(read_battery=False)
    sampler.sample()
    clock[0] += 1.0
    fake.disk = Disk(500, 500)  # appear later: must not crash
    assert sampler.sample().disk_io_rates is None
    clock[0] += 1.0
    fake.disk = Disk(1500, 700)
    assert sampler.sample().disk_io_rates == (1000.0, 200.0)


def test_failing_readers_fall_back(env):
    fake, clock = env
    sampler = MetricsSampler(read_battery=True)
    first = sampler.sample()
    fake.fail = {"cpu_freq", "disk_usage", "pids", "battery"}
    clock[0] += 1.0
    s = sampler.sample()
    assert s.cpu_freq_mhz is None
    assert s.battery is None
    # Last good values are kept.
    assert (s.disk_used, s.disk_total, s.disk_percent) == (
        first.disk_used, first.disk_total, first.disk_percent)
    assert s.process_count == first.process_count
