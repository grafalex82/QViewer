import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from file_mgr import FileMgr

class ImageLoaderApp(QMainWindow):
    def __init__(self, image_path=None):
        super().__init__()

        self.fit_to_window = True

        self.init_ui()
        self.create_menu()

        self.mgr = FileMgr()
        if image_path:
            self.prepare_for_file(image_path)


    def init_ui(self):
        self.setWindowTitle('Image Viewer')

        self.label = QLabel()
        self.label.setStyleSheet("background-color: black")
        self.label.setAlignment(Qt.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)
        self.setCentralWidget(self.scroll_area)

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

        self.fit_to_window_action = QAction("Fit to Window", self, checkable=True, checked=self.fit_to_window)
        self.fit_to_window_action.triggered.connect(self.set_fit_to_window)
        view_menu.addAction(self.fit_to_window_action)
        
        self.actual_size_action = QAction("1:1 (Actual Size)", self, checkable=True, checked=not self.fit_to_window)
        self.actual_size_action.triggered.connect(self.set_actual_size)
        view_menu.addAction(self.actual_size_action)    


    def open_file(self):
        # Open a file dialog to select an image
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.prepare_for_file(file_path)


    def prepare_for_file(self, image_path):
        self.mgr.load_file(image_path)
        self.load_image(self.mgr.current_file())


    def load_image(self, image_path):
        file_name = os.path.basename(image_path)
        self.setWindowTitle(file_name)

        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            print("Failed to load image.")
            return

        self.resize_image()


    def resize_image(self):
        if self.fit_to_window:
            # Scale the pixmap to fit the window while keeping the aspect ratio
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        else:
            # Display actual size (1:1)
            self.label.setPixmap(self.pixmap)
            self.label.adjustSize()


    def resizeEvent(self, event):
        # Handle window resize event
        self.resize_image()
        super().resizeEvent(event)


    def set_fit_to_window(self):
        self.fit_to_window = True
        self.fit_to_window_action.setChecked(True)
        self.actual_size_action.setChecked(False)
        self.resize_image()


    def set_actual_size(self):
        self.fit_to_window = False
        self.fit_to_window_action.setChecked(False)
        self.actual_size_action.setChecked(True)
        self.resize_image()


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


if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    app = QApplication(sys.argv)
    window = ImageLoaderApp(image_path)
    window.show()
    sys.exit(app.exec_())
