import numpy as np
import rtde_control
import rtde_receive
import time
import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

ROBOT_IP = "169.254.12.28"
SPEED = 0.3
ACCELERATION = 0.2
WAIT_TIME = 1

class RobotMover:
    def __init__(self, ip):
        # Calibración intrínseca
        self.K = np.array([
            [638.84041188, 0.0, 316.19997889],
            [0.0, 639.48589176, 235.72900301],
            [0.0, 0.0, 1.0]
        ])
        self.dist_coeffs = np.array([
            [0.052738184445369124],
            [-0.26104962527734826],
            [-0.0006974730165444789],
            [-0.002171005140480176],
            [0.39943371827476987]
        ])

        # Transformación cámara → TCP (obtenida por calibración hand-eye)
        self.T_cam2tcp = np.array([
            [-0.55708172,  0.62574654,  0.54598647, -0.10704214],
            [-0.70014542, -0.70745814,  0.09643328, -0.04109643],
            [ 0.44660536, -0.32854871,  0.83222557,  0.00796086],
            [0.0, 0.0, 0.0, 1.0]
        ])

        self.con_ctrl = rtde_control.RTDEControlInterface(ip)
        self.con_recv = rtde_receive.RTDEReceiveInterface(ip)

    def pose_to_homogeneous(self, tcp_pose):
        x, y, z, rx, ry, rz = tcp_pose
        rot_mat = cv2.Rodrigues(np.array([rx, ry, rz]))[0]
        T = np.eye(4)
        T[:3, :3] = rot_mat
        T[:3, 3] = [x, y, z]
        return T

    def pixel_to_robot(self, px, py, Z_plane_world=0.0):
        tcp_pose = self.con_recv.getActualTCPPose()
        T_tcp2world = self.pose_to_homogeneous(tcp_pose)
        T_cam2world = T_tcp2world @ self.T_cam2tcp

        pts = np.array([[[px, py]]], dtype=np.float32)
        undistorted = cv2.undistortPoints(pts, self.K, self.dist_coeffs, P=None)
        x, y = undistorted[0, 0]

        print(f"Pixel original: ({px}, {py})")
        print(f"Coordenadas normalizadas: ({x:.4f}, {y:.4f})")

        point_cam = np.array([x, y, 1.0, 1.0])
        origin_cam = np.array([0.0, 0.0, 0.0, 1.0])

        point_world = T_cam2world @ point_cam
        origin_world = T_cam2world @ origin_cam

        print(f"Point world (cam origin + rayo): {point_world[:3]}")
        print(f"Origin world (cam origin): {origin_world[:3]}")

        direction = point_world[:3] - origin_world[:3]
        norm_dir = np.linalg.norm(direction)
        direction = direction / norm_dir

        print(f"Vector dirección (normalizado): {direction}, longitud original: {norm_dir:.4f}")

        t = (tcp_pose[2] - origin_world[2]) / direction[2]
        intersection = origin_world[:3] + t * direction

        print(f"Intersección con plano Z={tcp_pose[2]}: {intersection}")

        return intersection.tolist()

    def move_linear(self, pose, speed, accel):
        print(f"Moviendo a: {pose}")
        self.con_ctrl.moveL(pose, speed, accel)
        time.sleep(WAIT_TIME)
        current_pose = self.con_recv.getActualTCPPose()
        print(f"Posición actual del robot: {current_pose}")
        return current_pose

    def move_to_pixel(self, px, py, speed=0.2, accel=0.3):   
        tcp_pose = self.con_recv.getActualTCPPose()
        z_plane = tcp_pose[2]  # altura actual
        xyz_target = self.pixel_to_robot(px, py, z_plane)
        target_pose = xyz_target + tcp_pose[3:6]  # mantener orientación
        return self.move_linear(target_pose, speed, accel)

    def disconnect(self):
        if self.con_ctrl.isConnected():
            self.con_ctrl.disconnect()
        if self.con_recv.isConnected():
            self.con_recv.disconnect()

# --- GUI para confirmar posición ---
class ImageViewer(QWidget):
    def __init__(self, frame, point):
        super().__init__()
        self.setWindowTitle("Confirmar posición objetivo")
        self.image = frame
        self.point = point
        self.accepted = False

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)

        self.btn_ok = QPushButton("Continuar")
        self.btn_ok.clicked.connect(self.accept)
        layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

        self.setLayout(layout)
        self.show_image()

    def show_image(self):
        image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        h, w, ch = image_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qt_image)
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 0, 0))
        painter.setBrush(QColor(255, 0, 0))
        painter.drawEllipse(self.point[0] - 5, self.point[1] - 5, 10, 10)
        painter.end()

        self.label.setPixmap(pixmap)

    def accept(self):
        self.accepted = True
        self.close()

    def reject(self):
        self.accepted = False
        self.close()

    def closeEvent(self, event):
        self.accepted = False
        super().closeEvent(event)

def mostrar_imagen_con_punto_pyqt(u, v):
    cap = cv2.VideoCapture(2)
    ret, image = cap.read()
    print(f"Image shape: {image.shape}")
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return False
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("No se pudo capturar imagen.")
        return False

    app = QApplication.instance() or QApplication(sys.argv)
    result = {'accepted': False}

    class Viewer(ImageViewer):
        def closeEvent(self, event):
            result['accepted'] = self.accepted
            event.accept()
            self.deleteLater()
            app.exit()

    viewer = Viewer(frame, (u, v))
    viewer.show()
    app.exec_()
    return result['accepted']

def seleccionar_pixel():
    opciones = {
        "1": ("Centro", 316, 236),
        "2": ("Esquina superior izquierda", 0, 0),
        "3": ("Esquina superior derecha", 632, 0),
        "4": ("Esquina inferior izquierda", 0, 472),
        "5": ("Esquina inferior derecha", 632, 472),
        "6": ("Coordenadas personalizadas", None, None)
    }

    print("\nSelecciona una posición de destino:")
    for k, (desc, _, _) in opciones.items():
        print(f"{k}: {desc}")

    while True:
        eleccion = input("Tu elección: ")
        if eleccion in opciones:
            desc, u, v = opciones[eleccion]
            if eleccion == "6":
                try:
                    u = int(input("Introduce coordenada u (horizontal): "))
                    v = int(input("Introduce coordenada v (vertical): "))
                    print(f"Seleccionado: Coordenadas personalizadas (u={u}, v={v})")
                    return u, v
                except ValueError:
                    print("Coordenadas inválidas. Intenta de nuevo.")
                    continue
            else:
                print(f"Seleccionado: {desc} (u={u}, v={v})")
                return u, v
        else:
            print("Opción inválida, intenta de nuevo.")

# --- MAIN ---
if __name__ == "__main__":
    robot = None
    try:
        print("Conectando al robot...")
        robot = RobotMover(ROBOT_IP)
        pose_actual = robot.con_recv.getActualTCPPose()
        print(f"Pose actual TCP: {pose_actual}")

        u, v = seleccionar_pixel()

        if not mostrar_imagen_con_punto_pyqt(u, v):
            print("Movimiento cancelado por el usuario.")
        else:
            robot.move_to_pixel(u, v, SPEED, ACCELERATION)
            print("Movimiento completado.")

        robot.con_ctrl.stopScript()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if robot:
            robot.disconnect()
        print("Conexión cerrada.")
