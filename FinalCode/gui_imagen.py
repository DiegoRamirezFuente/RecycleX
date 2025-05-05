import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont
from PyQt5.QtCore import Qt
from typing import Tuple

# ---- VALORES PREDEFINIDOS ----
valores = {
    'box1': {'valor': 100, 'x': 1010, 'y': 185},
    'box2': {'valor': 200, 'x': 1010, 'y': 425},
    'box3': {'valor': 300, 'x': 1455, 'y': 185},
    'box4': {'valor': 400, 'x': 1455, 'y': 425},
    'boxColor': {'valor': 'Green', 'x': 240, 'y': 710}
}

# ---- LABEL CLICKEABLE ----
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

    def set_cap_info(self, centroide: Tuple[int, int], bounding_box: Tuple[int, int, int, int], color: str):
        print(f"[INFO] Recibido centroide: {centroide}, bounding box: {bounding_box}, color: {color}")
        
        self.box1.setText("0")
        self.box2.setText("0")
        self.box3.setText("0")
        self.box4.setText("0")
        self.boxColor.setText(color)
        self.boxCoord.setText(f"({centroide[0]}, {centroide[1]}) px")

        # 1. Cargar imagen original
        imagen = cv2.imread("tapones3.jpg")
        if imagen is None:
            print("[ERROR] No se pudo cargar la imagen.")
            return

        # --- Bounding Box (x1, y1, x2, y2) ---
        x1, y1, x2, y2 = bounding_box
        cx, cy = centroide

        # 2. Dibujar el bounding box en la imagen original (verde)
        cv2.rectangle(imagen, (x1, y1), (x2, y2), (0, 255, 0), 10)
        cv2.circle(imagen, (cx, cy), 20, (0, 255, 255), -1)

        # 3. Rotar imagen 90° en el sentido de las agujas del reloj
        imagen = cv2.rotate(imagen, cv2.ROTATE_90_CLOCKWISE)

        # Nuevo centroide después de rotar
        new_cx = cy
        new_cy = imagen.shape[1] - cx

        print(f"[INFO] Centroide rotado: ({new_cx}, {new_cy})")

        # 4. Redimensionar imagen rotada
        alto, ancho = imagen.shape[:2]
        nuevo_ancho = 800
        nuevo_alto = int((nuevo_ancho / ancho) * alto)
        imagen = cv2.resize(imagen, (nuevo_ancho, nuevo_alto))

        # 5. Convertir y mostrar la imagen en Qt
        imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        h, w, ch = imagen_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(imagen_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_img))

    def create_value_boxes(self):
        # Fuente base
        font = QFont()
        
        # Estilo para box1 a box4
        style_boxes = """
            background-color: transparent;
            border: none;
            font-size: 50px;
            color: black;
        """
        font.setPointSize(45)

        for box_name in ['box1', 'box2', 'box3', 'box4']:
            config = valores[box_name]
            box = QLineEdit(self)
            box.setText(str(config['valor']))
            box.setReadOnly(True)
            box.setGeometry(config['x'], config['y'], 120, 80)  # mismo tamaño para todos
            box.setStyleSheet(style_boxes)
            box.setFont(font)
            setattr(self, box_name, box)

        # Estilo distinto para boxColor y boxCoord
        style_extra = """
            background-color: transparent;
            border: none;
            font-size: 30px;
            color: black;
        """
        font_extra = QFont()
        font_extra.setPointSize(30)

        # boxColor
        config = valores['boxColor']
        self.boxColor = QLineEdit(self)
        self.boxColor.setText(config['valor'])
        self.boxColor.setReadOnly(True)
        self.boxColor.setGeometry(config['x'], config['y'], 200, 80)
        self.boxColor.setStyleSheet(style_extra)
        self.boxColor.setFont(font_extra)

        # boxCoord
        self.boxCoord = QLineEdit(self)
        self.boxCoord.setReadOnly(True)
        self.boxCoord.setGeometry(290, 815, 200, 80)
        self.boxCoord.setStyleSheet(style_extra)
        self.boxCoord.setFont(font_extra)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)

    def finish_app(self):
        self.main_window.setCurrentIndex(0)

# ---- MAIN APP ----
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

# ---- INICIO ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
