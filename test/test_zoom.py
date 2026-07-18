import pytest

from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent, QPixmap, QWheelEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFrame

from image_view import ImageView
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


def prepare_wheel_zoom(view, app):
    view.pixmap = QPixmap(1600, 1200)
    view.pixmap.fill(Qt.white)
    view.reset_zoom()
    app.processEvents()


def send_wheel_event(view, position, angle_delta):
    global_position = view.viewport().mapToGlobal(position)
    event = QWheelEvent(
        QPointF(position),
        QPointF(global_position),
        QPoint(),
        QPoint(0, angle_delta),
        Qt.NoButton,
        Qt.NoModifier,
        Qt.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(view.viewport(), event)


def image_position_at_cursor(view, cursor_position):
    surface_position = view.surface.mapFrom(view.viewport(), cursor_position)
    pixmap_rect = view.surface.pixmap_rect()
    return QPointF(
        float(surface_position.x() - pixmap_rect.left()) / pixmap_rect.width(),
        float(surface_position.y() - pixmap_rect.top()) / pixmap_rect.height(),
    )


def send_mouse_move(widget, position, buttons, modifiers):
    event = QMouseEvent(
        QEvent.MouseMove,
        QPointF(position),
        QPointF(widget.mapToGlobal(position)),
        Qt.NoButton,
        buttons,
        modifiers,
    )
    QApplication.sendEvent(widget, event)


def test_lasso_zoom_fills_windowed_viewport(window, app):
    assert not window.isFullScreen()

    exercise_lasso_zoom(window, app)


def test_image_view_has_no_frame(window):
    assert window.image_view.frameShape() == QFrame.NoFrame


def test_fitted_image_uses_full_viewport_height(window, app):
    view = window.image_view
    view.pixmap = QPixmap(1, 1)
    view.pixmap.fill(Qt.white)
    view.set_fit_to_window()
    app.processEvents()

    assert view.surface.pixmap().height() == view.viewport().height()


def test_lasso_zoom_fills_full_screen_viewport(window, app):
    window.show_full_screen()
    window.image_view.show_file_name("image.jpg (1/1)")
    app.processEvents()
    assert window.isFullScreen()
    assert window.image_view.file_name_label.isVisible()

    exercise_lasso_zoom(window, app)


def test_full_screen_file_name_stays_fixed_when_image_is_zoomed(window, app):
    window.show_full_screen()
    view = window.image_view
    view.show_file_name("image.jpg (1/1)")
    prepare_wheel_zoom(view, app)
    app.processEvents()

    initial_geometry = view.file_name_label.geometry()
    view.zoom_in()
    view.zoom_in()
    app.processEvents()
    view.horizontalScrollBar().setValue(view.horizontalScrollBar().maximum())
    view.verticalScrollBar().setValue(view.verticalScrollBar().maximum())
    app.processEvents()

    assert view.file_name_label.parent() is view.viewport()
    assert view.file_name_label.geometry() == initial_geometry


def test_full_screen_file_name_has_bright_green_text_and_bottom_padding(window):
    style = window.image_view.file_name_label.styleSheet()

    assert "color: #00ff00" in style
    assert "padding-bottom: 2px" in style
    assert "border:" not in style


def test_full_screen_file_name_uses_fixed_width_font(window):
    assert window.image_view.file_name_label.font().fixedPitch()


@pytest.mark.parametrize(
    ("angle_delta", "expected_factor"),
    [(120, 1.10), (-120, 1.0 / 1.10)],
)
def test_mouse_wheel_changes_zoom_by_ten_percent(
    window, app, angle_delta, expected_factor
):
    view = window.image_view
    prepare_wheel_zoom(view, app)
    cursor_position = view.surface.pixmap_rect().center()
    initial_scale = view.scale_factor

    send_wheel_event(view, cursor_position, angle_delta)
    app.processEvents()

    assert view.zoom_changed
    assert view.scale_factor == pytest.approx(initial_scale * expected_factor)


@pytest.mark.parametrize("angle_delta", [120, -120])
def test_mouse_wheel_zoom_keeps_image_position_under_cursor(
    window, app, angle_delta
):
    view = window.image_view
    prepare_wheel_zoom(view, app)
    view.scale_factor *= 2
    view.zoom_changed = True
    view.resize_image()
    app.processEvents()
    view.horizontalScrollBar().setValue(view.horizontalScrollBar().maximum() // 2)
    view.verticalScrollBar().setValue(view.verticalScrollBar().maximum() // 2)
    cursor_position = QPoint(
        view.viewport().width() * 3 // 4,
        view.viewport().height() * 3 // 4,
    )
    initial_image_position = image_position_at_cursor(view, cursor_position)

    send_wheel_event(view, cursor_position, angle_delta)
    app.processEvents()

    zoomed_image_position = image_position_at_cursor(view, cursor_position)
    assert zoomed_image_position.x() == pytest.approx(
        initial_image_position.x(), abs=2.0 / view.surface.pixmap().width()
    )
    assert zoomed_image_position.y() == pytest.approx(
        initial_image_position.y(), abs=2.0 / view.surface.pixmap().height()
    )


@pytest.mark.parametrize(
    ("zoom_mode", "expected_scale"),
    [
        (ImageView.ZOOM_FIT_TO_WINDOW, None),
        (ImageView.ZOOM_1_TO_1, 1.0),
    ],
)
def test_ctrl_click_resets_zoom_to_current_mode(
    window, app, zoom_mode, expected_scale
):
    view = window.image_view
    prepare_wheel_zoom(view, app)

    if zoom_mode == ImageView.ZOOM_FIT_TO_WINDOW:
        view.set_fit_to_window()
        expected_scale = view.scale_factor
    else:
        view.set_original_size()

    view.zoom_in()
    assert view.zoom_changed
    assert view.scale_factor != pytest.approx(expected_scale)

    QTest.mouseClick(
        view.surface,
        Qt.LeftButton,
        Qt.ControlModifier,
        view.surface.pixmap_rect().center(),
    )
    app.processEvents()

    assert view.zoom_mode == zoom_mode
    assert not view.zoom_changed
    assert view.scale_factor == pytest.approx(expected_scale)
    assert view.surface.selection_rect.isEmpty()


def test_shift_mouse_drag_pans_zoomed_image(window, app):
    view = window.image_view
    prepare_wheel_zoom(view, app)
    view.scale_factor *= 2
    view.zoom_changed = True
    view.resize_image()
    app.processEvents()

    horizontal_scroll_bar = view.horizontalScrollBar()
    vertical_scroll_bar = view.verticalScrollBar()
    horizontal_scroll_bar.setValue(horizontal_scroll_bar.maximum() // 2)
    vertical_scroll_bar.setValue(vertical_scroll_bar.maximum() // 2)
    initial_scroll_position = QPoint(
        horizontal_scroll_bar.value(), vertical_scroll_bar.value()
    )
    start = view.surface.mapFrom(view.viewport(), view.viewport().rect().center())
    drag_delta = QPoint(40, 30)

    QTest.mousePress(view.surface, Qt.LeftButton, Qt.ShiftModifier, start)
    send_mouse_move(
        view.surface, start + drag_delta, Qt.LeftButton, Qt.ShiftModifier
    )
    QTest.mouseRelease(
        view.surface, Qt.LeftButton, Qt.ShiftModifier, start + drag_delta
    )
    app.processEvents()

    assert horizontal_scroll_bar.value() == initial_scroll_position.x() - drag_delta.x()
    assert vertical_scroll_bar.value() == initial_scroll_position.y() - drag_delta.y()
    assert view.surface.selection_rect.isEmpty()


def test_shift_mouse_drag_does_not_pan_fitted_image(window, app):
    view = window.image_view
    prepare_wheel_zoom(view, app)
    start = view.surface.pixmap_rect().center()

    QTest.mousePress(view.surface, Qt.LeftButton, Qt.ShiftModifier, start)
    send_mouse_move(
        view.surface, start + QPoint(20, 20), Qt.LeftButton, Qt.ShiftModifier
    )
    QTest.mouseRelease(
        view.surface, Qt.LeftButton, Qt.ShiftModifier, start + QPoint(20, 20)
    )
    app.processEvents()

    assert view.horizontalScrollBar().value() == 0
    assert view.verticalScrollBar().value() == 0
    assert not view.surface.selection_rect.isEmpty()
