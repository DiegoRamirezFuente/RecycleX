# decisionMaker.py  – v3  (normalización completa)
import json
from typing import List, Tuple, Dict, Optional

import cv2


class CapDecisionMaker:
    """
    Selecciona el tapón con mayor puntuación:
        score = k1 * conf_norm + k2 * square_norm + k3 * area_norm
    Todas las variables están normalizadas a [0, 1] por min-max en cada ciclo.
    Ajusta k1, k2 y k3 a tu gusto desde el constructor o a posteriori.
    """

    def __init__(
        self,
        json_path: str,
        k1: float = 5.0,
        k2: float = 1.0,
        k3: float = 3.0,
    ) -> None:
        self.json_path = json_path
        self.k1 = k1
        self.k2 = k2
        self.k3 = k3

    # ---------- utilidades internas ---------- #
    def load_detections(self) -> List[Dict]:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"ERROR cargando detecciones: {e}")
            return []

    @staticmethod
    def compute_squareness(bbox: List[int]) -> float:
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        if w <= 0 or h <= 0:
            return 0.0
        return 1.0 - abs(w - h) / max(w, h)    # 1.0 = cuadrado perfecto

    @staticmethod
    def _norm(value: float, vmin: float, vmax: float) -> float:
        """Min-max normalización a [0,1]; devuelve 1.0 si rango cero."""
        return 1.0 if vmax == vmin else (value - vmin) / (vmax - vmin)

    # ---------- API pública ---------- #
    def select_best_cap(self) -> Optional[Dict]:
        detections = self.load_detections()
        if not detections:
            return None

        # Pre-procesar métricas por cada detección
        metrics = []
        for det in detections:
            conf = float(det.get("confidence", 0.0))
            area = float(det.get("area", 0.0))
            square = self.compute_squareness(det.get("bounding_box", [0, 0, 0, 0]))
            metrics.append((det, conf, square, area))

        # Calcular min-max para normalizar
        confs, squares, areas = zip(*[(m[1], m[2], m[3]) for m in metrics])
        cmin, cmax = min(confs), max(confs)
        smin, smax = min(squares), max(squares)
        amin, amax = min(areas), max(areas)

        best_det: Optional[Dict] = None
        best_score: float = float("-inf")

        for det, conf, square, area in metrics:
            conf_n = self._norm(conf, cmin, cmax)
            square_n = self._norm(square, smin, smax)
            area_n = self._norm(area, amin, amax)

            score = self.k1 * conf_n + self.k2 * square_n + self.k3 * area_n
            if score > best_score:
                best_score = score
                best_det = det

        return best_det

    def get_best_cap_info(
        self,
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int, int, int], str]]:
        best = self.select_best_cap()
        if best is None:
            return None
        centroid = tuple(best["centroid"])
        bbox = tuple(best["bounding_box"])
        cap_identifier = f"Clase {best.get('class', '?')}"
        return centroid, bbox, cap_identifier

    def draw_selected_on_image(
        self,
        base_image: "cv2.typing.MatLike",
        selected_cap_data: Optional[Dict],
    ) -> Optional["cv2.typing.MatLike"]:
        if base_image is None:
            print("ERROR: imagen base nula.")
            return None

        img = base_image.copy()
        if selected_cap_data:
            try:
                x1, y1, x2, y2 = selected_cap_data["bounding_box"]
                cx, cy = selected_cap_data["centroid"]
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 128, 0), 2)
                cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            except KeyError as e:
                print(f"ERROR dibujando tapón: falta {e}")
        return img
