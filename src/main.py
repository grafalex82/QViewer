import sys

from PyQt5.QtWidgets import QApplication

from main_window import ImageViewerMainWindow

__all__ = ["ImageViewerMainWindow", "main"]


def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    app = QApplication(sys.argv)
    window = ImageViewerMainWindow(image_path)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
