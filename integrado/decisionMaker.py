import json
import cv2
from typing import List, Tuple, Dict, Optional

class CapDecisionMaker:
    def __init__(self, json_path: str, min_area: float = 1000.0, min_confidence: float = 0.9):
        self.json_path = json_path
        self.min_area = min_area
        self.min_confidence = min_confidence
        self.detections = self.load_detections()

    def load_detections(self) -> List[Dict]:
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        return data

    def is_valid(self, detection: Dict) -> bool:
        return (
            detection['area'] >= self.min_area and
            detection['confidence'] >= self.min_confidence
        )

    def compute_squareness(self, bbox: List[int]) -> float:
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        if max(width, height) == 0:
            return 0.0
        return 1.0 - abs(width - height) / max(width, height)

    def select_best_cap(self) -> Optional[Dict]:
        best_score = -1.0
        best_cap = None

        for det in self.detections:
            if not self.is_valid(det):
                continue
            score = self.compute_squareness(det['bounding_box'])
            if score > best_score:
                best_score = score
                best_cap = det

        return best_cap

    def get_best_cap_info(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int, int, int], str]]:
        best = self.select_best_cap()
        if best is None:
            return None
        centroid = tuple(best['centroid'])
        bounding_box = tuple(best['bounding_box'])  # (x1, y1, x2, y2)

        # Usa 'color' si existe, si no usa 'class' como texto
        cap_color = best.get('color', f"Clase {best.get('class', '?')}")

        return centroid, bounding_box, cap_color


    def resize_to_fit_screen(self, image, max_width=1920, max_height=1080):
        height, width = image.shape[:2]
        scale = min(max_width / width, max_height / height, 1.0)  # No agranda, solo reduce
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def draw_selected_on_image(self, image_path: str):
        best = self.select_best_cap()
        if best is None:
            print("[INFO] No se encontró ningún tapón válido para dibujar.")
            return

        image = cv2.imread(image_path)
        if image is None:
            print(f"[ERROR] No se pudo cargar la imagen: {image_path}")
            return

        x1, y1, x2, y2 = best['bounding_box']
        cx, cy = best['centroid']
        image_copy = image.copy()

        cv2.rectangle(image_copy, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.circle(image_copy, (cx, cy), 5, (0, 0, 255), -1)

        cap_color = best.get('color', f"Clase {best.get('class', '?')}")
        label = f"Clase: {best.get('class', '?')} | Conf: {best.get('confidence', 0):.2f} | Color: {cap_color}"

        cv2.putText(image_copy, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Redimensionar imagen para que quepa en pantalla
        image_resized = self.resize_to_fit_screen(image_copy)

        cv2.imshow("Tapón seleccionado", image_resized)
        print("[INFO] Pulsa ENTER para cerrar la ventana.")
        while True:
            key = cv2.waitKey(0)
            if key == 13:  # Enter
                break
        cv2.destroyAllWindows()


#####################################################################################
# EJEMPLO DE USO
#####################################################################################
if __name__ == "__main__":
    print("Ejemplo de uso de CapDecisionMaker")
    decision = CapDecisionMaker("capDetectionsFile.json", min_area=2000, min_confidence=0.9)
    result = decision.get_best_cap_info()

    if result:
        centroid, bounding_box, cap_color = result
        print(f"Tapón seleccionado en {centroid} | Bounding Box: {bounding_box} | Color: {cap_color}")
        decision.draw_selected_on_image("tapones3.jpg")
    else:
        print("No se encontró ningún tapón válido.")
