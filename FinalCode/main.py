# main.py
import sys
import time
import os
import json
import math
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Importar módulos 
from cameraControl import Camara
from gui import MainApp as GuiMainApp
from capDetection import TaponesDetector
from robotControl import RobotController
from decisionMaker import CapDecisionMaker

# --- CONFIGURACIÓN ---
ROBOT_IP = "169.254.12.28"             #
DIGITAL_OUTPUT_PIN = 4                 #
IMAGE_PATH = "captured_image.jpg"      # Imagen original capturada
JSON_OUTPUT_PATH = "capDetectionsFile.json" # Nombre de archivo consistente
MODEL_PATH = "train3/weights/best.pt"  #
RESOURCES_PATH = "resources"           #
START_IMG_PATH = os.path.join(RESOURCES_PATH, "start.png") #
MAIN_IMG_PATH = os.path.join(RESOURCES_PATH, "main.png")   #

# Rutas para las imágenes que se mostrarán en la GUI
ALL_DETECTIONS_DISPLAY_PATH = "gui_all_detections.jpg"
SELECTED_CAP_DISPLAY_PATH = "gui_selected_cap.jpg"

# Posiciones del Robot (de tu último main.py)
REST_POSITION_JOINTS = [1.4567713737487793, -1.6137963734068812, 0.03687411943544561,
                        -1.5324381862631817,  0.12954740226268768, -0.4755452314959925]
IMAGE_CAPTURE_POSITION_JOINTS = [1.3783482313156128, -1.7762123546996058, 1.3978703657733362,
                                 -1.1838005644134064, -1.522461239491598, -0.5920336882220667]

DEPOSIT_POSITIONS = {
    "Amarillo": [-2.2998903433429163, -1.047537164097168, 0.8475335280047815, 
                 -1.355234370832779, -1.549577538167135, -0.12971574464906865],
    "Azul":     [-1.97978383699526, -1.2401059430888672, 1.1353901068316858, 
                 -1.4570641231587906, -1.545737091694967, 0.19007229804992676],
    "Blanco":   [-1.6519644896136683, -1.7792769871153773, 1.716369930897848, 
                 -1.5064748388579865, -1.544976059590475, 0.5171940922737122],
    "Otro":     [-1.6237872282611292, -1.1733880204013367, 1.0451181570636194, 
                 -1.441781000500061, -1.5430405775653284, 0.5462017059326172],
    "Rojo":     [-2.607405487691061, -1.623392721215719, 1.5750983397113245, 
                 -1.5021473106792946, -1.5576460997210901, -0.4384530226336878],
    "Verde":    [-2.2127097288714808, -1.8773662052550257, 1.7805584112750452, 
                 -1.4597972196391602, -1.5507801214801233, -0.04370767274965459]
}

# Mapeo de Cajas de GUI a Nombres de Color (de tu último main.py)
COLOR_TO_BOX_MAP = {
    "Rojo":     "box1", "Amarillo": "box2", "Verde":    "box3",
    "Azul":     "box4", "Blanco":   "box5", "Otro":     "box6"
}
# Contadores de tapones
cap_counts = {color_name: 0 for color_name in DEPOSIT_POSITIONS.keys()}

CALIBRATION_FILE = "intrinsic_calibration_data.json"

if os.path.exists(CALIBRATION_FILE):
    with open(CALIBRATION_FILE, 'r') as f:
        data = json.load(f)
    camera_matrix = np.array(data["camera_matrix"])
    dist_coeffs = np.array(data["dist_coeffs"])
else:
    camera_matrix, dist_coeffs = None, None
    print(f"ADVERTENCIA: Archivo de calibración '{CALIBRATION_FILE}' no encontrado. No se desdistorsionarán imágenes.")

