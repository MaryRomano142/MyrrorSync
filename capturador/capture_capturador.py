import os
import mss
import numpy as np
import cv2
import win32gui
import config
import time

from core.debug import debug

from ui.mouse_coords import ocultar_visor_coordenadas, mostrar_visor_coordenadas

from capturador.capture_state import (
    captura_reforzada_activa
)

CARPETA_CAPTURAS = os.path.join(
    os.path.dirname(__file__),
    "capturas"
)

os.makedirs(
    CARPETA_CAPTURAS,
    exist_ok=True
)

MARGEN_VISOR = 1

def mejorar_imagen_capturador(imagen):

    if imagen is None:
        return None

    # ========================================================
    # ESCALA DE GRISES
    # ========================================================

    if len(imagen.shape) == 3:

        gris = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGR2GRAY
        )

    else:

        gris = imagen.copy()

    # ========================================================
    # 1. CONTRASTE LOCAL
    #
    # Hace más visibles las pequeñas diferencias entre:
    # - fondo
    # - celda
    # - borde
    # - radio
    # ========================================================

    clahe = cv2.createCLAHE(
        clipLimit=2.5,
        tileGridSize=(8, 8)
    )

    contraste = clahe.apply(
        gris
    )

    # ========================================================
    # 2. ENFOQUE SUAVE
    #
    # Refuerza letras, radios y bordes de 1 px.
    # ========================================================

    suavizada = cv2.GaussianBlur(
        contraste,
        (0, 0),
        0.8
    )

    nitida = cv2.addWeighted(
        contraste,
        1.8,
        suavizada,
        -0.8,
        0
    )

    # ========================================================
    # 3. GRADIENTE MORFOLÓGICO
    #
    # Especialmente útil para:
    # - círculos de radio muy finos
    # - líneas de celdas
    # - contornos de letras
    #
    # No es tan agresivo como Canny.
    # ========================================================

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3, 3)
    )

    bordes = cv2.morphologyEx(
        nitida,
        cv2.MORPH_GRADIENT,
        kernel
    )

    # ========================================================
    # 4. MEZCLAR IMAGEN + CONTORNOS
    # ========================================================

    reforzada = cv2.addWeighted(
        nitida,
        1.0,
        bordes,
        0.65,
        0
    )

    reforzada_bgr = cv2.cvtColor(
        reforzada,
        cv2.COLOR_GRAY2BGR
    )

    return reforzada_bgr

def recortar_opcion_desde_snapshot(snapshot,x_rel,y_rel,region_guardada):

    if snapshot is None:

        print(
            "[CAPTURADOR] "
            "No existe snapshot limpio "
            "para esta región."
        )

        return None

    ancho = (
        config.CAPTURADOR_OPCION_ANCHO
    )

    alto = (
        config.CAPTURADOR_OPCION_ALTO
    )

    offset_x = (
        config.CAPTURADOR_OPCION_OFFSET_X
    )

    offset_y = (
        config.CAPTURADOR_OPCION_OFFSET_Y
    )

    # ========================================================
    # CONVERTIR EL CLIC DE COORDENADAS DE VENTANA
    # A COORDENADAS INTERNAS DEL SNAPSHOT
    # ========================================================

    x_local = (
        x_rel
        - region_guardada["x_inicio"]
    )

    y_local = (
        y_rel
        - region_guardada["y_inicio"]
    )

    # ========================================================
    # CALCULAR EL RECTÁNGULO DE LA OPCIÓN
    #
    # Mantenemos exactamente la misma lógica de márgenes
    # que usaba la captura tradicional.
    # ========================================================

    x1 = (
        x_local
        + offset_x
        - ancho // 2
    )

    y1 = (
        y_local
        + offset_y
        - alto // 2
    )

    x2 = (
        x1
        + ancho
        - MARGEN_VISOR * 2
    )

    y2 = (
        y1
        + alto
        - MARGEN_VISOR * 2
    )

    # ========================================================
    # VALIDAR LÍMITES DEL SNAPSHOT
    # ========================================================

    alto_snapshot, ancho_snapshot = (
        snapshot.shape[:2]
    )

    if (
        x1 < 0
        or y1 < 0
        or x2 > ancho_snapshot
        or y2 > alto_snapshot
    ):

        print(
            "[CAPTURADOR] "
            "La opción quedó fuera "
            "del snapshot limpio."
        )

        return None

    imagen = snapshot[
        y1:y2,
        x1:x2
    ].copy()

    return imagen

