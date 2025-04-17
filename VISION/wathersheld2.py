import cv2
import numpy as np
from matplotlib import pyplot as plt

# === 1. Cargar imagen ===
image = cv2.imread('taponesjuntos.jpg')
original = image.copy()

# === 2. Convertir a HSV y usar canal V (brillo) ===
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
gray = v

# === 3. Suavizar para evitar bordes falsos ===
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# === 4. Detectar bordes con Canny ===
edges = cv2.Canny(blurred, 50, 150)

# === 5. Mejorar contornos con dilatación y cierre ===
kernel = np.ones((3, 3), np.uint8)
edges = cv2.dilate(edges, kernel, iterations=2)
edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

# === 6. Encontrar contornos ===
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# === 7. Dibujar solo contornos grandes (evita mesa) ===
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 1000:  # Filtrar ruido y bordes pequeños
        cv2.drawContours(image, [cnt], -1, (0, 255, 0), 2)

# === 8. Mostrar resultado ===
plt.figure(figsize=(10, 10))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.title("Detección de tapones con Canny + contornos grandes")
plt.axis("off")
plt.show()