class RobotWorker(QObject):
    update_gui_signal = pyqtSignal(dict)
    processing_finished_signal = pyqtSignal(str)
    # Señal para enviar la RUTA de la imagen que la GUI debe mostrar
    update_gui_image_display_signal = pyqtSignal(str)
    selected_cap_info_signal = pyqtSignal(tuple, str) # centroid_px, color_name

    def __init__(self):
        super().__init__()
        self.running = False
        self.robot = None
        # Usar Camara con tiempo de calentamiento, ej. 1 segundos
        self.cam = Camara(index=0, warmup_time=1)
        self.detector = None
        # Mapeo de clases YOLO a colores
        self._yolo_class_to_color_map = {
            0: ("Amarillo", "#FFFF00"), 1: ("Azul", "#0000FF"), 2: ("Blanco", "#FFFFFF"),
            3: ("Otro", "#888888"), 4: ("Rojo", "#FF0000"), 5: ("Verde", "#00FF00")
        }

    def _get_color_info_from_yolo_class(self, yolo_class_int: int) -> tuple[str, str]: #
        """Devuelve (nombre_color, hex_color) para un índice de clase YOLO."""
        return self._yolo_class_to_color_map.get(yolo_class_int, ("Desconocido", "#CCCCCC"))

    def run_process(self):
        self.running = True
        global cap_counts

        try:
            self.update_gui_signal.emit({"status": "Verificando archivos..."}) #
            if not os.path.exists(MODEL_PATH): #
                self.processing_finished_signal.emit(f"Error: Modelo YOLO no encontrado en {MODEL_PATH}.")
                self.running = False; return

            self.update_gui_signal.emit({"status": "Inicializando componentes..."}) #
            self.detector = TaponesDetector(MODEL_PATH) #

            self.update_gui_signal.emit({"status": "Conectando al robot..."}) #
            self.robot = RobotController(robot_ip=ROBOT_IP, digital_output_pin=DIGITAL_OUTPUT_PIN) #
            self.robot.connect() #

            self.update_gui_signal.emit({"status": "Robot conectado. Moviendo a reposo..."}) #
            self.robot.move_joint(REST_POSITION_JOINTS, speed=0.8, accel=1.2) #

            while self.running:
                self.update_gui_signal.emit({"status": "Moviendo a posición de captura..."}) #
                self.robot.move_joint(IMAGE_CAPTURE_POSITION_JOINTS, speed=3, accel=8) #

                self.update_gui_signal.emit({"status": "Capturando imagen (con calentamiento)..."}) #
                if not self.cam.tomar_foto(IMAGE_PATH): # tomar_foto ahora incluye calentamiento
                    self.update_gui_signal.emit({"status": "Error al capturar imagen. Reintentando..."}) #
                    if self.running: time.sleep(2)
                    continue

                # Cargar la imagen capturada con OpenCV para poder pasarla a decisionMaker
                captured_cv_image = cv2.imread(IMAGE_PATH)

                if camera_matrix is not None and dist_coeffs is not None:
                    captured_cv_image = cv2.undistort(captured_cv_image, camera_matrix, dist_coeffs)
                    cv2.imwrite(IMAGE_PATH, captured_cv_image)  # Sobrescribimos la imagen ya desdistorsionada
                else:
                    print("AVISO: No se pudo desdistorsionar la imagen por falta de parámetros de calibración.")

                if captured_cv_image is None:
                    self.update_gui_signal.emit({"status": "Error crítico: No se pudo leer la imagen capturada del disco."})
                    continue

                self.update_gui_signal.emit({"status": "Analizando imagen (YOLO)..."}) #
                # `analizar_imagen` devuelve `results` (objeto de YOLO) y `detections` (lista de dicts)
                yolo_results_obj, detections_list = self.detector.analizar_imagen(IMAGE_PATH) #
                self.detector.guardar_json(detections_list, JSON_OUTPUT_PATH) #

                # Guardar imagen con TODAS las detecciones para la GUI
                # `guardar_imagen_resultado` usa `results.plot()`
                self.detector.guardar_imagen_resultado(yolo_results_obj, ALL_DETECTIONS_DISPLAY_PATH)
                self.update_gui_image_display_signal.emit(ALL_DETECTIONS_DISPLAY_PATH) # Enviar a GUI

                self.update_gui_signal.emit({"status": "Seleccionando tapón..."}) #
                # min_area y min_confidence de tu último main.py
                decision_maker = CapDecisionMaker(JSON_OUTPUT_PATH, min_area=2000, min_confidence=0.7)
                selected_cap_data = decision_maker.select_best_cap() # Devuelve el diccionario del mejor tapón

                if selected_cap_data and self.running:
                    centroid_px = tuple(selected_cap_data['centroid']) #
                    yolo_class_index = selected_cap_data['class']      #
                    px, py = centroid_px                               #

                    cap_color_name, _ = self._get_color_info_from_yolo_class(yolo_class_index) #

                    if cap_color_name == "Desconocido": #
                        self.update_gui_signal.emit({"status": f"Clase YOLO desconocida ({yolo_class_index}). Ignorando tapón."}) #
                        # La imagen con todas las detecciones ya se mostró. No hacer nada más con este tapón.
                        time.sleep(1) # Pausa para que el mensaje sea visible
                        continue

                    self.selected_cap_info_signal.emit(centroid_px, cap_color_name) #
                    self.update_gui_signal.emit({"status": f"Tapón {cap_color_name} en ({px},{py}). Procesando..."}) #

                    # Dibujar SOLO el tapón seleccionado en la imagen original capturada
                    image_with_only_selected = decision_maker.draw_selected_on_image(captured_cv_image, selected_cap_data)
                    if image_with_only_selected is not None:
                        cv2.imwrite(SELECTED_CAP_DISPLAY_PATH, image_with_only_selected)
                        self.update_gui_image_display_signal.emit(SELECTED_CAP_DISPLAY_PATH) # Enviar a GUI
                    else:
                        # Si falla el dibujo, al menos mostrar la de todas las detecciones
                        self.update_gui_image_display_signal.emit(ALL_DETECTIONS_DISPLAY_PATH)

                    # --- Lógica del Robot ---
                    self.update_gui_signal.emit({"status": f"Moviendo robot a tapón {cap_color_name}..."}) #
                    self.robot.move_to_pixel(px, py, speed=0.25, accel=0.35) #

                    if self.robot.descend_until_contact(): #
                        self.update_gui_signal.emit({"status": "Contacto detectado. Ventosa activada."})
                        self.robot.descend_with_force(duration=0.75, force=15.0)
                        self.update_gui_signal.emit({"status": "Vacío generado. Tapón sujeto."})
                        self.robot.retract(dz=0.15) # dz=0.15 de tu último main.py

                        if cap_color_name in cap_counts: #
                            cap_counts[cap_color_name] += 1
                        else:
                            cap_counts[cap_color_name] = 1 #

                        gui_update_data = {"counts": cap_counts.copy(), #
                                           "status": f"Tapón {cap_color_name} recogido.",
                                           "last_picked_color_name": cap_color_name,
                                           "last_picked_coords": centroid_px}
                        self.update_gui_signal.emit(gui_update_data)

                        deposit_target_pose = DEPOSIT_POSITIONS.get(cap_color_name) #
                        if deposit_target_pose: #
                            self.update_gui_signal.emit({"status": f"Depositando tapón {cap_color_name}..."}) #
                            # move_joint para depositar según tu último main.py
                            self.robot.move_joint(deposit_target_pose, speed=3, accel=8)
                            self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False) # Soltar
                            time.sleep(0.5) #
                        else: #
                            self.update_gui_signal.emit({"status": f"Advertencia: Depósito no definido para {cap_color_name}."})
                            self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False)
                            time.sleep(0.5)
                        self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False) # Asegurar desactivación
                    else:
                        self.update_gui_signal.emit({"status": "Error: No se detectó contacto al coger."}) #
                        self.robot.retract(dz=0.05) # Retraer un poco
                     # --- Fin Lógica del Robot ---

                elif self.running: # No hay tapones válidos y el proceso no fue detenido externamente
                    self.update_gui_signal.emit({"status": "No se detectaron tapones válidos. Finalizando ciclo."}) #
                    self.running = False # Detener el bucle
                    self.processing_finished_signal.emit("Proceso completado: No hay más tapones detectados.") #
                    break # Salir del bucle while

                if not self.running: # Comprobar si se solicitó detener desde fuera del bucle
                    break
                time.sleep(0.1) # Pequeña pausa en el bucle

        except RuntimeError as e: #
            self.processing_finished_signal.emit(f"Error Crítico Robot/RTDE: {str(e)}")
        except Exception as e: #
            tb_lineno = e.__traceback__.tb_lineno if e.__traceback__ else "N/A"
            self.processing_finished_signal.emit(f"Error inesperado en RobotWorker: {str(e)} (Línea: {tb_lineno})")
        finally:
            if self.robot and self.robot.con_ctrl and self.robot.con_ctrl.isConnected(): #
                self.update_gui_signal.emit({"status": "Moviendo a reposo y desconectando..."}) #
                try:
                    self.robot.con_io.setStandardDigitalOut(DIGITAL_OUTPUT_PIN, False) #
                    self.robot.move_joint(REST_POSITION_JOINTS, speed=0.5, accel=1.0) #
                    self.robot.stop() #
                except Exception as e_stop: print(f"ERROR durante parada/desconexión del robot: {e_stop}")
                finally: self.robot.disconnect() #
            if self.cam: self.cam.cerrar() #
            self.running = False # Asegurar que el estado es false
            print("INFO: Proceso del robot finalizado.")


    def request_stop(self): #
        self.update_gui_signal.emit({"status": "Deteniendo proceso..."})
        self.running = False

