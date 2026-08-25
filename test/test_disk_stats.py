import os
from collections import namedtuple
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtTest import QTest

from file_mgr import DiskStats, FileMgr, KEEP, REJECT


def test_file_manager_calculates_current_directory_disk_stats(tmpdir, monkeypatch):
    images = {
        "a.jpg": 1_234,
        "b.png": 5_678,
        "c.jpeg": 90,
    }
    for name, size in images.items():
        tmpdir.join(name).write_binary(b"x" * size)
    tmpdir.join("ignored.txt").write_binary(b"x" * 50_000)

    mgr = FileMgr()
    mgr.load_file(tmpdir.join("b.png"))
    mgr.load_file(tmpdir.join("a.jpg"))
    mgr.set_current_review_state(KEEP)
    mgr.load_file(tmpdir.join("c.jpeg"))
    mgr.set_current_review_state(REJECT)
    mgr.load_file(tmpdir.join("b.png"))

    DiskUsage = namedtuple("DiskUsage", "total used free")
    disk_usage = Mock(return_value=DiskUsage(1_000_000, 123_211, 876_789))
    monkeypatch.setattr("file_mgr.shutil.disk_usage", disk_usage)

    assert mgr.current_disk_stats() == DiskStats(
        current_index=2,
        current_file_size=5_678,
        image_count=3,
        total_image_size=7_002,
        keep_count=1,
        keep_size=1_234,
        reject_count=1,
        reject_size=90,
        free_disk_space=876_789,
    )
    disk_usage.assert_called_once_with(os.path.realpath(tmpdir))


def test_file_manager_disk_stats_are_empty_without_a_directory():
    assert FileMgr().current_disk_stats() == DiskStats()


def test_disk_stats_format_uses_comma_delimited_bytes(window):
    text = window.format_disk_stats(
        DiskStats(
            current_index=12,
            current_file_size=1_234,
            image_count=23_456,
            total_image_size=7_890_123,
            keep_count=3,
            keep_size=45_678,
            reject_count=9,
            reject_size=101_112,
            free_disk_space=13_141_516,
        )
    )

    assert text.splitlines() == [
        "Image index: 12",
        "Image size: 1,234 bytes",
        "Images: 23,456",
        "Images size: 7,890,123 bytes",
        "KEEP: 3",
        "KEEP size: 45,678 bytes",
        "REJECT: 9",
        "REJECT size: 101,112 bytes",
        "Free disk space: 13,141,516 bytes",
    ]


@pytest.mark.parametrize("full_screen", (False, True))
def test_d_toggles_bottom_left_disk_stats_overlay(window, app, full_screen):
    window.mgr.current_disk_stats = Mock(
        return_value=DiskStats(current_index=1, image_count=1)
    )
    label = window.image_view.disk_stats_label
    if full_screen:
        window.show_full_screen()
        app.processEvents()

    assert not label.isVisible()

    QTest.keyClick(window, Qt.Key_D)
    app.processEvents()

    assert label.isVisible()
    assert label.parent() is window.image_view.viewport()
    assert label.x() == 0
    assert label.y() + label.height() == window.image_view.viewport().height()
    assert "background-color: black" in label.styleSheet()
    assert "color: lightgreen" in label.styleSheet()

    QTest.keyClick(window, Qt.Key_D)
    app.processEvents()

    assert not label.isVisible()


def test_disk_stats_overlay_remains_anchored_after_resize_and_zoom(window, app):
    window.mgr.current_disk_stats = Mock(return_value=DiskStats())
    view = window.image_view
    view.pixmap = QPixmap(1_600, 1_200)
    view.pixmap.fill(Qt.white)
    view.reset_zoom()
    QTest.keyClick(window, Qt.Key_D)
    app.processEvents()

    window.resize(900, 700)
    app.processEvents()

    label = view.disk_stats_label
    assert label.x() == 0
    assert label.y() + label.height() == view.viewport().height()

    view.zoom_in()
    app.processEvents()

    assert label.x() == 0
    assert label.y() + label.height() == view.viewport().height()
