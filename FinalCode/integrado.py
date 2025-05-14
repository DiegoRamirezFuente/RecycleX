import os
import json
import time
import cv2
import numpy as np
import rtde_io
import rtde_control
import rtde_receive
from camaraAcceso import Camara
from decision import CapDecisionMaker
from visionYOLO import TaponesDetector

# Ruta de la foto tomada por la cámara
IMAGE_PATH = "taponesjuntos.jpg"

# Archivos de salida
JSON_OUTPUT_PATH = "detecciones_tapones.json"
IMAGE_OUTPUT_PATH = "tapones_resultado.jpg"

# Modelo YOLO entrenado
MODEL_PATH = "train3/weights/best.pt"

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"  # Reemplaza con la IP real de tu robot
DIGITAL_OUTPUT_PIN = 4  # Salida digital a activar al detectar contacto

# Parámetros de movimiento
SPEED = 0.3  # m/s
ACCELERATION = 0.2  # m/s^2
WAIT_TIME = 2  # Tiempo de espera entre movimientos (segundos)

# Calibración (lineal)
CALIBRATION = {
    "coef_x": [-5.818951947422773e-05, -0.00037554940466236344],
    "intercept_x": 0.18865207994720062,
    "coef_y": [-0.0004022572004555222, 7.369792023301156e-05],
    "intercept_y": -0.26213300591687977,
    "z_fija": 0.23495259079391306
}

cam = Camara(index=0)  # Ajusta el índice de la cámara si es necesario
detector = TaponesDetector(MODEL_PATH)

# --- FUNCIONES ---
def pixel_to_robot_coords(px, py):
    """Convierte coordenadas en píxeles a coordenadas físicas en el sistema del robot."""
    x = CALIBRATION["coef_x"][0] * px + CALIBRATION["coef_x"][1] * py + CALIBRATION["intercept_x"]
    y = CALIBRATION["coef_y"][0] * px + CALIBRATION["coef_y"][1] * py + CALIBRATION["intercept_y"]
    z = CALIBRATION["z_fija"]
    return [x, y, z]

def move_linear(con_ctr, con_rcv, pose, speed, acceleration):
    print(f"Moviendo linealmente a: {pose}")
    con_ctr.moveL(pose, speed, acceleration)
    time.sleep(WAIT_TIME)
    current_pose = con_rcv.getActualTCPPose()
    print(f"Posición actual del robot: {current_pose}")
    return current_pose

def move_joint(con_ctr, con_rcv, q, speed, acceleration):
    print(f"Moviendo a la posición articular: {q}")
    con_ctr.moveJ(q, speed, acceleration)
    time.sleep(WAIT_TIME)
    current_pose = con_rcv.getActualTCPPose()
    print(f"Posición actual del robot: {current_pose}")
    return current_pose

# --- MAIN ---
if __name__ == "__main__":
    try:
        print("Estableciendo conexión con el robot...")
        con_ctr = rtde_control.RTDEControlInterface(ROBOT_IP)
        con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
        con_io = rtde_io.RTDEIOInterface(ROBOT_IP)
        print("Conexión establecida.")

        # 1. Movimientos iniciales
        q1 = [1.4567713737487793, -1.6137963734068812, 0.03687411943544561,
              -1.5324381862631817, 0.12954740226268768, -0.4755452314959925]
        move_joint(con_ctr, con_rcv, q1, 1.0, 1.4)

        q2 = [1.380723476409912, -1.6959606609740199, 0.17434245744814092,
              -1.6387573681273402, -1.5071643034564417, -0.43589860597719365]
        move_joint(con_ctr, con_rcv, q2, 1.0, 1.4)

        comfortable_q = [1.3806346654891968, -1.617410799066061, 1.3717930952655237, -1.3240544509938736, -1.5211947599994105, -0.4361074606524866]
        current_pose = move_joint(con_ctr, con_rcv, comfortable_q, 1.0, 1.4)
        if current_pose is None:
            raise Exception("No se pudo mover a la posición cómoda. Abortando.")
       
        # 2. Captura de imagen
        print("[INFO] Capturando imagen de la cámara...")
        if not cam.tomar_foto(IMAGE_PATH):
            print("[ERROR] No se pudo capturar la imagen. Inténtalo de nuevo.")
        print(f"[INFO] Imagen capturada: {IMAGE_PATH}")

        # 3. Detección de tapones con YOLO
        print("[INFO] Iniciando detección con YOLO...")
        results, detections = detector.analizar_imagen(IMAGE_PATH)
        detector.guardar_json(detections, JSON_OUTPUT_PATH)
        detector.guardar_imagen_resultado(results, IMAGE_OUTPUT_PATH)
        print(f"[INFO] JSON generado: {JSON_OUTPUT_PATH}")
        print(f"[INFO] Imagen de resultados: {IMAGE_OUTPUT_PATH}")

        # 4. Algoritmo de decisión
        print("[INFO] Ejecutando algoritmo de decisión...")
        decision = CapDecisionMaker(JSON_OUTPUT_PATH, min_area=2000, min_confidence=0.9)
        selected = decision.get_best_cap_info()

        if selected:
            centroid, bbox, color = selected
            print(f"[INFO] Tapón seleccionado: Centroid={centroid}, BBox={bbox}, Color={color}")
            decision.draw_selected_on_image(IMAGE_PATH)
        else:
            print("[INFO] No se encontró ningún tapón válido.")

        # 5. Introducción de coordenadas del tapón
        px = centroid[0]
        py = centroid[1]
        tap_on_tcp = pixel_to_robot_coords(px, py)
        print(f"Coordenadas del tapón en espacio real: {tap_on_tcp}")

        # Obtener orientación actual del TCP y construir pose destino
        current_pose = con_rcv.getActualTCPPose()
        target_pose = [
            tap_on_tcp[0],  # X
            tap_on_tcp[1],  # Y
            tap_on_tcp[2],  # Z fija
            current_pose[3],  # RX
            current_pose[4],  # RY
            current_pose[5]   # RZ
        ]
        move_linear(con_ctr, con_rcv, target_pose, 0.2, 0.3)

        # 6. Bajar hasta detectar contacto
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact_detected = con_ctr.moveUntilContact(speed_down)

        if contact_detected:
            con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, True)
            print("Contacto detectado, salida digital activada.")
            time.sleep(1.0)

        # 7. Subir después de contacto
        tcp_pose = con_rcv.getActualTCPPose()
        tcp_pose[2] += 0.10
        move_linear(con_ctr, con_rcv, tcp_pose, 0.1, 0.5)

        # 8. Moverse a una nueva posición lateral
        new_q = comfortable_q[:]
        new_q[0] -= 3.14159
        move_joint(con_ctr, con_rcv, new_q, 1.0, 1.4)

        # 9. Apagar la salida digital
        con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
        print("Salida digital desactivada.")
        time.sleep(0.2)

        # 10. Finalizar
        con_ctr.stopScript()
        print("Programa terminado.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")

    finally:
        if 'con_ctr' in locals() and con_ctr.isConnected():
            con_ctr.disconnect()
        if 'con_rcv' in locals() and con_rcv.isConnected():
            con_rcv.disconnect()
        if 'con_io' in locals() and con_io.isConnected():
            con_io.disconnect()
        print("Conexión cerrada.")