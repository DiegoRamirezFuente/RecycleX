import cv2
import numpy as np
from skimage.feature import peak_local_max
from scipy import ndimage as ndi

# --- 1. Cargar y preprocesar ------------------------
img = cv2.imread("taponesjuntos.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5, 5), 0)

# --- 2. Umbralización inversa con Otsu ---------------
_, bin_inv = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
# limpieza de ruido
kernel = np.ones((3,3), np.uint8)
bin_clean = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN,kernel, iterations=2)

# --- 3. Distancia y picos locales --------------------
# distancia Euclidiana
dist = cv2.distanceTransform(bin_clean, cv2.DIST_L2, 5)
# extraer coordenadas de picos locales
# min_distance debe ajustarse al radio aproximado de los tapones
coords = peak_local_max(dist,min_distance=20, threshold_rel=0.4, labels=bin_clean)
# crear máscara de marcadores vacía
markers = np.zeros(dist.shape, dtype=np.int32)
for i, (y, x) in enumerate(coords, start=1):
    markers[y, x] = i

# opcional: expandir ligeramente cada marcador
markers = ndi.grey_dilation(markers, size=(3,3))

# --- 4. Fondo seguro y región desconocida ------------
sure_bg = cv2.dilate(bin_clean, kernel, iterations=3)
unknown = cv2.subtract(sure_bg, (markers > 0).astype(np.uint8)*255)

# --- 5. Preparar marcadores para cv2.watershed -------
# watershed requiere:
#   • fondo etiquetado con 1
#   • marcadores internos >= 2
#   • región desconocida = 0
markers_ws = markers.copy()
markers_ws[markers_ws > 0] += 1      # ahora van de 2,3,4...
markers_ws[sure_bg == 0] = 1         # todo lo que no es tapón = fondo (etiqueta 1)
markers_ws[unknown == 255] = 0       # bordes/área desconocida

# --- 6. Watershed ------------------------------------
cv2.watershed(img, markers_ws)
# tras esto:
#   • pixels con -1 son fronteras
#   • etiquetas ≥ 2 son cada tapón

# --- 7. Visualizar segmentación y calcular centroides -
seg = np.zeros_like(img)
colores = {}
for lbl in np.unique(markers_ws):
    if lbl <= 1:  # saltar fondo y fronteras
        continue
    color = tuple(np.random.randint(0,255,3).tolist())
    colores[lbl] = color
    seg[markers_ws == lbl] = color

# dibujar fronteras en negro
seg[markers_ws == -1] = (0,0,0)

# calcular centroides
centroides = []
for lbl, color in colores.items():
    ys, xs = np.where(markers_ws == lbl)
    cx, cy = int(xs.mean()), int(ys.mean())
    centroides.append((cx, cy))
    # opcional: dibujar un círculo en el centro
    cv2.circle(seg, (cx, cy), 5, (255,255,255), -1)

# --- 8. Mostrar / guardar resultado ------------------
cv2.imshow("Segmentación mejorada", seg)
print("Centroides (x,y):", centroides)
cv2.waitKey(0)
cv2.destroyAllWindows()
