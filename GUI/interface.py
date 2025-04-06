import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QPushButton, QWidget, QStackedWidget, 
                            QLabel, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QFont
from PyQt5.QtCore import Qt, QTimer

# ---- VALORES PREDEFINIDOS MODIFICABLES POR EL PROGRAMADOR ----
valores = {
    'box1': {'valor': 100, 'x': 1010, 'y': 180},
    'box2': {'valor': 200, 'x': 1010, 'y': 420},
    'box3': {'valor': 300, 'x': 1475, 'y': 180},
    'box4': {'valor': 400, 'x': 1475, 'y': 420},
    'boxRed': {'valor': 'Red', 'x': 240, 'y': 690}
}

# ---- PANTALLA DE INICIO ----
class StartScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Cargar la imagen de fondo
        self.background_image = QPixmap("resources/start.png")

        # Botón START
        self.start_button = QPushButton("", self)
        self.start_button.setGeometry(500, 620, 900, 150)
        self.start_button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.start_button.clicked.connect(self.start_app)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
        painter.setPen(QColor(255, 0, 0))
        painter.setBrush(QColor(255, 0, 0, 100))
        #painter.drawEllipse(500, 620, 900, 150)

    def start_app(self):
        self.main_window.setCurrentIndex(1)

# ---- PANTALLA PRINCIPAL ----
class MainScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Cargar la imagen de fondo
        self.background_image = QPixmap("resources/main.png")

        # Botón FINISH
        self.finish_button = QPushButton("", self)
        self.finish_button.setGeometry(920, 500, 80, 80)
        self.finish_button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.finish_button.clicked.connect(self.finish_app)

        # Label para la cámara
        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(100, 100, 640, 480)

        # Crear cajas de texto grandes en posiciones personalizadas
        self.create_value_boxes()

        # Iniciar la cámara
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def create_value_boxes(self):
        # Configuración común para todas las cajas
        font = QFont()
        font.setPointSize(20)  # Fuente grande
        
        for box_name, config in valores.items():
            box = QLineEdit(self)
            box.setText(str(config['valor']))
            box.setReadOnly(True)
            box.setGeometry(config['x'], config['y'], 100, 80)  # 10 veces más grande (200x50)
            box.setStyleSheet("""
                background-color: white;
                border: 2px solid black;
                font-size: 50px;
            """)
            box.setFont(font)
            setattr(self, box_name, box)  # Guardar referencia como atributo

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
        painter.setPen(QColor(255, 0, 0))
        painter.setBrush(QColor(255, 0, 0, 100))
        #painter.drawEllipse(1750, 830, 120, 120)

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
        self.main_window.setCurrentIndex(0)

# ---- MAIN ----
class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.start_screen = StartScreen(self)
        self.main_screen = MainScreen(self)
        self.addWidget(self.start_screen)
        self.addWidget(self.main_screen)
        self.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())