import sys
import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
from ultralytics import YOLO
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QInputDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from sklearn.linear_model import LinearRegression

JSON_PATH = "calibracion_ur3.json"
INTRINSIC_PATH = "intrinsic_calibration_data.json"
YOLO_MODEL_PATH = "train3/weights/best.pt"
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

class TaponesDetectorYOLO:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detectar_tapones(self, imagen):
        results = self.model(imagen, verbose=False)[0]
        tapones = []
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            tapones.append((cx, cy))
        return tapones

class DetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detección de Tapones - YOLO")
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

        self.cap = cv2.VideoCapture(2)
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_frame)
        self.timer.start(30)

        self.detector = TaponesDetectorYOLO(YOLO_MODEL_PATH)
        self.modelo = None
        self.camera_matrix, self.dist_coeffs = cargar_intrinsecos()

    def actualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = desdistorsionar(frame, self.camera_matrix, self.dist_coeffs)
        tapones = self.detector.detectar_tapones(frame)

        for i, (cx, cy) in enumerate(tapones):
            cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)
            cv2.putText(frame, f"{i+1}:({cx},{cy})", (cx + 10, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img_qt = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img_qt))

    def calibrar(self):
        calibration_data = [
            [74, 234, 0.10451375775500947, -0.21446454639984242],
            [167, 250, 0.09463466016542989, -0.2559269405879417],
            [110, 117, 0.1549302672002666, -0.2308448481746369],
            [96, 360 , 0.050067568867785156, -0.22483128479262357],
            [199, 346 , 0.053403486117623855, -0.27182999772551025],
            [287, 326, 0.05934675846547215, -0.30956225746529376],
            [203, 130, 0.14665222403884706, -0.2737478422309574],
            [275, 224, 0.10429962303849383, -0.304970995630849],
            [295, 130, 0.14670222156107784, -0.31352600471197883],
            [273, 361, 0.04601885006450031, -0.3020983896813752],
            [387, 247, 0.09464134117551011, -0.3524716713187115],
            [472, 239, 0.09702348779859103, -0.38905703927714924],
            [527, 248, 0.0921144394196538, -0.41486945204596554],
            [406, 113, 0.15405608767562445, -0.362525629564258],
            [514, 110, 0.1532777462277647, -0.4098802562477491],
            [404, 332, 0.05699457691160333, -0.36001485990501797],
            [520, 343, 0.05159079506476518, -0.4094618992683562],

            [532, 342, 0.05157575454987444, -0.41653173380452946],
            [508, 121, 0.1487553726628163, -0.4085496494004466],

            [181, 326, 0.06339683035013766, -0.2630017819921016],
            [172, 171, 0.1308842400094375, -0.25895016187282],

            [201, 291, 0.07959036806313374, -0.27397493128330724],
            [368, 170, 0.12930088720198143, -0.3459554133860212],
            [210, 169, 0.13216295130495562, -0.27875241089568353],
            [391, 283, 0.08034358175480852, -0.3551612950071293],
            [505, 334, 0.057277548312499114, -0.4040646566330706]
            
        ]
        
        entrenar_y_guardar(calibration_data)
        self.modelo = cargar_modelo()

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
