import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont
from PyQt5.QtCore import Qt

# ---- VALORES PREDEFINIDOS PARA POSICIÓN Y NOMBRES DE CAJAS DE LA GUI ----
# Ajustado para 6 clases + Suma. Los nombres 'box1' a 'box6' se usan para los colores.
# Los labels son solo para referencia interna aquí, los nombres de colores vienen de main.py.
valores = {
    'box1': {'valor': 0, 'x': 980, 'y': 185, 'name': 'box1', 'label_ref': 'Rojo'},
    'box2': {'valor': 0, 'x': 980, 'y': 425, 'name': 'box2', 'label_ref': 'Amarillo'},
    'box3': {'valor': 0, 'x': 1295, 'y': 185, 'name': 'box3', 'label_ref': 'Verde'},
    'box4': {'valor': 0, 'x': 1295, 'y': 425, 'name': 'box4', 'label_ref': 'Azul'},
    'box5': {'valor': 0, 'x': 1610, 'y': 185, 'name': 'box5', 'label_ref': 'Blanco'},
    'box6': {'valor': 0, 'x': 1610, 'y': 425, 'name': 'box6', 'label_ref': 'Otro)'},
    'boxSum': {'valor': 0, 'x': 1495, 'y': 665, 'name': 'boxSum', 'label_ref': 'Total'},
    'boxColor': {'valor': 'N/A', 'x': 240, 'y': 710, 'name': 'boxColor_current'}, # Para el tapón actual
    # Coordenadas del tapón actual (posición definida en create_value_boxes)
}

# Mapeo de QLineEdit (boxN) a los nombres de color que main.py usará en el dict de contadores.
# ESTE ORDEN DEBE COINCIDIR CON COLOR_TO_BOX_MAP en main.py
GUI_BOX_TO_COLOR_NAME_MAP = {
    'box1': "Rojo",      # Clase 4
    'box2': "Amarillo",  # Clase 0
    'box3': "Verde",     # Clase 5
    'box4': "Azul",      # Clase 1
    'box5': "Blanco",    # Clase 2
    'box6': "Otro"       # Clase 3
}

# Mapeo de NUEVOS índices de clase YOLO a información de color para la GUI
# Debe ser consistente con _yolo_class_to_color_map en main.py RobotWorker
# Clase 0: amarillo, 1: azul, 2: blanco, 3: otro, 4: rojo, 5: verde
YOLO_CLASS_INDEX_TO_GUI_INFO = {
    0: {"name": "Amarillo", "hex": "#FFFF00"},
    1: {"name": "Azul",     "hex": "#0000FF"},
    2: {"name": "Blanco",   "hex": "#FFFFFF"},
    3: {"name": "Otro",     "hex": "#888888"},
    4: {"name": "Rojo",     "hex": "#FF0000"},
    5: {"name": "Verde",    "hex": "#00FF00"}
}


class ClickableLabel(QLabel): # Sin cambios
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setStyleSheet("background-color: transparent;")

    def mousePressEvent(self, event):
        if self.callback:
            self.callback()

class StartScreen(QWidget): # Sin cambios funcionales, solo verificación de ruta
    def __init__(self, main_window_ref, start_callback_func):
        super().__init__()
        self.main_window = main_window_ref
        self.background_image_path = os.path.join("resources", "start.png")
        self.background_image = QPixmap(self.background_image_path)

        self.start_button = ClickableLabel(start_callback_func, self)
        self.start_button.setGeometry(470, 645, 910, 140)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background_image.isNull():
             painter.drawPixmap(self.rect(), self.background_image)
        else:
            painter.fillRect(self.rect(), Qt.darkGray)
            painter.drawText(self.rect(), Qt.AlignCenter, f"Error: Imagen '{os.path.basename(self.background_image_path)}' no encontrada en '{os.path.dirname(self.background_image_path)}'")


