# gui.py (basado en tu última versión)
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QPainter, QFont
from PyQt5.QtCore import Qt

# Constantes (si RESOURCES_PATH no está definido globalmente, definirlo aquí para __main__)
if 'RESOURCES_PATH' not in globals():
    RESOURCES_PATH = "resources" # Para ejecución directa de gui.py

# VALORES y MAPEADOS (de tu último gui.py)
valores = {
    'box1': {'valor': 0, 'x': 980, 'y': 185, 'name': 'box1', 'label_ref': 'Rojo'},
    'box2': {'valor': 0, 'x': 980, 'y': 425, 'name': 'box2', 'label_ref': 'Amarillo'},
    'box3': {'valor': 0, 'x': 1295, 'y': 185, 'name': 'box3', 'label_ref': 'Verde'},
    'box4': {'valor': 0, 'x': 1295, 'y': 425, 'name': 'box4', 'label_ref': 'Azul'},
    'box5': {'valor': 0, 'x': 1610, 'y': 185, 'name': 'box5', 'label_ref': 'Blanco'},
    'box6': {'valor': 0, 'x': 1610, 'y': 425, 'name': 'box6', 'label_ref': 'Otro'}, # Corregido el paréntesis
    'boxSum': {'valor': 0, 'x': 1495, 'y': 665, 'name': 'boxSum', 'label_ref': 'Total'},
    'boxColor': {'valor': 'N/A', 'x': 240, 'y': 710, 'name': 'boxColor_current'},
}

GUI_BOX_TO_COLOR_NAME_MAP = { #
    'box1': "Rojo", 'box2': "Amarillo", 'box3': "Verde",
    'box4': "Azul", 'box5': "Blanco", 'box6': "Otro"
}

YOLO_CLASS_INDEX_TO_GUI_INFO = { #
    0: {"name": "Amarillo", "hex": "#FFFF00"}, 1: {"name": "Azul", "hex": "#0000FF"},
    2: {"name": "Blanco", "hex": "#FFFFFF"}, 3: {"name": "Otro", "hex": "#888888"},
    4: {"name": "Rojo", "hex": "#FF0000"}, 5: {"name": "Verde", "hex": "#00FF00"}
}


class ClickableLabel(QLabel): # Sin cambios
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setStyleSheet("background-color: transparent;")

    def mousePressEvent(self, event):
        if self.callback:
            self.callback()

class StartScreen(QWidget): # Sin cambios funcionales
    def __init__(self, main_window_ref, start_callback_func):
        super().__init__()
        self.main_window = main_window_ref
        self.background_image_path = os.path.join(RESOURCES_PATH, "start.png")
        self.background_image = QPixmap(self.background_image_path)
        self.start_button = ClickableLabel(start_callback_func, self)
        self.start_button.setGeometry(470, 645, 910, 140)

    def paintEvent(self, event): #
        painter = QPainter(self)
        if not self.background_image.isNull():
             painter.drawPixmap(self.rect(), self.background_image)
        else:
            painter.fillRect(self.rect(), Qt.darkGray)
            painter.drawText(self.rect(), Qt.AlignCenter, f"Error: Imagen '{os.path.basename(self.background_image_path)}' no encontrada.")

