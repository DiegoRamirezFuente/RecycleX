# cameraControl.py
import cv2
import time # Necesario para el delay

class Camara:
    def __init__(self, index=0, warmup_time=1.5): # warmup_time en segundos
        """
        Inicializa la cámara.
        warmup_time: Tiempo (s) para permitir que la cámara ajuste la exposición.
        """
        self.index = index
        self.cap = None
        self.warmup_time = warmup_time

    def abrir(self):
        """Abre el dispositivo de vídeo y espera para el ajuste."""
        # Usando el índice 2 y CAP_V4L2 como en tu archivo
        self.cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            # Intento alternativo si V4L2 falla con el índice específico
            print(f"WARN: No se pudo abrir la cámara {self.index} con CAP_V4L2. Intentando con API por defecto...")
            self.cap = cv2.VideoCapture(self.index) # Prueba con el índice original y API por defecto
            if not self.cap.isOpened():
                raise RuntimeError(f"No se pudo abrir la cámara con índice {self.index} (intentado con V4L2 y API por defecto)")

        if self.warmup_time > 0:
            print(f"INFO: Cámara {self.index} abierta. Esperando {self.warmup_time}s para ajuste de exposición...")
            time.sleep(self.warmup_time)
        else:
            print(f"INFO: Cámara {self.index} abierta.")


    def cerrar(self): # Sin cambios
        """Libera el dispositivo de vídeo."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def tomar_foto(self, ruta_archivo="fotoActual.jpg"): # Modificada para usar el nuevo abrir()
        """
        Abre la cámara (con calentamiento), captura un frame y lo guarda.
        """
        try:
            self.abrir() # abrir() ahora incluye el tiempo de calentamiento

            # Opcional: Capturar y descartar algunos frames iniciales adicionales
            # for _ in range(3): # Descarta 3 frames
            #     if self.cap: self.cap.grab()

            ret, frame = self.cap.read()
            if not ret:
                print("ERROR: No se pudo capturar el frame después del calentamiento.")
                return False

            exito = cv2.imwrite(ruta_archivo, frame)
            if not exito:
                print(f"ERROR: No se pudo guardar la foto en {ruta_archivo}.")
                return False

            print(f"INFO: Foto guardada en {ruta_archivo}")
            return True
        except Exception as e:
            print(f"ERROR: Excepción en tomar_foto: {e}")
            return False
        finally:
            self.cerrar()


# Ejemplo de uso (sin cambios)
if __name__ == "__main__":
    cam = Camara(index=0, warmup_time=2.0) # Ejemplo con 2 segundos de calentamiento
    exito = cam.tomar_foto()
    if exito:
        print("¡Captura completada!")
    else:
        print("La captura falló.")