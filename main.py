import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class ImageLoaderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Viewer')

        # Layout
        layout = QVBoxLayout()

        # Label to display the image
        self.imageLabel = QLabel(self)
        self.imageLabel.setText('No image loaded')
        layout.addWidget(self.imageLabel)

        # Button to load an image
        loadButton = QPushButton('Load Image', self)
        loadButton.clicked.connect(self.loadImage)
        layout.addWidget(loadButton)

        self.setLayout(layout)
        self.resize(800, 600)


    def loadImage(self):
        # Open a file dialog to select an image
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif)')
        
        if fileName:
            # Load the image and set it to the label
            pixmap = QPixmap(fileName)
            self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.size(), aspectRatioMode=1))  # Keep aspect ratio
            self.imageLabel.setText('')  # Clear the text

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageLoaderApp()
    window.show()
    sys.exit(app.exec_())
