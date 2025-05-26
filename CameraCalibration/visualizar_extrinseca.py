import numpy as np
import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.transform import Rotation as R

# === Funciones ===

def draw_axes(ax, T, label='cam', length=0.05):
    origin = T[:3, 3]
    R_mat = T[:3, :3]
    axes = np.eye(3) * length
    colors = ['r', 'g', 'b']
    labels = ['X', 'Y', 'Z']

    for i in range(3):
        vec = R_mat @ axes[:, i]
        ax.quiver(*origin, *vec, color=colors[i], arrow_length_ratio=0.1)
        ax.text(*(origin + vec), f'{label}-{labels[i]}', color=colors[i])

def draw_checkerboard(ax, board_size=(7, 7), square_size=0.025):
    rows, cols = board_size
    for i in range(rows):
        for j in range(cols):
            if (i + j) % 2 == 0:
                square = np.array([
                    [j, i, 0],
                    [j + 1, i, 0],
                    [j + 1, i + 1, 0],
                    [j, i + 1, 0],
                    [j, i, 0]
                ]) * square_size
                ax.plot(square[:, 0], square[:, 1], square[:, 2], 'k-')

# === Cargar datos ===

with open("extrinsic_calibration.json") as f:
    T_cam2tcp = np.array(json.load(f))

with open("tcp_poses.json") as f:
    tcp_poses = json.load(f)

# Tomamos la primera pose como ejemplo
x, y, z, rx, ry, rz = tcp_poses[1]
R_tcp = R.from_euler('xyz', [rx, ry, rz]).as_matrix()
T_tcp2world = np.eye(4)
T_tcp2world[:3, :3] = R_tcp
T_tcp2world[:3, 3] = [x, y, z]

# Transformación cámara en el mundo: T_cam2world = T_tcp2world @ T_cam2tcp
T_cam2world = T_tcp2world @ T_cam2tcp

# === Visualización ===

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_title("Visualización de la calibración extrínseca")

# Dibujar sistema de ejes del mundo, TCP y cámara
draw_axes(ax, np.eye(4), label='world', length=0.05)
draw_axes(ax, T_tcp2world, label='tcp', length=0.05)
draw_axes(ax, T_cam2world, label='cam', length=0.05)

# Dibujar checkerboard en el mundo (asumido en el origen de cámara para esta escena)
T_target2cam = np.eye(4)
T_target2cam[:3, 3] = [0, 0, 0.2]  # opcional: desplazar tablero 20 cm delante de la cámara
T_target2world = T_cam2world @ T_target2cam
draw_checkerboard(ax)  # en sistema local

# Ajustar vista
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_xlim([x - 0.1, x + 0.1])
ax.set_ylim([y - 0.1, y + 0.1])
ax.set_zlim([z - 0.1, z + 0.1])
plt.show()
