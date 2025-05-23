import json
import cv2
from typing import List, Tuple, Dict, Optional


class CapDecisionMaker:
    """
    Decide qué tapón manipular usando:
        score = k1*conf_norm + k2*sqr_norm + k3*area_norm
    Las tres magnitudes se normalizan a [0,1] con min-max.
    """

    # ------------------------------------------------------------------
    # INICIALIZACIÓN
    # ------------------------------------------------------------------
    def __init__(
        self,
        json_path: str,
        k1: float = 5.0,      # peso confianza
        k2: float = 1.0,      # peso cuadratez
        k3: float = 3.0       # peso área
    ):
        self.json_path = json_path
        self.k1, self.k2, self.k3 = k1, k2, k3
        self.detections: List[Dict] = self.load_detections()

        # Pre-calcula mínimos y máximos para la normalización
        self._prepare_normalization()

    # ------------------------------------------------------------------
    # UTILIDADES BÁSICAS
    # ------------------------------------------------------------------
    def load_detections(self) -> List[Dict]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def compute_squareness(bbox: List[int]) -> float:
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        if max(w, h) == 0:
            return 0.0
        return 1.0 - abs(w - h) / max(w, h)

    @staticmethod
    def _norm(value: float, vmin: float, vmax: float) -> float:
        """Normalización min-max a [0,1]."""
        return 0.0 if vmax == vmin else (value - vmin) / (vmax - vmin)

    # ------------------------------------------------------------------
    # NORMALIZACIÓN GLOBAL
    # ------------------------------------------------------------------
    def _prepare_normalization(self):
        """Obtiene rangos min-max de confianza, cuadratez y área."""
        if not self.detections:
            self.min_conf = self.max_conf = 0.0
            self.min_sqr = self.max_sqr = 0.0
            self.min_area = self.max_area = 0.0
            return

        confs, sqrs, areas = [], [], []
        for det in self.detections:
            confs.append(det.get("confidence", 0.0))
            areas.append(det.get("area", 0.0))
            sqrs.append(self.compute_squareness(det["bounding_box"]))

        self.min_conf, self.max_conf = min(confs), max(confs)
        self.min_sqr, self.max_sqr = min(sqrs), max(sqrs)
        self.min_area, self.max_area = min(areas), max(areas)

    # ------------------------------------------------------------------
    # PUNTUACIÓN
    # ------------------------------------------------------------------
    def compute_score(self, det: Dict) -> float:
        """Devuelve la puntuación normalizada ponderada."""
        conf = det.get("confidence", 0.0)
        area = det.get("area", 0.0)
        sqr = self.compute_squareness(det["bounding_box"])

        conf_n = self._norm(conf, self.min_conf, self.max_conf)
        area_n = self._norm(area, self.min_area, self.max_area)
        sqr_n = self._norm(sqr, self.min_sqr, self.max_sqr)

        return (self.k1 * conf_n) + (self.k2 * sqr_n) + (self.k3 * area_n)

    # ------------------------------------------------------------------
    # SELECCIÓN
    # ------------------------------------------------------------------
    def select_best_cap(self) -> Optional[Dict]:
        best_cap, best_score = None, float("-inf")

        for det in self.detections:
            score = self.compute_score(det)
            if score > best_score:
                best_score, best_cap = score, det

        return best_cap

    def get_best_cap_info(
        self
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int, int, int], str]]:
        best = self.select_best_cap()
        if best is None:
            return None
        centroid = tuple(best["centroid"])
        bbox = tuple(best["bounding_box"])
        color = best.get("color", f"Clase {best.get('class', '?')}")
        return centroid, bbox, color

    # ------------------------------------------------------------------
    # VISUALIZACIÓN (sin cambios relevantes)
    # ------------------------------------------------------------------
    @staticmethod
    def resize_to_fit_screen(img, mw=1920, mh=1080):
        h, w = img.shape[:2]
        scale = min(mw / w, mh / h, 1.0)
        return cv2.resize(img, (int(w * scale), int(h * scale)), cv2.INTER_AREA)

    def draw_selected_on_image(self, image_path: str):
        best = self.select_best_cap()
        if best is None:
            print("[INFO] No se encontró ningún tapón para dibujar.")
            return

        image = cv2.imread(image_path)
        if image is None:
            print(f"[ERROR] No se pudo cargar la imagen: {image_path}")
            return

        x1, y1, x2, y2 = best["bounding_box"]
        cx, cy = best["centroid"]

        img_draw = image.copy()
        cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.circle(img_draw, (cx, cy), 5, (0, 0, 255), -1)

        conf_n = self._norm(best["confidence"], self.min_conf, self.max_conf)
        area_n = self._norm(best["area"], self.min_area, self.max_area)
        sqr_n = self._norm(self.compute_squareness(best["bounding_box"]),
                           self.min_sqr, self.max_sqr)

        label = (f"c={conf_n:.2f}  q={sqr_n:.2f}  a={area_n:.2f}")
        cv2.putText(img_draw, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Tapón seleccionado", self.resize_to_fit_screen(img_draw))
        print("[INFO] Pulsa ENTER para cerrar la ventana.")
        while cv2.waitKey(0) != 13:
            pass
        cv2.destroyAllWindows()


# ----------------------------------------------------------------------
# EJEMPLO DE USO
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Prueba libre de pesos (k1, k2, k3)
    decision = CapDecisionMaker(
        "detecciones_tapones.json",
        k1=1.0, k2=2.0, k3=1.0
    )
    info = decision.get_best_cap_info()
    if info:
        cent, bbox, col = info
        print(f"Tapón en {cent} | BBox: {bbox} | Color: {col}")
        decision.draw_selected_on_image("tapones3.jpg")
    else:
        print("No se encontró ningún tapón.")
