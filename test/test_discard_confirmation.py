import os
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from file_mgr import DISCARD_DIRECTORY_NAME, DiscardResult, KEEP, REJECT


@pytest.fixture
def reviewed_window(window, tmpdir):
    paths = [tmpdir.join(name) for name in ("keep.jpg", "reject.jpg", "other.jpg")]
    for path in paths:
        path.write("")

    window.mgr.load_file(str(paths[0]))
    window.mgr.set_current_review_state(KEEP)
    window.mgr.load_file(str(paths[1]))
    window.mgr.set_current_review_state(REJECT)
    window.mgr.load_file(str(paths[2]))
    return window, paths


def test_discard_rejected_cancel_does_not_move_or_create_directory(
    reviewed_window, monkeypatch
):
    window, paths = reviewed_window
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: False)
    move = []
    monkeypatch.setattr(window.mgr, "move_to_discard_directory", move.append)

    result = window.discard_rejected()

    assert result is None
    assert move == []
    assert all(path.exists() for path in paths)
    assert not paths[0].dirpath(DISCARD_DIRECTORY_NAME).exists()


def test_discard_rejected_continue_moves_only_rejected(reviewed_window, monkeypatch):
    window, paths = reviewed_window
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)

    result = window.discard_rejected()

    assert result.moved == [os.path.realpath(str(paths[1]))]
    assert paths[0].exists()
    assert not paths[1].exists()
    assert paths[2].exists()


def test_discard_rejected_with_no_reject_reports_and_creates_nothing(
    window, tmpdir, monkeypatch
):
    image = tmpdir.join("undecided.jpg")
    image.write("")
    window.mgr.load_file(str(image))
    information = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args: information.append(args)
    )

    result = window.discard_rejected()

    assert result is None
    assert "marked Reject" in information[0][2]
    assert image.exists()
    assert not tmpdir.join(DISCARD_DIRECTORY_NAME).exists()


def test_keep_only_marked_confirmation_warns_when_keep_count_is_zero(
    window, tmpdir, monkeypatch
):
    for name in ("one.jpg", "two.jpg"):
        tmpdir.join(name).write("")
    window.mgr.load_directory(str(tmpdir))
    captured = {}

    def inspect_and_cancel(dialog):
        captured["title"] = dialog.windowTitle()
        captured["message"] = dialog.text()
        captured["default"] = dialog.defaultButton().text()
        captured["buttons"] = [button.text() for button in dialog.buttons()]
        dialog.done(0)
        return 0

    monkeypatch.setattr(QMessageBox, "exec_", inspect_and_cancel)

    window.keep_only_marked()

    assert captured["title"] == "Keep Only Marked"
    assert "Kept: 0\nRejected: 0\nUndecided: 2" in captured["message"]
    assert "every managed image" in captured["message"].lower()
    assert "2 images not marked Keep will be moved into:" in captured["message"]
    assert DISCARD_DIRECTORY_NAME in captured["message"]
    assert set(captured["buttons"]) == {"Continue", "Cancel"}
    assert captured["default"] == "Cancel"
    assert not tmpdir.join(DISCARD_DIRECTORY_NAME).exists()


def test_keep_only_marked_continue_moves_rejected_and_undecided(
    reviewed_window, monkeypatch
):
    window, paths = reviewed_window
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)

    result = window.keep_only_marked()

    assert result.moved == [
        os.path.realpath(str(paths[2])),
        os.path.realpath(str(paths[1])),
    ]
    assert paths[0].exists()
    assert not paths[1].exists()
    assert not paths[2].exists()


def test_keep_only_marked_with_zero_keep_moves_every_managed_image(
    window, tmpdir, monkeypatch
):
    images = [tmpdir.join("one.jpg"), tmpdir.join("two.png")]
    for image in images:
        image.write("")
    window.mgr.load_directory(str(tmpdir))
    window.mgr.set_current_review_state(REJECT)
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)

    result = window.keep_only_marked()

    assert set(result.moved) == {os.path.realpath(str(image)) for image in images}
    assert all(not image.exists() for image in images)
    assert window.mgr.current_file() is None
    assert window.image_view.pixmap is None


