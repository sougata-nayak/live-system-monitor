# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

A desktop live system monitor (PySide6 + psutil + pyqtgraph + numpy). No build step.

```
python -m venv venv
venv/bin/pip install -r requirements-dev.txt   # app deps + pytest + ruff
venv/bin/python src/main.py                    # run (must use the venv's python, not system python)
venv/bin/pytest                                # all tests
venv/bin/pytest tests/test_sampler.py::test_rates_never_negative   # a single test
venv/bin/ruff check .                          # lint; --fix sorts imports
```

All dependency versions are pinned. `PySide6` 6.11.3 in particular was chosen during the Qt plugin troubleshooting. `pyproject.toml` holds the ruff and pytest config (pytest puts `src/` on the path).

Tests: `tests/test_sampler.py` monkeypatches `monitors.sampler.psutil` with a fake; `tests/test_app_smoke.py` builds the real `MainWindow` with `QT_QPA_PLATFORM=offscreen` and drives it by calling `sampling_service.sample_now()` / `render_loop.tick()` directly instead of waiting on timers.

## Gotchas

- **Qt "Could not find the Qt platform plugin cocoa" error**: macOS can set the `hidden` file flag on the venv folder, and Qt's QDir skips hidden files. Fix with `chflags -R nohidden venv`. The venv is named `venv` (no leading dot) to reduce this.
- **Imports are rooted at `src/`** (`from ui.theme import ...`, `from monitors.sampler import ...`), so run `src/main.py` directly; do not use `python -m src.main`.
- **Strict behaviour-preservation**: the code was refactored from a single file with the rule that no functionality or behaviour may change. Pixel layout details matter (e.g. the header spacing must equal `SECTION_SPACING` = 22).

## Architecture

Data flows one way: **sampler → service → MainWindow → panels/charts**, with a separate animation clock.

- `monitors/` is Qt-free. `MetricsSampler.sample()` reads psutil and returns a `Snapshot` (`models.py`); network and disk rates are computed from counter deltas between calls, so they are `None` on the first sample, and are clamped at 0. Readers that can fail go through `_safe_call` and fall back to `None` or the last good value.
- `services/sampling_service.py` owns a QTimer (interval changeable from the header's interval selector) and emits `snapshot_ready(Snapshot)`.
- `services/render_loop.py` is a separate ~60 fps timer emitting `frame(now, dt)`. Charts, core bars and the live badge ease toward their latest targets on every frame (the `*_EASE_SECONDS` constants in `config/settings.py`), so data arrives at the sample interval but drawing is continuous. `MainWindow` stops the render loop while the window is hidden or minimized (sampling keeps running).
- `LineChart` keeps history in `committed_points` (deques) plus numpy mirrors rebuilt once per sample, so the per-frame path is vectorized.
- `ui/main_window.py` is the only place that wires everything: `_show_snapshot` fans a Snapshot out to the KPI tiles, charts and system panel; `_advance_frame` fans frames out to charts and core bars.
- `ui/theme.py` holds colors and the Apple system font (`.AppleSystemUIFont`); `ui/charts/axes.py` has the custom `UnitAxis`/`TimeAxis` labels.
- Tunables (history length, intervals, window size, easing) live in `config/settings.py`.
