import sys
import time
import os
import math # Para math.pi
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Import project modules
from gui import MainApp as GuiMainApp # Asumiendo que gui.py está actualizado
from cameraControl import Camara
from capDetection import TaponesDetector
from decisionMaker import CapDecisionMaker
from robotControl import RobotController

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"
DIGITAL_OUTPUT_PIN = 4
IMAGE_PATH = "captured_image.jpg"
JSON_OUTPUT_PATH = "capDetectionsFile.json"
MODEL_PATH = "train3/weights/best.pt" # ¡ASEGÚRATE QUE ESTE SEA EL NUEVO MODELO ENTRENADO CON 6 CLASES!
RESOURCES_PATH = "resources"
START_IMG_PATH = os.path.join(RESOURCES_PATH, "start.png")
MAIN_IMG_PATH = os.path.join(RESOURCES_PATH, "main.png")

# Robot positions (USER MUST DEFINE/VERIFY THESE ACTUAL VALUES)
REST_POSITION_JOINTS = [[1.4567713737487793, -1.6137963734068812, 0.03687411943544561,
                        -1.5324381862631817,  0.12954740226268768, -0.4755452314959925],
                        [1.380723476409912, -1.6959606609740199, 0.17434245744814092,
                         -1.6387573681273402, -1.5071643034564417, -0.43589860597719365]]
IMAGE_CAPTURE_POSITION_JOINTS = [1.3806346654891968, -1.617410799066061, 1.3717930952655237,
                                 -1.3240544509938736, -1.5211947599994105, -0.4361074606524866]

# Deposit positions per color (NUEVA ESTRUCTURA DE CLASES)
# Los nombres DEBEN coincidir con los nombres definidos en _yolo_class_to_color_map más abajo
DEPOSIT_POSITIONS = {
    "Amarillo": [-2.2998903433429163, -1.047537164097168, 0.8475335280047815,
                 -1.355234370832779, -1.549577538167135, -0.12971574464906865], # Placeholder para Amarillo (Clase 0)
    "Azul":     [-1.97978383699526, -1.2401059430888672, 1.1353901068316858,
                 -1.4570641231587906, -1.545737091694967, 0.19007229804992676], # Placeholder para Azul (Clase 1)
    "Blanco":   [-1.6519644896136683, -1.7792769871153773, 1.716369930897848,
                 -1.5064748388579865, -1.544976059590475, 0.5171940922737122], # Placeholder para Blanco (Clase 2)
    "Otro":     [-1.6237872282611292, -1.1733880204013367, 1.0451181570636194,
                 -1.441781000500061, -1.5430405775653284, 0.5462017059326172], # Placeholder para Otro (Clase 3)
    "Rojo":     [-2.607405487691061, -1.623392721215719, 1.5750983397113245,
                 -1.5021473106792946, -1.5576460997210901, -0.4384530226336878], # Placeholder para Rojo (Clase 4)
    "Verde":    [-2.2127097288714808, -1.8773662052550257, 1.7805584112750452,
                 -1.4597972196391602, -1.5507801214801233, -0.04370767274965459]  # Placeholder para Verde (Clase 5)
}

# Mapping GUI boxes to color names (Nombres de QLineEdit de gui.py)
# Este mapeo determina qué QLineEdit de la GUI (box1-box6) muestra el contador para cada color.
# Ajusta 'boxN' si los nombres de tus QLineEdit en gui.py son diferentes o si quieres un orden distinto.
COLOR_TO_BOX_MAP = {
    "Rojo":     "box1", # Clase 4
    "Amarillo": "box2", # Clase 0
    "Verde":    "box3", # Clase 5
    "Azul":     "box4", # Clase 1
    "Blanco":   "box5", # Clase 2
    "Otro":     "box6"  # Clase 3
}

# Inicializar contadores de tapones
cap_counts = {color_name: 0 for color_name in DEPOSIT_POSITIONS.keys()}


