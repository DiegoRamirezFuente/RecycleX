import cv2
import numpy as np

def detectar_tapones(imagen, umbral_area=500):
    # Convertir la imagen a espacio de color HSV
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    
    # Definir rangos de color para los tapones
    colores = {
        #"Rojo": [(0, 120, 70), (10, 255, 255)],
        "Azul": [(86, 47, 0), (132, 255, 255)],
        #"Verde": [(40, 40, 40), (80, 255, 255)],
        "Amarillo": [(10, 100, 100), (30, 255, 255)],
        #"Naranja": [(10, 100, 100), (25, 255, 255)]
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

# Cargar imagen
imagen = cv2.imread("tapones.jpg")

# Redimensionar imagen para mejor visualización
escala = 0.3
imagen_resized = cv2.resize(imagen, (int(imagen.shape[1] * escala), int(imagen.shape[0] * escala)))
cv2.imshow("Imagen Original", imagen_resized)

procesada, conteo = detectar_tapones(imagen, umbral_area=1000)
procesada_resized = cv2.resize(procesada, (int(procesada.shape[1] * escala), int(procesada.shape[0] * escala)))

# Mostrar resultados
for color, cantidad in conteo.items():
    print(f"{color}: {cantidad} tapones detectados")
    
cv2.imshow("Tapones Clasificados", procesada_resized)
cv2.waitKey(0)
cv2.destroyAllWindows()
