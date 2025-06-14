import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

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

num_imgs_list = []
reproj_errors = []
fxs, fys = [], []
cxs, cys = [], []
k1s, k2s, k3s = [], [], []
p1s, p2s = [], []
fx_mm, fy_mm = [], []

all_corners = []
all_errors = []

final_error_mean = 0 # Inicializar para almacenar el error medio final

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
        if n == len(images): # Solo para la última iteración (usando todas las imágenes)
            all_corners.extend([pt.ravel() for pt in corners2])

    if len(objpoints) < 3:
        continue

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)

    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], K, dist)
        error_per_point = np.linalg.norm(imgpoints[i].reshape(-1, 2) - imgpoints2.reshape(-1, 2), axis=1)
        total_error += np.mean(error_per_point)
        if n == len(images): # Solo para la última iteración (usando todas las imágenes)
            all_errors.extend(error_per_point.tolist())

    error_mean = total_error / len(objpoints)
    reproj_errors.append(error_mean)
    num_imgs_list.append(n)

    if n == len(images): # Guardar el error_mean final
        final_error_mean = error_mean

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

# ---
## Resultados del error de reproyección
print(f"El error_mean final (usando todas las imágenes) es: {final_error_mean:.4f} px")

if all_errors:
    min_reproj_error = np.min(all_errors)
    max_reproj_error = np.max(all_errors)
    mean_reproj_error_global = np.mean(all_errors)
    std_reproj_error_global = np.std(all_errors)

    print(f"Rango de error de reproyección (todos los puntos):")
    print(f"  Mínimo: {min_reproj_error:.4f} px")
    print(f"  Máximo: {max_reproj_error:.4f} px")
    print(f"  Media: {mean_reproj_error_global:.4f} px")
    print(f"  Desviación estándar: {std_reproj_error_global:.4f} px")
else:
    print("No se pudieron calcular los errores de reproyección por punto. Asegúrate de que las imágenes se procesen correctamente.")

# Gráficos métricas
fig, axs = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle("Evaluación de calibración intrínseca", fontsize=16)

axs[0, 0].plot(num_imgs_list, reproj_errors, marker='o')
axs[0, 0].set_title("Error de reproyección medio (px)")
axs[0, 0].grid(True)

axs[0, 1].plot(num_imgs_list, fxs, marker='o', label='fx (px)')
axs[0, 1].plot(num_imgs_list, fys, marker='o', label='fy (px)')
axs[0, 1].set_title("Longitud focal (px)")
axs[0, 1].legend()
axs[0, 1].grid(True)

axs[1, 0].plot(num_imgs_list, fx_mm, marker='o', label='fx (mm)')
axs[1, 0].plot(num_imgs_list, fy_mm, marker='o', label='fy (mm)')
axs[1, 0].set_title("Longitud focal (mm)")
axs[1, 0].legend()
axs[1, 0].grid(True)

axs[1, 1].plot(num_imgs_list, cxs, marker='o', label='cx')
axs[1, 1].plot(num_imgs_list, cys, marker='o', label='cy')
axs[1, 1].set_title("Punto principal (px)")
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

# ---
## Visualización de la distribución del error de reproyección

# Distribución de puntos
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

    # Mapa de calor con puntos de calibración
    if all_errors: # Asegurarse de que hay errores para graficar
        errors_array = np.array(all_errors)
        
        # Calcular el rango de la imagen a partir de los img_shape
        # img_shape se actualiza en cada iteración, necesitamos el final
        # para el `extent` del imshow.
        # Asumiendo que todas las imágenes tienen el mismo tamaño.
        if img_shape is None: # Fallback si no se encontró ninguna imagen válida
             img_shape = (640, 480) # Tamaño por defecto o un tamaño conocido de tus imágenes

        grid_x, grid_y = np.meshgrid(np.arange(img_shape[0]), np.arange(img_shape[1]))

        # Ajuste para griddata si los puntos de calibración no cubren toda la rejilla
        # Usamos `linear` o `nearest` primero para rellenar los valores NaN
        grid_errors = griddata(corners_array, errors_array, (grid_x, grid_y), method='linear')
        
        # Rellenar los valores NaN restantes con la interpolación más cercana
        mask_nan = np.isnan(grid_errors)
        if np.any(mask_nan):
            grid_errors[mask_nan] = griddata(corners_array, errors_array, (grid_x, grid_y), method='nearest')[mask_nan]


        plt.figure(figsize=(8, 6))
        plt.imshow(grid_errors, cmap='hot_r', origin='upper', extent=[0, img_shape[0], img_shape[1], 0])
        plt.colorbar(label='Error de reproyección (px)')
        plt.scatter(corners_array[:, 0], corners_array[:, 1], c='white', s=10, label='Puntos de calibración')
        plt.title("Mapa de calor de error de reproyección intrínseca")
        plt.xlabel("X (px)")
        plt.ylabel("Y (px)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    else:
        print("No hay datos de error para generar el mapa de calor.")
else:
    print("No hay puntos de esquina detectados para la visualización.")