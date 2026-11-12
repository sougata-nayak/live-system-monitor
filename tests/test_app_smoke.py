"""Builds the real window offscreen and drives it, with real psutil data."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from ui.main_window import MainWindow  # noqa: E402
from ui.theme import ui_font  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    application.setFont(ui_font(13))
    return application


@pytest.fixture
def window(app):
    w = MainWindow()
    w.show()
    app.processEvents()
    yield w
    w.close()


def test_samples_and_frames_update_widgets(app, window):
    for _ in range(3):
        window.sampling_service.sample_now()
        for _ in range(5):
            window.render_loop.tick()
    app.processEvents()
    assert window.cpu_tile.value_label.text() != "–"
    assert window.system_panel.value_labels["Processes"].text().isdigit()
    for chart in window.charts:
        assert any(len(points) for points in chart.committed_points.values())
    assert not window.grab().isNull()


def test_interval_selector_changes_sampling_interval(app, window):
    buttons = {b.text(): b for b in window.findChildren(QPushButton)}
    buttons["2 s"].click()
    assert window.sampling_service.timer.interval() == 2000
    buttons["0.5 s"].click()
    assert window.sampling_service.timer.interval() == 500


def test_render_loop_pauses_while_hidden(app, window):
    assert window.render_loop.timer.isActive()
    window.hide()
    app.processEvents()
    assert not window.render_loop.timer.isActive()
    assert window.sampling_service.timer.isActive()  # sampling keeps going
    window.show()
    app.processEvents()
    assert window.render_loop.timer.isActive()
