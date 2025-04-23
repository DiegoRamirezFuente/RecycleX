import os
import cv2
import numpy as np
import json
from scipy.spatial.transform import Rotation as R
import rtde_control
import rtde_receive
import rtde_io
import time

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"
DIGITAL_OUTPUT_PIN = 4
SPEED = 0.3
ACCELERATION = 0.2
WAIT_TIME = 2
PREDEFINED_Z = 0.3

# Ruta a los JSON
camera_params_file = "camera_params.json"
handeye_file = "handeye_params.json"
tcp_poses_file = "tcp_poses.json"

# --- FUNCIONES ---

def calcular_xy_en_tcp(u, v):
    with open(camera_params_file, 'r') as f:
        camera_data = json.load(f)
    with open(handeye_file, 'r') as f:
        handeye_data = json.load(f)

    mtx = np.array(camera_data['mtx'])
    dist = np.array(camera_data['dist'])
    T_cam_tcp = np.eye(4)
    T_cam_tcp[:3, :3] = np.array(handeye_data['rotation'])
    T_cam_tcp[:3, 3] = np.array(handeye_data['translation'])

    fx, fy = mtx[0, 0], mtx[1, 1]
    cx, cy = mtx[0, 2], mtx[1, 2]

    pts = np.array([[[u, v]]], dtype=np.float32)
    pts_undist = cv2.undistortPoints(pts, mtx, dist, P=mtx)
    u_norm, v_norm = pts_undist[0][0]

    X_cam = (u_norm - cx) * PREDEFINED_Z / fx
    Y_cam = (v_norm - cy) * PREDEFINED_Z / fy
    point_cam = np.array([X_cam, Y_cam, PREDEFINED_Z, 1.0])

    point_tcp = T_cam_tcp @ point_cam
    return point_tcp[:3]

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

        # 1️⃣ MoveJ iniciales
        q1 = [1.4567713737487793, -1.6137963734068812, 0.03687411943544561, 
              -1.5324381862631817, 0.12954740226268768, -0.4755452314959925]
        move_joint(con_ctr, con_rcv, q1, 1.0, 1.4)

        q2 = [1.380723476409912, -1.6959606609740199, 0.17434245744814092, 
              -1.6387573681273402, -1.5071643034564417, -0.43589860597719365]
        move_joint(con_ctr, con_rcv, q2, 1.0, 1.4)
        
        comfortable_q = [-0.038115290797877656, -0.41458715972364596, 1.6180241743670862, 2.889211098622066, -1.1969863123337179, -0.05512171977058779]

        current_pose = move_joint(con_ctr, con_rcv, comfortable_q, 1.0, 1.4)
        if current_pose is None:
            raise Exception("No se pudo mover a la posición cómoda. Abortando.")

        # 2️⃣ Recibir coordenadas de imagen
        print("Introduce coordenadas del objeto en la imagen (u v):")
        u, v = map(int, input("> ").split())

        pos_tcp = calcular_xy_en_tcp(u, v)
        print(f"📌 Coordenadas en TCP (X, Y): {pos_tcp[0]:.4f}, {pos_tcp[1]:.4f}")

        # 3️⃣ Posicionarse sobre el tapón antes de bajar
        current_tcp = con_rcv.getActualTCPPose()
        target_pose = current_tcp[:]
        target_pose[0] = pos_tcp[0]
        target_pose[1] = pos_tcp[1]
        target_pose[2] = PREDEFINED_Z
        move_linear(con_ctr, con_rcv, target_pose, SPEED, ACCELERATION)

        # 4️⃣ Bajar hasta contacto
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact_detected = con_ctr.moveUntilContact(speed_down)

        if contact_detected:
            con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, True)
            print("Contacto detectado, salida digital activada.")
            time.sleep(1.0)

        # 5️⃣ Subir
        tcp_pose = con_rcv.getActualTCPPose()
        tcp_pose[2] += 0.10
        move_linear(con_ctr, con_rcv, tcp_pose, 0.1, 0.5)

        # 6️⃣ Moverse lateralmente
        new_q = comfortable_q[:]
        new_q[0] -= 3.14159
        move_joint(con_ctr, con_rcv, new_q, 1.0, 1.4)

        # 7️⃣ Apagar salida digital
        con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
        print("Salida digital desactivada.")
        time.sleep(0.2)

        # 8️⃣ Terminar
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
