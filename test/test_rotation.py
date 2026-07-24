from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtTest import QTest

from file_mgr import KEEP


def create_image(path, width=40, height=20, color=Qt.red):
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(color)
    assert image.save(str(path))


def test_rotation_shortcuts_turn_view_left_and_right(window, app, tmpdir):
    image_path = tmpdir.join("image.png")
    create_image(image_path)
    window.prepare_for_file(str(image_path))

    QTest.keyClick(window, Qt.Key_L)
    app.processEvents()

    assert window.image_view.rotation_degrees == 270
    assert window.image_view.oriented_pixmap().size().width() == 20
    assert window.image_view.oriented_pixmap().size().height() == 40

    QTest.keyClick(window, Qt.Key_R)
    app.processEvents()

    assert window.image_view.rotation_degrees == 0
    assert window.image_view.oriented_pixmap().size().width() == 40
    assert window.image_view.oriented_pixmap().size().height() == 20


def test_rotation_shortcuts_work_in_full_screen(window, app, tmpdir):
    image_path = tmpdir.join("image.png")
    create_image(image_path)
    window.prepare_for_file(str(image_path))
    window.show_full_screen()
    app.processEvents()

    QTest.keyClick(window, Qt.Key_R)
    app.processEvents()

    assert window.image_view.rotation_degrees == 90


def test_rotation_does_not_change_file_or_review_state(window, app, tmpdir):
    image_path = tmpdir.join("image.png")
    create_image(image_path)
    window.prepare_for_file(str(image_path))
    window.mgr.set_current_review_state(KEEP)
    original_contents = image_path.read_binary()

    QTest.keyClick(window, Qt.Key_R)
    app.processEvents()

    assert window.mgr.current_file() == str(image_path)
    assert window.mgr.get_current_review_state() == KEEP
    assert image_path.read_binary() == original_contents


def test_navigation_discards_rotation_state(window, app, tmpdir):
    first = tmpdir.join("a.png")
    second = tmpdir.join("b.png")
    create_image(first, color=Qt.red)
    create_image(second, color=Qt.blue)
    window.prepare_for_file(str(first))
    QTest.keyClick(window, Qt.Key_L)
    app.processEvents()
    assert window.image_view.rotation_degrees == 270

    QTest.keyClick(window, Qt.Key_Right)
    app.processEvents()

    assert window.mgr.current_file() == str(second)
    assert window.image_view.rotation_degrees == 0
