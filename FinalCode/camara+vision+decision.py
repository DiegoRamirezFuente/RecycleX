from visionYOLO import TaponesDetector
from decision import CapDecisionMaker
from camaraAcceso import Camara
#from movRobot import RobotController

# Ruta de la foto tomada por la cámara
IMAGE_PATH = "taponesjuntos.jpg"

# Archivos de salida
JSON_OUTPUT_PATH = "detecciones_tapones.json"
IMAGE_OUTPUT_PATH = "tapones_resultado.jpg"

# Modelo YOLO entrenado
MODEL_PATH = "train3/weights/best.pt"

def main():
    cam = Camara(index=0)  # Ajusta el índice de la cámara si es necesario
    detector = TaponesDetector(MODEL_PATH)

    while True:
        entrada = input("\n[INFO] Presiona Enter para iniciar el proceso o escribe 'q' para salir: ")
        if entrada.lower() == 'q':
            print("[INFO] Saliendo del programa.")
            break

        # 1. Captura de imagen
        print("[INFO] Capturando imagen de la cámara...")
        if not cam.tomar_foto(IMAGE_PATH):
            print("[ERROR] No se pudo capturar la imagen. Inténtalo de nuevo.")
            continue
        print(f"[INFO] Imagen capturada: {IMAGE_PATH}")

        # 2. Detección de tapones con YOLO
        print("[INFO] Iniciando detección con YOLO...")
        results, detections = detector.analizar_imagen(IMAGE_PATH)
        detector.guardar_json(detections, JSON_OUTPUT_PATH)
        detector.guardar_imagen_resultado(results, IMAGE_OUTPUT_PATH)
        print(f"[INFO] JSON generado: {JSON_OUTPUT_PATH}")
        print(f"[INFO] Imagen de resultados: {IMAGE_OUTPUT_PATH}")

        # 3. Algoritmo de decisión
        print("[INFO] Ejecutando algoritmo de decisión...")
        decision = CapDecisionMaker(JSON_OUTPUT_PATH, min_area=2000, min_confidence=0.9)
        selected = decision.get_best_cap_info()

        if selected:
            centroid, bbox, color = selected
            print(f"[INFO] Tapón seleccionado: Centroid={centroid}, BBox={bbox}, Color={color}")
            #decision.draw_selected_on_image(IMAGE_PATH)
        else:
            print("[INFO] No se encontró ningún tapón válido.")

if __name__ == "__main__":
    main()
