import rtde_receive
import json
import os

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"  # Reemplaza con la IP real de tu robot
JSON_FILE = "tcp_poses.json"

# --- FUNCIONES AUXILIARES ---
def guardar_tcp_pose_en_json(pose, archivo):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(pose)

    with open(archivo, "w") as f:
        json.dump(data, f, indent=4)

# --- MAIN ---
if __name__ == "__main__":
    # Inicializar conexión con el robot
    con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
    
    # Obtener datos actuales del robot
    current_joints = con_rcv.getActualQ()  # Posiciones articulares [rad]
    current_tcp_pose = con_rcv.getActualTCPPose()  # Pose del TCP [mm, rad]
    
    # Guardar la pose actual del TCP en el archivo JSON
    guardar_tcp_pose_en_json(current_tcp_pose, JSON_FILE)
    
    # Nombres de las articulaciones (según UR)
    joint_names = ["Base", "Shoulder", "Elbow", "Wrist1", "Wrist2", "Wrist3"]
    
    # Imprimir posiciones articulares
    print("\nPosiciones actuales de las articulaciones (rad):")
    for name, pos in zip(joint_names, current_joints):
        print(f"  {name}: {pos}")
    
    # Imprimir pose del TCP
    print("\nPose actual del TCP:")
    print(f"  Posición (mm): [X: {current_tcp_pose[0]}, Y: {current_tcp_pose[1]}, Z: {current_tcp_pose[2]}]")
    print(f"  Orientación (rad): [RX: {current_tcp_pose[3]}, RY: {current_tcp_pose[4]}, RZ: {current_tcp_pose[5]}]")
