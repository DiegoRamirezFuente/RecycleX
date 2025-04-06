import rtde_receive

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"  # Reemplaza con la IP real de tu robot

# --- MAIN ---
if __name__ == "__main__":
    # Inicializar conexión con el robot
    con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
    
    # Obtener datos actuales del robot
    current_joints = con_rcv.getActualQ()  # Posiciones articulares [rad]
    current_tcp_pose = con_rcv.getActualTCPPose()  # Pose del TCP [mm, rad]
    
    # Nombres de las articulaciones (según UR)
    joint_names = ["Base", "Shoulder", "Elbow", "Wrist1", "Wrist2", "Wrist3"]
    
    # Imprimir posiciones articulares (valores completos)
    print("\nPosiciones actuales de las articulaciones (rad):")
    for name, pos in zip(joint_names, current_joints):
        print(f"  {name}: {pos}")  # Sin formato de decimales
    
    # Imprimir pose del TCP (valores completos)
    print("\nPose actual del TCP:")
    print(f"  Posición (mm): [X: {current_tcp_pose[0]}, Y: {current_tcp_pose[1]}, Z: {current_tcp_pose[2]}]")
    print(f"  Orientación (rad): [RX: {current_tcp_pose[3]}, RY: {current_tcp_pose[4]}, RZ: {current_tcp_pose[5]}]")