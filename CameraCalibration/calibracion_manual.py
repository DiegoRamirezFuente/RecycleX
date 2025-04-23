import cv2
import numpy as np
import json
from sklearn.linear_model import LinearRegression

# PASO 1 - Poner el robot en una buena posición en donde vaya a tomar imagenes de la caja de tapones. Ajustar también Z_FIJA en el código
# PASO 2 - Anotar las coordenadas del TCP (en píxeles será el centro de la imagen)
# PASO 3 - Poner mínimo 2 tapones visibles por la cámara, ejecutar modo 1 del código y anotar el píxel central de cada tapón
# PASO 4 - Rellenar la matriz del modo 2 con las coordenadas anotadas y ejecutar el modo 2
# PASO 5 - Probar modo 3

JSON_PATH = "calibracion_ur3.json"
Z_FIJA = 300.0  # Altura constante

# === VISIÓN ===
def detectar_tapones(imagen, umbral_area=500):
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    colores = {
        "Amarillo": [(10, 100, 100), (30, 255, 255)],
        "Verde": [(35, 80, 80), (85, 255, 255)],
        "Azul": [(90, 50, 50), (130, 255, 255)],
    }

    tapones_centrales = []
    kernel = np.ones((5, 5), np.uint8)

    for color, (lower, upper) in colores.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mascara = cv2.inRange(hsv, lower, upper)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)

        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contornos_filtrados = [cnt for cnt in contornos if cv2.contourArea(cnt) > umbral_area]

        for contorno in contornos_filtrados:
            x, y, w, h = cv2.boundingRect(contorno)
            u = x + w // 2
            v = y + h // 2
            tapones_centrales.append((u, v))
            cv2.circle(imagen, (u, v), 5, (255, 255, 255), -1)
            cv2.rectangle(imagen, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.putText(imagen, color, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return imagen, tapones_centrales

# === CALIBRACIÓN CON MATRIZ MANUAL ===
def entrenar_y_guardar(calibration_data):
    data = np.array(calibration_data)
    u, v, x, y = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
    U = np.stack([u, v], axis=1)

    modelo_x = LinearRegression().fit(U, x)
    modelo_y = LinearRegression().fit(U, y)

    resultado = {
        "coef_x": modelo_x.coef_.tolist(),
        "intercept_x": modelo_x.intercept_,
        "coef_y": modelo_y.coef_.tolist(),
        "intercept_y": modelo_y.intercept_,
        "z_fija": Z_FIJA,
    }

    with open(JSON_PATH, "w") as f:
        json.dump(resultado, f, indent=4)

    print("✅ Calibración guardada en", JSON_PATH)

def cargar_modelo():
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def predecir_tcp(modelo, u, v):
    X = np.dot(modelo["coef_x"], [u, v]) + modelo["intercept_x"]
    Y = np.dot(modelo["coef_y"], [u, v]) + modelo["intercept_y"]
    Z = modelo["z_fija"]
    return X, Y, Z

# === MAIN ===
def main():
    cam = cv2.VideoCapture(0)
    modo = input("Selecciona modo: (1) Detectar píxeles, (2) Calibrar y probar: ")

    if modo == "1":
        print("🔍 MODO DETECCIÓN: Mostrando píxeles de los tapones detectados. Presiona Q para salir.")
        while True:
            ret, frame = cam.read()
            if not ret:
                break

            imagen, centros = detectar_tapones(frame)
            for i, (u, v) in enumerate(centros):
                cv2.putText(imagen, f"{i+1}: ({u},{v})", (u + 10, v), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.imshow("Detección", imagen)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

    elif modo == "2":
        # Aquí introduces los valores manualmente (matriz final)
        calibration_data = [
            # [u, v, X, Y]
            [960, 540, 500.0, 200.0],
            [1060, 540, 520.0, 200.0],
            [960, 640, 500.0, 220.0],
            [860, 540, 480.0, 200.0],
            [960, 440, 500.0, 180.0],
        ]

        entrenar_y_guardar(calibration_data)
        modelo = cargar_modelo()

        while True:
            entrada = input("\nIntroduce coordenadas u,v para predecir (o 'salir'): ")
            if entrada.lower() == 'salir':
                break
            try:
                u_px, v_px = map(float, entrada.strip().split(","))
                X, Y, Z = predecir_tcp(modelo, u_px, v_px)
                print(f"→ Coordenadas TCP: X = {X:.2f} mm, Y = {Y:.2f} mm, Z = {Z:.2f} mm")
            except:
                print("❌ Entrada inválida. Usa formato: u,v")

if __name__ == "__main__":
    main()
