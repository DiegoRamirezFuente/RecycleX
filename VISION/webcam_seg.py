import cv2
import numpy as np

def detectar_tapones(imagen, umbral_area=500):
    # Convertir la imagen a espacio de color HSV
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    
    # Definir rangos de color para los tapones
    colores = {
        #"Rojo": [(4.32, 26.52, 64.51), (172, 255, 239.19)],
        "Amarillo": [(10, 100, 100), (30, 255, 255)],
        "Verde": [(28.44, 120.36, 75.735), (78.12, 255, 255)],
        "Azul": [(86, 47, 0), (132, 255, 255)],
    }
    
    resultado = {}
    kernel = np.ones((5, 5), np.uint8)
    
    for color, (lower, upper) in colores.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mascara = cv2.inRange(hsv, lower, upper)
        
        # Aplicar operaciones morfológicas
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
        
        # Encontrar contornos
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos por tamaño mínimo
        contornos_filtrados = [cnt for cnt in contornos if cv2.contourArea(cnt) > umbral_area]
        resultado[color] = len(contornos_filtrados)
        
        for contorno in contornos_filtrados:
            x, y, w, h = cv2.boundingRect(contorno)
            cv2.rectangle(imagen, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.putText(imagen, color, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    
    return imagen, resultado

# Captura de video desde la webcam
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionar para mejor visualización
    escala = 2
    frame_resized = cv2.resize(frame, (int(frame.shape[1] * escala), int(frame.shape[0] * escala)))

    # Procesar la imagen
    procesada, conteo = detectar_tapones(frame_resized, umbral_area=1000)

    # Mostrar resultados
    for color, cantidad in conteo.items():
        print(f"{color}: {cantidad} tapones detectados")

    cv2.imshow("Detección de Tapones", procesada)

    # Salir con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar ventanas
cap.release()
cv2.destroyAllWindows()
