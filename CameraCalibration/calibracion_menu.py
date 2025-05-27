from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QThread
import cv2
import numpy as np
import os
import sys

# Configuración
output_dir = "calib_images"
chessboard_size = (6, 7)

class CameraCapture(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Captura de imágenes de calibración")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel("Cargando cámara...")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        os.makedirs(output_dir, exist_ok=True)

        print("🔄 Intentando abrir la cámara...")
        self.cap = cv2.VideoCapture(2)  # Cambia a 0 o 1 si tu cámara está en otro índice
        if not self.cap.isOpened():
            print("❌ No se pudo abrir la cámara")
            sys.exit(1)
        else:
            print("✅ Cámara abierta correctamente")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.latest_frame = None
        self.pattern_found = False

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret_chess, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

        display = frame.copy()
        if ret_chess:
            cv2.drawChessboardCorners(display, chessboard_size, corners, ret_chess)
            self.pattern_found = True
        else:
            self.pattern_found = False

        self.latest_frame = frame
        img_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        qimg = QImage(img_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qimg))

    def capturar(self):
        if self.latest_frame is None or not self.pattern_found:
            print("⚠️ No se detectó el patrón del tablero.")
            return

        img_count = len(os.listdir(output_dir)) + 1
        filename = os.path.join(output_dir, f"calib_{img_count:03d}.jpg")
        cv2.imwrite(filename, self.latest_frame)
        print(f"✅ Imagen {img_count} guardada en '{filename}'")

    def closeEvent(self, event):
        print("🔒 Cerrando cámara y saliendo...")
        self.cap.release()
        event.accept()

class TerminalListener(QThread):
    def __init__(self, camera_widget):
        super().__init__()
        self.camera = camera_widget

    def run(self):
        print("\n📷 Comandos disponibles:\n  [c] Capturar imagen\n  [q] Salir\n")
        while True:
            cmd = input("> ").strip().lower()
            if cmd == 'c':
                self.camera.capturar()
            elif cmd == 'q':
                QApplication.quit()
                break
            else:
                print("❓ Comando no reconocido. Usa 'c' o 'q'.")

def capturar_imagenes():
    app = QApplication(sys.argv)
    camera_widget = CameraCapture()
    camera_widget.show()

    listener = TerminalListener(camera_widget)
    listener.start()

    sys.exit(app.exec_())

if __name__ == "__main__":
    capturar_imagenes()
