import cv2

class Camara:
    def __init__(self, index=0):
        """
        Inicializa la cámara con el índice especificado.
        Por defecto index=0, que suele corresponder a la webcam USB principal.
        """
        self.index = index
        self.cap = None

    def abrir(self):
        """Abre el dispositivo de vídeo."""
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara con índice {self.index}")

    def cerrar(self):
        """Libera el dispositivo de vídeo."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def tomar_foto(self, ruta_archivo="fotoActual.jpg"):
        """
        Abre la cámara, captura un frame y lo guarda en ruta_archivo.
        Devuelve True si la foto se guardó correctamente, False en caso contrario.
        """
        try:
            self.abrir()
            ret, frame = self.cap.read()
            if not ret:
                print("Error: no se pudo capturar el frame.")
                return False

            # Guarda la imagen en disco
            exito = cv2.imwrite(ruta_archivo, frame)
            if not exito:
                print(f"Error: no se pudo guardar la foto en {ruta_archivo}.")
                return False

            print(f"Foto guardada en {ruta_archivo}")
            return True

        finally:
            # Asegura liberar la cámara aunque ocurra un error
            self.cerrar()


# Ejemplo de uso:
if __name__ == "__main__":
    cam = Camara(index=0)
    éxito = cam.tomar_foto()  # Guarda por defecto en "fotoActual.jpg"
    if éxito:
        print("¡Captura completada!")
    else:
        print("La captura falló.")
