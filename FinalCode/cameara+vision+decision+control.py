from visionYOLO import TaponesDetector
from decision import CapDecisionMaker
from camaraAcceso import Camara
from movRobot import RobotController
import time

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"            # IP del robot UR
DIGITAL_OUTPUT_PIN = 4                 # Pin digital para contacto

# Rutas y modelo
IMAGE_PATH = "taponesjuntos.jpg"
JSON_OUTPUT_PATH = "detecciones_tapones.json"
IMAGE_OUTPUT_PATH = "tapones_resultado.jpg"
MODEL_PATH = "train3/weights/best.pt"


def main():
    # Instancias de cámara, detector y robot
    cam = Camara(index=0)
    detector = TaponesDetector(MODEL_PATH)
    robot = RobotController(robot_ip=ROBOT_IP,
                             digital_output_pin=DIGITAL_OUTPUT_PIN)

    # Conectar robot (solo una vez)
    robot.connect()
    try:
        while True:
            entrada = input("\n[INFO] Presiona Enter para iniciar o 'q' + Enter para salir: ")
            if entrada.lower() == 'q':
                print("[INFO] Saliendo del programa.")
                break

            # 1️⃣ Posicionamiento inicial del robot
            print("[INFO] Moviendo robot a posición de trabajo...")
            robot.initial_moves()

            # 2️⃣ Captura de imagen
            print("[INFO] Capturando imagen...")
            if not cam.tomar_foto(IMAGE_PATH):
                print("[ERROR] Falla al capturar imagen. Reintentando...")
                continue
            print(f"[INFO] Imagen guardada en {IMAGE_PATH}")

            # 3️⃣ Detección YOLO
            print("[INFO] Ejecutando detección de tapones...")
            results, detections = detector.analizar_imagen(IMAGE_PATH)
            detector.guardar_json(detections, JSON_OUTPUT_PATH)
            detector.guardar_imagen_resultado(results, IMAGE_OUTPUT_PATH)
            print(f"[INFO] Resultados guardados en {JSON_OUTPUT_PATH}, {IMAGE_OUTPUT_PATH}")

            # 4️⃣ Algoritmo de decisión
            print("[INFO] Aplicando criterio de selección...")
            decision = CapDecisionMaker(JSON_OUTPUT_PATH,
                                        min_area=2000,
                                        min_confidence=0.9)
            selected = decision.get_best_cap_info()

            if selected:
                centroid, bbox, color = selected
                px, py = centroid
                print(f"[INFO] Tapón elegido en píxeles: X={px}, Y={py}, Color={color}")
                #decision.draw_selected_on_image(IMAGE_PATH)

                # 5️⃣ Movimiento hacia el tapón
                print("[INFO] Moviendo robot hacia el tapón detectado...")
                robot.move_to_pixel(px, py)

                # 6️⃣ Descenso hasta contacto
                #if robot.descend_until_contact():
                #    print("[INFO] Contacto detectado. Pin activado.")
                #    time.sleep(1.0)
                # 6️⃣ Descenso con fuerza controlada
                if robot.descend_until_contact():
                    print("[INFO] Contacto detectado. Aplicando fuerza adicional...")
                    robot.descend_with_force(duration=2.0, force=-10.0)  # solo aplica fuerza

                    # 7️⃣ Retracción y recogida
                    print("[INFO] Retrayendo TCP...")
                    robot.retract()
                    print("[INFO] Rotación lateral de cierre...")
                    robot.lateral_rotation()

                    # 8️⃣ Desactivar señal
                    robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
                    print("[INFO] Pin desactivado.")
                else:
                    print("[WARN] No se detectó contacto al descender.")
            else:
                print("[INFO] No hay tapones válidos para procesar.")

    except Exception as e:
        print(f"[ERROR] Ocurrió un fallo: {e}")
    finally:
        # Finalizar script RTDE y desconexiones
        robot.stop()
        robot.disconnect()
        print("[INFO] Conexión robot cerrada.")


if __name__ == "__main__":
    main()
