import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QLabel, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
from typing import Tuple

# ---- VALORES PREDEFINIDOS MODIFICABLES POR EL PROGRAMADOR ----
valores = {
    'box1': {'valor': 0, 'x': 980, 'y': 185},
    'box2': {'valor': 0, 'x': 980, 'y': 425},
    'box3': {'valor': 0, 'x': 1295, 'y': 185},
    'box4': {'valor': 0, 'x': 1295, 'y': 425},
    'box5': {'valor': 0, 'x': 1610, 'y': 185},
    'box6': {'valor': 0, 'x': 1610, 'y': 425},
    'box7': {'valor': 0, 'x': 980, 'y': 665},
    'boxSum': {'valor': 0, 'x': 1495, 'y': 665},
    'boxColor': {'valor': 'Green', 'x': 240, 'y': 710}
}

# ---- Mapa de Clase a Color ----
def clase_a_color(clase_str: str) -> Tuple[str, str]:
    mapa = {
        "Clase 0": ("Red", "#FF0000"),
        "Clase 1": ("Red", "#FF0000"),
        "Clase 2": ("Yellow", "#FFFF00"),
        "Clase 3": ("Green", "#00FF00"),
        "Clase 4": ("Blue", "#0000FF"),
        "Clase 5": ("White", "#FFFFFF"),
        "Clase 6": ("Black", "#000000"),
        "Clase 7": ("Rest", "#888888"),
    }
    return mapa.get(clase_str, (clase_str, "#CCCCCC"))

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

        # Aquí se actualizarán los valores de las cajas 1 a 6 con variables externas (ejemplo aquí con 0)
        # En un futuro reemplaza estos valores con las variables que recibas del otro script
        valores_reales = {
            'box1': 0,
            'box2': 0,
            'box3': 0,
            'box4': 0,
            'box5': 0,
            'box6': 0,
            'box7': 0
        }
        for box_name, valor in valores_reales.items():
            getattr(self, box_name).setText(str(valor))

        # Actualizar suma en boxSum
        suma = sum(valores_reales.values())
        self.boxSum.setText(str(suma))

        # Traducir clase a nombre y color hexadecimal
        nombre_color, color_hex = clase_a_color(color)

        # Actualizar caja de color con color de fondo
        self.boxColor.setText(nombre_color)
        self.boxColor.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            font-size: 30px;
        """)

        # Actualizar coordenadas con formato y sin borde
        self.boxCoord.setText(f"({centroide[0]}, {centroide[1]}) px")

    def create_value_boxes(self):
        font = QFont()
        font.setPointSize(20)

        # Crear cajas para box1 a box7 y boxSum
        for box_name in ['box1', 'box2', 'box3', 'box4', 'box5', 'box6', 'box7', 'boxSum']:
            config = valores[box_name]
            box = QLineEdit(self)
            box.setText(str(config['valor']))
            box.setReadOnly(True)
            box.setGeometry(config['x'], config['y'], 100, 80)
            box.setStyleSheet("""
                background-color: white;
                border: none;
                font-size: 30px;
            """)
            box.setFont(font)
            setattr(self, box_name, box)

        # Caja adicional para coordenadas (bajo boxColor)
        self.boxCoord = QLineEdit(self)
        self.boxCoord.setReadOnly(True)
        self.boxCoord.setGeometry(290, 815, 200, 80)
        self.boxCoord.setStyleSheet("""
            background-color: white;
            border: none;
            font-size: 30px;
        """)
        self.boxCoord.setFont(font)

        # Crear caja para boxColor (color con fondo)
        config_color = valores['boxColor']
        self.boxColor = QLineEdit(self)
        self.boxColor.setText(config_color['valor'])
        self.boxColor.setReadOnly(True)
        self.boxColor.setGeometry(config_color['x'], config_color['y'], 200, 80)
        self.boxColor.setStyleSheet("""
            border: none;
            font-size: 30px;
            color: black;
        """)
        self.boxColor.setFont(font)

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
