import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMessageBox

from file_mgr import (
    DISCARD_DIRECTORY_NAME,
    KEEP,
    REJECT,
    UNDECIDED,
    FileMgr,
)
from image_view import ImageView


class ImageViewerMainWindow(QMainWindow):
    """Coordinate QViewer's UI, file navigation, and application actions.

    The main window connects ``FileMgr`` and ``ImageView``, builds menus and
    keyboard shortcuts, loads the selected image, and manages transitions
    between normal and full-screen viewing modes.
    """

    MAX_REPORTED_DISCARD_FAILURES = 10
    MAX_DISCARD_ERROR_LENGTH = 160

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

        prev_keep_action = QAction("Previous Keep Image", self)
        prev_keep_action.setShortcut("Shift+Left")
        prev_keep_action.triggered.connect(self.prev_keep_image)
        view_menu.addAction(prev_keep_action)
        self.addAction(prev_keep_action)

        next_keep_action = QAction("Next Keep Image", self)
        next_keep_action.setShortcut("Shift+Right")
        next_keep_action.triggered.connect(self.next_keep_image)
        view_menu.addAction(next_keep_action)
        self.addAction(next_keep_action)

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
        self.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        self.addAction(zoom_out_action)

        # Create the Review menu. Register these actions on the main window as
        # well so their shortcuts remain active while the menu bar is hidden.
        review_menu = menu_bar.addMenu("Review")

        self.toggle_keep_action = QAction("Toggle Keep", self)
        self.toggle_keep_action.setShortcut("K")
        self.toggle_keep_action.triggered.connect(self.toggle_keep)
        review_menu.addAction(self.toggle_keep_action)
        self.addAction(self.toggle_keep_action)

        self.toggle_reject_action = QAction("Toggle Reject", self)
        self.toggle_reject_action.setShortcut("X")
        self.toggle_reject_action.triggered.connect(self.toggle_reject)
        review_menu.addAction(self.toggle_reject_action)
        self.addAction(self.toggle_reject_action)

        review_menu.addSeparator()

        self.keep_and_next_action = QAction("Keep and Next", self)
        self.keep_and_next_action.setShortcut("Ctrl+Up")
        self.keep_and_next_action.triggered.connect(
            lambda: self.set_review_state_and_next(KEEP)
        )
        review_menu.addAction(self.keep_and_next_action)
        self.addAction(self.keep_and_next_action)

        self.reject_and_next_action = QAction("Reject and Next", self)
        self.reject_and_next_action.setShortcut("Ctrl+Down")
        self.reject_and_next_action.triggered.connect(
            lambda: self.set_review_state_and_next(REJECT)
        )
        review_menu.addAction(self.reject_and_next_action)
        self.addAction(self.reject_and_next_action)

        review_menu.addSeparator()

        self.discard_current_action = QAction("Discard Current Image...", self)
        self.discard_current_action.setShortcut("Delete")
        self.discard_current_action.triggered.connect(self.discard_current)
        review_menu.addAction(self.discard_current_action)
        self.addAction(self.discard_current_action)

        self.delete_current_action = QAction("Delete Current Image...", self)
        self.delete_current_action.setShortcut("Shift+Delete")
        self.delete_current_action.triggered.connect(self.delete_current)
        review_menu.addAction(self.delete_current_action)
        self.addAction(self.delete_current_action)

        review_menu.addSeparator()

        self.discard_rejected_action = QAction("Discard Rejected...", self)
        self.discard_rejected_action.setShortcut("Ctrl+Delete")
        self.discard_rejected_action.triggered.connect(self.discard_rejected)
        review_menu.addAction(self.discard_rejected_action)
        self.addAction(self.discard_rejected_action)

        self.keep_only_marked_action = QAction("Keep Only Marked...", self)
        self.keep_only_marked_action.setShortcut("Ctrl+Shift+Delete")
        self.keep_only_marked_action.triggered.connect(self.keep_only_marked)
        review_menu.addAction(self.keep_only_marked_action)
        self.addAction(self.keep_only_marked_action)

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
        full_path = os.path.abspath(image_path)
        display_name = f"{full_path} ({position}/{total})"
        state = self.mgr.get_current_review_state()
        state_markers = {
            KEEP: " [KEEP]",
            REJECT: " [REJECT]",
            UNDECIDED: "",
        }
        return display_name + state_markers[state]

    def refresh_current_file_display(self):
        display_name = self.current_file_display_name()
        self.setWindowTitle(display_name or "")

        if self.isFullScreen():
            self.image_view.show_file_name(display_name)

    def load_image(self, image_path):
        self.refresh_current_file_display()
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

    def prev_keep_image(self):
        if self.mgr.prev_keep():
            self.load_image(self.mgr.current_file())

    def next_keep_image(self):
        if self.mgr.next_keep():
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

    def toggle_keep(self):
        self.mgr.toggle_keep()
        self.refresh_current_file_display()

    def toggle_reject(self):
        self.mgr.toggle_reject()
        self.refresh_current_file_display()

    def set_review_state_and_next(self, state):
        if not self.mgr.current_file():
            return

        self.mgr.set_current_review_state(state)

        if self.mgr.next():
            self.load_image(self.mgr.current_file())
        else:
            self.refresh_current_file_display()

    def confirm_bulk_discard(
        self,
        operation_name,
        keep_count,
        reject_count,
        undecided_count,
        move_count,
        current_directory,
        proposed_quarantine_location,
    ):
        """Ask whether a bulk move into the quarantine folder should proceed."""
        if move_count == 0:
            QMessageBox.information(
                self,
                operation_name,
                "There is nothing to discard.",
            )
            return False

        image_word = "image" if move_count == 1 else "images"
        if operation_name == "Keep Only Marked":
            kept_word = "image" if keep_count == 1 else "images"
            question = f"Keep only the {keep_count} {kept_word} marked Keep?"
            moved_description = f"{move_count} {image_word} not marked Keep"
        else:
            question = (
                f"Move {move_count} rejected {image_word} out of the current folder?"
            )
            moved_description = f"The {move_count} rejected {image_word}"

        warning = ""
        if operation_name == "Keep Only Marked" and keep_count == 0:
            warning = (
                "WARNING: No images are marked Keep. Every managed image in the "
                "current directory will be moved.\n\n"
            )

        message = (
            f"{question}\n\n"
            f"Kept: {keep_count}\n"
            f"Rejected: {reject_count}\n"
            f"Undecided: {undecided_count}\n\n"
            f"{warning}"
            f"{moved_description} will be moved into:\n"
            f"{proposed_quarantine_location}"
        )
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(operation_name)
        dialog.setText(message)
        continue_button = dialog.addButton("Continue", QMessageBox.AcceptRole)
        cancel_button = dialog.addButton(QMessageBox.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.exec_()
        return dialog.clickedButton() is continue_button

    def confirm_current_file_action(self, operation_name, image_path, permanent=False):
        """Confirm moving or permanently deleting the current image."""
        if not image_path:
            return False

        if permanent:
            question = (
                "Permanently delete this image from disk?\n\n"
                f"{os.path.abspath(image_path)}\n\n"
                "This action cannot be undone."
            )
            button_text = "Delete"
        else:
            question = (
                "Move this image to the discarded files folder?\n\n"
                f"{os.path.abspath(image_path)}"
            )
            button_text = "Discard"

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(operation_name)
        dialog.setText(question)
        continue_button = dialog.addButton(button_text, QMessageBox.DestructiveRole)
        cancel_button = dialog.addButton(QMessageBox.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.exec_()
        return dialog.clickedButton() is continue_button

    def report_discard_failures(self, operation_name, result):
        """Show the files that could not be moved by a bulk operation."""
        if not result.failed:
            return

        visible_failures = result.failed[: self.MAX_REPORTED_DISCARD_FAILURES]
        details = []
        for source, reason in visible_failures:
            concise_reason = str(reason).replace("\r", " ").replace("\n", " ")
            if len(concise_reason) > self.MAX_DISCARD_ERROR_LENGTH:
                concise_reason = (
                    concise_reason[: self.MAX_DISCARD_ERROR_LENGTH - 3] + "..."
                )
            source_name = os.path.basename(os.fspath(source))
            details.append(f"{source_name}: {concise_reason}")

        omitted_count = len(result.failed) - len(visible_failures)
        if omitted_count:
            details.append(f"...and {omitted_count} more failure(s).")

        moved_count = len(result.moved)
        moved_word = "file" if moved_count == 1 else "files"
        QMessageBox.warning(
            self,
            f"{operation_name} - Move Failures",
            f"Moved {moved_count} {moved_word} successfully.\n\n"
            f"The following files could not be moved:\n\n"
            + "\n".join(details),
        )

    def report_discard_success(self, operation_name, result):
        """Report a completed bulk move in an information dialog."""
        moved_count = len(result.moved)
        moved_word = "file" if moved_count == 1 else "files"
        QMessageBox.information(
            self,
            f"{operation_name} - Complete",
            f"Moved {moved_count} {moved_word}.\n\n"
            f"Quarantine session:\n{result.destination}",
        )

    def run_bulk_discard(
        self,
        operation_name,
        candidates,
        empty_message="There is nothing to discard.",
    ):
        """Confirm and run a bulk discard operation for *candidates*."""
        if not candidates:
            QMessageBox.information(self, operation_name, empty_message)
            return None

        counts = self.mgr.current_review_counts()
        directory = self.mgr.current_directory()
        quarantine = (
            os.path.join(directory, DISCARD_DIRECTORY_NAME) + os.sep
            if directory is not None
            else DISCARD_DIRECTORY_NAME + os.sep
        )
        if not self.confirm_bulk_discard(
            operation_name,
            counts[KEEP],
            counts[REJECT],
            counts[UNDECIDED],
            len(candidates),
            directory,
            quarantine,
        ):
            return None

        result = self.mgr.move_to_discard_directory(candidates)
        self.load_image(self.mgr.current_file())
        if result.failed:
            self.report_discard_failures(operation_name, result)
        else:
            self.report_discard_success(operation_name, result)
        return result

    def discard_rejected(self):
        """Move rejected images in the current directory after confirmation."""
        return self.run_bulk_discard(
            "Discard Rejected",
            self.mgr.current_rejected_files(),
            "Nothing in the current directory is marked Reject.",
        )

    def discard_current(self):
        """Move the current image into quarantine after confirmation."""
        current_file = self.mgr.current_file()
        if not current_file or not self.confirm_current_file_action(
            "Discard Current Image", current_file
        ):
            return None

        result = self.mgr.move_to_discard_directory([current_file])
        self.load_image(self.mgr.current_file())
        if result.failed:
            self.report_discard_failures("Discard Current Image", result)
        return result

    def delete_current(self):
        """Permanently delete the current image after confirmation."""
        current_file = self.mgr.current_file()
        if not current_file or not self.confirm_current_file_action(
            "Delete Current Image", current_file, permanent=True
        ):
            return None

        try:
            deleted = self.mgr.delete_current_file()
        except OSError as error:
            QMessageBox.warning(
                self,
                "Delete Current Image - Failed",
                f"Could not delete {os.path.basename(current_file)}:\n\n{error}",
            )
            return None

        self.load_image(self.mgr.current_file())
        return deleted

    def keep_only_marked(self):
        """Move rejected and undecided images after confirmation."""
        return self.run_bulk_discard(
            "Keep Only Marked",
            self.mgr.current_not_kept_files(),
            "There is nothing to discard.",
        )

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.show_normal()
        else:
            self.maximized = self.isMaximized()
            self.show_full_screen()

    def show_full_screen(self):
        self.menuBar().setVisible(False)
        self.image_view.set_scroll_bars_visible(False)
        self.showFullScreen()
        self.refresh_current_file_display()

    def show_normal(self):
        if self.maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self.showMaximized()
        else:
            self.showNormal()
        self.menuBar().setVisible(True)
        self.image_view.set_scroll_bars_visible(True)
        self.image_view.show_file_name(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.show_normal()
            else:
                self.close()
            return

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_F:
            self.toggle_full_screen()
            return

        super().keyPressEvent(event)
