import pytest

from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent, QPixmap
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


def exercise_lasso_zoom(window, app):
    view = window.image_view
    view.pixmap = QPixmap(1600, 1200)
    view.pixmap.fill(Qt.white)
    view.reset_zoom()
    app.processEvents()

    displayed_image = view.surface.pixmap_rect()
    start = displayed_image.topLeft() + QPoint(
        displayed_image.width() // 4, displayed_image.height() // 4
    )
    end = displayed_image.topLeft() + QPoint(
        displayed_image.width() * 3 // 4,
        displayed_image.height() * 3 // 4,
    )

    QTest.mousePress(view.surface, Qt.LeftButton, pos=start)
    move_event = QMouseEvent(
        QEvent.MouseMove,
        QPointF(end),
        Qt.NoButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    QApplication.sendEvent(view.surface, move_event)
    app.processEvents()
    QTest.mouseRelease(view.surface, Qt.LeftButton, pos=end)
    selection_size = view.surface.selection_rect.size()
    initial_scale = view.scale_factor
    viewport_size = view.viewport().size()

    QTest.mouseClick(view.surface, Qt.LeftButton, pos=(start + end) / 2)
    app.processEvents()

    expected_scale = initial_scale * min(
        viewport_size.width() / selection_size.width(),
        viewport_size.height() / selection_size.height(),
    )
    assert view.zoom_changed
    assert view.scale_factor == pytest.approx(expected_scale)
    assert view.surface.selection_rect.isEmpty()


def test_lasso_zoom_fills_windowed_viewport(window, app):
    assert not window.isFullScreen()

    exercise_lasso_zoom(window, app)


def test_lasso_zoom_fills_full_screen_viewport(window, app):
    window.show_full_screen()
    window.image_view.show_file_name("image.jpg (1/1)")
    app.processEvents()
    assert window.isFullScreen()
    assert window.image_view.surface.file_name

    exercise_lasso_zoom(window, app)
