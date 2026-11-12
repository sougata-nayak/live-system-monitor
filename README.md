# System Monitor

A live desktop dashboard for CPU, memory, network, and disk activity. System Monitor samples your machine with [psutil](https://github.com/giampaolo/psutil) and displays the results in an animated dark interface built with [PySide6](https://doc.qt.io/qtforpython/) and [pyqtgraph](https://www.pyqtgraph.org/).

![System Monitor dashboard showing live charts, per-core CPU load, and system information](docs/screenshot.png)

## Features

- **Live metrics:** CPU usage, RAM and swap, network upload and download, and disk read and write rates, with 60 seconds of chart history.
- **Detailed inspection:** hover over a chart to see values at a sample; check individual logical CPU cores in the per-core panel.
- **System overview:** see memory and root filesystem usage, process count, uptime, and battery status when available.
- **Top processes:** switch the bottom-right panel to **Processes** to see up to six accessible processes ranked by CPU usage, with their memory usage.
- **Adjustable refresh:** choose 0.5, 1, 2, or 5 seconds. The default is 1 second; drawing runs separately for smooth animation.

## Getting started

### Requirements

- macOS with a graphical desktop. The project has been developed on macOS; other platforms have not been verified.
- Python 3 and `pip`. The existing development environment uses Python 3.14.
- Git, if cloning the repository.

The application runs from source; there is no packaged installer. Dependencies are pinned in [`requirements.txt`](requirements.txt).

### Installation and launch

In Terminal:

```bash
git clone https://github.com/sougata-nayak/live-system-monitor.git
cd live-system-monitor
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python src/main.py
```

Run the last command from the project root whenever you want to start the app. Close the window to quit.

## Using the dashboard

1. Select a refresh interval in the top-right corner. Charts show up to the most recent 60 seconds, so history fills in as the app runs.
2. Hover over a chart to inspect the nearest recorded sample.
3. Use **Overview** and **Processes** in the bottom-right card to switch between system information and the process list. The first process reading needs a short priming period; processes that cannot be read with your account's permissions are omitted.

Network and disk rates are derived from changes in system counters, so they appear after a subsequent sample. Disk capacity refers to the root filesystem (`/`). Drawing pauses while the window is hidden or minimized, but sampling continues.

## Development

Install the development dependencies in the same virtual environment, then run the tests and linter:

```bash
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m pytest
venv/bin/ruff check .
```

The tests cover formatting, metric sampling, process selection, and an offscreen Qt window smoke test. The smoke test reads real system information, so it needs an environment where those readings are available.

### Project structure

```text
src/
├── main.py             Application entry point
├── config/             Sampling, animation, and window settings
├── monitors/           psutil readers and data models (independent of Qt)
├── services/           Sampling, process scanning, and animation timers
├── ui/                 Window, charts, panels, components, and theme
└── utils/              Formatting and animation helpers
tests/                  Unit and offscreen application tests
docs/                   README screenshot
```

Metrics flow from `monitors` through the services to the window and its widgets. Process scans are split into short slices on the UI thread; the render loop is independent of the sampling interval. To adjust refresh options or window dimensions, see [`src/config/settings.py`](src/config/settings.py); visual tokens live in [`src/ui/theme.py`](src/ui/theme.py).

## Troubleshooting

- **Qt cannot find the `cocoa` platform plugin:** on macOS, check whether the virtual environment has acquired the hidden file flag, particularly in an iCloud-synced folder. From the project root, `chflags -R nohidden venv` has resolved this for this project. You can also recreate the virtual environment in a non-synced directory.
- **Some process entries are missing:** macOS may restrict access to processes owned by other users or the system. The list includes only processes the current account can read.
- **Charts start empty:** wait for samples to accumulate; network and disk rates require two counter readings.

## Contributing

Issues and pull requests are welcome. For a change, create a branch, keep the scope focused, and run the tests and linter above before opening a pull request. Include reproduction steps for bug reports and screenshots for visual changes.

## License

Distributed under the [MIT License](LICENSE). Copyright © 2026 Sougata Nayak.
