# System Monitor

A live system monitor (CPU, memory, network, disk) with animated charts.
Built with Python, PySide6, psutil and pyqtgraph.

## Run

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/main.py
```

## Where to find things

```
src/
├── main.py               Entry point (creates the app and shows the window)
├── config/
│   └── settings.py       Behaviour settings: refresh intervals, history length, window size
├── monitors/             Reads the machine (psutil) and returns plain data. No Qt.
│   ├── sampler.py        Takes a Snapshot of CPU, memory, network, disk, battery
│   ├── system_info.py    Core count, OS name, battery present?
│   └── models.py         The data types (Snapshot, ByteRates, ...)
├── services/             Runtime plumbing
│   ├── sampling_service.py   Timer that samples and publishes Snapshots
│   └── render_loop.py        ~60 fps clock that drives the animations
├── utils/                Pure helpers
│   ├── formatting.py     "1.2 MB/s", "3d 7h 21m", ...
│   └── animation.py      Easing math
└── ui/                   Everything on screen
    ├── main_window.py    Lays out the panels, connects services to widgets
    ├── theme.py          Colors and fonts
    ├── components/       Small building blocks: card, labels, logo, live badge, interval selector
    ├── charts/           Line chart, per-core bars, axis labels
    └── panels/           Dashboard sections: header, KPI tile, CPU per core, system info
```

Common changes:

| I want to...                         | Look in                         |
|--------------------------------------|---------------------------------|
| Change refresh options / window size | `src/config/settings.py`        |
| Change colors or the font            | `src/ui/theme.py`               |
| Change how a number is displayed     | `src/utils/formatting.py`       |
| Add or change a measured metric      | `src/monitors/` then `main_window.py` |
| Change a chart's look or axes        | `src/ui/charts/`                |
| Change a card, tile or the header    | `src/ui/panels/`, `src/ui/components/` |
| Change animation speed               | `src/config/settings.py` (easing constants) |
