import os
import json
import time
import cv2
import numpy as np
import rtde_control
import rtde_receive
import rtde_io

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"
DIGITAL_OUTPUT_PIN = 4
SPEED = 0.3
ACCELERATION = 0.2
WAIT_TIME = 2
CALIB_JSON = "calibracion_ur3.json"

# --- Cargar modelo de calibración ---
def calcular_xy_en_tcp(u, v):
    with open(CALIB_JSON, 'r') as f:
        modelo = json.load(f)
    x = modelo["coef_x"][0] * u + modelo["coef_x"][1] * v + modelo["intercept_x"]
    y = modelo["coef_y"][0] * u + modelo["coef_y"][1] * v + modelo["intercept_y"]
    z = modelo["z_fija"]
    return x, y, z

# --- Movimiento robot ---
def move_linear(con_ctr, con_rcv, pose, speed, acceleration):
    print(f"Moviendo linealmente a: {pose}")
    con_ctr.moveL(pose, speed, acceleration)
    time.sleep(WAIT_TIME)
    return con_rcv.getActualTCPPose()

def move_joint(con_ctr, con_rcv, q, speed, acceleration):
    print(f"Moviendo a la posición articular: {q}")
    con_ctr.moveJ(q, speed, acceleration)
    time.sleep(WAIT_TIME)
    return con_rcv.getActualTCPPose()

# --- MAIN ---
if __name__ == "__main__":
    try:
        print("Estableciendo conexión con el robot...")
        con_ctr = rtde_control.RTDEControlInterface(ROBOT_IP)
        con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
        con_io = rtde_io.RTDEIOInterface(ROBOT_IP)
        print("Conexión establecida.")

        # Posición inicial segura
        comfortable_q = [-0.0381, -0.4146, 1.6180, 2.8892, -1.1970, -0.0551]
        move_joint(con_ctr, con_rcv, comfortable_q, 1.0, 1.4)

        # 1️⃣ Coordenadas de píxeles del tapón
        print("Introduce coordenadas del tapón en la imagen (u v):")
        u, v = map(int, input("> ").split())

        x_tcp, y_tcp, z_tcp = calcular_xy_en_tcp(u, v)
        print(f"📍 Coordenadas TCP estimadas: X = {x_tcp:.2f}, Y = {y_tcp:.2f}, Z = {z_tcp:.2f}")

        # 2️⃣ Moverse encima del tapón
        current_tcp = con_rcv.getActualTCPPose()
        target_pose = current_tcp[:]
        target_pose[0] = x_tcp
        target_pose[1] = y_tcp
        target_pose[2] = z_tcp
        move_linear(con_ctr, con_rcv, target_pose, SPEED, ACCELERATION)

        # 3️⃣ Bajar hasta hacer contacto
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact_detected = con_ctr.moveUntilContact(speed_down)

        if contact_detected:
            con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, True)
            print("✅ Contacto detectado, ventosa activada.")
            time.sleep(1.0)

        # 4️⃣ Subir
        tcp_pose = con_rcv.getActualTCPPose()
        tcp_pose[2] += 0.10
        move_linear(con_ctr, con_rcv, tcp_pose, 0.1, 0.5)

        # 5️⃣ Moverse a posición lateral
        new_q = comfortable_q[:]
        new_q[0] -= 3.14159
        move_joint(con_ctr, con_rcv, new_q, 1.0, 1.4)

        # 6️⃣ Apagar ventosa
        con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
        print("Ventosa desactivada.")

        # 7️⃣ Finalizar
        con_ctr.stopScript()
        print("✅ Programa terminado.")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

    finally:
        if 'con_ctr' in locals() and con_ctr.isConnected():
            con_ctr.disconnect()
        if 'con_rcv' in locals() and con_rcv.isConnected():
            con_rcv.disconnect()
        if 'con_io' in locals() and con_io.isConnected():
            con_io.disconnect()
        print("🔌 Conexión cerrada.")
