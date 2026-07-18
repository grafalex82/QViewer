from PyQt5.QtCore import QMargins, QRect, Qt, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QScrollArea

from image_surface import ImageSurface


class ImageView(QScrollArea):
    """Display an image and manage its zoom and scrolling behavior.

    This widget owns the ``ImageSurface``, loads image pixmaps, scales them for
    fit-to-window or original-size viewing, and translates selection-based zoom
    requests into updated scale and scroll positions.
    """

    ZOOM_UNSET = 0
    ZOOM_1_TO_1 = 1
    ZOOM_FIT_TO_WINDOW = 2

    def __init__(self):
        super().__init__()

        self.pixmap = None
        self.surface = ImageSurface()
        self.setWidgetResizable(True)
        self.setWidget(self.surface)

        self.surface.zoom_to_selection.connect(self.zoom_to_selection)

        # Flags and variables
        self.scale_factor = 1.0
        self.zoom_mode = self.ZOOM_FIT_TO_WINDOW
        self.zoom_changed = False


    def show_file_name(self, file_name):
        self.surface.show_file_name(file_name)


    def set_scroll_bars_visible(self, visible):
        policy = Qt.ScrollBarAsNeeded if visible else Qt.ScrollBarAlwaysOff
        self.setHorizontalScrollBarPolicy(policy)
        self.setVerticalScrollBarPolicy(policy)


    def load_image(self, image_path):
        if not image_path:
            self.pixmap = None
            return

        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            print("Failed to load image.")
            return

        self.reset_zoom()
        self.surface.reset_selection()

    # Events
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_image()

    # Zoom methods

    def set_fit_to_window(self):
        self.zoom_mode = self.ZOOM_FIT_TO_WINDOW
        self.zoom_changed = False
        self.resize_image()


    def set_original_size(self):
        self.zoom_mode = self.ZOOM_1_TO_1
        self.zoom_changed = False
        self.scale_factor = 1.0
        self.resize_image()


    def zoom_in(self):
        self.zoom_changed = True
        self.scale_factor *= 1.25
        self.resize_image()


    def zoom_out(self):
        self.zoom_changed = True
        self.scale_factor /= 1.25
        self.resize_image()


    def reset_zoom(self):
        self.scale_factor = 1.0
        self.zoom_changed = False
        self.resize_image()


    def resize_image(self):
        if not self.pixmap:
            return

        viewport_size = self.viewport().size()
        if self.zoom_mode == self.ZOOM_FIT_TO_WINDOW and not self.zoom_changed:
            factor_h = float(viewport_size.height()) / self.pixmap.size().height()
            factor_w = float(viewport_size.width()) / self.pixmap.size().width()
            self.scale_factor = min(factor_h, factor_w)
            scaled_pixmap = self.pixmap.scaled(
                viewport_size.shrunkBy(QMargins(1, 1, 1, 1)),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        else:
            scaled_size = self.pixmap.size() * self.scale_factor
            scaled_pixmap = self.pixmap.scaled(
                scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        print(f"Original size: {self.pixmap.size()}")
        print(f"Scaled size: {scaled_pixmap.size()}")
        self.surface.setPixmap(scaled_pixmap)
        self.surface.adjustSize()

    @pyqtSlot(QRect)
    def zoom_to_selection(self, rect):
        rect = rect.normalized()
        if not self.pixmap or rect.isEmpty():
            return

        viewport_size = self.viewport().size()
        if viewport_size.isEmpty():
            return

        print()
        print(f"Zoom to selection: {rect}")
        print(f"Current scale factor: {self.scale_factor}")
        print(
            "Zoom rect in Image coordinates: "
            f"{rect.topLeft() / self.scale_factor} ({rect.size() / self.scale_factor})"
        )

        center = rect.center() / self.scale_factor
        size = rect.size() / self.scale_factor
        print(f"Zoom center: {center}")

        # TODO Remove
        sb = self.horizontalScrollBar()
        print(f"Scroll Bar: {sb.minimum()}/{sb.value()}/{sb.maximum()} ({sb.pageStep()})")

        # Calculate new scale factor
        factor_h = float(rect.size().height()) / viewport_size.height()
        factor_w = float(rect.size().width()) / viewport_size.width()
        extra_scale = max(factor_h, factor_w)
        self.scale_factor /= extra_scale
        self.zoom_changed = True
        self.resize_image()

        print(f"New scale factor: {self.scale_factor}")

        # Scroll to position
        new_size = size * self.scale_factor
        print(f"New screen Size: {new_size}")
        new_center = center * self.scale_factor
        print(f"New center: {new_center}")
        print(f"Screen size: {viewport_size}")
        size_diff = viewport_size - new_size

        x = (
            (center.x() - size.width() / 2) * self.scale_factor
            - size_diff.width() / 2
        )
        y = (
            (center.y() - size.height() / 2) * self.scale_factor
            - size_diff.height() / 2
        )
        print(f"Scroll To: {x}, {y}")
        self.horizontalScrollBar().setSliderPosition(int(x))
        self.verticalScrollBar().setSliderPosition(int(y))

        # TODO Remove
        sb = self.horizontalScrollBar()
        print(f"Scroll Bar: {sb.minimum()}/{sb.value()}/{sb.maximum()} ({sb.pageStep()})")