class RobotWorker(QObject):
    update_gui_signal = pyqtSignal(dict)
    processing_finished_signal = pyqtSignal(str)
    new_image_captured_signal = pyqtSignal(str)
    selected_cap_info_signal = pyqtSignal(tuple, str) # centroid_px, color_name

    def __init__(self):
        super().__init__()
        self.running = False
        self.robot = None
        self.cam = None
        self.detector = None
        # NUEVO Mapeo de clases YOLO (0-5) a nombres de color y códigos hexadecimales
        # BASADO EN LA INFORMACIÓN DEL USUARIO:
        # Clase 0: amarillo, Clase 1: azul, Clase 2: blanco, Clase 3: otro, Clase 4: rojo, Clase 5: verde
        self._yolo_class_to_color_map = {
            0: ("Amarillo", "#FFFF00"), # Amarillo
            1: ("Azul",     "#0000FF"), # Azul
            2: ("Blanco",   "#FFFFFF"), # Blanco
            3: ("Otro",     "#888888"), # Otro (Resto)
            4: ("Rojo",     "#FF0000"), # Rojo
            5: ("Verde",    "#00FF00")  # Verde
        }

    def _get_color_info_from_yolo_class(self, yolo_class_int: int) -> tuple[str, str]:
        """Devuelve (nombre_color, hex_color) para un índice de clase YOLO dado."""
        return self._yolo_class_to_color_map.get(yolo_class_int, ("Desconocido", "#CCCCCC"))

    def run_process(self):
        self.running = True
        global cap_counts # Usar la variable global definida arriba

        try:
            # ... (verificaciones de archivos como antes) ...
            self.update_gui_signal.emit({"status": "Verificando archivos..."})
            if not os.path.exists(MODEL_PATH):
                self.processing_finished_signal.emit(f"Error: Modelo YOLO no encontrado en {MODEL_PATH}. ¡Usa el nuevo modelo!")
                self.running = False; return
            if not os.path.exists(RESOURCES_PATH) or not os.path.exists(START_IMG_PATH) or not os.path.exists(MAIN_IMG_PATH):
                self.processing_finished_signal.emit(f"Error: Carpeta '{RESOURCES_PATH}' o imágenes GUI no encontradas.")
                self.running = False; return


            self.update_gui_signal.emit({"status": "Inicializando componentes..."})
            self.cam = Camara(index=0) # Asegúrate que el índice de la cámara sea correcto
            self.detector = TaponesDetector(MODEL_PATH) # Carga el NUEVO modelo

            self.update_gui_signal.emit({"status": "Conectando al robot..."})
            self.robot = RobotController(robot_ip=ROBOT_IP, digital_output_pin=DIGITAL_OUTPUT_PIN)
            self.robot.connect()

            self.update_gui_signal.emit({"status": "Robot conectado. Moviendo a reposo..."})
            self.robot.move_joint(REST_POSITION_JOINTS[0], speed=0.8, accel=1.2)

            while self.running:
                self.update_gui_signal.emit({"status": "Moviendo a posición de captura..."})
                self.robot.move_joint(IMAGE_CAPTURE_POSITION_JOINTS, speed=0.8, accel=1.2)

                self.update_gui_signal.emit({"status": "Capturando imagen..."})
                if not self.cam.tomar_foto(IMAGE_PATH):
                    self.update_gui_signal.emit({"status": "Error al capturar imagen. Reintentando..."})
                    if self.running: time.sleep(2)
                    continue
                self.new_image_captured_signal.emit(IMAGE_PATH)

                self.update_gui_signal.emit({"status": "Analizando imagen (YOLO)..."})
                # capDetection.py devuelve 'class' como el entero crudo del modelo (0-5).
                _, detections = self.detector.analizar_imagen(IMAGE_PATH)
                self.detector.guardar_json(detections, JSON_OUTPUT_PATH)

                self.update_gui_signal.emit({"status": "Seleccionando tapón..."})
                decision_maker_obj = CapDecisionMaker(JSON_OUTPUT_PATH, min_area=2000, min_confidence=0.9)
                best_cap_detection_dict = decision_maker_obj.select_best_cap() # Devuelve el dict completo

                if best_cap_detection_dict and self.running:
                    centroid_px = tuple(best_cap_detection_dict['centroid'])
                    yolo_class_int = best_cap_detection_dict['class'] # Índice de clase 0-5
                    px, py = centroid_px

                    cap_color_name, _ = self._get_color_info_from_yolo_class(yolo_class_int)

                    if cap_color_name == "Desconocido":
                        self.update_gui_signal.emit({"status": f"Tapón con clase YOLO desconocida ({yolo_class_int}). Ignorando."})
                        time.sleep(0.5) # Pequeña pausa para que el mensaje sea visible
                        continue # Saltar este tapón

                    self.selected_cap_info_signal.emit(centroid_px, cap_color_name) # Envía nombre del color
                    self.update_gui_signal.emit({"status": f"Tapón {cap_color_name} en ({px},{py}). Moviendo..."})

                    self.robot.move_to_pixel(px, py, speed=0.25, accel=0.35)

                    if self.robot.descend_until_contact():
                        self.robot.descend_with_force(duration=2.0, force=-10.0)
                        self.update_gui_signal.emit({"status": "Contacto. Tapón sujeto."})
                        #self.robot.retract(dz=0.02)

                        if cap_color_name in cap_counts:
                            cap_counts[cap_color_name] += 1
                        else:
                            # Esto no debería ocurrir si _yolo_class_to_color_map y cap_counts están sincronizados
                            print(f"Advertencia: El color '{cap_color_name}' no está en cap_counts. Añadiendo.")
                            cap_counts[cap_color_name] = 1


                        gui_update_data = {"counts": cap_counts.copy(),
                                           "status": f"Tapón {cap_color_name} recogido.",
                                           "last_picked_color_name": cap_color_name, # Usado por GUI
                                           "last_picked_coords": centroid_px}
                        self.update_gui_signal.emit(gui_update_data)

                        deposit_target_pose = DEPOSIT_POSITIONS.get(cap_color_name)
                        if deposit_target_pose:
                            self.update_gui_signal.emit({"status": f"Depositando tapón {cap_color_name}..."})
                            self.robot.move_joint(deposit_target_pose, speed=0.5, accel=0.5)
                            self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False) # Soltar
                            time.sleep(0.5)
                        else:
                            self.update_gui_signal.emit({"status": f"Advertencia: Depósito no definido para {cap_color_name}. Soltando."})
                            self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
                            time.sleep(0.5)
                        self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False) # Asegurar que está desactivado
                    else:
                        self.update_gui_signal.emit({"status": "Error: No se detectó contacto al coger."})
                elif self.running: # No hay tapones válidos y el proceso no fue detenido externamente
                    self.update_gui_signal.emit({"status": "No se detectaron tapones válidos. Finalizando ciclo."})
                    self.running = False # Detener el bucle
                    self.processing_finished_signal.emit("Proceso completado: No hay más tapones detectados.")
                    break # Salir del bucle while

                if not self.running: # Comprobar si se solicitó detener desde fuera del bucle
                    break
                time.sleep(0.1) # Pequeña pausa

        except RuntimeError as e:
            self.processing_finished_signal.emit(f"Error Crítico Robot/RTDE: {str(e)}")
        except Exception as e:
            self.processing_finished_signal.emit(f"Error inesperado en RobotWorker: {str(e)} (Línea: {e.__traceback__.tb_lineno})")
        finally:
            # ... (código de limpieza como antes) ...
            if self.robot and self.robot.con_ctrl and self.robot.con_ctrl.isConnected():
                self.update_gui_signal.emit({"status": "Moviendo a reposo y desconectando..."})
                try:
                    self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
                    self.robot.move_joint(REST_POSITION_JOINTS[0], speed=0.5, accel=1.0)
                    self.robot.stop()
                except Exception as e_stop: print(f"Error durante parada/desconexión del robot: {e_stop}")
                finally: self.robot.disconnect()
            if self.cam: self.cam.cerrar()
            self.running = False # Asegurar que el estado es false
            print("Proceso del robot finalizado.")


    def request_stop(self):
        self.update_gui_signal.emit({"status": "Deteniendo proceso..."})
        self.running = False

