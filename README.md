# RecycleX

## Descripción
El reciclado de productos plásticos es de vital importancia para el desarrollo sostenible del planeta. Es por esto por lo que, los compañeros de la asociación de reciclaje se han puesto manos a la obra con el reciclaje de tapones, dándole una segunda vida al plástico, convirtiéndolo en material para máquinas de impresión 3D. Puesto que cada bobina de filamentos es de un determinado color, surge la necesidad de clasificar los tapones por colores para su posterior tratamiento. Con este trabajo se busca automatizar ese proceso mediante el uso de un brazo robótico (robot UR3) y una cámara acoplada al mismo, de tal manera que el robot sea capaz de categorizar visualmente los tapones según convenga y situarlos en los diferentes depósitos adyacentes, uno para cada color.

Para ello se desarrollará un método de visión que pueda identificar el color de cada tapón, junto con un algoritmo de control que permita el posicionamiento del robot y posterior agarre, transporte y depósito del tapón. Adicionalmente puede surgir la necesidad de diseñar un agarre para el extremo del brazo que permita coger tapones de diferentes tamaños y formas.

## Módulos Principales
- **WP200:** Herramienta del UR.
- **WP300:** Algoritmo de visión por computador.
- **WP400:** Algoritmo de decisión.
- **WP500:** Estudio del comportamiento, funcionamiento y control del robot UR.
- **WP600:** Planificación de la acción del UR.
- **WP700:** Integración de los diferentes WP.
- **WP800:** Validación.

## Instalación
Para ejecutar el proyecto, clona este repositorio y sigue las instrucciones específicas para cada módulo.
```bash
    git clone https://github.com/tu-usuario/RecycleX.git
    cd RecycleX
```
