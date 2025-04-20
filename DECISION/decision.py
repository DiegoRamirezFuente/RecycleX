import cv2
import numpy as np
import math

class CapSelector:
    """
    Clase para seleccionar el tapón de mayor circularidad entre un conjunto de contornos.

    Métodos públicos:
    • compute_circularity(contour) → float
        Calcula la circularidad de un contorno: 4·π·area/perímetro² (valor en [0,1]).
    • compute_centroid(contour) → (int x, int y)
        Calcula el centroide (x,y) de un contorno usando momentos de imagen.
    • select_best_contour(contours) → contour | None
        Devuelve el contorno con mayor circularidad del listado, o None si está vacío.
    • get_best_centroid(contours) → (int x, int y) | None
        Selecciona el contorno óptimo y devuelve sus coordenadas de centroide.

    Uso ejemplo:
        from cap_selector import CapSelector

        # 'contours' es la lista de contornos obtenida en tu pipeline de visión
        best_cnt = CapSelector.select_best_contour(contours)
        if best_cnt is not None:
            x, y = CapSelector.compute_centroid(best_cnt)
            print(f"Tapón más circular en: ({x}, {y})")
        # o directamente:
        coords = CapSelector.get_best_centroid(contours)
        if coords:
            print("Tapón objetivo en:", coords)
    """

    @staticmethod
    def compute_circularity(contour: np.ndarray) -> float:
        """
        Calcula la circularidad de un contorno:
            C = 4 * π * area / (perimeter²)
        Un círculo perfecto tiene C = 1.
        """
        area = cv2.contourArea(contour)
        if area <= 0:
            return 0.0
        perim = cv2.arcLength(contour, True)
        if perim <= 0:
            return 0.0
        return 4 * math.pi * area / (perim * perim)

    @staticmethod
    def compute_centroid(contour: np.ndarray) -> (int, int):
        """
        Calcula el centroide (x, y) de un contorno usando momentos.
        Si m00 es cero, cae en la media aritmética de los puntos.
        """
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            pts = contour.reshape(-1, 2)
            cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
        return int(cx), int(cy)

    @classmethod
    def select_best_contour(cls, contours: list) -> np.ndarray or None:
        """
        Selecciona y devuelve el contorno con mayor circularidad.
        Si la lista está vacía, devuelve None.
        """
        best = None
        best_score = -1.0
        for cnt in contours:
            score = cls.compute_circularity(cnt)
            if score > best_score:
                best_score = score
                best = cnt
        return best

    @classmethod
    def get_best_centroid(cls, contours: list) -> (int, int) or None:
        """
        Selecciona el contorno más circular y devuelve sus coordenadas (x, y).
        Devuelve None si no hay contornos.
        """
        best = cls.select_best_contour(contours)
        if best is None:
            return None
        return cls.compute_centroid(best)
