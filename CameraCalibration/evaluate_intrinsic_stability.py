
import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt
import os

CHECKERBOARD = (10, 7)
SQUARE_SIZE = 0.025
images_path = 'calib_images/calib_img_*.png'
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

SENSOR_WIDTH_MM = 3.67
SENSOR_HEIGHT_MM = 2.74

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

images = sorted(glob.glob(images_path))
assert len(images) >= 5, "Se necesitan al menos 5 imágenes."

# Métricas
num_imgs_list = []
reproj_errors = []
fxs, fys = [], []
cxs, cys = [], []
k1s, k2s, k3s = [], [], []
p1s, p2s = [], []
fx_mm, fy_mm = [], []
all_corners = []

for n in range(5, len(images) + 1):
    sub_imgs = images[:n]
    objpoints, imgpoints = [], []
    img_shape = None

    for fname in sub_imgs:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_shape = gray.shape[::-1]
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
        if not ret:
            continue
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        objpoints.append(objp)
        imgpoints.append(corners2)
        if n == len(images):  # solo en el pase final guardamos para el gráfico de cobertura
            all_corners.extend([pt.ravel() for pt in corners2])

    if len(objpoints) < 3:
        continue

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)

    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], K, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error

    error_mean = total_error / len(objpoints)
    reproj_errors.append(error_mean)
    num_imgs_list.append(n)

    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    fxs.append(fx)
    fys.append(fy)
    cxs.append(cx)
    cys.append(cy)

    dist_flat = dist.flatten()
    k1s.append(dist_flat[0] if len(dist_flat) > 0 else 0)
    k2s.append(dist_flat[1] if len(dist_flat) > 1 else 0)
    p1s.append(dist_flat[2] if len(dist_flat) > 2 else 0)
    p2s.append(dist_flat[3] if len(dist_flat) > 3 else 0)
    k3s.append(dist_flat[4] if len(dist_flat) > 4 else 0)

    fx_mm.append(fx * SENSOR_WIDTH_MM / img_shape[0])
    fy_mm.append(fy * SENSOR_HEIGHT_MM / img_shape[1])

# === Graficar métricas (sin la distribución) ===
fig, axs = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle("Evaluación de calibración intrínseca", fontsize=16)

axs[0, 0].plot(num_imgs_list, reproj_errors, marker='o')
axs[0, 0].set_title("Error de reproyección medio (px)")
axs[0, 0].grid(True)

axs[0, 1].plot(num_imgs_list, fxs, marker='o', label='fx (px)')
axs[0, 1].plot(num_imgs_list, fys, marker='o', label='fy (px)')
axs[0, 1].set_title("Focal Lengths (px)")
axs[0, 1].legend()
axs[0, 1].grid(True)

axs[1, 0].plot(num_imgs_list, fx_mm, marker='o', label='fx (mm)')
axs[1, 0].plot(num_imgs_list, fy_mm, marker='o', label='fy (mm)')
axs[1, 0].set_title("Focal Lengths (mm)")
axs[1, 0].legend()
axs[1, 0].grid(True)

axs[1, 1].plot(num_imgs_list, cxs, marker='o', label='cx')
axs[1, 1].plot(num_imgs_list, cys, marker='o', label='cy')
axs[1, 1].set_title("Puntos principales (px)")
axs[1, 1].legend()
axs[1, 1].grid(True)

axs[2, 0].plot(num_imgs_list, k1s, marker='o', label='k1')
axs[2, 0].plot(num_imgs_list, k2s, marker='o', label='k2')
axs[2, 0].plot(num_imgs_list, k3s, marker='o', label='k3')
axs[2, 0].set_title("Distorsión radial")
axs[2, 0].legend()
axs[2, 0].grid(True)

axs[2, 1].plot(num_imgs_list, p1s, marker='o', label='p1')
axs[2, 1].plot(num_imgs_list, p2s, marker='o', label='p2')
axs[2, 1].set_title("Distorsión tangencial")
axs[2, 1].legend()
axs[2, 1].grid(True)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()


# === Nueva figura para distribución de puntos ===
if all_corners:
    corners_array = np.array(all_corners)
    plt.figure(figsize=(8, 6))
    plt.scatter(corners_array[:, 0], corners_array[:, 1], s=5, alpha=0.5)
    plt.gca().invert_yaxis()
    plt.title("Distribución de puntos de calibración (px)")
    plt.xlabel("X (px)")
    plt.ylabel("Y (px)")
    plt.grid(True)
    plt.show()
