from datetime import datetime

import pytest
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from image_stats import (
    ImageStats,
    format_aspect_ratio,
    format_image_stats,
    read_image_stats,
)


@pytest.mark.parametrize(
    ("dimensions", "expected"),
    [
        ((2000, 1000), "2:1"),
        ((1920, 1080), "16:9"),
        ((1000, 667), "3:2"),
        ((1600, 1200), "4:3"),
        ((1080, 1920), "9:16"),
        ((1234, 1000), "617:500 (1.234)"),
    ],
)
def test_standard_aspect_ratios_are_detected(dimensions, expected):
    assert format_aspect_ratio(*dimensions) == expected


def test_jpeg_metadata_includes_file_image_and_exif_values(tmp_path):
    image_path = tmp_path / "metadata.jpg"
    exif = Image.Exif()
    exif[306] = "2025:01:02 03:04:05"
    exif[36867] = "2024:11:12 13:14:15"
    exif[36868] = "2024:11:12 13:14:16"
    Image.new("RGB", (120, 80), "blue").save(
        image_path,
        format="JPEG",
        dpi=(300, 150),
        exif=exif,
    )

    stats = read_image_stats(image_path)

    assert (stats.width, stats.height) == (120, 80)
    assert stats.compression_type == "JPEG"
    assert stats.dpi == pytest.approx((300, 150))
    assert stats.color_depth == 24
    assert stats.color_mode == "RGB"
    assert stats.file_size == image_path.stat().st_size
    assert stats.file_datetime is not None
    assert stats.capture_datetime == "2024:11:12 13:14:15"
    assert stats.other_exif_times == (
        ("DateTime", "2025:01:02 03:04:05"),
        ("DateTimeDigitized", "2024:11:12 13:14:16"),
    )


def test_png_metadata_reports_deflate_and_color_depth(tmp_path):
    image_path = tmp_path / "metadata.png"
    Image.new("RGBA", (40, 30), "red").save(image_path, dpi=(96, 96))

    stats = read_image_stats(image_path)

    assert stats.compression_type == "DEFLATE"
    assert stats.color_depth == 32
    assert stats.color_mode == "RGBA"
    assert stats.dpi == pytest.approx((96, 96), abs=0.02)


def test_image_stats_format_contains_static_and_live_values():
    stats = ImageStats(
        width=1920,
        height=1080,
        file_size=1_234_567,
        file_datetime=datetime(2026, 8, 25, 17, 45, 12),
        compression_type="JPEG",
        compression_level="90",
        dpi=(300, 300),
        color_depth=24,
        color_mode="RGB",
        capture_datetime="2026:08:24 12:13:14",
        other_exif_times=(("DateTimeDigitized", "2026:08:24 12:13:15"),),
    )

    text = format_image_stats(stats, 0.75, (1440, 810), (3, 12))

    assert text.splitlines() == [
        "Image resolution: 1920 x 1080 px",
        "Zoom factor: 75.0%",
        "Visible resolution: 1440 x 810 px",
        "Aspect ratio: 16:9",
        "Compression: JPEG, level 90",
        "DPI: 300 x 300",
        "Color depth: 24-bit (RGB)",
        "File size: 1,234,567 bytes",
        "File index: 3 / 12",
        "File date/time: 2026-08-25 17:45:12",
        "EXIF capture date/time: 2026:08:24 12:13:14",
        "EXIF DateTimeDigitized: 2026:08:24 12:13:15",
    ]


@pytest.mark.parametrize("full_screen", (False, True))
def test_i_toggles_bottom_right_image_stats_overlay(
    window, app, tmp_path, full_screen
):
    image_path = tmp_path / "image.png"
    Image.new("RGB", (640, 480), "white").save(image_path)
    window.prepare_for_file(str(image_path))
    label = window.image_view.image_stats_label
    if full_screen:
        window.show_full_screen()
        app.processEvents()

    QTest.keyClick(window, Qt.Key_I)
    app.processEvents()

    assert label.isVisible()
    assert label.parent() is window.image_view.viewport()
    assert label.x() + label.width() == window.image_view.viewport().width()
    assert label.y() + label.height() == window.image_view.viewport().height()
    assert "background-color: black" in label.styleSheet()
    assert "color: lightgreen" in label.styleSheet()
    assert "Image resolution: 640 x 480 px" in label.text()
    assert "File index: 1 / 1" in label.text()

    QTest.keyClick(window, Qt.Key_I)
    app.processEvents()

    assert not label.isVisible()


def test_image_stats_overlay_updates_and_remains_anchored_when_zoomed(
    window, app, tmp_path
):
    image_path = tmp_path / "image.png"
    Image.new("RGB", (1600, 1200), "white").save(image_path)
    window.prepare_for_file(str(image_path))
    QTest.keyClick(window, Qt.Key_I)
    app.processEvents()
    label = window.image_view.image_stats_label
    initial_text = label.text()

    window.image_view.zoom_in()
    app.processEvents()

    assert label.text() != initial_text
    assert f"Zoom factor: {window.image_view.scale_factor * 100:.1f}%" in label.text()
    displayed_width, displayed_height = window.image_view.displayed_image_size()
    assert (
        f"Visible resolution: {displayed_width} x {displayed_height} px"
        in label.text()
    )
    assert label.x() + label.width() == window.image_view.viewport().width()
    assert label.y() + label.height() == window.image_view.viewport().height()
