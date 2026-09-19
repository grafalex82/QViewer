import os

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from file_mgr import KEEP


@pytest.fixture(autouse=True)
def dismiss_information_dialogs(monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)


@pytest.fixture
def reviewed_directory(window, tmpdir):
    selected = tmpdir.join("selected.jpg")
    other = tmpdir.join("other.png")
    selected.write("selected")
    other.write("other")
    destination = tmpdir.mkdir("picked")
    window.mgr.load_file(selected)
    window.mgr.set_current_review_state(KEEP)
    return window, selected, other, destination


def test_copy_marked_keeps_exports_only_keep_and_preserves_source(
    reviewed_directory, monkeypatch
):
    window, selected, other, destination = reviewed_directory
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", lambda *args: str(destination)
    )
    monkeypatch.setattr(window, "confirm_copy_marked_keeps", lambda *args: True)

    result = window.copy_marked_keeps()

    assert result.copied == [os.path.realpath(selected)]
    assert result.failed == []
    assert destination.join("selected.jpg").read() == "selected"
    assert not destination.join("other.png").exists()
    assert selected.read() == "selected"
    assert other.read() == "other"
    assert window.mgr.current_file() == str(selected)
    assert window.mgr.get_current_review_state() == KEEP


def test_copy_marked_keeps_without_keep_does_not_open_destination_dialog(
    window, tmpdir, monkeypatch
):
    image = tmpdir.join("undecided.jpg")
    image.write("")
    window.mgr.load_file(image)
    calls = []
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", lambda *args: calls.append(args)
    )

    result = window.copy_marked_keeps()

    assert result is None
    assert calls == []


@pytest.mark.parametrize("full_screen", (False, True))
def test_copy_marked_keeps_shortcut_is_active_in_both_window_modes(
    reviewed_directory, app, monkeypatch, full_screen
):
    window, selected, _, destination = reviewed_directory
    chosen_directories = []
    confirmations = []
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args: chosen_directories.append(args) or str(destination),
    )
    monkeypatch.setattr(
        window,
        "confirm_copy_marked_keeps",
        lambda *args: confirmations.append(args) or False,
    )
    if full_screen:
        window.show_full_screen()
        app.processEvents()

    QTest.keyClick(window, Qt.Key_K, Qt.ControlModifier | Qt.AltModifier)
    app.processEvents()

    assert len(chosen_directories) == 1
    assert confirmations == [(1, str(destination))]
    assert selected.isfile()
    assert not destination.join("selected.jpg").exists()
