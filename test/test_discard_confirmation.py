import os

import pytest
from PyQt5.QtWidgets import QMessageBox

from file_mgr import DISCARD_DIRECTORY_NAME, KEEP, REJECT


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
