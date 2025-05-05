import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QLabel, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
from typing import Tuple

# ---- VALORES PREDEFINIDOS MODIFICABLES POR EL PROGRAMADOR ----
valores = {
    'box1': {'valor': 100, 'x': 1010, 'y': 185},
    'box2': {'valor': 200, 'x': 1010, 'y': 425},
    'box3': {'valor': 300, 'x': 1455, 'y': 185},
    'box4': {'valor': 400, 'x': 1455, 'y': 425},
    'boxColor': {'valor': 'Red', 'x': 240, 'y': 710}
}

# ---- LABEL CLICKEABLE INVISIBLE ----
class ClickableLabel(QLabel):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setStyleSheet("background-color: transparent;")

    def mousePressEvent(self, event):
        self.callback()

# ---- PANTALLA DE INICIO ----
class StartScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.background_image = QPixmap("resources/start.png")

        # Área clickeable START (antes botón)
        self.start_button = ClickableLabel(self.start_app, self)
        self.start_button.setGeometry(470, 645, 910, 140)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

    def start_app(self):
        self.main_window.setCurrentIndex(1)

# ---- PANTALLA PRINCIPAL ----
class MainScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.background_image = QPixmap("resources/main.png")

        # Área clickeable FINISH (antes botón)
        self.finish_button = ClickableLabel(self.finish_app, self)
        self.finish_button.setGeometry(1690, 860, 110, 110)

        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(100, 100, 640, 480)

        self.create_value_boxes()

        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def set_cap_info(self, centroide: Tuple[int, int], color: str):
        print(f"[INFO] Recibido centroide: {centroide}, color: {color}")

        # Mostrar coordenadas del centroide en un campo (puedes crear un box específico si lo deseas)
        self.box1.setText("100") 
        self.box2.setText("200")

        # Mostrar color en boxColor
        self.boxColor.setText(color)
        self.boxCoord.setText(f"({centroide[0]}, {centroide[1]})")

    def create_value_boxes(self):
        font = QFont()
        font.setPointSize(20)
        
        for box_name, config in valores.items():
            # Crear caja para mostrar coordenadas del centroide debajo de boxColor
            self.boxCoord = QLineEdit(self)
            self.boxCoord.setReadOnly(True)
            self.boxCoord.setGeometry(valores['boxColor']['x'], valores['boxColor']['y'] + 90, 200, 80)  # Misma X, +90 en Y
            self.boxCoord.setStyleSheet("""
                background-color: white;
                border: 2px solid black;
                font-size: 30px;
            """)
            self.boxCoord.setFont(font)

            box = QLineEdit(self)
            box.setText(str(config['valor']))
            box.setReadOnly(True)
            box.setGeometry(config['x'], config['y'], 100, 80)
            box.setStyleSheet("""
                background-color: white;
                border: 2px solid black;
                font-size: 50px;
            """)
            box.setFont(font)
            setattr(self, box_name, box)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

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

        # Una sola ejecución de la lógica de decisión
        from decision import CapDecisionMaker  # Asegúrate de importar correctamente tu clase

        decision = CapDecisionMaker("detecciones_tapones.json", min_area=2000, min_confidence=0.9)
        result = decision.get_best_cap_info()

        if result:
            centroide, _, color = result
            self.main_screen.set_cap_info(centroide, color)
        else:
            print("[INFO] No se encontró ningún tapón válido.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())