"""Read and format metadata used by the image statistics overlay."""

import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction

from PIL import ExifTags, Image


@dataclass(frozen=True)
class ImageStats:
    """Metadata that does not change while an image is being viewed."""

    width: int
    height: int
    file_size: int | None = None
    file_datetime: datetime | None = None
    compression_type: str | None = None
    compression_level: str | None = None
    dpi: tuple[float, float] | None = None
    color_depth: int | None = None
    color_mode: str | None = None
    capture_datetime: str | None = None
    other_exif_times: tuple[tuple[str, str], ...] = field(default_factory=tuple)


STANDARD_ASPECT_RATIOS = (
    (1, 1),
    (5, 4),
    (4, 3),
    (3, 2),
    (16, 10),
    (16, 9),
    (2, 1),
    (21, 9),
)


def format_aspect_ratio(width, height):
    """Format integer pixel ``width`` and ``height`` as an aspect ratio.

    A familiar standard ratio is returned when the dimensions are within one
    percent of it; otherwise the exact reduced ratio and decimal value are
    returned.
    """
    if width <= 0 or height <= 0:
        return "N/A"

    ratio = float(width) / height
    candidates = STANDARD_ASPECT_RATIOS
    if ratio < 1:
        candidates = tuple(
            (height_part, width_part)
            for width_part, height_part in candidates
        )

    closest = min(
        candidates,
        key=lambda parts: abs(ratio - parts[0] / parts[1]),
    )
    closest_value = closest[0] / closest[1]
    if abs(ratio - closest_value) / closest_value <= 0.01:
        return f"{closest[0]}:{closest[1]}"

    reduced = Fraction(width, height)
    return f"{reduced.numerator}:{reduced.denominator} ({ratio:.3f})"


def _normalized_dpi(value):
    """Convert Pillow DPI metadata to a positive ``(x_dpi, y_dpi)`` tuple.

    ``value`` is the value from ``PIL.Image.Image.info["dpi"]``. Pillow may
    provide a two-item tuple/list or a single numeric value. Invalid, missing,
    non-finite, and non-positive values return ``None``.
    """
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        values = value[:2]
    elif isinstance(value, (int, float)):
        values = (value, value)
    else:
        return None

    try:
        dpi = tuple(float(component) for component in values)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    if not all(math.isfinite(component) and component > 0 for component in dpi):
        return None
    return dpi


def _color_depth(image):
    """Return the total bits per pixel for an open ``PIL.Image.Image``.

    The calculation uses ``image.mode`` and, for palette images, the optional
    ``image.info["bits"]`` value. Unknown modes return ``None``.
    """
    mode_depths = {
        "1": 1,
        "L": 8,
        "LA": 16,
        "P": image.info.get("bits", 8),
        "RGB": 24,
        "RGBA": 32,
        "RGBX": 32,
        "CMYK": 32,
        "YCbCr": 24,
        "I": 32,
        "F": 32,
        "I;16": 16,
        "I;16B": 16,
        "I;16L": 16,
    }
    depth = mode_depths.get(image.mode)
    try:
        return int(depth) if depth is not None else None
    except (TypeError, ValueError):
        return None


def _compression_details(image):
    """Return compression type and optional level for a Pillow image.

    ``image`` is an open ``PIL.Image.Image`` whose ``format`` and ``info``
    attributes have been populated by ``Image.open``. The result is a
    ``(compression_type, compression_level)`` tuple; either item may be
    ``None`` when the source format does not expose it.
    """
    image_format = (image.format or "").upper()
    if image_format in ("JPG", "JPEG"):
        compression_type = "JPEG"
        if image.info.get("progressive") or image.info.get("progression"):
            compression_type += " (progressive)"
    elif image_format == "PNG":
        compression_type = "DEFLATE"
    else:
        compression_type = str(image.info.get("compression") or image_format) or None

    level = image.info.get("compress_level")
    if level is None:
        level = image.info.get("quality")
    return compression_type, str(level) if level is not None else None


def _text_value(value):
    """Convert an EXIF metadata value to display text.

    ``value`` may be a byte string or any value with a useful string
    representation. Byte strings are decoded as UTF-8 with replacement for
    invalid bytes and have trailing NUL characters removed.
    """
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00")
    return str(value)


