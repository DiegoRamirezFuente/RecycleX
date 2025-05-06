from visionYOLO import TaponesDetector
from decision import CapDecisionMaker

# Ruta de la imagen a procesar
IMAGE_PATH = "tapones3.jpg"

# Archivos de salida
JSON_OUTPUT_PATH = "detecciones_tapones.json"
IMAGE_OUTPUT_PATH = "tapones_resultado.jpg"

# Modelo YOLO entrenado
MODEL_PATH = "train3/weights/best.pt"

def main():
    # 1. Detección de tapones
    print("[INFO] Iniciando detección con YOLO...")
    detector = TaponesDetector(MODEL_PATH)
    results, detections = detector.analizar_imagen(IMAGE_PATH)
    detector.guardar_json(detections, JSON_OUTPUT_PATH)
    detector.guardar_imagen_resultado(results, IMAGE_OUTPUT_PATH)
    print(f"[INFO] JSON generado: {JSON_OUTPUT_PATH}")

    # 2. Algoritmo de decisión
    print("[INFO] Ejecutando algoritmo de decisión...")
    decision = CapDecisionMaker(JSON_OUTPUT_PATH, min_area=2000, min_confidence=0.9)
    selected = decision.get_best_cap_info()

    if selected:
        centroid, bbox, color = selected
        print(f"[INFO] Tapón seleccionado: Centroid={centroid}, BBox={bbox}, Color={color}")
        decision.draw_selected_on_image(IMAGE_PATH)
    else:
        print("[INFO] No se encontró ningún tapón válido.")

if __name__ == "__main__":
    main()
