import cv2
import numpy as np
import json
from matplotlib import pyplot as plt

# Aqui se pondria la funcion para diferenciar colores (la actual es provisional)
def clasificar_color(hsv_avg):
    h, s, v = hsv_avg
    if 0 <= h <= 10 or 160 <= h <= 180:
        return "ROJO"
    elif 35 <= h <= 85:
        return "VERDE"
    elif 90 <= h <= 130:
        return "AZUL"
    elif 20 <= h <= 30:
        return "AMARILLO"
    else:
        return "OTROS"

# Nombre de archivo
image_filename = 'taponesjuntos.jpg'
json_output_yolo = 'tapones_detectados.json'
json_output_labelme = 'taponesjuntos.json'

# Cargar imagen
image = cv2.imread(image_filename)
original = image.copy()
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
img_height, img_width = gray.shape

# Umbral y morfología
ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
kernel = np.ones((3, 3), np.uint8)
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

# Fondo y foreground
sure_bg = cv2.dilate(opening, kernel, iterations=3)
dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
ret, sure_fg = cv2.threshold(dist_transform, 0.4 * dist_transform.max(), 255, 0)
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg, sure_fg)

# Componentes conectados y watershed
ret, markers = cv2.connectedComponents(sure_fg)
markers = markers + 1
markers[unknown == 255] = 0
markers = cv2.watershed(image, markers)

# Convertir a HSV
hsv_image = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)

# Listas para exportar
tapones_detectados = []
labelme_shapes = []

# Detección y clasificación
for marker_id in range(2, np.max(markers) + 1):
    mask = np.uint8(markers == marker_id) * 255
    x, y, w, h = cv2.boundingRect(mask)
    if w * h < 100:
        continue

    # Color dominante
    tapón_hsv = hsv_image[y:y+h, x:x+w]
    mask_crop = mask[y:y+h, x:x+w]
    mean_color = cv2.mean(tapón_hsv, mask_crop)[:3]
    color_nombre = clasificar_color(mean_color)

    # Datos para JSON YOLO-style
    tapones_detectados.append({
        "label": color_nombre,
        "x": int(x),
        "y": int(y),
        "width": int(w),
        "height": int(h)
    })

    # Datos para LabelMe
    shape = {
        "label": color_nombre,
        "points": [[x, y], [x + w, y + h]],
        "group_id": None,
        "shape_type": "rectangle",
        "flags": {}
    }
    labelme_shapes.append(shape)

# Guardar JSON tipo YOLO
with open(json_output_yolo, "w") as f:
    json.dump(tapones_detectados, f, indent=4)

# Guardar JSON tipo LabelMe
labelme_json = {
    "version": "5.0.1",
    "flags": {},
    "shapes": labelme_shapes,
    "imagePath": image_filename,
    "imageData": None,
    "imageHeight": img_height,
    "imageWidth": img_width
}
with open(json_output_labelme, "w") as f:
    json.dump(labelme_json, f, indent=4)

# Mostrar imagen con etiquetas
for t in tapones_detectados:
    cv2.rectangle(image, (t["x"], t["y"]), (t["x"]+t["width"], t["y"]+t["height"]), (0, 255, 0), 2)
    cv2.putText(image, t["label"], (t["x"], t["y"] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36, 255, 12), 1)

plt.figure(figsize=(12, 12))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.title('Tapones etiquetados por color')
plt.axis('off')
plt.show()
