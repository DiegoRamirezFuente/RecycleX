import cv2
import numpy as np
from matplotlib import pyplot as plt

# Cargar la imagen
image = cv2.imread('taponesjuntos.jpg')
original = image.copy()

# Convertir a escala de grises
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Aplicar threshold binario inverso + Otsu
ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# Eliminar ruido con morfología
kernel = np.ones((3, 3), np.uint8)
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

# Dilatar para obtener área de fondo
sure_bg = cv2.dilate(opening, kernel, iterations=3)

# Usar distancia euclidiana para encontrar centros
dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
ret, sure_fg = cv2.threshold(dist_transform, 0.4 * dist_transform.max(), 255, 0)

# Convertir a uint8 y restar fondo - objeto para zona desconocida
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg, sure_fg)

# Etiquetar los componentes conectados
ret, markers = cv2.connectedComponents(sure_fg)

# Sumar 1 para que fondo no sea 0 (reservado para desconocido)
markers = markers + 1

# Marcar región desconocida con 0
markers[unknown == 255] = 0

# Aplicar algoritmo Watershed
markers = cv2.watershed(image, markers)
image[markers == -1] = [0, 0, 255]  # Bordes marcados en rojo

# Mostrar resultados
plt.figure(figsize=(10, 10))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.title('Resultado con Watershed (tapones detectados)')
plt.axis('off')
plt.show()