class MainScreen(QWidget): #
    def __init__(self, main_window_ref, finish_callback_func):
        super().__init__()
        self.main_window = main_window_ref
        self.background_image_path = os.path.join(RESOURCES_PATH, "main.png")
        self.background_image = QPixmap(self.background_image_path)

        self.finish_button = ClickableLabel(finish_callback_func, self)
        self.finish_button.setGeometry(1690, 860, 110, 110)

        self.camera_label = QLabel("Esperando imagen del sistema...", self) # Texto inicial
        self.camera_label.setGeometry(100, 100, 640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #2E2E2E; color: white; border: 1px solid #4A4A4A; font-size: 15px;")

        self.status_label = QLabel("Estado: Listo", self) #
        self.status_label.setGeometry(100, 590, 640, 40)
        font_status = QFont(); font_status.setPointSize(12)
        self.status_label.setFont(font_status)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: black; background-color: rgba(255,255,255,0.65); border-radius: 5px; padding: 3px;")

        self.create_value_boxes() #

        # Asegurarse de que no haya código de cámara en vivo aquí (QTimer, cv2.VideoCapture)
        # La versión de gui.py en tenía esto, la versión en no, lo cual es correcto.

    def create_value_boxes(self): # Como en tu gui.py
        font = QFont(); font.setPointSize(28)
        box_keys_to_create = list(GUI_BOX_TO_COLOR_NAME_MAP.keys()) + ['boxSum']
        for box_key in box_keys_to_create:
            if box_key in valores:
                config = valores[box_key]
                box = QLineEdit(self); box.setText(str(config['valor'])); box.setReadOnly(True)
                box.setGeometry(config['x'], config['y'], 100, 80)
                box.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 28px; qproperty-alignment: AlignCenter;")
                box.setFont(font); setattr(self, box_key, box)
        cfg_color_actual = valores['boxColor']
        self.boxColor_current = QLineEdit(self)
        self.boxColor_current.setText(cfg_color_actual['valor']); self.boxColor_current.setReadOnly(True)
        self.boxColor_current.setGeometry(cfg_color_actual['x'], cfg_color_actual['y'], 200, 80)
        self.boxColor_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 26px; color: black; qproperty-alignment: AlignCenter;")
        self.boxColor_current.setFont(font)
        self.boxCoord_current = QLineEdit(self); self.boxCoord_current.setReadOnly(True)
        self.boxCoord_current.setGeometry(290, 815, 200, 80) # Coordenadas del tapón actual
        self.boxCoord_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 24px; qproperty-alignment: AlignCenter;")
        font_coords = QFont(); font_coords.setPointSize(24)
        self.boxCoord_current.setFont(font_coords)
        self.clear_selected_cap_details()

    def update_info_panel(self, data: dict): # Como en tu gui.py
        if "status" in data: self.status_label.setText(f"Estado: {data['status']}")
        if "counts" in data:
            current_counts = data["counts"]; total_sum = 0
            for box_qlineedit_name, color_name_key in GUI_BOX_TO_COLOR_NAME_MAP.items():
                if hasattr(self, box_qlineedit_name):
                    count_val = current_counts.get(color_name_key, 0)
                    getattr(self, box_qlineedit_name).setText(str(count_val))
                    total_sum += count_val
            if hasattr(self, "boxSum"): self.boxSum.setText(str(total_sum))

    def update_camera_image_from_file(self, image_path: str): # Como en tu gui.py
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.width(),
                                                      self.camera_label.height(),
                                                      Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.camera_label.setText(f"Imagen no encontrada:\n{os.path.basename(image_path)}")
            print(f"ERROR GUI: Imagen en {image_path} no encontrada para mostrar.")

    def clear_camera_image(self): # Como en tu gui.py
        self.camera_label.clear()
        self.camera_label.setText("Esperando imagen del sistema...") # Texto actualizado

    def update_selected_cap_details(self, centroid: tuple, color_name_from_main: str): # Como en tu gui.py
        self.boxColor_current.setText(color_name_from_main)
        self.boxCoord_current.setText(f"({centroid[0]}, {centroid[1]}) px")
        hex_color = "#CCCCCC"; text_color = "black"
        for class_info in YOLO_CLASS_INDEX_TO_GUI_INFO.values():
            if class_info["name"] == color_name_from_main:
                hex_color = class_info["hex"]; break
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "white" if luminance < 0.45 else "black"
        except ValueError: pass
        self.boxColor_current.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #B0B0B0; font-size: 26px; color: {text_color}; qproperty-alignment: AlignCenter;")

    def clear_selected_cap_details(self): # Como en tu gui.py
        self.boxColor_current.setText("N/A")
        self.boxColor_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 26px; color: black; qproperty-alignment: AlignCenter;")
        self.boxCoord_current.setText("(-,-) px")

    def paintEvent(self, event): # Como en tu gui.py
        painter = QPainter(self)
        if not self.background_image.isNull():
            painter.drawPixmap(self.rect(), self.background_image)
        else:
            painter.fillRect(self.rect(), Qt.lightGray)
            painter.drawText(self.rect(), Qt.AlignCenter, f"Error: Imagen '{os.path.basename(self.background_image_path)}' no encontrada.")

    def finish_app(self): # Adaptado del, eliminando cámara en vivo
        self.main_window.setCurrentIndex(0)


class MainApp(QStackedWidget): # Adaptado para callbacks
    def __init__(self, start_callback, finish_callback):
        super().__init__()
        self.start_screen = StartScreen(self, start_callback)
        self.main_screen = MainScreen(self, finish_callback)
        self.addWidget(self.start_screen)
        self.addWidget(self.main_screen)
        self.setCurrentIndex(0)


if __name__ == "__main__": #
    # Asegurar que RESOURCES_PATH está definido para ejecución directa
    if 'RESOURCES_PATH' not in globals(): RESOURCES_PATH = "resources"
    if not os.path.exists(RESOURCES_PATH): os.makedirs(RESOURCES_PATH, exist_ok=True)


    app = QApplication(sys.argv)
    def _dummy_start(): print("GUI Test: Start presionado."); window.setCurrentIndex(1)
    def _dummy_finish(): print("GUI Test: Finish presionado."); window.setCurrentIndex(0)
    window = MainApp(start_callback=_dummy_start, finish_callback=_dummy_finish)
    window.showMaximized()
    sys.exit(app.exec_())