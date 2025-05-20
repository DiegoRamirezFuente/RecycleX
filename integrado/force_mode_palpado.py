import rtde_control
import rtde_receive
import rtde_io
import time
import math

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"  # IP del robot
DIGITAL_OUTPUT_PIN = 4      # Salida digital para la ventosa

# Parámetros de movimiento
SPEED = 0.3  # m/s
ACCELERATION = 0.2  # m/s^2
WAIT_TIME = 2  # s de espera entre movimientos

# Parámetros de fuerza
FORCE_MAGNITUDE = -10         # Newtons (negativo = presionar hacia abajo)
FORCE_PRESS_DURATION = 1.5    # Segundos aplicando fuerza
Z_OBJETIVO = 0.25             # Altura a la que se debe subir tras presionar (en metros)

# --- FUNCIONES ---
def is_pose_close(pose1, pose2, tol=0.005):
    """Compara si dos poses (solo XYZ) están suficientemente cerca."""
    return all(abs(p1 - p2) < tol for p1, p2 in zip(pose1[:3], pose2[:3]))

def move_linear(con_ctr, con_rcv, pose, speed, acceleration):
    print(f"Moviendo linealmente a: {pose}")
    con_ctr.moveL(pose, speed, acceleration)
    time.sleep(WAIT_TIME)
    current_pose = con_rcv.getActualTCPPose()
    print(f"Posición actual del robot: {current_pose}")
    if not is_pose_close(current_pose, pose):
        print("⚠️ Advertencia: No se alcanzó la posición esperada (linear).")
    return current_pose

def move_joint(con_ctr, con_rcv, q, speed, acceleration):
    print(f"Moviendo a la posición articular: {q}")
    con_ctr.moveJ(q, speed, acceleration)
    time.sleep(WAIT_TIME)
    current_pose = con_rcv.getActualTCPPose()
    print(f"Posición actual del robot: {current_pose}")
    if not is_pose_close(current_pose, con_ctr.getForwardKinematics(q)):
        print("⚠️ Advertencia: No se alcanzó la posición esperada (joint).")
    return current_pose

def oscillate_pose(con_ctr, base_pose, cycle_idx, freq=5, angle_amplitude=0.05, rot_amplitude=0.1):
    # Oscila inclinación Rx y rotación Rz con onda senoidal suave
    offset_rx = angle_amplitude * math.sin(2 * math.pi * freq * cycle_idx / 500)
    offset_rz = rot_amplitude * math.sin(2 * math.pi * freq * cycle_idx / 500)
    new_pose = base_pose[:]
    new_pose[3] = base_pose[3] + offset_rx  # Rx
    new_pose[5] = base_pose[5] + offset_rz  # Rz
    con_ctr.servoL(new_pose, 0.1, 0.2, 0.02, 0.005)

# --- MAIN ---
if __name__ == "__main__":
    try:
        print("Estableciendo conexión con el robot...")
        con_ctr = rtde_control.RTDEControlInterface(ROBOT_IP)
        con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
        con_io = rtde_io.RTDEIOInterface(ROBOT_IP)
        print("Conexión establecida.")

        # 1️⃣ Posiciones iniciales con moveJ
        q1 = [1.4567713737487793, -1.6137963734068812, 0.03687411943544561,
              -1.5324381862631817, 0.12954740226268768, -0.4755452314959925]
        q2 = [1.380723476409912, -1.6959606609740199, 0.17434245744814092,
              -1.6387573681273402, -1.5071643034564417, -0.43589860597719365]
        comfortable_q = [1.3809702396392822, -1.6433397732176722, 1.6180241743670862,
                         -1.544386738245823, -1.5217412153827112, -0.43589860597719365]

        move_joint(con_ctr, con_rcv, q1, 1.0, 1.4)
        move_joint(con_ctr, con_rcv, q2, 1.0, 1.4)
        current_pose = move_joint(con_ctr, con_rcv, comfortable_q, 1.0, 1.4)
        if current_pose is None:
            raise Exception("No se pudo mover a la posición cómoda. Abortando.")

        # 2️⃣ Bajar hasta detectar contacto
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact_detected = con_ctr.moveUntilContact(speed_down)

        if contact_detected:
            print("Contacto detectado. Activando ventosa...")
            con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, True)

            # 3️⃣ Aplicar fuerza controlada hacia abajo con palpado oscilante
            print(f"Aplicando fuerza de {FORCE_MAGNITUDE} N con palpado por {FORCE_PRESS_DURATION} s...")
            task_frame = [0, 0, 0, 0, 0, 0]
            selection_vector = [0, 0, 1, 0, 0, 0]
            wrench = [0, 0, FORCE_MAGNITUDE, 0, 0, 0]
            force_type = 2
            limits = [0.01, 0.01, 0.02, 0.1, 0.1, 0.1]

            base_pose = con_rcv.getActualTCPPose()
            start_time = time.time()
            cycle_idx = 0
            while time.time() - start_time < FORCE_PRESS_DURATION:
                t_start = con_ctr.initPeriod()
                con_ctr.forceMode(task_frame, selection_vector, wrench, force_type, limits)
                oscillate_pose(con_ctr, base_pose, cycle_idx)
                con_ctr.waitPeriod(t_start)
                cycle_idx += 1

            con_ctr.forceModeStop()
            print("Fuerza aplicada. Subiendo a Z fija...")
            time.sleep(0.5)

            # 4️⃣ Subir verticalmente con moveL a Z_OBJETIVO
            current_pose = con_rcv.getActualTCPPose()
            target_pose = current_pose[:]
            target_pose[2] = Z_OBJETIVO
            move_linear(con_ctr, con_rcv, target_pose, 0.1, 0.5)

            # 5️⃣ Moverse a una posición lateral
            new_q = comfortable_q[:]
            new_q[0] -= 3.14159
            move_joint(con_ctr, con_rcv, new_q, 1.0, 1.4)

            # 6️⃣ Apagar la ventosa
            con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
            print("Ventosa desactivada.")
            time.sleep(0.2)

            # 7️⃣ Finalizar
            con_ctr.stopScript()
            print("Programa terminado.")

        else:
            current_pose = con_rcv.getActualTCPPose()
            print(f"❌ No se detectó contacto. Posición actual del robot: {current_pose}")
            raise Exception("No se detectó contacto. Abortando operación.")

    except Exception as e:
        print(f"🛑 Ocurrió un error: {e}")

    finally:
        if 'con_ctr' in locals() and con_ctr.isConnected():
            con_ctr.disconnect()
        if 'con_rcv' in locals() and con_rcv.isConnected():
            con_rcv.disconnect()
        if 'con_io' in locals() and con_io.isConnected():
            con_io.disconnect()
        print("🔌 Conexión cerrada.")
