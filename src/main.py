import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from file_mgr import FileMgr


class ImageSurface(QLabel):
    zoom_to_selection_signal = pyqtSignal(QRect, name='zoom_to_selection')

    def __init__(self):
        super().__init__()

        # Adjust look
        self.setStyleSheet("background-color: black")
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)

        self.reset_selection()

    def reset_selection(self):
        self.is_selecting = False
        self.selection_start = QPoint()
        self.selection_rect = QRect()

    def pixmap_rect(self):
        rect = self.pixmap().rect()
        rect.moveCenter(self.rect().center())
        return rect

    # Event handlers

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:   
            if self.selection_rect.contains(event.pos()):
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
        if self.is_selecting:
            self.selection_rect = self.pixmap_rect().intersected(QRect(self.selection_start, event.pos()))
            self.update()
        else:
            if self.selection_rect.contains(event.pos()):
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False

    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_selecting:
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceXorDestination)
            painter.setPen(QPen(Qt.white, 3, Qt.DashLine))
            painter.drawRect(self.selection_rect)



class ImageView(QScrollArea):
    ZOOM_UNSET          = 0
    ZOOM_1_TO_1         = 1
    ZOOM_FIT_TO_WINDOW  = 2

    def __init__(self):
        super().__init__()

        self.surface = ImageSurface()
        self.setWidgetResizable(True)
        self.setWidget(self.surface)

        self.surface.zoom_to_selection.connect(self.zoom_to_selection)

        # Flags and variables
        self.scale_factor = 1.
        self.zoom_mode = self.ZOOM_FIT_TO_WINDOW
        self.zoom_changed = False


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
        self.scale_factor = 1.
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
        self.scale_factor = 1.
        self.zoom_changed = False
        self.resize_image()
            
    def resize_image(self):
        if not self.pixmap:
            return

        if self.zoom_mode == self.ZOOM_FIT_TO_WINDOW and not self.zoom_changed:
            factor_h = float(self.size().height()) / self.pixmap.size().height()
            factor_w = float(self.size().width()) / self.pixmap.size().width()
            self.scale_factor = min(factor_h, factor_w)
            scaled_pixmap = self.pixmap.scaled(self.size().shrunkBy(QMargins(1, 1, 1, 1)),
                                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaled_size = self.pixmap.size() * self.scale_factor
            scaled_pixmap = self.pixmap.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        print(f"Original size: {self.pixmap.size()}")
        print(f"Scaled size: {scaled_pixmap.size()}")
        self.surface.setPixmap(scaled_pixmap)
        self.surface.adjustSize()

    @pyqtSlot(QRect)
    def zoom_to_selection(self, rect):
        print()
        rect = rect.normalized()
        print(f"Zoom to selection: {rect}")
        print(f"Current scale factor: {self.scale_factor}")
        print(f"Zoom rect in Image coordinates: {rect.topLeft() / self.scale_factor} ({rect.size() / self.scale_factor})")

        center = rect.center() / self.scale_factor
        size = rect.size() / self.scale_factor
        print(f"Zoom center: {center}")

        # TODO Remove
        sb = self.horizontalScrollBar()
        print(f"Scroll Bar: {sb.minimum()}/{sb.value()}/{sb.maximum()} ({sb.pageStep()})")

        # Calculate new scale factor
        factor_h = float(rect.size().height()) / self.size().height()
        factor_w = float(rect.size().width()) / self.size().width()
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
        print(f"Screen size: {self.size()}")
        size_diff = self.size() - new_size

        x = (center.x() - size.width() / 2) * self.scale_factor - size_diff.width() / 2
        y = (center.y() - size.height() / 2) * self.scale_factor - size_diff.height() / 2
        print(f"Scroll To: {x}, {y}")
        self.horizontalScrollBar().setSliderPosition(int(x))
        self.verticalScrollBar().setSliderPosition(int(y))

        # TODO Remove
        sb = self.horizontalScrollBar()
        print(f"Scroll Bar: {sb.minimum()}/{sb.value()}/{sb.maximum()} ({sb.pageStep()})")


class ImageViewerApp(QMainWindow):
    def __init__(self, image_path=None):
        super().__init__()

        # Flags and variables
        self.fit_to_window = True
        self.mgr = FileMgr()
        self.maximized = False

        self.init_ui()
        self.create_menu()

        self.prepare_for_file(image_path)


    def init_ui(self):
        self.setWindowTitle('Image Viewer')

        self.image_view = ImageView()
        self.setCentralWidget(self.image_view)

        self.resize(800, 600)
        self.setMinimumSize(640, 480)


    def create_menu(self):
        # Create the main menu bar
        menu_bar = self.menuBar()

        # Create the File menu
        file_menu = menu_bar.addMenu("File")

        # Create "Open File" action
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Create "Exit" action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create the View menu
        view_menu = menu_bar.addMenu("View")

        # Create navigation actions
        prev_action = QAction("Previous Image", self)
        prev_action.setShortcut("Left")
        prev_action.triggered.connect(self.prev_image)
        view_menu.addAction(prev_action)

        next_action = QAction("Next Image", self)
        next_action.setShortcut("Right")
        next_action.triggered.connect(self.next_image)
        view_menu.addAction(next_action)

        prev_dir_action = QAction("Previous Directory", self)
        prev_dir_action.setShortcut("Ctrl+Left")
        prev_dir_action.triggered.connect(self.prev_dir)
        view_menu.addAction(prev_dir_action)

        next_dir_action = QAction("Next Directory", self)
        next_dir_action.setShortcut("Ctrl+Right")
        next_dir_action.triggered.connect(self.next_dir)
        view_menu.addAction(next_dir_action)

        view_menu.addSeparator()

        self.fit_to_window_action = QAction("Fit to Window", self, checkable=True)
        self.fit_to_window_action.triggered.connect(self.set_fit_to_window)
        view_menu.addAction(self.fit_to_window_action)
        
        self.original_size_action = QAction("1:1 (Original Size)", self, checkable=True)
        self.original_size_action.triggered.connect(self.set_original_size)
        view_menu.addAction(self.original_size_action)

        full_screen_action = QAction("Toggle Full screen", self)
        full_screen_action.setShortcut("F")
        full_screen_action.triggered.connect(self.toggle_full_screen)
        view_menu.addAction(full_screen_action)

        self.update_zoom_menus()

        view_menu.addSeparator()

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("+")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

    # File operations

    def open_file(self):
        # Open a file dialog to select an image
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.prepare_for_file(file_path)


    def prepare_for_file(self, image_path):
        self.mgr.load_file(image_path)
        self.load_image(self.mgr.current_file())


    def load_image(self, image_path):
        if image_path:
            file_name = os.path.basename(image_path)
            self.setWindowTitle(file_name)
        else:
            self.setWindowTitle("")

        self.image_view.load_image(image_path)


    # Actions    

    def set_fit_to_window(self):
        self.image_view.set_fit_to_window()
        self.update_zoom_menus()


    def set_original_size(self):
        self.image_view.set_original_size()
        self.update_zoom_menus()


    def zoom_in(self):
        self.image_view.zoom_in()
        self.update_zoom_menus()


    def zoom_out(self):
        self.image_view.zoom_out()
        self.update_zoom_menus()


    def update_zoom_menus(self):
        self.fit_to_window_action.setChecked(self.image_view.zoom_mode == ImageView.ZOOM_FIT_TO_WINDOW)
        self.original_size_action.setChecked(self.image_view.zoom_mode == ImageView.ZOOM_1_TO_1)


    def prev_image(self):
        if self.mgr.prev():
            self.load_image(self.mgr.current_file())


    def next_image(self):
        if self.mgr.next():
            self.load_image(self.mgr.current_file())


    def prev_dir(self):
        if self.mgr.prev_dir():
            self.load_image(self.mgr.current_file())


    def next_dir(self):
        if self.mgr.next_dir():
            self.load_image(self.mgr.current_file())


    def toggle_full_screen(self):
        if self.isFullScreen():
            self.show_normal()
        else:
            self.maximized = self.isMaximized()
            self.show_full_screen()


    def show_full_screen(self):
        self.menuBar().setVisible(False)
        self.showFullScreen()


    def show_normal(self):
        if self.maximized:
            print("Show Maximized")
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self.showMaximized()
        else:
            print("Show Normal")
            self.showNormal()
        self.menuBar().setVisible(True)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_F:
            self.toggle_full_screen()

        # Allow 'Escape' key to exit full screen
        if event.key() == Qt.Key_Escape:
            self.show_normal()


if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    app = QApplication(sys.argv)
    window = ImageViewerApp(image_path)
    window.show()
    sys.exit(app.exec_())
