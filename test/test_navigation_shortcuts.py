import os

import pytest
from unittest.mock import Mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from file_mgr import KEEP, REJECT, UNDECIDED


def exercise_navigation_shortcuts(window, app):
    shortcuts = (
        (window.mgr.prev, Qt.Key_Left, Qt.NoModifier),
        (window.mgr.next, Qt.Key_Right, Qt.NoModifier),
        (window.mgr.prev_keep, Qt.Key_Left, Qt.ShiftModifier),
        (window.mgr.next_keep, Qt.Key_Right, Qt.ShiftModifier),
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


@pytest.mark.parametrize(
    ("review_state", "marker"),
    (
        (KEEP, " [KEEP]"),
        (REJECT, " [REJECT]"),
        (UNDECIDED, ""),
    ),
)
def test_current_file_display_name_uses_full_path_and_review_state(
    window, review_state, marker
):
    image_path = os.path.join("images", "image.jpg")
    window.mgr.current_file = Mock(return_value=image_path)
    window.mgr.current_file_position = Mock(return_value=(1, 2))
    window.mgr.get_current_review_state = Mock(return_value=review_state)

    display_name = window.current_file_display_name()

    assert display_name == f"{os.path.abspath(image_path)} (1/2){marker}"


@pytest.mark.parametrize(
    ("review_state", "marker"),
    (
        (KEEP, " [KEEP]"),
        (REJECT, " [REJECT]"),
        (UNDECIDED, ""),
    ),
)
def test_review_state_is_displayed_in_window_title(window, review_state, marker):
    image_path = os.path.join("images", "image.jpg")
    window.mgr.current_file = Mock(return_value=image_path)
    window.mgr.current_file_position = Mock(return_value=(2, 10))
    window.mgr.get_current_review_state = Mock(return_value=review_state)

    window.refresh_current_file_display()

    assert window.windowTitle() == f"{os.path.abspath(image_path)} (2/10){marker}"


@pytest.mark.parametrize(
    ("review_state", "marker"),
    (
        (KEEP, " [KEEP]"),
        (REJECT, " [REJECT]"),
        (UNDECIDED, ""),
    ),
)
def test_review_state_is_displayed_in_full_screen_overlay(
    window, app, review_state, marker
):
    image_path = os.path.join("images", "image.jpg")
    window.mgr.current_file = Mock(return_value=image_path)
    window.mgr.current_file_position = Mock(return_value=(2, 10))
    window.mgr.get_current_review_state = Mock(return_value=review_state)

    window.show_full_screen()
    app.processEvents()

    expected = f"{os.path.abspath(image_path)} (2/10){marker}"
    assert window.windowTitle() == expected
    assert window.image_view.file_name_label.text() == expected
    assert window.image_view.file_name_label.isVisible()


@pytest.mark.parametrize(
    ("key", "toggle_method"),
    (
        (Qt.Key_K, "toggle_keep"),
        (Qt.Key_X, "toggle_reject"),
    ),
)
def test_review_shortcuts_refresh_display_without_reloading_image(
    window, app, key, toggle_method
):
    setattr(window.mgr, toggle_method, Mock())
    window.refresh_current_file_display = Mock()
    window.load_image = Mock()

    QTest.keyClick(window, key)
    app.processEvents()

    getattr(window.mgr, toggle_method).assert_called_once_with()
    window.refresh_current_file_display.assert_called_once_with()
    window.load_image.assert_not_called()


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