def test_keep_only_marked_cancel_leaves_everything_untouched(
    reviewed_window, monkeypatch
):
    window, paths = reviewed_window
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: False)

    result = window.keep_only_marked()

    assert result is None
    assert all(path.exists() for path in paths)
    assert not paths[0].dirpath(DISCARD_DIRECTORY_NAME).exists()


def test_keep_only_marked_does_not_process_child_or_sibling_directories(
    window, tmpdir, monkeypatch
):
    current = tmpdir.mkdir("current")
    sibling = tmpdir.mkdir("sibling")
    child = current.mkdir("child")
    current_image = current.join("current.jpg")
    sibling_image = sibling.join("sibling.jpg")
    child_image = child.join("child.jpg")
    for image in (current_image, sibling_image, child_image):
        image.write("")
    window.mgr.load_directory(str(current))
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)

    result = window.keep_only_marked()

    assert result.moved == [os.path.realpath(str(current_image))]
    assert not current_image.exists()
    assert sibling_image.exists()
    assert child_image.exists()
    assert not sibling.join(DISCARD_DIRECTORY_NAME).exists()
    assert not child.join(DISCARD_DIRECTORY_NAME).exists()


@pytest.mark.parametrize(
    ("operation", "modifier"),
    (
        ("discard_rejected", Qt.ControlModifier),
        ("keep_only_marked", Qt.ControlModifier | Qt.ShiftModifier),
    ),
)
@pytest.mark.parametrize("full_screen", (False, True))
def test_bulk_discard_shortcuts_work_windowed_and_full_screen(
    window, app, tmpdir, monkeypatch, operation, modifier, full_screen
):
    image = tmpdir.join("candidate.jpg")
    image.write("")
    window.mgr.load_file(str(image))
    if operation == "discard_rejected":
        window.mgr.set_current_review_state(REJECT)
    confirmations = []
    monkeypatch.setattr(
        window,
        "confirm_bulk_discard",
        lambda *args: confirmations.append(args) or False,
    )
    if full_screen:
        window.show_full_screen()
        app.processEvents()

    QTest.keyClick(window, Qt.Key_Delete, modifier)
    app.processEvents()

    assert len(confirmations) == 1
    assert image.exists()


def test_bulk_discard_refreshes_display_and_navigation(reviewed_window, monkeypatch):
    window, paths = reviewed_window
    window.mgr.load_file(str(paths[1]))
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)
    load_image = Mock(wraps=window.image_view.load_image)
    monkeypatch.setattr(window.image_view, "load_image", load_image)

    window.discard_rejected()

    assert window.mgr.current_file() == str(paths[2])
    load_image.assert_called_once_with(str(paths[2]))
    assert os.path.abspath(str(paths[2])) in window.windowTitle()
    assert window.mgr.current_file_position() == (2, 2)


def test_bulk_discard_reports_move_failures(reviewed_window, monkeypatch):
    window, paths = reviewed_window
    failure = (os.path.realpath(str(paths[1])), "simulated failure")
    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)
    monkeypatch.setattr(
        window.mgr,
        "move_to_discard_directory",
        lambda candidates: DiscardResult(failed=[failure]),
    )
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    result = window.discard_rejected()

    assert result.failed == [failure]
    assert str(paths[1]) in warnings[0][2]
    assert "simulated failure" in warnings[0][2]


def test_zero_candidates_reports_nothing_without_confirmation(
    window, tmpdir, monkeypatch
):
    image = tmpdir.join("keep.jpg")
    image.write("")
    window.mgr.load_file(str(image))
    window.mgr.set_current_review_state(KEEP)
    confirmations = []
    information = []
    monkeypatch.setattr(QMessageBox, "exec_", lambda *args: confirmations.append(args))
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args: information.append(args)
    )

    result = window.keep_only_marked()

    assert result is None
    assert confirmations == []
    assert information and information[0][2] == "There is nothing to discard."
    assert not tmpdir.join(DISCARD_DIRECTORY_NAME).exists()
