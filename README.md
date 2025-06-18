
# ♻️ RecycleX: Clasificación Robótica de Tapones por Color

**RecycleX** es un sistema robótico inteligente desarrollado como parte del *Máster Universitario en Automática y Robótica*, cuyo objetivo es automatizar la clasificación de tapones plásticos por color para su reciclaje y reutilización como filamento en impresión 3D.  

Este sistema integra visión artificial, inteligencia artificial, algoritmos de decisión y control robótico mediante un robot colaborativo UR3.

![RecycleX](assets/RecycleX.png)

---

## 🧠 Motivación

El reciclaje manual de tapones es ineficiente, especialmente cuando deben clasificarse por color. Este proyecto propone una solución automatizada que:

- Detecta tapones y clasifica por color mediante visión artificial (YOLOv8).
- Escoge el más accesible usando lógica de decisión.
- Controla un brazo robótico UR3 para manipularlos.
- Deposita cada tapón en el contenedor correspondiente.
- Permite supervisar el proceso a través de una interfaz de usuario.

> 🌱 RecycleX contribuye a una economía circular y sostenible mediante la automatización del proceso de reciclaje.

---

## 🧩 Arquitectura por Módulos

![Diagrama general del sistema](assets/overview.png)

---

## ⚙️ Características Principales

- 🎨 Detección de tapones y clasificación por color con **YOLOv8**.
- ✅ Lógica de decisión basada en área, confianza de detección y cuadratez del bounding box.
- 🤖 Control de un robot **UR3** vía RTDE o TCP/IP.
- 🧲 Herramienta de agarre por **ventosa**.
- 🖥️ GUI en **PyQt5** para visualización y control.
- 🔁 Ciclo completo e **iterativo** de manipulación de tapones.

---

## 📂 Estructura del Proyecto

```bash
RecycleX/
│
├── FinalCode/                          # Código principal del sistema
│   ├── main.py                         # Script principal
│   ├── cameraControl.py                # Control y adquisición de imagen
│   ├── capDetection.py                 # Detección con YOLOv8
│   ├── decisionMaker.py                # Selección del tapón óptimo
│   ├── robotControl.py                 # Control del UR3
│   ├── gui.py                          # Interfaz gráfica (PyQt)
│   ├── intrinsic_calibration_data.json # Calibración de cámara (copia)
│   ├── capDetectionsFile.json          # Resultados de detección
│   ├── resources/                      # Recursos gráficos para GUI
│   ├── train3/                         # Modelo YOLO entrenado
│   ├── assets/                         # Imágenes para documentación (README)
│   └── requirements.txt                # Librerías necesarias
│
├── CameraCalibration/                  # Scripts y datos para calibración
│   ├── 1_calibrate_intrinsics.py       # Calibración intrínseca de cámara
│   ├── calibracion_manual_yolo.py      # Calibración manual para YOLO
│   ├── calib_manual_hsv.py             # Calibración de color manual (HSV)
│   ├── evaluate_calib.py               # Evaluación global de calibración
│   ├── evaluate_intrinsic_stability.py # Prueba de estabilidad de la calibración
│   ├── calibracion_ur3.json            # Calibración extrínseca UR3-cámara
│   ├── intrinsic_calibration_data.json # Archivo de parámetros intrínsecos
│   ├── calib_images/                   # Imágenes usadas para calibrar
│   └── output/                         # Resultados y visualizaciones de calibración
│
├── auxiliar.py                         # Script de funciones auxiliares útiles para el control del UR3
└── cam.py                              # Script para el correcto posicionamiento de la cámara al comienzo
```

---

## 📸 Módulos Principales

### 🔍 Detección con YOLOv8
![Detección YOLO](assets/yolo_detection.png)
- Entrenado con imágenes de tapones.
- Precisión y rapidez para uso en tiempo real.

### 🧠 Algoritmo de Decisión
- Elige el tapón más accesible según área visible, confianza de la detección y cuadratez del bounding box.

### 🤖 Control del UR3
- Comunicación mediante protocolo RTDE o TCP/IP.
- Control por movimientos `MoveL` y `MoveJ`.
- Movimiento hasta contacto mediante `MoveUntilContact`.
- Control de fuerza mediante `forceMode`.

