import cv2
import numpy as np
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
import math

# --- 1. Cargar y preprocesar ------------------------
img = cv2.imread("tapones5.jpg")
cv2.imshow("Paso 1 - Original", img)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow("Paso 2 - Escala de grises", gray)

gray = cv2.GaussianBlur(gray, (5, 5), 0)
cv2.imshow("Paso 3 - Suavizado Gaussiano", gray)
cv2.waitKey(0)

# --- 2. Umbralización inversa con Otsu ---------------
_, bin_inv = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
cv2.imshow("Paso 4 - Umbral inv. (Otsu)", bin_inv)

kernel = np.ones((3,3), np.uint8)
bin_clean = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN,kernel, iterations=2)
cv2.imshow("Paso 5 - Apertura (limpieza ruido)", bin_clean)
cv2.waitKey(0)

# --- 3. Distancia y picos locales --------------------
dist = cv2.distanceTransform(bin_clean, cv2.DIST_L2, 5)
# normalizamos para visualizar mejor
dist_vis = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
cv2.imshow("Paso 6 - Transformada de distancia", dist_vis)

coords = peak_local_max(dist, min_distance=30,
                        threshold_rel=0.4, labels=bin_clean)
# dibujar marcadores sobre la imagen original
mark_vis = img.copy()
for (y, x) in coords:
    cv2.circle(mark_vis, (x, y), 5, (0,0,255), -1)
cv2.imshow("Paso 7 - Marcadores iniciales", mark_vis)
cv2.waitKey(0)

# creamos el array de marcadores numéricos
markers = np.zeros(dist.shape, dtype=np.int32)
for i, (y, x) in enumerate(coords, start=1):
    markers[y, x] = i
markers = ndi.grey_dilation(markers, size=(3,3))

# --- 4. Fondo seguro y región desconocida ------------
sure_bg = cv2.dilate(bin_clean, kernel, iterations=3)
cv2.imshow("Paso 8 - Fondo seguro", sure_bg)

unknown = cv2.subtract(sure_bg, (markers > 0).astype(np.uint8)*255)
cv2.imshow("Paso 9 - Región desconocida", unknown)
cv2.waitKey(0)

# --- 5. Preparar marcadores para cv2.watershed -------
markers_ws = markers.copy()
markers_ws[markers_ws > 0] += 1
markers_ws[sure_bg == 0] = 1
markers_ws[unknown == 255] = 0

# para visualizar los marcadores antes de watershed:
m_vis = cv2.normalize(markers_ws.astype(np.uint8), None, 0, 255,cv2.NORM_MINMAX)
cv2.applyColorMap(m_vis, cv2.COLORMAP_JET, m_vis)
cv2.imshow("Paso 10 - Marcadores pre‑watershed", m_vis)
cv2.waitKey(0)

# --- 6. Watershed ------------------------------------
cv2.watershed(img, markers_ws)
# marcas fronteras con -1

# visualizar fronteras superpuestas
ws_vis = img.copy()
ws_vis[markers_ws == -1] = (0, 0, 0)
cv2.imshow("Paso 11 - Tras Watershed (fronteras negras)", ws_vis)
cv2.waitKey(0)

# --- 7. Comprobar circularidad ------------------------------------

# ... tras cv2.watershed y antes de crear 'seg'

labels_filtradas = []
for lbl in np.unique(markers_ws):
    if lbl <= 1:
        continue

    # 1) máscara binaria de la región lbl
    mask = np.uint8(markers_ws == lbl)
    # 2) extraer contornos (puede sólo haber uno si la región es conexa)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        continue
    cnt = max(cnts, key=cv2.contourArea)

    area = cv2.contourArea(cnt)
    if area < 100:           # descartar zonas muy pequeñas
        continue

    # 3) perímetro y circularidad
    perim = cv2.arcLength(cnt, True)
    circ = 4 * math.pi * area / (perim**2)

    # 4) ajuste de elipse (necesita al menos 5 puntos)
    aspecto = 0
    if len(cnt) >= 5:
        ellipse = cv2.fitEllipse(cnt)
        (xc, yc), (eje_may, eje_men), ang = ellipse
        aspecto = eje_men / eje_may if eje_may>0 else 0

    # 5) umbrales: circularidad>0.7 y aspecto>0.6 (ajusta según datos)
    if circ > 0.5 and aspecto > 0.5:
        labels_filtradas.append(lbl)

# --- tras haber rellenado labels_filtradas ---

# 1) etiquetas no circulares
labels_all = [lbl for lbl in np.unique(markers_ws) if lbl > 1]
labels_non = [lbl for lbl in labels_all if lbl not in labels_filtradas]

# 2) calcular color medio BGR de cada etiqueta no circular
col_medios = {}
for lbl in labels_non:
    mask = (markers_ws == lbl)
    # extraemos pixeles de img donde mask es True
    pix = img[mask]
    if len(pix)==0: 
        continue
    col_medios[lbl] = np.mean(pix, axis=0)  # [B, G, R]

# 3) agrupar por color parecido (umbral euclídeo)
UMBRAL_COLOR = 10  # ajusta según variación de color de tapones
grupos = []        # lista de listas de etiquetas
usado = set()

for lbl, col in col_medios.items():
    if lbl in usado:
        continue
    grupo = [lbl]
    usado.add(lbl)
    for otro, col2 in col_medios.items():
        if otro in usado:
            continue
        if np.linalg.norm(col - col2) < UMBRAL_COLOR:
            grupo.append(otro)
            usado.add(otro)
    grupos.append(grupo)

# 4) para cada grupo, intentamos fusionar si forma un círculo
for grupo in grupos:
    # unir máscaras de todas las etiquetas del grupo
    mask_grp = np.zeros_like(markers_ws, dtype=np.uint8)
    for lbl in grupo:
        mask_grp[markers_ws == lbl] = 255

    # contornos de la máscara unida
    cnts, _ = cv2.findContours(mask_grp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
        aspecto = eje_men / eje_may if eje_may>0 else 0

    # si el grupo unido ahora sí es “circular”:
    if circ > 0.5 and aspecto > 0.5:
        # le asignamos una nueva etiqueta (o reutilizamos la primera del grupo)
        nueva_lbl = markers_ws.max() + 1
        markers_ws[mask_grp==255] = nueva_lbl
        labels_filtradas.append(nueva_lbl)
        # opcional: eliminar las etiquetas individuales del grupo
        for lbl in grupo:
            if lbl in labels_filtradas:
                labels_filtradas.remove(lbl)


# Ahora sólo coloreamos esas etiquetas válidas
seg = np.zeros_like(img)
colores = {}
centroides = []

for lbl in labels_filtradas:
    color = tuple(np.random.randint(0,255,3).tolist())
    colores[lbl] = color
    seg[markers_ws == lbl] = color

    # calcular y dibujar centroide
    ys, xs = np.where(markers_ws == lbl)
    cx, cy = int(xs.mean()), int(ys.mean())
    centroides.append((cx, cy))
    cv2.circle(seg, (cx, cy), 5, (255,255,255), -1)

# fronteras en negro
seg[markers_ws == -1] = (0,0,0)

cv2.imshow("Sólo tapones circulares", seg)
print("Centroides filtrados:", centroides)
cv2.waitKey(0)
cv2.destroyAllWindows()
