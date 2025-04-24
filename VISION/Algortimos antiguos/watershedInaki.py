import cv2
import numpy as np
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
import math

# --- 1. Cargar y preprocesar ------------------------
img = cv2.imread("taponesjuntos.jpg")
cv2.imshow("Paso 1 - Original", img)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow("Paso 2 - Escala de grises", gray)

gray = cv2.GaussianBlur(gray, (5, 5), 0)
cv2.imshow("Paso 3 - Suavizado Gaussiano", gray)
cv2.waitKey(0)

# --- 2. Umbralización inversa con Otsu ---------------
_, bin_inv = cv2.threshold(
    gray, 0, 255,
    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
)
cv2.imshow("Paso 4 - Umbral inv. (Otsu)", bin_inv)

kernel = np.ones((3,3), np.uint8)
bin_clean = cv2.morphologyEx(
    bin_inv, cv2.MORPH_OPEN,
    kernel, iterations=2
)
cv2.imshow("Paso 5 - Apertura (limpieza ruido)", bin_clean)
cv2.waitKey(0)

# --- 3. Distancia y picos locales --------------------
dist = cv2.distanceTransform(bin_clean, cv2.DIST_L2, 5)
dist_vis = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
cv2.imshow("Paso 6 - Transformada de distancia", dist_vis)

coords = peak_local_max(
    dist, min_distance=20,
    threshold_rel=0.4, labels=bin_clean
)
mark_vis = img.copy()
for (y, x) in coords:
    cv2.circle(mark_vis, (x, y), 5, (0,0,255), -1)
cv2.imshow("Paso 7 - Marcadores iniciales", mark_vis)
cv2.waitKey(0)

markers = np.zeros(dist.shape, dtype=np.int32)
for i, (y, x) in enumerate(coords, start=1):
    markers[y, x] = i
markers = ndi.grey_dilation(markers, size=(3,3))

# --- 4. Fondo seguro y región desconocida ------------
sure_bg = cv2.dilate(bin_clean, kernel, iterations=3)
cv2.imshow("Paso 8 - Fondo seguro", sure_bg)

unknown = cv2.subtract(
    sure_bg,
    (markers > 0).astype(np.uint8) * 255
)
cv2.imshow("Paso 9 - Región desconocida", unknown)
cv2.waitKey(0)

# --- 5. Preparar marcadores para cv2.watershed -------
markers_ws = markers.copy()
markers_ws[markers_ws > 0] += 1
markers_ws[sure_bg == 0] = 1
markers_ws[unknown == 255] = 0

m_vis = cv2.normalize(
    markers_ws.astype(np.uint8),
    None, 0, 255, cv2.NORM_MINMAX
)
cv2.applyColorMap(m_vis, cv2.COLORMAP_JET, m_vis)
cv2.imshow("Paso 10 - Marcadores pre‑watershed", m_vis)
cv2.waitKey(0)

# --- 6. Watershed ------------------------------------
cv2.watershed(img, markers_ws)

# --- X. Extraer y mostrar todos los contornos detectados -------
all_contours = []
for lbl in np.unique(markers_ws):
    if lbl <= 1:
        continue
    # máscara de la región lbl
    mask = np.uint8(markers_ws == lbl)
    cnts, _ = cv2.findContours(mask,
                              cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        continue
    # elegir el contorno más grande
    cnt = max(cnts, key=cv2.contourArea)
    # convertir a lista de pares (x,y)
    pts = cnt.reshape(-1, 2).tolist()
    all_contours.append(pts)

print("=== Lista de contornos detectados ===")
# imprime una lista de listas de [x,y]
print(all_contours)
# ahora puedes copiar/pegar este output para probar tu selector

ws_vis = img.copy()
ws_vis[markers_ws == -1] = (0, 0, 0)
cv2.imshow("Paso 11 - Tras Watershed (fronteras negras)", ws_vis)
cv2.waitKey(0)

# --- 7. Comprobar circularidad y guardar contornos ----

labels_filtradas = []
valid_contours = []      # ⇨ GUARDAR contornos válidos
centroides = []

for lbl in np.unique(markers_ws):
    if lbl <= 1:
        continue

    mask = np.uint8(markers_ws == lbl)
    cnts, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    if not cnts:
        continue
    cnt = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area < 100:
        continue

    perim = cv2.arcLength(cnt, True)
    circ  = 4 * math.pi * area / (perim**2)

    aspecto = 0
    if len(cnt) >= 5:
        (_, _), (eje_may, eje_men), _ = cv2.fitEllipse(cnt)
        aspecto = eje_men / eje_may if eje_may > 0 else 0

    if circ > 0.5 and aspecto > 0.5:
        labels_filtradas.append(lbl)
        valid_contours.append(cnt)        # ⇨ AÑADIR contorno
        M = cv2.moments(cnt)
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        centroides.append((cx, cy))

# --- 8. Mostrar resultados finales --------------------

# Segmentación final coloreada
seg = np.zeros_like(img)
for lbl in labels_filtradas:
    color = tuple(np.random.randint(0,255,3).tolist())
    seg[markers_ws == lbl] = color
seg[markers_ws == -1] = (0,0,0)
for (cx, cy) in centroides:
    cv2.circle(seg, (cx, cy), 5, (255,255,255), -1)

cv2.imshow("Paso 12 - Solo tapones circulares", seg)
cv2.waitKey(0)
cv2.destroyAllWindows()

# --- 9. Imprimir lista de contornos válidos ------------
print("Contornos válidos ({}):".format(len(valid_contours)))
for i, cnt in enumerate(valid_contours, start=1):
    print(f"  {i}. número de puntos: {len(cnt)}  área: {cv2.contourArea(cnt):.1f}")
