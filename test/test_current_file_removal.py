import os
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from file_mgr import DISCARD_DIRECTORY_NAME, REJECT


@pytest.fixture
def removal_window(window, tmpdir):
    images = [tmpdir.join(name) for name in ("a.jpg", "b.jpg", "c.jpg")]
    for image in images:
        image.write("")
    window.mgr.load_file(str(images[1]))
    return window, images


@pytest.mark.parametrize(
    ("modifier", "method_name"),
    ((Qt.NoModifier, "discard_current"), (Qt.ShiftModifier, "delete_current")),
)
@pytest.mark.parametrize("full_screen", (False, True))
def test_current_file_shortcuts_work_windowed_and_full_screen(
    removal_window, app, monkeypatch, modifier, method_name, full_screen
):
    window, images = removal_window
    action = Mock(return_value=None)
    getattr(window, f"{method_name}_action").triggered.disconnect()
    getattr(window, f"{method_name}_action").triggered.connect(action)
    if full_screen:
        window.show_full_screen()
        app.processEvents()

    QTest.keyClick(window, Qt.Key_Delete, modifier)
    app.processEvents()

    action.assert_called_once()
    assert all(image.exists() for image in images)


@pytest.mark.parametrize("method_name", ("discard_current", "delete_current"))
def test_cancel_keeps_current_file_untouched(removal_window, monkeypatch, method_name):
    window, images = removal_window
    monkeypatch.setattr(window, "confirm_current_file_action", lambda *args, **kwargs: False)

    result = getattr(window, method_name)()

    assert result is None
    assert window.mgr.current_file() == str(images[1])
    assert all(image.exists() for image in images)
    assert not images[0].dirpath(DISCARD_DIRECTORY_NAME).exists()


def test_delete_discards_current_file_and_advances_to_next(
    removal_window, monkeypatch
):
    window, images = removal_window
    monkeypatch.setattr(window, "confirm_current_file_action", lambda *args, **kwargs: True)

    result = window.discard_current()

    assert result.moved == [os.path.realpath(str(images[1]))]
    assert not images[1].exists()
    assert window.mgr.current_file() == str(images[2])
    assert window.mgr.directory_files == ["a.jpg", "c.jpg"]
    assert os.path.exists(os.path.join(result.destination, "b.jpg"))


def test_shift_delete_permanently_deletes_current_file_and_advances(
    removal_window, monkeypatch
):
    window, images = removal_window
    window.mgr.set_current_review_state(REJECT)
    monkeypatch.setattr(window, "confirm_current_file_action", lambda *args, **kwargs: True)

    deleted = window.delete_current()

    assert deleted == os.path.realpath(str(images[1]))
    assert not images[1].exists()
    assert window.mgr.current_file() == str(images[2])
    assert window.mgr.directory_files == ["a.jpg", "c.jpg"]
    assert deleted not in window.mgr.review_states
    assert not images[0].dirpath(DISCARD_DIRECTORY_NAME).exists()


def test_confirmation_dialogs_default_to_cancel(removal_window, monkeypatch):
    window, images = removal_window
    captured = []

    def inspect_and_cancel(dialog):
        captured.append(
            (
                dialog.windowTitle(),
                dialog.text(),
                dialog.defaultButton().text(),
                [button.text() for button in dialog.buttons()],
            )
        )
        dialog.done(0)
        return 0

    monkeypatch.setattr(QMessageBox, "exec_", inspect_and_cancel)

    window.discard_current()
    window.delete_current()

    assert captured[0][0] == "Discard Current Image"
    assert set(captured[0][3]) == {"Discard", "Cancel"}
    assert captured[1][0] == "Delete Current Image"
    assert "cannot be undone" in captured[1][1]
    assert set(captured[1][3]) == {"Delete", "Cancel"}
    assert all(dialog[2] == "Cancel" for dialog in captured)
    assert all(image.exists() for image in images)


def test_permanent_delete_failure_keeps_selection_and_reports_error(
    removal_window, monkeypatch
):
    window, images = removal_window
    monkeypatch.setattr(window, "confirm_current_file_action", lambda *args, **kwargs: True)
    monkeypatch.setattr(window.mgr, "delete_current_file", Mock(side_effect=OSError("access denied")))
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    result = window.delete_current()

    assert result is None
    assert window.mgr.current_file() == str(images[1])
    assert images[1].exists()
    assert "access denied" in warnings[0][2]