class MainScreen(QWidget): # Cambios en create_value_boxes y update_selected_cap_details
    def __init__(self, main_window_ref, finish_callback_func):
        super().__init__()
        self.main_window = main_window_ref
        self.background_image_path = os.path.join("resources", "main.png")
        self.background_image = QPixmap(self.background_image_path)

        self.finish_button = ClickableLabel(finish_callback_func, self)
        self.finish_button.setGeometry(1690, 860, 110, 110)

        self.camera_label = QLabel("Esperando inicio...", self)
        self.camera_label.setGeometry(100, 100, 640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("background-color: black; color: white; border: 1px solid gray;")

        self.status_label = QLabel("Estado: Listo", self)
        self.status_label.setGeometry(100, 590, 640, 40) # Ajusta Y y altura
        font_status = QFont()
        font_status.setPointSize(12)
        self.status_label.setFont(font_status)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: black; background-color: rgba(255,255,255,0.6); border-radius: 5px; padding: 3px;")

        self.create_value_boxes()

    def create_value_boxes(self):
        font = QFont()
        font.setPointSize(28) # Tamaño de fuente para los números

        # Crear QLineEdits para contadores (box1 a box6) y boxSum
        # Estos deben existir en el diccionario `valores`
        box_keys_to_create = list(GUI_BOX_TO_COLOR_NAME_MAP.keys()) + ['boxSum']

        for box_key in box_keys_to_create:
            if box_key in valores:
                config = valores[box_key]
                box = QLineEdit(self)
                box.setText(str(config['valor']))
                box.setReadOnly(True)
                # Usa las coordenadas x, y de `valores`
                box.setGeometry(config['x'], config['y'], 100, 80) # Tamaño estándar, ajusta si es necesario
                box.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 28px; qproperty-alignment: AlignCenter;")
                box.setFont(font)
                setattr(self, box_key, box) # Ej: self.box1 = QLineEdit(...)
            else:
                print(f"Advertencia GUI: Configuración para QLineEdit '{box_key}' no encontrada en 'valores'.")

        # QLineEdit para el color del tapón actualmente seleccionado
        cfg_color_actual = valores['boxColor'] # Asume que 'boxColor' está en `valores`
        self.boxColor_current = QLineEdit(self) # Nombrado diferente para evitar conflicto con un posible método
        self.boxColor_current.setText(cfg_color_actual['valor'])
        self.boxColor_current.setReadOnly(True)
        self.boxColor_current.setGeometry(cfg_color_actual['x'], cfg_color_actual['y'], 200, 80)
        self.boxColor_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 26px; color: black; qproperty-alignment: AlignCenter;")
        self.boxColor_current.setFont(font) # Reusa la fuente grande

        # QLineEdit para las coordenadas del tapón actual
        self.boxCoord_current = QLineEdit(self)
        self.boxCoord_current.setReadOnly(True)
        self.boxCoord_current.setGeometry(290, 815, 200, 80) # Posición de tu diseño original
        self.boxCoord_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 24px; qproperty-alignment: AlignCenter;")
        font_coords = QFont() # Fuente ligeramente más pequeña para coordenadas si es necesario
        font_coords.setPointSize(24)
        self.boxCoord_current.setFont(font_coords)
        self.clear_selected_cap_details()


    def update_info_panel(self, data: dict): # data viene de RobotWorker
        if "status" in data:
            self.status_label.setText(f"Estado: {data['status']}")

        if "counts" in data: # data['counts'] es {"Rojo": N, "Amarillo": M, ...}
            current_counts = data["counts"]
            total_sum = 0
            # Itera sobre el mapeo GUI_BOX_TO_COLOR_NAME_MAP para asegurar el orden correcto de actualización
            for box_qlineedit_name, color_name_key in GUI_BOX_TO_COLOR_NAME_MAP.items():
                if hasattr(self, box_qlineedit_name):
                    count_val = current_counts.get(color_name_key, 0) # Obtiene el contador para este color
                    getattr(self, box_qlineedit_name).setText(str(count_val))
                    total_sum += count_val
                # else:
                #    print(f"Advertencia GUI: QLineEdit '{box_qlineedit_name}' no existe en MainScreen.")

            if hasattr(self, "boxSum"): # Actualiza el QLineEdit para la suma total
                self.boxSum.setText(str(total_sum))
            # else:
            #    print("Advertencia GUI: QLineEdit 'boxSum' no existe en MainScreen.")


    def update_camera_image_from_file(self, image_path: str): # Sin cambios
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.width(),
                                                      self.camera_label.height(),
                                                      Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.camera_label.setText("Imagen no disponible")


    def clear_camera_image(self): # Sin cambios
        self.camera_label.clear()
        self.camera_label.setText("Cámara desactivada.")

    # Este método es llamado con el nombre del color y las coordenadas desde RobotWorker
    def update_selected_cap_details(self, centroid: tuple, color_name_from_main: str):
        self.boxColor_current.setText(color_name_from_main)
        self.boxCoord_current.setText(f"({centroid[0]}, {centroid[1]}) px")

        hex_color = "#CCCCCC" # Default si el color no se encuentra
        text_color = "black"  # Default

        # Buscar el color_name_from_main en nuestro mapeo YOLO_CLASS_INDEX_TO_GUI_INFO
        # para obtener su código hexadecimal.
        for class_info in YOLO_CLASS_INDEX_TO_GUI_INFO.values():
            if class_info["name"] == color_name_from_main:
                hex_color = class_info["hex"]
                break
        
        # Simple heurística para el color del texto basado en la luminancia del fondo
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "white" if luminance < 0.45 else "black" # Ajusta el umbral 0.45 según sea necesario
        except ValueError: # En caso de que hex_color no sea válido
             pass


        self.boxColor_current.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #B0B0B0; font-size: 26px; color: {text_color}; qproperty-alignment: AlignCenter;"
        )

    def clear_selected_cap_details(self): # Sin cambios
        self.boxColor_current.setText("N/A")
        self.boxColor_current.setStyleSheet("background-color: white; border: 1px solid #CCC; font-size: 26px; color: black; qproperty-alignment: AlignCenter;")
        self.boxCoord_current.setText("(-,-) px")

    def paintEvent(self, event): # Sin cambios funcionales, solo verificación de ruta
        painter = QPainter(self)
        if not self.background_image.isNull():
            painter.drawPixmap(self.rect(), self.background_image)
        else:
            painter.fillRect(self.rect(), Qt.lightGray)
            painter.drawText(self.rect(), Qt.AlignCenter, f"Error: Imagen '{os.path.basename(self.background_image_path)}' no encontrada en '{os.path.dirname(self.background_image_path)}'")


class MainApp(QStackedWidget): # Sin cambios
    def __init__(self, start_callback, finish_callback):
        super().__init__()
        self.start_screen = StartScreen(self, start_callback)
        self.main_screen = MainScreen(self, finish_callback)

        self.addWidget(self.start_screen)
        self.addWidget(self.main_screen)
        self.setCurrentIndex(0)

if __name__ == "__main__": # Sin cambios
    print("Para ejecutar la aplicación completa, corre 'main.py'.")
    app = QApplication(sys.argv)
    def _dummy_start(): print("Dummy Start presionado."); window.setCurrentIndex(1)
    def _dummy_finish(): print("Dummy Finish presionado."); window.setCurrentIndex(0)
    window = MainApp(start_callback=_dummy_start, finish_callback=_dummy_finish)
    window.showMaximized()
    sys.exit(app.exec_())