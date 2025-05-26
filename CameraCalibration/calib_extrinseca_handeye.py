# calib_extrinseca_handeye.py
import cv2
import numpy as np
import json
import glob
from scipy.spatial.transform import Rotation as R

CHECKERBOARD = (7, 7)
SQUARE_SIZE = 0.025
images_path = 'output/sin_distorsion/calib_*.jpg'

# === Cargar calibración intrínseca ===
with open("calibration_data.json") as f:
    data = json.load(f)
K = np.array(data["camera_matrix"])
dist = np.array(data["dist_coeffs"])

# === Cargar poses del TCP ===
with open("tcp_poses.json") as f:
    tcp_poses = json.load(f)

# === Inicializar ===
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

images = sorted(glob.glob(images_path))
assert len(images) == len(tcp_poses)

R_gripper2base, t_gripper2base = [], []
R_target2cam, t_target2cam = [], []

for i, fname in enumerate(images):
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    if not ret:
        raise ValueError(f"Esquinas no detectadas en {fname}")

    corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))

    # PnP → patrón respecto a cámara
    success, rvec, tvec = cv2.solvePnP(objp, corners2, K, dist)
    R_cam, _ = cv2.Rodrigues(rvec)
    R_target2cam.append(R_cam)
    t_target2cam.append(tvec)

    # Pose del TCP respecto al mundo (robot)
    x, y, z, rx, ry, rz = tcp_poses[i]
    R_grip = R.from_euler('xyz', [rx, ry, rz]).as_matrix()
    R_gripper2base.append(R_grip)
    t_gripper2base.append(np.array([[x], [y], [z]]))

# === Calibración mano-ojo ===
R_cam2grip, t_cam2grip = cv2.calibrateHandEye(
    R_gripper2base, t_gripper2base,
    R_target2cam, t_target2cam,
    method=cv2.CALIB_HAND_EYE_TSAI  # o cv2.CALIB_HAND_EYE_DANIILIDIS
)

T_cam2grip = np.eye(4)
T_cam2grip[:3, :3] = R_cam2grip
T_cam2grip[:3, 3] = t_cam2grip.flatten()

# === Guardar resultado ===
with open("extrinsic_calibration.json", "w") as f:
    json.dump(T_cam2grip.tolist(), f, indent=4)

print("=== Calibración Extrínseca (Hand-Eye) completada ===")
print("Transformación cámara → TCP:\n", T_cam2grip)
