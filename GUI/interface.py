import sys
import cv2
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QStackedWidget, QLabel
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QTimer

# ---- PANTALLA DE INICIO ----
class StartScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Cargar la imagen de fondo
        self.background_image = QPixmap("resources/start.png")

        # Botón START
        self.start_button = QPushButton("", self)
        self.start_button.setGeometry(500, 620, 900, 150)  # Ajusta la posición si es necesario
        self.start_button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Transparente
        self.start_button.clicked.connect(self.start_app)

    def paintEvent(self, event):
        # Dibujar la imagen de fondo
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

        # Dibujar un círculo rojo en la posición del botón
        painter.setPen(QColor(255, 0, 0))  # Color rojo
        painter.setBrush(QColor(255, 0, 0, 100))  # Relleno rojo semitransparente
        painter.drawEllipse(500, 620, 900, 150)  # Dibuja un círculo en la posición del botón

    def start_app(self):
        self.main_window.setCurrentIndex(1)  # Cambia a la pantalla principal

# ---- PANTALLA PRINCIPAL ----
class MainScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Cargar la imagen de fondo
        self.background_image = QPixmap("resources/main.png")

        # Botón FINISH para volver al inicio
        self.finish_button = QPushButton("", self)
        self.finish_button.setGeometry(920, 500, 80, 80)
        self.finish_button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.finish_button.clicked.connect(self.finish_app)

        # Label para mostrar la cámara
        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(100, 100, 640, 480)  # Ajusta la posición y tamaño según sea necesario

        # Iniciar la cámara
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)  # Actualizar cada 20 ms

    def paintEvent(self, event):
        # Dibujar la imagen de fondo
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

        # Dibujar círculos rojos en las posiciones de los botones
        painter.setPen(QColor(255, 0, 0))  # Color rojo
        painter.setBrush(QColor(255, 0, 0, 100))  # Relleno rojo semitransparente
        painter.drawEllipse(1750, 830, 120, 120)  # Dibuja un círculo en la posición del botón FINISH

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))

    def finish_app(self):
        self.timer.stop()
        self.capture.release()
        self.main_window.setCurrentIndex(0)  # Vuelve a la pantalla de inicio

# ---- MAIN ----
class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()

        # Crear pantallas
        self.start_screen = StartScreen(self)
        self.main_screen = MainScreen(self)

        # Agregar pantallas al stacked widget
        self.addWidget(self.start_screen)
        self.addWidget(self.main_screen)

        # Mostrar la pantalla de inicio
        self.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()  # Muestra la ventana maximizada pero no en pantalla completa
    sys.exit(app.exec_())