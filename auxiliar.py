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
    print("3: Bajar hasta contacto y subir 10 cm")
    print("4: Mostrar posición actual del robot")
    print("5: Movimiento manual en X/Y con teclas (wasd/q para salir)")

    modo = input("> ")

    if modo == "1":
        # Posición de descanso
        q = [1.4567713737487793, -1.6137963734068812, 0.03687411943544561, 
              -1.5324381862631817, 0.12954740226268768, -0.4755452314959925]
        move_joint(con_ctr, con_rcv, q, SPEED, ACCELERATION)

    elif modo == "2":
        # 1️⃣ Mover a la posición articular de toma de imagen
        q = [1.380723476409912, -1.6959606609740199, 0.17434245744814092, 
              -1.6387573681273402, -1.5071643034564417, -0.43589860597719365]
        move_joint(con_ctr, con_rcv, q, SPEED, ACCELERATION)

        # Tercera posición articular (posición cómoda)
        comfortable_q = [1.3806346654891968, -1.617410799066061, 1.3717930952655237, -1.3240544509938736, -1.5211947599994105, -0.4361074606524866]
        current_pose = move_joint(con_ctr, con_rcv, comfortable_q, 1.0, 1.4)
        if current_pose is None:
            raise Exception("No se pudo mover a la posición cómoda. Abortando.")

        # 2️⃣ Obtener la posición actual del TCP
        #pose = con_rcv.getActualTCPPose()

        # 3️⃣ Ajustar orientación para que esté paralelo a la mesa
        #pose[3] = 0.0     # RX
        #pose[4] = 0.0     # RY
        #pose[5] = 0.0     # RZ

        #print("Ajustando orientación para estar paralelo a la mesa...")
        #move_linear(con_ctr, con_rcv, pose, SPEED, ACCELERATION)

    elif modo == "3":
        print("Descendiendo hasta contacto...")
        speed_down = [0, 0, -0.05, 0, 0, 0]
        contact = con_ctr.moveUntilContact(speed_down)
        if contact:
            print("Contacto detectado. Subiendo 10 cm.")
            pose = con_rcv.getActualTCPPose()
            pose[2] += 0.1
            move_linear(con_ctr, con_rcv, pose, 0.1, 0.5)

    elif modo == "4":
        joints = con_rcv.getActualQ()
        pose = con_rcv.getActualTCPPose()
        print("\nJoints:")
        print(joints)
        print("\nTCP Pose:")
        print(pose)

    elif modo == "5":
        print("Control manual por consola:")
        print("Movimiento lineal: W/S (Y), A/D (X)")
        print("Rotación: I/K (Rx), J/L (Ry), U/O (Rz)")
        print("Q: Salir")

        step_pos = 0.01    # metros
        step_rot = 0.05    # radianes

        while True:
            key = input("Tecla > ").lower()
            pose = con_rcv.getActualTCPPose()
            updated = False

            if key == "w":
                pose[1] += step_pos
                updated = True
            elif key == "s":
                pose[1] -= step_pos
                updated = True
            elif key == "a":
                pose[0] -= step_pos
                updated = True
            elif key == "d":
                pose[0] += step_pos
                updated = True
            elif key == "i":
                pose[3] += step_rot
                updated = True
            elif key == "k":
                pose[3] -= step_rot
                updated = True
            elif key == "j":
                pose[4] += step_rot
                updated = True
            elif key == "l":
                pose[4] -= step_rot
                updated = True
            elif key == "u":
                pose[5] += step_rot
                updated = True
            elif key == "o":
                pose[5] -= step_rot
                updated = True
            elif key == "q":
                print("Saliendo del control manual.")
                break
            else:
                print("Tecla no válida.")
                continue

            if updated:
                print(f"Moviendo a nueva pose: {pose}")
                move_linear(con_ctr, con_rcv, pose, 0.1, 0.5)


    con_ctr.disconnect()
    con_rcv.disconnect()