class ApplicationController(QObject): # Basado en tu último main.py
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.gui_main_app = GuiMainApp(start_callback=self.start_robot_operations,
                                       finish_callback=self.stop_robot_operations)

        self.robot_thread_obj = QThread()
        self.robot_worker = RobotWorker()
        self.robot_worker.moveToThread(self.robot_thread_obj)

        # Conexiones de señales
        self.robot_worker.update_gui_signal.connect(self.gui_main_app.main_screen.update_info_panel)
        self.robot_worker.processing_finished_signal.connect(self.handle_processing_finished)
        # Conectar la nueva señal para mostrar imágenes en la GUI
        self.robot_worker.update_gui_image_display_signal.connect(self.gui_main_app.main_screen.update_camera_image_from_file)
        self.robot_worker.selected_cap_info_signal.connect(self.gui_main_app.main_screen.update_selected_cap_details)

        self.robot_thread_obj.started.connect(self.robot_worker.run_process)
        self.robot_worker.processing_finished_signal.connect(self.robot_thread_obj.quit)
        # Opcional: Limpieza de objetos QThread y QObject cuando terminan
        # self.robot_thread_obj.finished.connect(self.robot_thread_obj.deleteLater)
        # self.robot_worker.processing_finished_signal.connect(self.robot_worker.deleteLater)


        self.gui_main_app.showMaximized()

    def start_robot_operations(self): # Basado en tu último main.py
        global cap_counts
        # Reiniciar contadores para la nueva ejecución
        cap_counts = {color_name: 0 for color_name in DEPOSIT_POSITIONS.keys()}

        self.gui_main_app.main_screen.update_info_panel({"counts": cap_counts.copy(), "status": "Iniciando..."})
        self.gui_main_app.main_screen.clear_camera_image() # Limpiar imagen anterior
        self.gui_main_app.main_screen.clear_selected_cap_details() # Limpiar detalles del tapón anterior

        if not self.robot_thread_obj.isRunning():
            self.gui_main_app.setCurrentIndex(1) # Cambiar a la pantalla principal de la GUI
            self.robot_thread_obj.start()
        else:
            print("ADVERTENCIA: El hilo del robot ya está en ejecución.")
            self.gui_main_app.setCurrentIndex(1) # Asegurarse de estar en la pantalla principal


    def stop_robot_operations(self): # Basado en tu último main.py
        if self.robot_thread_obj.isRunning():
            self.robot_worker.request_stop()
        # El worker emitirá processing_finished_signal, que llamará a handle_processing_finished

    def handle_processing_finished(self, message): # Basado en tu último main.py
        self.gui_main_app.main_screen.update_info_panel({"status": message})
        if self.robot_thread_obj.isRunning(): # Asegurarse de que el hilo se detenga si aún no lo ha hecho
             self.robot_thread_obj.quit()
             if not self.robot_thread_obj.wait(2000): # Esperar un poco
                 print("ADVERTENCIA: El hilo del robot no se detuvo limpiamente tras la señal de finalización.")
        # Opcional: volver a la pantalla de inicio
        # self.gui_main_app.setCurrentIndex(0)

    def run_app(self): # Basado en tu último main.py
        self.app.aboutToQuit.connect(self.cleanup_on_exit) # Manejar cierre de ventana
        exit_code = self.app.exec_()
        sys.exit(exit_code)

    def cleanup_on_exit(self): # Basado en tu último main.py
        print("INFO: Limpiando recursos antes de salir...")
        if self.robot_thread_obj.isRunning():
            self.robot_worker.request_stop() # Solicitar parada
            self.robot_thread_obj.quit()     # Pedir al hilo que termine su bucle de eventos
            if not self.robot_thread_obj.wait(3000): # Esperar máx 3 seg.
                print("ADVERTENCIA: El hilo del robot no terminó a tiempo, forzando terminación.")
                self.robot_thread_obj.terminate() # Usar como último recurso


if __name__ == "__main__": # Basado en tu último main.py
    # Verificaciones críticas de archivos antes de iniciar la GUI
    if not os.path.exists(RESOURCES_PATH) or \
       not os.path.exists(START_IMG_PATH) or \
       not os.path.exists(MAIN_IMG_PATH):
        print(f"ERROR CRÍTICO: La carpeta '{RESOURCES_PATH}' o las imágenes GUI no se encuentran.")
        sys.exit(1)
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR CRÍTICO: El modelo YOLO '{MODEL_PATH}' no se encuentra.")
        sys.exit(1)

    controller = ApplicationController()
    controller.run_app()