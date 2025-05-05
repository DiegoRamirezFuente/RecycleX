import rtde_control
import rtde_receive
import time

ROBOT_IP = "169.254.12.28"
SPEED = 1.0
ACCELERATION = 1.4
WAIT_TIME = 2.0

def move_joint(con_ctr, con_rcv, q, speed, acceleration):
    print(f"Moviendo a la posición articular: {q}")
    con_ctr.moveJ(q, speed, acceleration)
    time.sleep(WAIT_TIME)
    return con_rcv.getActualTCPPose()

def move_linear(con_ctr, con_rcv, pose, speed, acceleration):
    con_ctr.moveL(pose, speed, acceleration)
    time.sleep(WAIT_TIME)
    return con_rcv.getActualTCPPose()

if __name__ == "__main__":
    con_ctr = rtde_control.RTDEControlInterface(ROBOT_IP)
    con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

    print("Selecciona una opción:")
    print("1: Ir a posición de descanso")
    print("2: Ir a posición de toma de imagen (paralela a la mesa)")
    print("3: Bajar hasta contacto y subir 30 cm")
    print("4: Mostrar posición actual del robot")
    print("5: Movimiento manual en X/Y con teclas (wasd/q para salir)")

    modo = input("> ")

    if modo == "1":
        # Posición de descanso
        q = [-0.0381, -0.4146, 1.6180, 2.8892, -1.1970, -0.0551]
        move_joint(con_ctr, con_rcv, q, SPEED, ACCELERATION)

    elif modo == "2":
        # 1️⃣ Mover a la posición articular de toma de imagen
        q = [1.2231, -0.8813, 0.0533, -0.7452, -1.5391, 0.7979]
        move_joint(con_ctr, con_rcv, q, SPEED, ACCELERATION)

        # 2️⃣ Obtener la posición actual del TCP
        pose = con_rcv.getActualTCPPose()

        # 3️⃣ Ajustar orientación para que esté paralelo a la mesa
        pose[3] = 0.0     # RX
        pose[4] = 0.0     # RY
        pose[5] = 0.0     # RZ

        print("Ajustando orientación para estar paralelo a la mesa...")
        move_linear(con_ctr, con_rcv, pose, SPEED, ACCELERATION)

    elif modo == "3":
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact = con_ctr.moveUntilContact(speed_down)
        if contact:
            print("Contacto detectado. Subiendo 30 cm.")
            pose = con_rcv.getActualTCPPose()
            pose[2] += 0.30
            move_linear(con_ctr, con_rcv, pose, 0.1, 0.5)

    elif modo == "4":
        joints = con_rcv.getActualQ()
        pose = con_rcv.getActualTCPPose()
        print("\nJoints:")
        print(joints)
        print("\nTCP Pose:")
        print(pose)

    elif modo == "5":
        print("Control manual: usa W/S para Y+, Y-, A/D para X-, X+, Q para salir.")
        step = 0.01
        import keyboard
        while True:
            pose = con_rcv.getActualTCPPose()
            if keyboard.is_pressed("w"):
                pose[1] += step
            elif keyboard.is_pressed("s"):
                pose[1] -= step
            elif keyboard.is_pressed("a"):
                pose[0] -= step
            elif keyboard.is_pressed("d"):
                pose[0] += step
            elif keyboard.is_pressed("q"):
                break
            else:
                continue
            move_linear(con_ctr, con_rcv, pose, 0.1, 0.5)

    con_ctr.disconnect()
    con_rcv.disconnect()
