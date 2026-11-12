# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

A desktop live system monitor for macOS (PySide6 + psutil + pyqtgraph + numpy).

```
python -m venv venv
venv/bin/pip install -r requirements-dev.txt   # app deps + pytest + ruff + nuitka
venv/bin/python src/main.py                    # run (must use the venv's python, not system python)
venv/bin/pytest                                # all tests
venv/bin/pytest tests/test_sampler.py::test_rates_never_negative   # a single test
venv/bin/ruff check .                          # lint; --fix sorts imports
venv/bin/python scripts/build_app.py           # -> dist/System Monitor.app
```

All dependency versions are pinned. `pyproject.toml` holds the ruff and pytest config (pytest puts `src/` on the path).

Tests: `tests/test_sampler.py` and `tests/test_processes.py` monkeypatch the module's `psutil` with a fake. `tests/test_app_smoke.py` builds the real `MainWindow` with `QT_QPA_PLATFORM=offscreen` and drives it by calling `sampling_service.sample_now()` / `render_loop.tick()` directly instead of waiting on timers; hover is tested by setting `chart.hover.mouse_x`.

## Gotchas

- **The project lives in `~/Desktop`, which is iCloud-synced** (a File Provider folder). Synced files get extra macOS metadata (`com.apple.provenance`, file flags). Consequences:
  - Qt "Could not find the Qt platform plugin cocoa": the venv folder got the `hidden` flag and Qt's QDir skips hidden files. Fix: `chflags -R nohidden venv`. (The venv was renamed from `.venv` to `venv` while chasing this. iCloud is the likely, not proven, source of the flag.)
  - `codesign` refuses to sign an app built inside the project. `scripts/build_app.py` therefore compiles in `~/Library/Caches/system-monitor-build` and copies only the finished `.app` into `dist/`.
- **Imports are rooted at `src/`** (`from ui.theme import ...`), so run `src/main.py` directly; do not use `python -m src.main`.
- **Keep every frame under ~16 ms.** The 60 fps render loop runs on the UI thread, so slow work there causes visible stutter. **Python threads don't fix this:** a worker still competes for the GIL, and PySide releases/re-takes it on every Qt call. Reading all processes (~30 ms) on a thread pushed the slowest 1% of frames from 18 ms to 39 ms. `ProcessService` instead consumes the `iter_processes()` generator in 3 ms slices on a timer, which measured flat (p99 ~18 ms). Measure frame gaps (connect to `render_loop.frame`) when adding periodic work.
- **The app costs ~70% of one core while visible**, almost all of it pyqtgraph redrawing four charts at 60 fps. This predates the features; a lower frame rate (larger `RENDER_INTERVAL_MS`) or skipping redraws when nothing moves would be the lever.
- **psutil per-process `cpu_percent` is relative to the previous call on the same `Process` object.** `process_iter` caches those objects between scans; the first scan is all zeros, so `ProcessService` primes once and rescans 0.5 s later. About a third of processes (root/other users) are unreadable without admin rights and are skipped.
- **Build:** `pyside6-deploy` was tried first and dropped: it ignored its Nuitka version pin and passed an empty `--include-qt-plugins=` that newer Nuitka rejects. The build script calls Nuitka 4.1.1 directly (it warns that Python 3.14 support is "experimental"; the built app works). pyqtgraph imports `PySide6.QtOpenGL` via `importlib`, invisible to Nuitka, so it is included explicitly. Without that the app compiles fine and crashes at launch, so **always launch the built app** (`"dist/System Monitor.app/Contents/MacOS/System Monitor"` shows tracebacks in the terminal). A build takes about a minute (one early build took 24 minutes for unclear reasons).
- Hover can't be fully tested with synthetic mouse events on cocoa: the real cursor's position also arrives and wins. Tests set `chart.hover.mouse_x` directly.
- Pixel layout details matter (e.g. the header spacing must equal `SECTION_SPACING` = 22); see the history below.

## Architecture

Data flows one way: **monitors → services → MainWindow → panels/charts**, with a separate animation clock.

