import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class CamaraWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cámara con Punto Central")

        # Layout
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Cámara
        self.cap = cv2.VideoCapture(2)
        if not self.cap.isOpened():
            raise Exception("No se pudo abrir la cámara.")

        # Timer para actualizar frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 fps

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Dibuja un punto rojo en el centro
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        cv2.circle(frame, center, 5, (0, 0, 255), -1)

        # Convertir a formato Qt
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)

        # Mostrar en el QLabel
        self.image_label.setPixmap(pix)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CamaraWidget()
    win.show()
    sys.exit(app.exec_())
