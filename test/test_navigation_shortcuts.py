import pytest
from unittest.mock import Mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from main import ImageViewerApp


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    viewer = ImageViewerApp()
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


def test_navigation_shortcuts_work_in_full_screen_mode(window, app):
    window.show_full_screen()
    app.processEvents()
    assert window.isFullScreen()
    assert not window.menuBar().isVisible()
    exercise_navigation_shortcuts(window, app)