# ... (Clase ApplicationController como antes) ...
class ApplicationController(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        # Pasa los callbacks de inicio/fin a GuiMainApp
        self.gui_main_app = GuiMainApp(start_callback=self.start_robot_operations,
                                       finish_callback=self.stop_robot_operations)

        self.robot_thread_obj = QThread()
        self.robot_worker = RobotWorker()
        self.robot_worker.moveToThread(self.robot_thread_obj)

        # Conectar señales del worker a slots de la GUI
        self.robot_worker.update_gui_signal.connect(self.gui_main_app.main_screen.update_info_panel)
        self.robot_worker.processing_finished_signal.connect(self.handle_processing_finished)
        self.robot_worker.new_image_captured_signal.connect(self.gui_main_app.main_screen.update_camera_image_from_file)
        self.robot_worker.selected_cap_info_signal.connect(self.gui_main_app.main_screen.update_selected_cap_details)

        # Conectar señales del hilo
        self.robot_thread_obj.started.connect(self.robot_worker.run_process)
        # Cuando el worker termina, puede señalar al hilo para que se cierre
        self.robot_worker.processing_finished_signal.connect(self.robot_thread_obj.quit)


        self.gui_main_app.showMaximized()

    def start_robot_operations(self):
        global cap_counts
        # Reiniciar contadores para una nueva ejecución
        cap_counts = {color_name: 0 for color_name in DEPOSIT_POSITIONS.keys()}

        self.gui_main_app.main_screen.update_info_panel({"counts": cap_counts.copy(), "status": "Iniciando..."})
        self.gui_main_app.main_screen.clear_camera_image()
        self.gui_main_app.main_screen.clear_selected_cap_details()

        if not self.robot_thread_obj.isRunning():
            self.gui_main_app.setCurrentIndex(1) # Cambiar a la pantalla principal
            self.robot_thread_obj.start()
        else:
            print("Advertencia: El hilo del robot ya está en ejecución.")
            self.gui_main_app.setCurrentIndex(1) # Asegurarse de estar en la pantalla principal


    def stop_robot_operations(self):
        if self.robot_thread_obj.isRunning():
            self.robot_worker.request_stop()
        # El worker emitirá processing_finished_signal, que llamará a handle_processing_finished

    def handle_processing_finished(self, message):
        self.gui_main_app.main_screen.update_info_panel({"status": message})
        if self.robot_thread_obj.isRunning(): # Asegurarse de que el hilo se detenga si aún no lo ha hecho
             self.robot_thread_obj.quit()
             if not self.robot_thread_obj.wait(2000): # Esperar un poco
                 print("Advertencia: El hilo del robot no se detuvo limpiamente tras la señal de finalización.")
        # Opcional: volver a la pantalla de inicio
        # self.gui_main_app.setCurrentIndex(0)

    def run_app(self):
        self.app.aboutToQuit.connect(self.cleanup_on_exit) # Manejar cierre de ventana
        exit_code = self.app.exec_()
        sys.exit(exit_code)

    def cleanup_on_exit(self):
        print("Limpiando recursos antes de salir...")
        if self.robot_thread_obj.isRunning():
            self.robot_worker.request_stop() # Solicitar parada
            self.robot_thread_obj.quit()     # Pedir al hilo que termine su bucle de eventos
            if not self.robot_thread_obj.wait(3000): # Esperar máx 3 seg.
                print("Advertencia: El hilo del robot no terminó a tiempo, forzando terminación.")
                self.robot_thread_obj.terminate() # Usar como último recurso


if __name__ == "__main__":
    # ... (verificaciones de archivos como antes) ...
    if not os.path.exists(RESOURCES_PATH) or \
       not os.path.exists(START_IMG_PATH) or \
       not os.path.exists(MAIN_IMG_PATH):
        print(f"ERROR CRÍTICO: La carpeta '{RESOURCES_PATH}' o las imágenes 'start.png'/'main.png' no se encuentran.")
        print("Asegúrate de que la carpeta 'resources' esté en el mismo directorio que main.py y contenga las imágenes.")
        sys.exit(1)
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR CRÍTICO: El modelo YOLO '{MODEL_PATH}' no se encuentra.")
        print("Asegúrate de que esta ruta apunte a tu NUEVO modelo entrenado con 6 clases.")
        sys.exit(1)

    controller = ApplicationController()
    controller.run_app()