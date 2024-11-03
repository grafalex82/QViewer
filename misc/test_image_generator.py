import sys
from PyQt5.QtGui import QImage, QPainter, QColor, QPen, QFont, QGuiApplication
from PyQt5.QtCore import Qt

# Set image size and grid parameters
width, height = 2000, 2000
grid_step = 100
grid_color = QColor(200, 200, 200)  # Grey color
label_interval = 200

# We need to use QGuiApplication to make fonts to work
app = QGuiApplication(sys.argv)

grid_pen = QPen(grid_color, 1, Qt.SolidLine)
label_pen = QPen(Qt.green)

# Create a new QImage with a white background
image = QImage(width, height, QImage.Format_ARGB32)
image.fill(Qt.black)

# Initialize QPainter to draw on the image
painter = QPainter(image)

# Set font for position labels
font = QFont("Arial", 10)
painter.setFont(font)

print("Painting verticals")
# Draw vertical grid lines and labels
for x in range(0, width, grid_step):
    painter.setPen(grid_pen)
    painter.drawLine(x, 0, x, height)
    # Add position labels every 200 pixels
    if x % label_interval == 0:
        for y in range(0, height, label_interval):
            # Save the current painter state
            painter.save()
            # Move to position, rotate, and draw text vertically
            painter.translate(x + 15, y + 70)  # Move to desired position
            painter.rotate(-90)           # Rotate text 90 degrees counterclockwise
            painter.setPen(label_pen)
            painter.drawText(0, 0, str(x))  # Draw text at the transformed position
            # Restore painter to previous state
            painter.restore()

print("Painting horizontals")
# Draw horizontal grid lines and labels
for y in range(0, height, grid_step):
    painter.setPen(grid_pen)
    painter.drawLine(0, y, width, y)
    # Add position labels every 200 pixels
    if y % label_interval == 0:
        for x in range(0, width, label_interval):
            painter.setPen(label_pen)
            painter.drawText(x + 35, y + 15, str(y))

# Finalize painting
painter.end()

print("Done")

# Save the image to a PNG file
image.save("grid_image.png", "PNG")

app.quit()