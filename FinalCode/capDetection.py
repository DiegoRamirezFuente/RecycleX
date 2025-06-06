import cv2
import json
import matplotlib.pyplot as plt
from ultralytics import YOLO

class TaponesDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def analizar_imagen(self, image_path):
        results = self.model(image_path)[0]
        detections = []

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
                "class": cls
            })

        return results, detections

    def guardar_json(self, detections, output_path="detecciones_tapones.json"):
        with open(output_path, 'w') as f:
            json.dump(detections, f, indent=4)

    def guardar_imagen_resultado(self, results, output_path="tapones_resultado.jpg"):
        image_with_boxes = results.plot()
        cv2.imwrite(output_path, image_with_boxes)

    def mostrar_resultado(self, results, title="Detección de Tapones (YOLO Style)"):
        image_with_boxes = results.plot()
        image_rgb = cv2.cvtColor(image_with_boxes, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(12, 10))
        plt.imshow(image_rgb)
        plt.axis('off')
        plt.title(title)
        plt.show()

# Ejemplo de uso
if __name__ == "__main__":
    modelo = "train3/weights/best.pt"
    imagen = "tapones3.jpg"

    detector = TaponesDetector(modelo)
    resultados, detecciones = detector.analizar_imagen(imagen)

    detector.guardar_json(detecciones)
    detector.guardar_imagen_resultado(resultados)
    detector.mostrar_resultado(resultados)
