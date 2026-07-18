import os

import pytest
from unittest.mock import Mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from main import ImageViewerMainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    viewer = ImageViewerMainWindow()
    viewer.show()
    app.processEvents()
    yield viewer
    viewer.close()


def exercise_navigation_shortcuts(window, app):
    shortcuts = (
        (window.mgr.prev, Qt.Key_Left, Qt.NoModifier),
        (window.mgr.next, Qt.Key_Right, Qt.NoModifier),
        (window.mgr.first, Qt.Key_Home, Qt.NoModifier),
        (window.mgr.last, Qt.Key_End, Qt.NoModifier),
        (window.mgr.prev_dir, Qt.Key_Left, Qt.ControlModifier),
        (window.mgr.next_dir, Qt.Key_Right, Qt.ControlModifier),
    )

    for method, _, _ in shortcuts:
        setattr(window.mgr, method.__name__, Mock(return_value=False))

    for _, key, modifier in shortcuts:
        QTest.keyClick(window, key, modifier)
    app.processEvents()

    for method, _, _ in shortcuts:
        getattr(window.mgr, method.__name__).assert_called_once_with()


def test_navigation_shortcuts_work_in_windowed_mode(window, app):
    assert not window.isFullScreen()
    assert window.menuBar().isVisible()
    exercise_navigation_shortcuts(window, app)


def test_current_file_display_name_uses_full_path(window):
    image_path = os.path.join("images", "image.jpg")
    window.mgr.current_file = Mock(return_value=image_path)
    window.mgr.current_file_position = Mock(return_value=(1, 2))

    display_name = window.current_file_display_name()

    assert display_name == f"{os.path.abspath(image_path)} (1/2)"


def test_navigation_shortcuts_work_in_full_screen_mode(window, app):
    window.show_full_screen()
    app.processEvents()
    assert window.isFullScreen()
    assert not window.menuBar().isVisible()
    assert window.image_view.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert window.image_view.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    exercise_navigation_shortcuts(window, app)


def exercise_zoom_shortcuts(window, app):
    window.image_view.scale_factor = 1.0

    QTest.keyClick(window, Qt.Key_Plus)
    app.processEvents()
    assert window.image_view.scale_factor == pytest.approx(1.25)

    QTest.keyClick(window, Qt.Key_Minus)
    app.processEvents()
    assert window.image_view.scale_factor == pytest.approx(1.0)


def test_zoom_shortcuts_work_in_windowed_mode(window, app):
    assert not window.isFullScreen()
    exercise_zoom_shortcuts(window, app)


def test_zoom_shortcuts_work_in_full_screen_mode(window, app):
    window.show_full_screen()
    app.processEvents()
    assert window.isFullScreen()
    assert not window.menuBar().isVisible()
    exercise_zoom_shortcuts(window, app)


def test_scroll_bars_are_restored_after_full_screen(window, app):
    window.show_full_screen()
    app.processEvents()

    window.show_normal()
    app.processEvents()

    assert not window.isFullScreen()
    assert window.image_view.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert window.image_view.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded


def test_escape_closes_windowed_application(window, app):
    assert not window.isFullScreen()

    QTest.keyClick(window, Qt.Key_Escape)
    app.processEvents()

    assert not window.isVisible()


def test_escape_exits_full_screen_before_closing(window, app):
    window.show_full_screen()
    app.processEvents()

    QTest.keyClick(window, Qt.Key_Escape)
    app.processEvents()

    assert window.isVisible()
    assert not window.isFullScreen()

    QTest.keyClick(window, Qt.Key_Escape)
    app.processEvents()

    assert not window.isVisible()
