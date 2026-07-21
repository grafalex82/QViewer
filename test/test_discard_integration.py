import os
from pathlib import Path

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from file_mgr import DISCARD_DIRECTORY_NAME, KEEP, REJECT, UNDECIDED


@pytest.fixture
def discard_fixture(window, app, tmp_path, monkeypatch):
    current = tmp_path / "current"
    current.mkdir()
    nested = current / "nested"
    nested.mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()

    images = {
        KEEP: current / "01-keep.JPG",
        REJECT: current / "02-reject.JpEg",
        UNDECIDED: current / "03-undecided.PNG",
    }
    for state, path in images.items():
        path.write_bytes(f"{state}-image".encode())

    protected_files = {
        current / "notes.txt": b"current metadata",
        nested / "nested.jpg": b"nested image",
        sibling / "sibling.jpeg": b"sibling image",
        tmp_path / "outside.png": b"outside image",
    }
    for path, contents in protected_files.items():
        path.write_bytes(contents)

    window.mgr.load_directory(str(current))
    window.load_image(window.mgr.current_file())
    app.processEvents()

    # Exercise the real review and navigation actions. The third image remains
    # undecided deliberately.
    QTest.keyClick(window, Qt.Key_K)
    QTest.keyClick(window, Qt.Key_Right)
    QTest.keyClick(window, Qt.Key_X)
    QTest.keyClick(window, Qt.Key_Right)
    app.processEvents()

    assert window.mgr.get_review_state(images[KEEP]) == KEEP
    assert window.mgr.get_review_state(images[REJECT]) == REJECT
    assert window.mgr.get_review_state(images[UNDECIDED]) == UNDECIDED

    # Select the rejected image so each mode also exercises replacement of a
    # current image that is moved.
    window.mgr.load_file(str(images[REJECT]))
    window.load_image(window.mgr.current_file())
    app.processEvents()

    monkeypatch.setattr(window, "confirm_bulk_discard", lambda *args: True)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)

    return window, current, images, protected_files


def assert_protected_files_unchanged(protected_files):
    for path, expected_contents in protected_files.items():
        assert path.is_file()
        assert path.read_bytes() == expected_contents


def assert_quarantine_contains_only(result, expected_paths):
    assert result.destination is not None
    destination = Path(result.destination)
    assert destination.parent.name == DISCARD_DIRECTORY_NAME

    quarantined_names = sorted(path.name for path in destination.iterdir())
    assert quarantined_names == sorted(path.name for path in expected_paths)
    for source in expected_paths:
        quarantined = destination / source.name
        expected_contents = f"{source.stem.split('-', 1)[1].lower()}-image".encode()
        assert quarantined.is_file()
        assert quarantined.read_bytes() == expected_contents


def test_discard_rejected_moves_only_reject_and_updates_file_manager(
    discard_fixture,
):
    window, current, images, protected_files = discard_fixture

    result = window.discard_rejected()

    assert result.failed == []
    assert result.moved == [os.path.realpath(images[REJECT])]
    assert images[KEEP].is_file()
    assert not images[REJECT].exists()
    assert images[UNDECIDED].is_file()
    assert_quarantine_contains_only(result, [images[REJECT]])
    assert os.path.dirname(os.path.dirname(result.destination)) == str(current)

    assert window.mgr.directory_files == [images[KEEP].name, images[UNDECIDED].name]
    assert window.mgr.current_file() == str(images[UNDECIDED])
    assert window.mgr.current_file_position() == (2, 2)
    assert window.mgr.get_review_state(images[KEEP]) == KEEP
    assert window.mgr.get_review_state(images[REJECT]) == UNDECIDED
    assert window.mgr.get_review_state(images[UNDECIDED]) == UNDECIDED
    assert_protected_files_unchanged(protected_files)


def test_keep_only_marked_moves_reject_and_undecided_and_updates_file_manager(
    discard_fixture,
):
    window, current, images, protected_files = discard_fixture

    result = window.keep_only_marked()

    moved = [images[REJECT], images[UNDECIDED]]
    assert result.failed == []
    assert result.moved == [os.path.realpath(path) for path in moved]
    assert images[KEEP].is_file()
    assert not images[REJECT].exists()
    assert not images[UNDECIDED].exists()
    assert_quarantine_contains_only(result, moved)
    assert os.path.dirname(os.path.dirname(result.destination)) == str(current)

    assert window.mgr.directory_files == [images[KEEP].name]
    assert window.mgr.current_file() == str(images[KEEP])
    assert window.mgr.current_file_position() == (1, 1)
    assert window.mgr.get_current_review_state() == KEEP
    assert window.mgr.get_review_state(images[REJECT]) == UNDECIDED
    assert window.mgr.get_review_state(images[UNDECIDED]) == UNDECIDED
    assert_protected_files_unchanged(protected_files)