def _exif_times(image):
    """Extract date/time tags from an open ``PIL.Image.Image``.

    Returns ``(capture_datetime, other_times)``. ``capture_datetime`` is the
    EXIF ``DateTimeOriginal`` value or ``None``; ``other_times`` is a sorted
    tuple of ``(tag_name, value)`` pairs for the remaining date/time tags.
    """
    try:
        exif = image.getexif()
    except (AttributeError, OSError, SyntaxError, ValueError):
        return None, ()

    capture_datetime = None
    other_times = []
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        normalized_name = tag_name.lower()
        if not any(part in normalized_name for part in ("datetime", "date", "time")):
            continue

        text = _text_value(value)
        if tag_name == "DateTimeOriginal":
            capture_datetime = text
        else:
            other_times.append((tag_name, text))

    other_times.sort(key=lambda item: item[0])
    return capture_datetime, tuple(other_times)


def read_image_stats(image_path):
    """Read metadata for the image at path-like ``image_path``.

    The path is passed to both the operating-system file APIs and
    ``PIL.Image.open``. The function returns an ``ImageStats`` instance, or
    ``None`` when the path is empty, unreadable, or not a supported image.
    """
    if not image_path:
        return None

    try:
        file_size = os.path.getsize(image_path)
        file_datetime = datetime.fromtimestamp(os.path.getmtime(image_path))
    except OSError:
        file_size = None
        file_datetime = None

    try:
        with Image.open(image_path) as image:
            compression_type, compression_level = _compression_details(image)
            capture_datetime, other_exif_times = _exif_times(image)
            return ImageStats(
                width=image.width,
                height=image.height,
                file_size=file_size,
                file_datetime=file_datetime,
                compression_type=compression_type,
                compression_level=compression_level,
                dpi=_normalized_dpi(image.info.get("dpi")),
                color_depth=_color_depth(image),
                color_mode=image.mode,
                capture_datetime=capture_datetime,
                other_exif_times=other_exif_times,
            )
    except (OSError, SyntaxError, ValueError):
        return None


def _format_number(value):
    """Format numeric ``value`` with at most two decimal places."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def format_image_stats(stats, zoom_factor, visible_size, file_position):
    """Format an ``ImageStats`` instance and current view state for display.

    ``zoom_factor`` is a multiplier where ``1.0`` means 100 percent;
    ``visible_size`` is the displayed image's ``(width, height)`` in scroll-area
    pixels; and ``file_position`` is ``(one_based_index, directory_total)`` or
    ``None``. Passing ``None`` as ``stats`` returns an empty string.
    """
    if stats is None:
        return ""

    visible_width, visible_height = visible_size
    lines = [
        f"Image resolution: {stats.width} x {stats.height} px",
        f"Zoom factor: {zoom_factor * 100:.1f}%",
        f"Visible resolution: {visible_width} x {visible_height} px",
        f"Aspect ratio: {format_aspect_ratio(stats.width, stats.height)}",
    ]

    if stats.compression_type:
        compression = stats.compression_type
        if stats.compression_level is not None:
            compression += f", level {stats.compression_level}"
        lines.append(f"Compression: {compression}")
    if stats.dpi:
        dpi_x, dpi_y = stats.dpi
        lines.append(f"DPI: {_format_number(dpi_x)} x {_format_number(dpi_y)}")
    if stats.color_depth is not None:
        mode = f" ({stats.color_mode})" if stats.color_mode else ""
        lines.append(f"Color depth: {stats.color_depth}-bit{mode}")
    if stats.file_size is not None:
        lines.append(f"File size: {stats.file_size:,} bytes")
    if file_position:
        lines.append(f"File index: {file_position[0]} / {file_position[1]}")
    if stats.file_datetime:
        file_datetime = stats.file_datetime.isoformat(sep=" ", timespec="seconds")
        lines.append(f"File date/time: {file_datetime}")
    if stats.capture_datetime:
        lines.append(f"EXIF capture date/time: {stats.capture_datetime}")
    for name, value in stats.other_exif_times:
        lines.append(f"EXIF {name}: {value}")
    return "\n".join(lines)
