import os
import cv2
import numpy as np
import glob
import json
from scipy.spatial.transform import Rotation as R

# --- Configuración global ---
output_dir = "calib_images"
camera_params_file = "camera_params.json"
handeye_file = "handeye_params.json"
tcp_poses_file = "tcp_poses.json"  # Nuevo archivo para guardar poses del TCP
chessboard_size = (7, 7)
square_size = 0.025
predefined_z = 0.3  # Altura preestablecida para el TCP sobre el tapón
tcp_to_cam_offset = [-0.074, 0.0, -0.035]  # x, y, z en metros
tcp_to_cam_rot_offset = [0.6450934905627825, -3.0645195408800863, 0.0076346200951948485]  # rx, ry, rz en radianes
# ----------------------------

def capturar_imagenes():
    os.makedirs(output_dir, exist_ok=True)
    
    # Verificar si ya hay poses guardadas
    tcp_poses = []
    if os.path.exists(tcp_poses_file):
        with open(tcp_poses_file, 'r') as f:
            tcp_poses = json.load(f)
    
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error al abrir la cámara.")
        return

    print("\n=== CAPTURA DE IMÁGENES ===")
    print("1. Coloca el tablero en una posición")
    print("2. Mueve el robot a la posición deseada")
    print("3. Introduce las coordenadas TCP actuales")
    print("4. Presiona 'c' para capturar (con patrón visible)")
    print("5. 'q' para terminar\n")

    img_count = len(os.listdir(output_dir))
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Error al leer la imagen de la cámara.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret_chess, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

        display_frame = frame.copy()
        if ret_chess:
            cv2.drawChessboardCorners(display_frame, chessboard_size, corners, ret_chess)

        cv2.imshow("Vista previa", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') and ret_chess:
            # Pedir coordenadas TCP actuales
            print("Introduce las coordenadas TCP actuales (x y z rx ry rz):")
            try:
                tcp_pose = list(map(float, input("> ").split()))
                if len(tcp_pose) != 6:
                    raise ValueError
                
                img_count += 1
                filename = os.path.join(output_dir, f"calib_{img_count:03d}.jpg")
                cv2.imwrite(filename, frame)
                tcp_poses.append(tcp_pose)
                
                # Guardar las poses actualizadas
                with open(tcp_poses_file, 'w') as f:
                    json.dump(tcp_poses, f, indent=4)
                
                print(f"✅ Imagen {img_count} guardada con pose TCP: {tcp_pose}")
            except:
                print("✘ Formato incorrecto. Usa: x y z rx ry rz")
        elif key == ord('c'):
            print("✘ No se detectó el patrón. Ajusta el tablero.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def calibrar_camara_y_handeye():
    print("\n=== CALIBRACIÓN COMPLETA ===")
    
    # Cargar poses TCP si existen
    if not os.path.exists(tcp_poses_file):
        print("❌ No hay poses TCP guardadas.")
        return None, None, None
    
    with open(tcp_poses_file, 'r') as f:
        tcp_poses = json.load(f)
    
    # Preparar puntos del tablero
    objp = np.zeros((chessboard_size[0]*chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2) * square_size
    
    objpoints, imgpoints = [], []
    images = glob.glob(os.path.join(output_dir, "*.jpg"))
    
    if len(images) != len(tcp_poses):
        print("❌ Número de imágenes no coincide con poses TCP.")
        return None, None, None
    
    # Procesar imágenes
    valid_images = []
    for fname, tcp_pose in zip(images, tcp_poses):
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1),
                        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            objpoints.append(objp)
            imgpoints.append(corners2)
            valid_images.append((fname, tcp_pose))
            print(f"✔ Patrón válido en {os.path.basename(fname)}")
        else:
            print(f"✘ Patrón NO encontrado en {os.path.basename(fname)}")
    
    if len(objpoints) < 3:
        print("⚠ Se necesitan al menos 3 imágenes válidas.")
        return None, None, None
    
    # Calibrar cámara
    print("🛠 Calibrando cámara...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    
    if not ret:
        print("❌ Falló la calibración de cámara.")
        return None, None, None
    
    # Guardar parámetros de cámara
    camera_data = {
        'mtx': mtx.tolist(),
        'dist': dist.tolist()
    }
    with open(camera_params_file, 'w') as f:
        json.dump(camera_data, f, indent=4)
    print(f"✅ Parámetros de cámara guardados en {camera_params_file}")
    
    # Calibrar Hand-Eye
    print("🛠 Calibrando Hand-Eye...")
    R_cam_to_board = [cv2.Rodrigues(rvec)[0] for rvec in rvecs]
    t_cam_to_board = [tvec.reshape(3,1) for tvec in tvecs]

    # Aplicar offset a las poses TCP
    R_tcp_to_cam = R.from_rotvec(tcp_to_cam_rot_offset).as_matrix()
    t_tcp_to_cam = np.array(tcp_to_cam_offset).reshape(3, 1)

    R_base_to_tcp = [R.from_rotvec(pose[3:6]).as_matrix() for _, pose in valid_images]
    t_base_to_tcp = [np.array(pose[:3]).reshape(3,1) for _, pose in valid_images]

    # Convertir de base->tcp a base->cam
    R_base_to_cam = [r_base_tcp @ R_tcp_to_cam for r_base_tcp in R_base_to_tcp]
    t_base_to_cam = [r_base_tcp @ t_tcp_to_cam + t_base_tcp for r_base_tcp, t_base_tcp in zip(R_base_to_tcp, t_base_to_tcp)]

    try:
        R_cam_to_tcp, t_cam_to_tcp = cv2.calibrateHandEye(
            R_gripper2base=R_base_to_cam,  # Usamos las poses convertidas a cámara
            t_gripper2base=t_base_to_cam,
            R_target2cam=R_cam_to_board,
            t_target2cam=t_cam_to_board,
            method=cv2.CALIB_HAND_EYE_TSAI
        )
        
        T = {
            'rotation': R_cam_to_tcp.tolist(),
            'translation': t_cam_to_tcp.flatten().tolist()
        }
        
        with open(handeye_file, 'w') as f:
            json.dump(T, f, indent=4)
        
        print(f"✅ Transformación cámara → TCP guardada en {handeye_file}")
        return mtx, dist, T
    except Exception as e:
        print(f"❌ Error en calibración Hand-Eye: {str(e)}")
        return mtx, dist, None

def calcular_posicion_tcp(mtx, dist, T_cam_to_tcp):
    if T_cam_to_tcp is None:
        print("⚠ No hay transformación Hand-Eye cargada.")
        return
    
    print("\n=== CÁLCULO DE POSICIÓN TCP ===")
    print(f"Altura preestablecida (Z): {predefined_z} m")
    print("Introduce coordenadas del centro del tapón en píxeles (u v):")
    u, v = map(int, input("> ").split())
    
    # Convertir coordenadas de imagen a coordenadas de cámara
    fx, fy = mtx[0,0], mtx[1,1]
    cx, cy = mtx[0,2], mtx[1,2]
    
    # 1. Convertir píxeles a coordenadas de cámara (sin distorsión)
    pts = np.array([[[u, v]]], dtype=np.float32)
    pts_undist = cv2.undistortPoints(pts, mtx, dist, P=mtx)
    u_norm, v_norm = pts_undist[0][0]
    
    # 2. Calcular posición en coordenadas de cámara (asumiendo Z conocido)
    X_cam = (u_norm - cx) * predefined_z / fx
    Y_cam = (v_norm - cy) * predefined_z / fy
    point_cam = np.array([X_cam, Y_cam, predefined_z, 1.0])
    
    # 3. Convertir a coordenadas TCP
    T_cam_tcp = np.eye(4)
    T_cam_tcp[:3, :3] = np.array(T_cam_to_tcp['rotation'])
    T_cam_tcp[:3, 3] = np.array(T_cam_to_tcp['translation'])
    point_tcp = T_cam_tcp @ point_cam
    
    # 4. Mostrar resultado (solo posición, manteniendo orientación original)
    print(f"\n📌 Posición calculada para el TCP:")
    print(f"X: {point_tcp[0]:.4f} m")
    print(f"Y: {point_tcp[1]:.4f} m")
    print(f"Z: {predefined_z:.4f} m (predefinida)")
    print("\nNota: Usa los mismos valores de rotación (rx ry rz) que durante la calibración")

def main():
    mtx, dist, T_cam_to_tcp = None, None, None
    
    while True:
        print("\n==== MENÚ PRINCIPAL ====")
        print("1. Capturar imágenes y poses TCP")
        print("2. Calibrar cámara y Hand-Eye")
        print("3. Calcular posición TCP para tapón")
        print("4. Salir")
        opcion = input("Selecciona una opción: ")

        if opcion == '1':
            capturar_imagenes()
        elif opcion == '2':
            mtx, dist, T_cam_to_tcp = calibrar_camara_y_handeye()
        elif opcion == '3':
            if mtx is None or dist is None or T_cam_to_tcp is None:
                print("⚠ Falta calibrar cámara y/o hand-eye.")
            else:
                calcular_posicion_tcp(mtx, dist, T_cam_to_tcp)
        elif opcion == '4':
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción inválida.")
            
if __name__ == "__main__":
    main()