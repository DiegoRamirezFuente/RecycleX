import rtde_control
import rtde_receive
import rtde_io
import time
import numpy as np
import cv2

class RobotController:
    """
    Clase para gestionar movimientos de un robot UR:
      - Conexión RTDE
      - Movimientos articulares y lineales
      - Conversión píxeles→coordenadas robot
      - Descenso hasta contacto y control de IO
    """

    def __init__(self, robot_ip: str,
                 digital_output_pin: int = 4,
                 wait_time: float = 2.0):
        self.robot_ip = robot_ip
        self.digital_output_pin = digital_output_pin
        self.wait_time = wait_time
        
        # Hardcodear matriz intrínseca (K)
        self.K = np.array([
            [1.43141740e+03, 0.00000000e+00, 9.63097808e+02],
            [0.00000000e+00, 1.43085086e+03, 5.27575982e+02],
            [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
        ])

        # Hardcodear coeficientes de distorsión
        self.dist_coeffs = np.array([
            6.14327887e-02, -2.41696976e-01, -3.53959131e-03, 1.14080494e-04, 1.09212227e-01
        ])

        # Hardcodear matriz extrínseca cámara → TCP, última calibración que hiciste
        self.T_cam2tcp = np.array([
            [ 0.85011681, -0.45225934,  0.26974597, -0.31966518],
            [ 0.41792422,  0.89109111,  0.17690673, -0.14078716],
            [-0.32037595, -0.03765801,  0.94654166, -0.43525681],
            [ 0.        ,  0.        ,  0.        ,  1.        ]
        ])

        self.con_ctrl = None
        self.con_recv = None
        self.con_io = None

    def connect(self):
        """Establecer conexión RTDE con el robot."""
        self.con_ctrl = rtde_control.RTDEControlInterface(self.robot_ip)
        self.con_recv = rtde_receive.RTDEReceiveInterface(self.robot_ip)
        self.con_io   = rtde_io.RTDEIOInterface(self.robot_ip)

    def disconnect(self):
        """Cerrar conexiones RTDE."""
        if self.con_ctrl and self.con_ctrl.isConnected():
            self.con_ctrl.disconnect()
        if self.con_recv and self.con_recv.isConnected():
            self.con_recv.disconnect()
        if self.con_io and self.con_io.isConnected():
            self.con_io.disconnect()

    def pixel_to_robot(self, px: float, py: float, Z_cam: float = 0.24130366699128894) -> list:
            """Convierte píxeles y profundidad Z_cam en coordenadas TCP 3D."""

            pts = np.array([[[px, py]]], dtype=np.float32)
            undistorted_pts = cv2.undistortPoints(pts, self.K, self.dist_coeffs, P=self.K)
            x_ud, y_ud = undistorted_pts[0, 0]

            XYZ_cam = Z_cam * np.array([x_ud, y_ud, 1.0])
            XYZ_cam_hom = np.append(XYZ_cam, 1.0)

            XYZ_tcp_hom = self.T_cam2tcp @ XYZ_cam_hom
            return XYZ_tcp_hom[:3].tolist()

    def move_joint(self, joints: list, speed: float, accel: float) -> list:
        """Movimiento en espacio articular (moveJ)."""
        self.con_ctrl.moveJ(joints, speed, accel)
        time.sleep(self.wait_time)
        return self.con_recv.getActualTCPPose()

    def move_linear(self, pose: list, speed: float, accel: float) -> list:
        """Movimiento lineal del TCP (moveL)."""
        self.con_ctrl.moveL(pose, speed, accel)
        time.sleep(self.wait_time)
        return self.con_recv.getActualTCPPose()

    def initial_moves(self):
        """Ejecuta la secuencia articular inicial del código original."""
        q_list = [
            [1.4567713737487793, -1.6137963734068812, 0.03687411943544561,
             -1.5324381862631817,  0.12954740226268768, -0.4755452314959925],
            [1.380723476409912, -1.6959606609740199, 0.17434245744814092,
             -1.6387573681273402, -1.5071643034564417, -0.43589860597719365],
            [1.3783674240112305, -1.7762352428831996, 1.3978703657733362,
             -1.183793382053711, -1.5224693457232874, -0.5920613447772425]
        ]
        for q in q_list:
            self.move_joint(q, speed=1.0, accel=1.4)

    def move_to_pixel(self, px: float, py: float, speed: float=0.2, accel: float=0.3) -> list:
        """Convierte píxeles y mueve linealmente al objetivo."""
        tcp_pose = self.con_recv.getActualTCPPose()  # [x,y,z,rx,ry,rz]
        Z_cam = tcp_pose[2]
        xyz = self.pixel_to_robot(px, py, Z_cam)
        ori = tcp_pose[3:6]
        target = xyz + ori
        return self.move_linear(target, speed, accel)

    def descend_until_contact(self, speed_down: list=None) -> bool:
        """Desciende hasta contacto (moveUntilContact) y activa IO."""
        sd = speed_down or [0,0,-0.05,0,0,0]
        contact = self.con_ctrl.moveUntilContact(sd)
        if contact:
            self.con_io.setStandardDigitalOut(self.digital_output_pin, True)
        return contact
    
    def descend_with_force(self, duration, force, control_freq: float = 500.0):
        """
        Desciende aplicando fuerza controlada con forceMode, luego activa la salida digital.
        """
        task_frame = self.con_recv.getActualTCPPose()
        selection_vector = [0, 0, 1, 0, 0, 0]  # solo fuerza Z
        wrench = [0, 0, force, 0, 0, 0]  # fuerza hacia abajo
        #print(force)
        force_type = 2  # tipo de fuerza
        limits = [0.1, 0.1, 0.05, 0.05, 0.05, 0.05]  # límites de movimiento permitidos
        cycles = int(duration * control_freq)

        for i in range(cycles):
            t_start = self.con_ctrl.initPeriod()
            self.con_ctrl.forceMode(task_frame, selection_vector, wrench, force_type, limits)
            self.con_ctrl.waitPeriod(t_start)
        self.con_ctrl.forceModeStop()
        #self.con_io.setStandardDigitalOut(self.digital_output_pin, True)
        return True


    def retract(self, dz: float=0.1, speed: float=0.1, accel: float=0.5):
        """Eleva el TCP en dz metros linealmente."""
        pose = self.con_recv.getActualTCPPose()
        pose[2] = 0.23495259079391306
        self.move_linear(pose, speed, accel)

    def lateral_rotation(self, delta: float=3.14159, speed: float=1.0, accel: float=1.4):
        """Rota la primera junta en delta radianes."""
        q = self.con_recv.getActualQ()
        q[0] -= delta
        self.move_joint(q, speed, accel)

    def stop(self):
        """Finaliza script RTDE."""
        self.con_ctrl.stopScript()
