import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QLabel, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont
from PyQt5.QtCore import Qt
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

    def set_cap_info(self, centroide: Tuple[int, int], bounding_box: Tuple[int, int, int, int], color: str):
        print(f"[INFO] Recibido centroide: {centroide}, bounding box: {bounding_box}, color: {color}")

        self.box1.setText("100")
        self.box2.setText("200")
        self.boxColor.setText(color)
        self.boxCoord.setText(f"({centroide[0]}, {centroide[1]})")

        # Cargar imagen
        imagen = cv2.imread("tapones3.jpg")
        if imagen is None:
            print("[ERROR] No se pudo cargar la imagen.")
            return

        # Rotar imagen 90º en sentido horario
        imagen = cv2.rotate(imagen, cv2.ROTATE_90_CLOCKWISE)

        # Redimensionar la imagen para que tenga un ancho de 800px
        alto, ancho = imagen.shape[:2]
        nuevo_ancho = 800
        nuevo_alto = int((nuevo_ancho / ancho) * alto)
        imagen = cv2.resize(imagen, (nuevo_ancho, nuevo_alto))

        # Ajuste de las coordenadas del bounding box
        box_x, box_y, box_width, box_height = bounding_box
        scale_x = nuevo_ancho / ancho
        scale_y = nuevo_alto / alto

        # Ajustar las coordenadas del bounding box al tamaño de la imagen redimensionada
        box_x_resized = int(box_x * scale_x)
        box_y_resized = int(box_y * scale_y)
        box_width_resized = int(box_width * scale_x)
        box_height_resized = int(box_height * scale_y)

        # Dibujar el bounding box ajustado
        top_left = (box_x_resized - box_width_resized // 2, box_y_resized - box_height_resized // 2)
        bottom_right = (box_x_resized + box_width_resized // 2, box_y_resized + box_height_resized // 2)
        cv2.rectangle(imagen, top_left, bottom_right, (255, 0, 0), 3)  # Azul (RGB)

        # Convertir a QImage y mostrar
        imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        h, w, ch = imagen_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(imagen_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_img))

    def create_value_boxes(self):
        font = QFont()
        font.setPointSize(20)
        
        for box_name, config in valores.items():
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

        # Crear campo adicional para mostrar coordenadas
        self.boxCoord = QLineEdit(self)
        self.boxCoord.setReadOnly(True)
        self.boxCoord.setGeometry(valores['boxColor']['x'], valores['boxColor']['y'] + 90, 200, 80)
        self.boxCoord.setStyleSheet(""" 
            background-color: white;
            border: 2px solid black;
            font-size: 30px;
        """)
        self.boxCoord.setFont(font)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

    def finish_app(self):
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

        # Lógica de decisión
        from decision import CapDecisionMaker

        decision = CapDecisionMaker("detecciones_tapones.json", min_area=2000, min_confidence=0.9)
        result = decision.get_best_cap_info()

        if result:
            centroide, bounding_box, color = result
            self.main_screen.set_cap_info(centroide, bounding_box, color)
        else:
            print("[INFO] No se encontró ningún tapón válido.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