def capturar_opcion(mouse_x,mouse_y,numero_seccion,numero_region,numero_opcion):

    imagen = capturar_imagen_opcion(
        mouse_x,
        mouse_y
    )

    return guardar_imagen_opcion(
        imagen,
        numero_seccion,
        numero_region,
        numero_opcion
    )

def capturar_region_opciones(hwnd, region_guardada=None):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    if region_guardada is None:

        x_inicio = config.CAPTURADOR_OPCIONES_X_INICIO
        x_fin = config.CAPTURADOR_OPCIONES_X_FIN
        y_inicio = config.CAPTURADOR_OPCIONES_Y_INICIO
        y_fin = config.CAPTURADOR_OPCIONES_Y_FIN

    else:

        x_inicio = region_guardada["x_inicio"]
        x_fin = region_guardada["x_fin"]
        y_inicio = region_guardada["y_inicio"]
        y_fin = region_guardada["y_fin"]

    x1 = izquierda + x_inicio + MARGEN_VISOR
    x2 = izquierda + x_fin - MARGEN_VISOR

    y1 = arriba + y_inicio + MARGEN_VISOR
    y2 = arriba + y_fin - MARGEN_VISOR

    ancho = x2 - x1
    alto = y2 - y1

    if ancho <= 0 or alto <= 0:

        print(
            f"Región de opciones inválida: "
            f"{ancho}x{alto}"
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho,
        "height": alto
    }

    ocultar_visor_coordenadas()

    time.sleep(0.02)

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )
    
    mostrar_visor_coordenadas()

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    if captura_reforzada_activa():

        imagen = mejorar_imagen_capturador(
            imagen
        )

    return imagen

def limpiar_capturas():

    if not os.path.exists(
        CARPETA_CAPTURAS
    ):
        return

    for nombre in os.listdir(
        CARPETA_CAPTURAS
    ):

        ruta = os.path.join(
            CARPETA_CAPTURAS,
            nombre
        )

        if (
            os.path.isfile(ruta)
            and nombre.lower().endswith(
                ".png"
            )
        ):

            try:

                os.remove(
                    ruta
                )

            except Exception as e:

                print(
                    f"No se pudo eliminar "
                    f"{nombre}: {e}"
                )

    debug(
        "[CAPTURADOR] "
        "Capturas anteriores eliminadas."
    )

def capturar_imagen_opcion(mouse_x,mouse_y):

    ancho = (
        config.CAPTURADOR_OPCION_ANCHO
    )

    alto = (
        config.CAPTURADOR_OPCION_ALTO
    )

    offset_x = (
        config.CAPTURADOR_OPCION_OFFSET_X
    )

    centro_x = (
        mouse_x
        + offset_x
    )

    x1 = (
        centro_x
        - ancho // 2
        + MARGEN_VISOR
    )

    y1 = (
        mouse_y
        - alto // 2
        + MARGEN_VISOR
    )

    ancho_captura = (
        ancho
        - MARGEN_VISOR * 2
    )

    alto_captura = (
        alto
        - MARGEN_VISOR * 2
    )

    if (
        ancho_captura <= 0
        or alto_captura <= 0
    ):

        print(
            "Región de captura inválida."
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho_captura,
        "height": alto_captura
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    if captura_reforzada_activa():

        imagen = mejorar_imagen_capturador(
            imagen
        )

    return imagen

def guardar_imagen_opcion(imagen,numero_seccion,numero_region,numero_opcion):

    if imagen is None:
        return None

    nombre = (
        f"opcion_"
        f"{numero_seccion}_"
        f"{numero_region}_"
        f"{numero_opcion}.png"
    )

    ruta = os.path.join(
        CARPETA_CAPTURAS,
        nombre
    )

    cv2.imwrite(
        ruta,
        imagen
    )

    debug(
        f"Opción capturada: "
        f"{nombre}"
    )

    return ruta


