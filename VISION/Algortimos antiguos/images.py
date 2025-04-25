import cv2
import os
from datetime import datetime

# Índice de la cámara USB
indice_camara = 0

# Crear carpeta para guardar fotos
carpeta = "fotos"
os.makedirs(carpeta, exist_ok=True)

# Conectar a la cámara correcta
cap = cv2.VideoCapture(indice_camara)
if not cap.isOpened():
    print(f"No se pudo acceder a la cámara en el índice {indice_camara}.")
    exit()

print("Presiona 's' para tomar una foto. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar imagen.")
        break

    cv2.imshow("Webcam", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join(carpeta, f"foto_{timestamp}.jpg")
        cv2.imwrite(ruta, frame)
        print(f"Foto guardada en: {ruta}")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
