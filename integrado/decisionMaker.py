# decisionMaker.py
import json
import cv2
from typing import List, Tuple, Dict, Optional

class CapDecisionMaker:
    def __init__(self, json_path: str, min_area: float = 1000.0, min_confidence: float = 0.9): # Como en tu archivo
        self.json_path = json_path
        self.min_area = min_area
        self.min_confidence = min_confidence
        # self.detections = self.load_detections() # Cargar bajo demanda

    def load_detections(self) -> List[Dict]: # Como en tu archivo
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"ERROR: Archivo de detecciones '{self.json_path}' no encontrado.")
            return []
        except json.JSONDecodeError:
            print(f"ERROR: Error al decodificar JSON desde '{self.json_path}'. ¿Está vacío o corrupto?")
            return []


    def is_valid(self, detection: Dict) -> bool: # Como en tu archivo
        return (
            detection.get('area', 0) >= self.min_area and
            detection.get('confidence', 0) >= self.min_confidence
        )

    def compute_squareness(self, bbox: List[int]) -> float: # Como en tu archivo
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0: # Asegurar dimensiones positivas
            return 0.0
        return 1.0 - abs(width - height) / max(width, height)

    def select_best_cap(self) -> Optional[Dict]: # Como en tu archivo
        self.detections = self.load_detections() # Carga las detecciones más recientes
        best_score = -1.0  # Inicializar con un valor que cualquier tapón válido pueda superar
        best_cap = None

        valid_detections = [det for det in self.detections if self.is_valid(det)]
        if not valid_detections:
            return None

        for det in valid_detections:
            # Criterio principal: "cuadratura" del bounding box
            # Tapones más cuadrados suelen ser mejores detecciones frontales.
            score = self.compute_squareness(det['bounding_box'])

            # Opcional: añadir otros factores al score, como confianza o área (con pesos)
            # score += det['confidence'] * 0.2 # Darle un peso a la confianza
            # score += (det['area'] / 10000) * 0.1 # Darle un peso al área (normalizada)

            if score > best_score:
                best_score = score
                best_cap = det
        return best_cap


    def get_best_cap_info(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int, int, int], str]]: # Como en tu archivo
        best = self.select_best_cap()
        if best is None:
            return None
        centroid = tuple(best['centroid'])
        bounding_box = tuple(best['bounding_box'])
        # La clase 'class' del JSON es el índice numérico. El color real se mapea en main.py
        cap_identifier = f"Clase {best.get('class', '?')}" # Mantenemos esto para depuración si es necesario
        return centroid, bounding_box, cap_identifier


    def draw_selected_on_image(self, base_image: cv2.typing.MatLike, selected_cap_data: Optional[Dict]) -> Optional[cv2.typing.MatLike]:
        """
        Dibuja el tapón seleccionado (bounding box y centroide) en una COPIA de la imagen base.
        Si no hay tapón seleccionado, devuelve la imagen base sin modificar.

        Args:
            base_image: La imagen original (objeto NumPy de OpenCV) donde dibujar.
            selected_cap_data: El diccionario de la detección del tapón seleccionado.

        Returns:
            Una nueva imagen con el tapón seleccionado dibujado, o la imagen original si no hay selección.
        """
        if base_image is None:
            print("ERROR: draw_selected_on_image recibió una imagen base nula.")
            return None

        image_to_draw_on = base_image.copy() # Siempre trabajar sobre una copia

        if selected_cap_data:
            try:
                x1, y1, x2, y2 = selected_cap_data['bounding_box']
                cx, cy = selected_cap_data['centroid']

                # Dibujar el bounding box del tapón seleccionado (e.g., azul brillante)
                cv2.rectangle(image_to_draw_on, (x1, y1), (x2, y2), (255, 128, 0), 2) # BGR, grosor 2
                # Dibujar el centroide (e.g., punto rojo)
                cv2.circle(image_to_draw_on, (cx, cy), 5, (0, 0, 255), -1) # BGR, círculo relleno
            except KeyError as e:
                print(f"ERROR: Faltan datos en selected_cap_data para dibujar: {e}")
                return image_to_draw_on # Devuelve la copia sin dibujar si faltan datos
        
        return image_to_draw_on

    # La función resize_to_fit_screen y el ejemplo de uso en __main__ pueden eliminarse o adaptarse,
    # ya que el dimensionamiento principal para la GUI lo hará Qt y el flujo es desde main.py
    # def resize_to_fit_screen(...): #
    # if __name__ == "__main__": #