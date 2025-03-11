import cv2

index = 0
while True:
    cap = cv2.VideoCapture(index)
    if not cap.read()[0]:
        break
    print(f"Cámara encontrada en índice {index}")
    cap.release()
    index += 1
