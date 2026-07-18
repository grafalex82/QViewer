from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QLabel


class ImageSurface(QLabel):
    """Paint the displayed image overlay and handle selection gestures.

    The surface is the low-level presentation widget used by ``ImageView``.
    It draws the optional file-name overlay, tracks rectangular mouse
    selections, and emits a zoom request when the user activates a selection.
    """

    zoom_to_selection_signal = pyqtSignal(QRect, name="zoom_to_selection")
    reset_zoom_signal = pyqtSignal(name="reset_zoom")
    pan_signal = pyqtSignal(QPoint, name="pan")

    def __init__(self):
        super().__init__()

        # Variables
        self.file_name = None
        self.panning_enabled = False
        self.is_panning = False
        self.pan_position = QPoint()

        # Adjust look
        self.setStyleSheet("background-color: black")
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)

        self.reset_selection()


    def show_file_name(self, file_name):
        self.file_name = file_name
        self.update()


    def reset_selection(self):
        self.is_selecting = False
        self.selection_start = QPoint()
        self.selection_rect = QRect()


    def set_panning_enabled(self, enabled):
        self.panning_enabled = enabled
        if not enabled:
            self.is_panning = False


    def pixmap_rect(self):
        rect = self.pixmap().rect()
        rect.moveCenter(self.rect().center())
        return rect

    # Event handlers

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.panning_enabled and event.modifiers() & Qt.ShiftModifier:
                self.is_panning = True
                self.pan_position = event.globalPos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            elif event.modifiers() & Qt.ControlModifier:
                self.reset_selection()
                self.reset_zoom_signal.emit()
            elif self.selection_rect.contains(event.pos()):
                # Handle click in a selected area, to trigger zoom to selection

                # First convert widget coordinates to image coordinates
                tl = self.pixmap_rect().topLeft()
                self.zoom_to_selection_signal.emit(self.selection_rect.translated(-tl))
                self.selection_rect = QRect()
            else:
                # Nothing was selected earlier, then probably this is a new selection
                self.is_selecting = True
                self.selection_start = event.pos()

            self.update()


    def mouseMoveEvent(self, event):
        if self.is_panning:
            position = event.globalPos()
            self.pan_signal.emit(position - self.pan_position)
            self.pan_position = position
        elif self.is_selecting:
            self.selection_rect = self.pixmap_rect().intersected(
                QRect(self.selection_start, event.pos())
            )
            self.update()
        else:
            if self.selection_rect.contains(event.pos()):
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
            elif self.is_selecting:
                self.is_selecting = False


    def paintEvent(self, event):
        # Draw image as usual
        super().paintEvent(event)

        if not self.is_selecting and not self.file_name:
            return

        painter = QPainter(self)

        # Draw zoom lasso
        if self.is_selecting:
            painter.save()
            painter.setCompositionMode(
                QPainter.CompositionMode.RasterOp_SourceXorDestination
            )
            painter.setPen(QPen(Qt.white, 3, Qt.DashLine))
            painter.drawRect(self.selection_rect)
            painter.restore()

        # Draw file name
        if self.file_name:
            # Measure text size
            painter.setFont(QFont("Arial", 12))
            text_rect = painter.boundingRect(
                0,
                0,
                self.width(),
                self.height(),
                Qt.TextSingleLine,
                self.file_name,
            )
            painter.setBrush(QBrush(QColor("black")))
            painter.drawRect(text_rect)

            # Draw the text
            painter.setPen(QColor("green"))
            painter.drawText(text_rect, Qt.TextSingleLine, self.file_name)
