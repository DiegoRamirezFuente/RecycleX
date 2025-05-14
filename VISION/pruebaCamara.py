import cv2

def main():
    # Intenta abrir la cámara en el índice 0 (puedes cambiarlo si tienes varias cámaras)
    cap = cv2.VideoCapture(0)
    
    # Comprueba que se haya abierto correctamente
    if not cap.isOpened():
        print("Error: no se pudo abrir la cámara.")
        return

    print("Presiona 'q' para salir.")

    while True:
        # Captura frame a frame
        ret, frame = cap.read()
        if not ret:
            print("Error: no se recibió un frame.")
            break

        # Muestra el frame en una ventana llamada 'Webcam'
        cv2.imshow('Webcam', frame)

        # Espera 1 ms y comprueba si se ha pulsado 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Al salir, libera el dispositivo y cierra ventanas
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
