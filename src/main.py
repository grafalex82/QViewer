import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from file_mgr import FileMgr

class ImageLoaderApp(QMainWindow):
    def __init__(self, image_path=None):
        super().__init__()

        self.init_ui()
        self.create_menu()

        self.mgr = FileMgr()
        if image_path:
            self.load_image(image_path)


    def init_ui(self):
        self.setWindowTitle('Image Viewer')

        self.label = QLabel()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)
        self.setCentralWidget(self.scroll_area)

        self.resize(800, 600)


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
        prev_dir_action.setShortcut("Ctrl-Left")
        prev_dir_action.triggered.connect(self.prev_dir)
        view_menu.addAction(prev_dir_action)

        next_dir_action = QAction("Next Directory", self)
        next_dir_action.setShortcut("Ctrl-Right")
        next_dir_action.triggered.connect(self.next_dir)
        view_menu.addAction(next_dir_action)


    def open_file(self):
        # Open a file dialog to select an image
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.load_image(file_path)


    def load_image(self, image_path):
        self.mgr.load_file(image_path)
        self.display_image(image_path)


    def display_image(self, image_path):
        # Load and display the image
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Failed to load image.")
            return

        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignCenter)


    def prev_image(self):
        if self.mgr.prev():
            self.display_image(self.mgr.current_file())


    def next_image(self):
        if self.mgr.next():
            self.display_image(self.mgr.current_file())


    def prev_dir(self):
        if self.mgr.prev_dir():
            self.display_image(self.mgr.current_file())


    def next_dir(self):
        if self.mgr.next_dir():
            self.display_image(self.mgr.current_file())


if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    app = QApplication(sys.argv)
    window = ImageLoaderApp(image_path)
    window.show()
    sys.exit(app.exec_())
