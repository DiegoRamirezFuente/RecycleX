import rtde_control
import rtde_receive
import time
import numpy as np

ROBOT_IP = "169.254.12.28"
SPEED = 0.3
ACCELERATION = 0.2
WAIT_TIME = 2

target_pose = [
    0.01577837774791503,  # x [m]
    -0.038877167858539514, # y [m]
    0.25656991551460406,  # z [m]
    -0.6093773650106467,  # rx [rad]
    3.0330689687075947,   # ry [rad]
    -0.013034483702638643 # rz [rad]
]

def main():
    con_ctr = None
    con_rcv = None
    try:
        print("Conectando al robot...")
        con_ctr = rtde_control.RTDEControlInterface(ROBOT_IP)
        con_rcv = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

        print(f"Pose actual del TCP: {con_rcv.getActualTCPPose()}")

        print(f"Moviendo a: {target_pose}")
        con_ctr.moveL(target_pose, SPEED, ACCELERATION)

        time.sleep(WAIT_TIME)  # esperar para asegurar que termine el movimiento

        current_pose = con_rcv.getActualTCPPose()
        print(f"Posición actual del robot: {current_pose}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con_ctr is not None and con_ctr.isConnected():
            con_ctr.disconnect()
        if con_rcv is not None and con_rcv.isConnected():
            con_rcv.disconnect()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()
