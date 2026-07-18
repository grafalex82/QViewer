import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow

from file_mgr import FileMgr
from image_view import ImageView


class ImageViewerMainWindow(QMainWindow):
    """Coordinate QViewer's UI, file navigation, and application actions.

    The main window connects ``FileMgr`` and ``ImageView``, builds menus and
    keyboard shortcuts, loads the selected image, and manages transitions
    between normal and full-screen viewing modes.
    """

    def __init__(self, image_path=None):
        super().__init__()

        # Flags and variables
        self.fit_to_window = True
        self.mgr = FileMgr()
        self.maximized = False

        self.init_ui()
        self.create_menu()

        self.prepare_for_path(image_path)

    def init_ui(self):
        self.setWindowTitle("Image Viewer")

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
        self.addAction(prev_action)

        next_action = QAction("Next Image", self)
        next_action.setShortcut("Right")
        next_action.triggered.connect(self.next_image)
        view_menu.addAction(next_action)
        self.addAction(next_action)

        first_action = QAction("First Image", self)
        first_action.setShortcut("Home")
        first_action.triggered.connect(self.first_image)
        view_menu.addAction(first_action)
        self.addAction(first_action)

        last_action = QAction("Last Image", self)
        last_action.setShortcut("End")
        last_action.triggered.connect(self.last_image)
        view_menu.addAction(last_action)
        self.addAction(last_action)

        prev_dir_action = QAction("Previous Directory", self)
        prev_dir_action.setShortcut("Ctrl+Left")
        prev_dir_action.triggered.connect(self.prev_dir)
        view_menu.addAction(prev_dir_action)
        self.addAction(prev_dir_action)

        next_dir_action = QAction("Next Directory", self)
        next_dir_action.setShortcut("Ctrl+Right")
        next_dir_action.triggered.connect(self.next_dir)
        view_menu.addAction(next_dir_action)
        self.addAction(next_dir_action)

        view_menu.addSeparator()

        self.fit_to_window_action = QAction("Fit to Window", self, checkable=True)
        self.fit_to_window_action.triggered.connect(self.set_fit_to_window)
        view_menu.addAction(self.fit_to_window_action)

        self.original_size_action = QAction(
            "1:1 (Original Size)", self, checkable=True
        )
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.prepare_for_file(file_path)

    def prepare_for_file(self, image_path):
        self.mgr.load_file(image_path)
        self.load_image(self.mgr.current_file())

    def prepare_for_path(self, image_path):
        self.mgr.load_path(image_path)
        self.load_image(self.mgr.current_file())

    def current_file_display_name(self):
        image_path = self.mgr.current_file()
        if not image_path:
            return None

        position, total = self.mgr.current_file_position()
        file_name = os.path.basename(image_path)
        return f"{file_name} ({position}/{total})"

    def load_image(self, image_path):
        display_name = self.current_file_display_name()
        self.setWindowTitle(display_name or "")

        if self.isFullScreen():
            self.image_view.show_file_name(display_name)

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
        self.fit_to_window_action.setChecked(
            self.image_view.zoom_mode == ImageView.ZOOM_FIT_TO_WINDOW
        )
        self.original_size_action.setChecked(
            self.image_view.zoom_mode == ImageView.ZOOM_1_TO_1
        )

    def prev_image(self):
        if self.mgr.prev():
            self.load_image(self.mgr.current_file())

    def next_image(self):
        if self.mgr.next():
            self.load_image(self.mgr.current_file())

    def first_image(self):
        if self.mgr.first():
            self.load_image(self.mgr.current_file())

    def last_image(self):
        if self.mgr.last():
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
        self.image_view.show_file_name(self.current_file_display_name())
        self.showFullScreen()

    def show_normal(self):
        if self.maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self.showMaximized()
        else:
            self.showNormal()
        self.menuBar().setVisible(True)
        self.image_view.show_file_name(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_F:
            self.toggle_full_screen()

        # Allow 'Escape' key to exit full screen
        if event.key() == Qt.Key_Escape:
            self.show_normal()