- `monitors/` is Qt-free. `MetricsSampler.sample()` returns a `Snapshot` (`models.py`); network/disk rates come from counter deltas between calls, so they are `None` on the first sample, and are clamped at 0. Readers that can fail go through `_safe_call` and fall back to `None` or the last good value. `monitors/processes.py` has `iter_processes()` (a generator of `ProcessInfo`) and `top_processes()`.
- `services/sampling_service.py`: QTimer (interval from the header's selector) emitting `snapshot_ready(Snapshot)`. `services/process_service.py`: time-sliced scan (see Gotchas) emitting `processes_ready(list)`; `request()` is a no-op while a scan is in progress. `MainWindow` requests processes on each snapshot only while the Processes view is showing and the window is visible.
- `services/render_loop.py`: ~60 fps timer emitting `frame(now, dt)`. Charts, core bars and the live badge ease toward their targets each frame (`*_EASE_SECONDS` in `config/settings.py`). `MainWindow` stops it while the window is hidden/minimized; sampling keeps running.
- `ui/charts/line_chart.py`: history in `committed_points` (deques) plus numpy mirrors rebuilt once per sample, so the per-frame path is vectorized. `ui/charts/hover.py` (`ChartHover`) draws the guide line, dots and readout; it snaps to the nearest sample and is redrawn every frame while hovered, since the data scrolls.
- `ui/main_window.py` is the only place that wires everything together.
- `ui/components/segmented_control.py` is the shared pill switch (`IntervalSelector` is a thin subclass; the bottom-right card uses a compact one). `ui/components/logo_mark.py` (`paint_logo`) draws the logo for the header, the Dock icon (`logo_icon()` in `main.py`) and the `.icns` (`scripts/make_icon.py`), so there are no image assets to keep in sync.
- `ui/theme.py`: colors and the Apple system font (`.AppleSystemUIFont`). Tunables live in `config/settings.py`.

## How the project got here

The approach throughout: get something working first, then change one thing at a time, and verify each change by running the real app (and, once it existed, a harness) rather than assuming.

1. **Prototype** (`cb5fd3a`). One file, `system_monitor.py`: psutil polled on a QTimer, pyqtgraph line charts, plain widgets.
2. **The Qt "cocoa" plugin error.** First misdiagnosed as a PySide6 6.12.0 bug, which led to pinning 6.11.3. The real cause was macOS's `hidden` flag on `.venv`, which made Qt skip its own plugins. `chflags nohidden` fixed it, but the flag kept coming back. It was later traced to the folder being iCloud-synced (see Gotchas). Lesson: confirm a root cause before pinning or rewriting.
3. **Smoothness.** Sampling and drawing were decoupled: a separate ~60 fps render loop eases the newest point, the Y-scale and the core bars, instead of the charts jumping once a second. Axis labels became human-readable (`UnitAxis`, `TimeAxis`).
4. **Design** (`3fc2ca2`, `cf6f8fd`). The UI was redesigned as an HTML mock-up with Claude Design, then ported by hand to Qt: cards, KPI tiles, Live badge, segmented interval selector, dark palette. Then the Apple system font, and chart text 20% larger.
5. **Refactor into `src/`** (`4ab52ef`). The rule was that no functionality or behaviour may change. It was verified with an equivalence harness that runs the old single file and the new package under identical fake psutil data and a frozen clock, then compares screenshots byte for byte, internal state, and psutil call counts, with and without a battery. It caught one real regression: header spacing that the old nested layout had inherited.
6. **Hygiene and robustness** (`ef0ac96`, `c9500fb`). Renamed the venv, pushed to GitHub, then: negative rates clamped, failing psutil readers isolated, animation paused while hidden, numpy per-frame path, cached fonts, pinned versions, pytest + ruff, MIT license, README screenshot. The harness was re-run; the only difference from the original was the intended negative-rate fix, which was confirmed by applying the same fix to a copy of the original and getting identical output.
7. **Features.** Chart hover readouts; a Top processes view; an app icon drawn from the logo code; a `.app` build via Nuitka. Measurement drove the processes design. Reading costs ~30 ms, so it first went on a background thread. Frame timing on the real app showed that still stuttered because of the GIL, so it became a time-sliced scan on the UI thread. The build hit the iCloud codesign problem, which is also the likely explanation for the old `hidden` flag mystery. Launching the built app (not just building it) caught the missing `QtOpenGL` module.
