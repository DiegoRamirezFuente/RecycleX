import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata

def analyze_calibration(calibration_data, image_width=640, image_height=480):
    data = np.array(calibration_data)
    u_px, v_px, x_tcp_m, y_tcp_m = data[:, 0], data[:, 1], data[:, 2], data[:, 3]

    U_px = np.stack([u_px, v_px], axis=1)

    model_x = LinearRegression().fit(U_px, x_tcp_m)
    model_y = LinearRegression().fit(U_px, y_tcp_m)

    predicted_x_m = model_x.predict(U_px)
    predicted_y_m = model_y.predict(U_px)

    errors_x_m = np.abs(x_tcp_m - predicted_x_m)
    errors_y_m = np.abs(y_tcp_m - predicted_y_m)
    total_error_m = np.sqrt(errors_x_m**2 + errors_y_m**2)

    # Cuadrícula para toda la imagen 640x480
    grid_u, grid_v = np.meshgrid(np.arange(image_width), np.arange(image_height))

    points = np.stack([u_px, v_px], axis=1)

    # Interpolación cúbica para suavidad dentro del área de puntos
    grid_errors = griddata(points, total_error_m, (grid_u, grid_v), method='cubic')

    # Rellenar con vecino más cercano fuera del área convexa para evitar huecos
    mask_nan = np.isnan(grid_errors)
    grid_errors[mask_nan] = griddata(points, total_error_m, (grid_u, grid_v), method='nearest')[mask_nan]

    plt.figure(figsize=(8, 6))
    plt.imshow(grid_errors, cmap='hot_r', origin='upper', extent=[0, image_width, image_height, 0])
    plt.colorbar(label='Error Total (m)')
    plt.scatter(u_px, v_px, c='blue', marker='o', s=50, label='Puntos de Calibración')
    plt.title('Mapa de Calor de Errores de Calibración (640×480)')
    plt.xlabel('U (píxeles)')
    plt.ylabel('V (píxeles)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Puntos de calibración con eje Y invertido para coordenadas de imagen
    plt.figure(figsize=(8, 6))
    plt.scatter(u_px, v_px, c='red', marker='x', s=100, label='Puntos de Calibración')
    plt.gca().invert_yaxis()
    plt.title('Puntos de Calibración en Coordenadas de Imagen (píxeles)')
    plt.xlabel('U (píxeles)')
    plt.ylabel('V (píxeles)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Gráficas de regresión para X e Y
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    sorted_indices = np.argsort(u_px)
    x_tcp_m_sorted = x_tcp_m[sorted_indices]
    predicted_x_m_sorted = predicted_x_m[sorted_indices]

    axes[0].scatter(x_tcp_m_sorted, predicted_x_m_sorted, color='blue', label='Real vs Predicho X')
    min_x = min(np.min(x_tcp_m), np.min(predicted_x_m))
    max_x = max(np.max(x_tcp_m), np.max(predicted_x_m))
    axes[0].plot([min_x, max_x], [min_x, max_x], 'r--', label='Ajuste Ideal')
    axes[0].set_title('Regresión para Coordenada X')
    axes[0].set_xlabel('X Real (m)')
    axes[0].set_ylabel('X Predicha (m)')
    axes[0].legend()
    axes[0].grid(True)

    sorted_indices = np.argsort(v_px)
    y_tcp_m_sorted = y_tcp_m[sorted_indices]
    predicted_y_m_sorted = predicted_y_m[sorted_indices]

    axes[1].scatter(y_tcp_m_sorted, predicted_y_m_sorted, color='green', label='Real vs Predicho Y')
    min_y = min(np.min(y_tcp_m), np.min(predicted_y_m))
    max_y = max(np.max(y_tcp_m), np.max(predicted_y_m))
    axes[1].plot([min_y, max_y], [min_y, max_y], 'r--', label='Ajuste Ideal')
    axes[1].set_title('Regresión para Coordenada Y')
    axes[1].set_xlabel('Y Real (m)')
    axes[1].set_ylabel('Y Predicha (m)')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

# Datos de calibración
calibration_data = [
    [74, 234, 0.10451375775500947, -0.21446454639984242],
    [167, 250, 0.09463466016542989, -0.2559269405879417],
    [110, 117, 0.1549302672002666, -0.2308448481746369],
    [96, 360 , 0.050067568867785156, -0.22483128479262357],
    [199, 346 , 0.053403486117623855, -0.27182999772551025],
    [287, 326, 0.05934675846547215, -0.30956225746529376],
    [203, 130, 0.14665222403884706, -0.2737478422309574],
    [275, 224, 0.10429962303849383, -0.304970995630849],
    [295, 130, 0.14670222156107784, -0.31352600471197883],
    [273, 361, 0.04601885006450031, -0.3020983896813752],
    [387, 247, 0.09464134117551011, -0.3524716713187115],
    [472, 239, 0.09702348779859103, -0.38905703927714924],
    [527, 248, 0.0921144394196538, -0.41486945204596554],
    [406, 113, 0.15405608767562445, -0.362525629564258],
    [514, 110, 0.1532777462277647, -0.4098802562477491],
    [404, 332, 0.05699457691160333, -0.36001485990501797],
    [520, 343, 0.05159079506476518, -0.4094618992683562],
    [532, 342, 0.05157575454987444, -0.41653173380452946],
    [508, 121, 0.1487553726628163, -0.4085496494004466],
    [181, 326, 0.06339683035013766, -0.2630017819921016],
    [172, 171, 0.1308842400094375, -0.25895016187282],
    [201, 291, 0.07959036806313374, -0.27397493128330724],
    [368, 170, 0.12930088720198143, -0.3459554133860212],
    [210, 169, 0.13216295130495562, -0.27875241089568353],
    [391, 283, 0.08034358175480852, -0.3551612950071293],
    [505, 334, 0.057277548312499114, -0.4040646566330706]
]

if __name__ == "__main__":
    analyze_calibration(calibration_data)
