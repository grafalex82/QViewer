import pytest

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from file_mgr import KEEP, REJECT, UNDECIDED


@pytest.fixture
def loaded_window(window, app, tmpdir):
    first = tmpdir.join("first.jpg")
    second = tmpdir.join("second.jpg")
    third = tmpdir.join("third.jpg")
    first.write("")
    second.write("")
    third.write("")
    window.mgr.load_file(str(first))
    window.refresh_current_file_display()
    app.processEvents()
    return window


@pytest.mark.parametrize(
    ("key", "initial_state", "expected_state"),
    (
        (Qt.Key_K, UNDECIDED, KEEP),
        (Qt.Key_K, KEEP, UNDECIDED),
        (Qt.Key_K, REJECT, KEEP),
        (Qt.Key_X, UNDECIDED, REJECT),
        (Qt.Key_X, REJECT, UNDECIDED),
        (Qt.Key_X, KEEP, REJECT),
    ),
)
def test_review_shortcut_transitions_without_changing_file(
    loaded_window, app, key, initial_state, expected_state
):
    loaded_window.mgr.set_current_review_state(initial_state)
    initial_index = loaded_window.mgr.file_index
    initial_file = loaded_window.mgr.current_file()

    QTest.keyClick(loaded_window, key)
    app.processEvents()

    assert loaded_window.mgr.get_current_review_state() == expected_state
    assert loaded_window.mgr.file_index == initial_index
    assert loaded_window.mgr.current_file() == initial_file


@pytest.mark.parametrize("key", (Qt.Key_K, Qt.Key_X))
@pytest.mark.parametrize("full_screen", (False, True))
def test_review_shortcuts_work_with_menu_bar_visible_or_hidden(
    loaded_window, app, key, full_screen
):
    if full_screen:
        loaded_window.show_full_screen()
        app.processEvents()

    assert loaded_window.menuBar().isVisible() is not full_screen

    QTest.keyClick(loaded_window, key)
    app.processEvents()

    expected_state = KEEP if key == Qt.Key_K else REJECT
    assert loaded_window.mgr.get_current_review_state() == expected_state


@pytest.mark.parametrize("key", (Qt.Key_K, Qt.Key_X))
def test_review_shortcuts_are_safe_without_a_loaded_file(window, app, key):
    assert window.mgr.current_file() is None

    QTest.keyClick(window, key)
    app.processEvents()

    assert window.mgr.current_file() is None
    assert window.mgr.get_current_review_state() == UNDECIDED


@pytest.mark.parametrize(
    ("key", "requested_state", "initial_state"),
    (
        (Qt.Key_Up, KEEP, UNDECIDED),
        (Qt.Key_Up, KEEP, REJECT),
        (Qt.Key_Up, KEEP, KEEP),
        (Qt.Key_Down, REJECT, UNDECIDED),
        (Qt.Key_Down, REJECT, KEEP),
        (Qt.Key_Down, REJECT, REJECT),
    ),
)
@pytest.mark.parametrize("full_screen", (False, True))
def test_set_state_and_next_shortcuts_replace_state_then_advance(
    loaded_window, app, key, requested_state, initial_state, full_screen
):
    loaded_window.mgr.next()
    reviewed_file = loaded_window.mgr.current_file()
    loaded_window.mgr.set_current_review_state(initial_state)

    if full_screen:
        loaded_window.show_full_screen()
        app.processEvents()

    QTest.keyClick(loaded_window, key, Qt.ControlModifier)
    app.processEvents()

    assert loaded_window.mgr.get_review_state(reviewed_file) == requested_state
    assert loaded_window.mgr.file_index == 2
    assert loaded_window.mgr.current_file() != reviewed_file


@pytest.mark.parametrize(
    ("key", "requested_state"),
    ((Qt.Key_Up, KEEP), (Qt.Key_Down, REJECT)),
)
def test_set_state_and_next_shortcuts_set_state_at_last_image_without_moving(
    loaded_window, app, key, requested_state
):
    loaded_window.mgr.last()
    last_file = loaded_window.mgr.current_file()

    QTest.keyClick(loaded_window, key, Qt.ControlModifier)
    app.processEvents()

    assert loaded_window.mgr.current_file() == last_file
    assert loaded_window.mgr.get_review_state(last_file) == requested_state


@pytest.mark.parametrize("key", (Qt.Key_Up, Qt.Key_Down))
@pytest.mark.parametrize("full_screen", (False, True))
def test_plain_vertical_arrows_do_not_set_state_or_advance(
    loaded_window, app, key, full_screen
):
    initial_file = loaded_window.mgr.current_file()

    if full_screen:
        loaded_window.show_full_screen()
        app.processEvents()

    QTest.keyClick(loaded_window, key)
    app.processEvents()

    assert loaded_window.mgr.current_file() == initial_file
    assert loaded_window.mgr.get_review_state(initial_file) == UNDECIDED


@pytest.mark.parametrize("key", (Qt.Key_Up, Qt.Key_Down))
def test_set_state_and_next_shortcuts_are_safe_without_a_loaded_file(
    window, app, key
):
    assert window.mgr.current_file() is None

    QTest.keyClick(window, key, Qt.ControlModifier)
    app.processEvents()

    assert window.mgr.current_file() is None
    assert window.mgr.get_current_review_state() == UNDECIDED