### 🧲 Efector Final (Ventosa)
![Ventosa](assets/gripper_tool.png)
- Herramienta seleccionada tras pruebas de agarre.
- Adaptación a distintos tamaños de tapones.

### 🖥️ Interfaz Gráfica (GUI)
![Interfaz gráfica](assets/gui.png)
- Visualización en tiempo real del proceso.
- Registro de eventos, detecciones y estado del robot.
- Control de marcha y parada.

---

## 🛠️ Requisitos

- Python 3.10
- YOLOv8 (PyTorch)
- OpenCV (Headless), NumPy, PyQt5
- URControl vía RTDE / TCP/IP
- Cámara HD 2D

---

## 🚀 Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/DiegoRamirezFuente/RecycleX.git
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Puesta en Marcha del Sistema

Antes de ejecutar el sistema, asegúrate de seguir los siguientes pasos para una correcta configuración física y lógica:

1. **Conexiones iniciales**:
   - Conecta el robot **UR3** al PC mediante **Ethernet**.
   - Conecta la **cámara** al PC a través del **puerto USB-C**.

2. **Posicionamiento inicial del robot**:
   - Ejecuta el script auxiliar:
     ```bash
     python3 auxiliar.py
     ```
   - En el menú que aparece, selecciona la **opción 2** para colocar el robot en la **posición de toma de imagen**.

3. **Alineación de la cámara**:
   - Lanza la visualización de la cámara:
     ```bash
     python3 cam.py
     ```
   - Ajusta la posición de la cámara de modo que el **punto rojo de la imagen** coincida con el **punto de calibración** físico (ver plano en `assets/plano_calibracion.png` para más detalles sobre la referencia física del punto de calibración).

4. **Colocación del entorno físico**:
   - Coloca la **ventosa mediana** como herramienta del robot, alineada lo más perpendicular posible a la superficie de la mesa.
   - Sitúa los **depósitos de colores** y la **caja con los tapones** siguiendo las posiciones indicadas en el plano adjunto (`assets/plano_colocacion.png`).

### 📐 Planos de Referencia

<p align="center">
  <img src="assets/plano_calibracion.png" alt="Plano de calibración" width="45%" />
  <img src="assets/plano_colocacion.png" alt="Plano de colocación" width="45%" />
</p>

5. **Ejecución del sistema**:
   - Una vez preparado todo el entorno, ejecuta:
     ```bash
     python3 main.py
     ```
   - Se abrirá la interfaz gráfica:
     - Pulsa **Start** para comenzar el ciclo de clasificación.
     - Al finalizar, pulsa **Fin** para detener el proceso de forma segura.

> ⚠️ Asegúrate de haber realizado todos los pasos anteriores antes de iniciar el sistema para evitar errores en la detección o la manipulación de tapones.

---

## 📈 Resultados Esperados

- ✔️ Precisión de agarre > 98%
- ⏱️ Tiempo de ciclo por tapón < 13 s
- 🔁 Procesamiento iterativo continuo
- 🧩 Robustez ante variaciones de color/tamaño

---

## 👥 Equipo de Desarrollo

Este proyecto fue desarrollado como parte de la asignatura *Laboratorio de Robótica y Automática* del Máster Universitario en Automática y Robótica de la *Universidad Politécnica de Madrid*.

| Integrantes             |
|-------------------------|
| Iñaki Dellibarda Varela |
| Pablo Hita Pérez        |
| Carlos Mesa Sierra      |
| Diego Ramírez Fuente    |
---

## 🎥 Vídeos del Proyecto

- 📽️ **Vídeo técnico**  
  Explica la arquitectura del sistema, calibración de cámara y robot, integración de módulos y funcionamiento interno del sistema completo.  
  👉 [Ver vídeo técnico en YouTube](https://www.youtube.com/watch?v=Oh661WRXyLc)

- 🌟 **Vídeo promocional y de demostración**  
  Muestra el sistema en funcionamiento clasificando tapones, con énfasis en su utilidad práctica, impacto ecológico y potencial de automatización.  
  👉 [Ver vídeo demostrativo en YouTube](https://www.youtube.com/watch?v=3DejUVXnluY)

---

