from unittest.mock import Mock


def test_long_window_title_is_trimmed_from_the_left(window, app):
    display_name = "C:/" + "very-long-directory/" * 20 + "image.jpg (2/10) [KEEP]"
    window.current_file_display_name = Mock(return_value=display_name)
    window.resize(640, 480)

    window.refresh_current_file_display()
    app.processEvents()

    visible_name = window.windowTitle()
    assert visible_name.startswith("…")
    assert display_name.endswith(visible_name[1:])
    assert window.fontMetrics().horizontalAdvance(visible_name) <= window.width()


def test_full_screen_file_name_is_trimmed_from_the_left_to_fit(window, app):
    view = window.image_view
    display_name = "C:/" + "very-long-directory/" * 100 + "image.jpg (1/1)"
    view.resize(640, 480)
    view.show_file_name(display_name)
    app.processEvents()

    visible_name = view.file_name_label.text()
    assert visible_name.startswith("…")
    assert display_name.endswith(visible_name[1:])
    assert view.file_name_label.width() <= view.viewport().width()


def test_full_screen_file_name_is_retrimmed_when_view_width_changes(window, app):
    view = window.image_view
    display_name = "C:/" + "long-directory/" * 50 + "image.jpg (1/1)"
    view.show_file_name(display_name)
    view.resize(700, 480)
    app.processEvents()
    wide_name = view.file_name_label.text()

    view.resize(640, 480)
    app.processEvents()

    narrow_name = view.file_name_label.text()
    assert len(narrow_name) < len(wide_name)
    assert display_name.endswith(narrow_name[1:])
