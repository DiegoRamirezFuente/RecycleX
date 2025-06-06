import sys
import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QInputDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from sklearn.linear_model import LinearRegression

JSON_PATH = "calibracion_ur3.json"
INTRINSIC_PATH = "intrinsic_calibration_data.json"
Z_FIJA = 0.24130077681581635

def cargar_intrinsecos():
    with open(INTRINSIC_PATH, "r") as f:
        data = json.load(f)
        camera_matrix = np.array(data["camera_matrix"])
        dist_coeffs = np.array(data["dist_coeffs"])
    return camera_matrix, dist_coeffs

def desdistorsionar(imagen, camera_matrix, dist_coeffs):
    h, w = imagen.shape[:2]
    new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1)
    return cv2.undistort(imagen, camera_matrix, dist_coeffs, None, new_camera_matrix)

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

def cargar_modelo():
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def predecir_tcp(modelo, u, v):
    X = np.dot(modelo["coef_x"], [u, v]) + modelo["intercept_x"]
    Y = np.dot(modelo["coef_y"], [u, v]) + modelo["intercept_y"]
    Z = modelo["z_fija"]
    return X, Y, Z

def graficar_regresion(calibration_data):
    data = np.array(calibration_data)
    u, v, x, y = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
    U = np.stack([u, v], axis=1)

    modelo_x = LinearRegression().fit(U, x)
    modelo_y = LinearRegression().fit(U, y)

    x_pred = modelo_x.predict(U)
    y_pred = modelo_y.predict(U)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.scatter(x_pred, x, color='blue')
    ax1.plot(x_pred, x_pred, 'r--')
    ax1.set_title("u,v → x")
    ax2.scatter(y_pred, y, color='green')
    ax2.plot(y_pred, y_pred, 'r--')
    ax2.set_title("u,v → y")
    plt.show()

class DetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detección de Tapones - HSV")
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

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_frame)
        self.timer.start(30)

        self.modelo = None
        self.camera_matrix, self.dist_coeffs = cargar_intrinsecos()

    def actualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = desdistorsionar(frame, self.camera_matrix, self.dist_coeffs)
        centros = detectar_tapones(frame)

        for i, (color, u, v) in enumerate(centros):
            cv2.circle(frame, (u, v), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"{i+1}:({u},{v})", (u + 10, v), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img_qt = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img_qt))

    def calibrar(self):
        calibration_data = [
            [133, 259, 0.0947, -0.2552],
            [385, 306, 0.0709, -0.3529],
            [512, 278, 0.0825, -0.4054],
        ]
        entrenar_y_guardar(calibration_data)
        self.modelo = cargar_modelo()
        graficar_regresion(calibration_data)

        while True:
            entrada, ok = QInputDialog.getText(self, "Predicción", "Introduce coordenadas u,v:")
            if not ok or entrada.lower() == "salir":
                break
            try:
                u, v = map(float, entrada.strip().split(","))
                X, Y, Z = predecir_tcp(self.modelo, u, v)
                print(f"→ Coordenadas TCP: X={X:.2f}, Y={Y:.2f}, Z={Z:.2f}")
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
