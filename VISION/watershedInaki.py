import cv2
import numpy as np

# === 1. Cargar imagen ===
image = cv2.imread('taponesjuntos.jpg')
original = image.copy()

# === 2. Convertir a HSV y usar canal V (brillo) ===
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
_, _, v = cv2.split(hsv)
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

# === 7. Filtrar contornos grandes ===
grandes = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]

# === 8. Mostrar cada tapón segmentado uno a uno ===
for i, cnt in enumerate(grandes, start=1):
    # 8.1 Crear máscara del contorno
    mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.drawContours(mask, [cnt], -1, 255, -1)
    
    # 8.2 Aplicar máscara sobre la imagen original
    segment = cv2.bitwise_and(original, original, mask=mask)
    
    # 8.3 Recortar al bounding box del contorno
    x, y, w, h = cv2.boundingRect(cnt)
    segment = segment[y:y+h, x:x+w]
    
    # 8.4 Mostrar
    cv2.imshow('Tapón segmentado', segment)
    print(f"Mostrando tapón {i}/{len(grandes)}. Pulsa Enter para el siguiente...")
    
    # Espera hasta que se pulse Enter (código 13 o 10)
    while True:
        k = cv2.waitKey(0)
        if k in (13, 10):
            break

cv2.destroyAllWindows()
