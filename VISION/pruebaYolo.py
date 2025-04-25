from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import json

# Cargar modelo
model = YOLO('train3/weights/best.pt')

# Ruta de la imagen
image_path = 'tapones3.jpg'

# Inferencia
results = model(image_path)[0]

# Lista para almacenar resultados
detections = []

# Extraer datos para el JSON personalizado
for box in results.boxes:
    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    confidence = float(box.conf[0])
    cls = int(box.cls[0]) if box.cls is not None else -1
    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
    area = (x2 - x1) * (y2 - y1)

    detections.append({
        "bounding_box": [x1, y1, x2, y2],
        "centroid": [cx, cy],
        "area": area,
        "confidence": round(confidence, 4),
        "class": cls,
    })

# Guardar detecciones en archivo JSON
with open('detecciones_tapones.json', 'w') as f:
    json.dump(detections, f, indent=4)

# Mostrar imagen con BBoxes "por defecto" de YOLO
image_with_yolo_boxes = results.plot()

# Guardar imagen
output_image_path = 'tapones_resultado.jpg'
cv2.imwrite(output_image_path, image_with_yolo_boxes)

# Mostrar con matplotlib
image_rgb = cv2.cvtColor(image_with_yolo_boxes, cv2.COLOR_BGR2RGB)
plt.figure(figsize=(12, 10))
plt.imshow(image_rgb)
plt.axis('off')
plt.title('Detección de Tapones (YOLO Style)')
plt.show()
