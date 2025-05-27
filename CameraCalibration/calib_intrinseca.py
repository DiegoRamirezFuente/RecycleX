# calib_intrinseca.py
import cv2
import numpy as np
import glob
import os
import json

CHECKERBOARD = (6, 7)
SQUARE_SIZE = 0.025
images_path = 'calib_images/calib_*.jpg'
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints, imgpoints = [], []
images = sorted(glob.glob(images_path))

os.makedirs("output/con_esquinas", exist_ok=True)
os.makedirs("output/sin_distorsion", exist_ok=True)

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    if ret:
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        objpoints.append(objp)
        imgpoints.append(corners2)
        img_vis = cv2.drawChessboardCorners(img.copy(), CHECKERBOARD, corners2, ret)

         # Dibuja la esquina de referencia (primera esquina)
        corner_ref = corners2[0].ravel()
        cv2.circle(img_vis, (int(corner_ref[0]), int(corner_ref[1])), 10, (0, 0, 255), 3)
        cv2.putText(img_vis, 'Ref', (int(corner_ref[0]) + 10, int(corner_ref[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        cv2.imwrite(f"output/con_esquinas/{os.path.basename(fname)}", img_vis)
    else:
        print(f"[!] No se detectaron esquinas en {fname}")

# Calibración
if objpoints:
    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    print("Matriz intrínseca (K):\n", K)
    print("Distorsión:\n", dist.ravel())

    # Error de reproyección
    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], K, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error
    print("Error medio de reproyección: {:.5f}".format(total_error / len(objpoints)))

    # Guardar calibración
    with open("calibration_data.json", "w") as f:
        json.dump({"camera_matrix": K.tolist(), "dist_coeffs": dist.tolist()}, f, indent=4)

    for fname in images:
        img = cv2.imread(fname)
        h, w = img.shape[:2]
        newcameramtx, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
        undistorted = cv2.undistort(img, K, dist, None, newcameramtx)
        cv2.imwrite(f"output/sin_distorsion/{os.path.basename(fname)}", undistorted)
