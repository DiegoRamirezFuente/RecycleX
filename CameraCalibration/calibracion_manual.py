import sys
import cv2
import numpy as np
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QInputDialog
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import QTimer
from sklearn.linear_model import LinearRegression

JSON_PATH = "calibracion_ur3.json"
Z_FIJA = 0.24130077681581635

def detectar_tapones(imagen, umbral_area=500):
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    colores = {
        "Rojo1": [(0, 100, 100), (10, 255, 255)],
        "Rojo2": [(160, 100, 100), (179, 255, 255)],
        "Amarillo": [(10, 100, 100), (30, 255, 255)],
        "Verde": [(35, 80, 80), (85, 255, 255)],
        "Azul": [(90, 50, 50), (130, 255, 255)],
    }

    tapones_centrales = []
    kernel = np.ones((5, 5), np.uint8)

    for color, (lower, upper) in colores.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mascara = cv2.inRange(hsv, lower, upper)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)

        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contornos_filtrados = [cnt for cnt in contornos if cv2.contourArea(cnt) > umbral_area]

        for contorno in contornos_filtrados:
            x, y, w, h = cv2.boundingRect(contorno)
            u = x + w // 2
            v = y + h // 2
            tapones_centrales.append((color, u, v))

    return tapones_centrales

def entrenar_y_guardar(calibration_data):
    data = np.array(calibration_data)
    u, v, x, y = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
    U = np.stack([u, v], axis=1)

    modelo_x = LinearRegression().fit(U, x)
    modelo_y = LinearRegression().fit(U, y)

    resultado = {
        "coef_x": modelo_x.coef_.tolist(),
        "intercept_x": modelo_x.intercept_,
        "coef_y": modelo_y.coef_.tolist(),
        "intercept_y": modelo_y.intercept_,
        "z_fija": Z_FIJA,
    }

    with open(JSON_PATH, "w") as f:
        json.dump(resultado, f, indent=4)

    print("✅ Calibración guardada en", JSON_PATH)

def cargar_modelo():
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def predecir_tcp(modelo, u, v):
    X = np.dot(modelo["coef_x"], [u, v]) + modelo["intercept_x"]
    Y = np.dot(modelo["coef_y"], [u, v]) + modelo["intercept_y"]
    Z = modelo["z_fija"]
    return X, Y, Z

class DetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detección de Tapones - PyQt")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel("Cámara")
        self.label.setScaledContents(True)
        self.btn_calibrar = QPushButton("Calibrar y Probar")
        self.btn_calibrar.clicked.connect(self.calibrar)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_calibrar)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        #self.cap = cv2.VideoCapture(1)
        self.cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_frame)
        self.timer.start(30)

        self.modelo = None

    def actualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        centros = detectar_tapones(frame)

        for i, (color, u, v) in enumerate(centros):
            # Dibujar el punto en el centro del tapón
            cv2.circle(frame, (u, v), 5, (0, 0, 255), -1)  # rojo, relleno

            # Mostrar texto con coordenadas
            cv2.putText(frame, f"{i+1}:({u},{v})", (u + 10, v), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img_qt = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img_qt))

    def calibrar(self):
        calibration_data = [
            #[109, 234, 0.09443086163351676, -0.288733727432007],
            #[307, 230, 0.08441153439626911, -0.3686754448031324],
            #[424, 52, 0.14445115464768518, -0.42885776705790457],

            # [59, 136, 0.13942205238607033, -0.2702960440878998],
            # [80, 253, 0.09087865974181032, -0.2702012729113393],
            # [171, 447, 0.006719475200923367, -0.2955539170204759],
            # [277, 332, 0.046405518796637193, -0.34501928607539717],
            # [303, 129, 0.12580446659960104, -0.36827710145447695],
            # [361, 221, 0.08444678610804258, -0.3843803177748221],
            # [388, 405, 0.00986533019489656, -0.38110182235245194],
            # [461, 201, 0.08403304667249649, -0.42687364194799526],
            # [529, 302, 0.03945667889346765, -0.44475940030473854],
            # [473, 116, 0.1170123853455502, -0.4380936151578808],

            [133, 259, 0.09470575427732816, -0.2552292599299162],
            [385, 306, 0.07091129277138782, -0.3529143644649094],
            [512, 278, 0.0825063469682454, -0.40543737047690903],

        ]
        entrenar_y_guardar(calibration_data)
        self.modelo = cargar_modelo()

        while True:
            entrada, ok = QInputDialog.getText(self, "Predicción", "Introduce coordenadas u,v:")
            if not ok or entrada.lower() == "salir":
                break
            try:
                u_px, v_px = map(float, entrada.strip().split(","))
                X, Y, Z = predecir_tcp(self.modelo, u_px, v_px)
                print(f"→ Coordenadas TCP: X = {X:.2f} mm, Y = {Y:.2f} mm, Z = {Z:.2f} mm")
            except Exception as e:
                print("❌ Entrada inválida:", e)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DetectorGUI()
    ventana.show()
    sys.exit(app.exec_())
