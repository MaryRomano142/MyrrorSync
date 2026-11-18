import os
import mss
import numpy as np
import cv2
import win32gui
import config

from core.debug import debug

MARGEN_VISOR = 1

# ============================================================
# CARPETA DE CAPTURAS
# ============================================================

CARPETA_CAPTURAS = os.path.join(
    os.path.dirname(__file__),
    "capturas"
)

os.makedirs(
    CARPETA_CAPTURAS,
    exist_ok=True
)

# ============================================================
# CAPTURAR AFIRMACIÓN
# ============================================================

def capturar_afirmacion(hwnd, numero_seccion):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x1 = (izquierda + config.BLOCK_SECCIONES_AFIRMACION_X_INICIO)
    x2 = (izquierda + config.BLOCK_SECCIONES_AFIRMACION_X_FIN)
    y1 = (arriba + config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO)
    y2 = (arriba + config.BLOCK_SECCIONES_AFIRMACION_Y_FIN)

    x1 += MARGEN_VISOR
    y1 += MARGEN_VISOR
    x2 -= MARGEN_VISOR
    y2 -= MARGEN_VISOR

    region = {
        "left": x1,
        "top": y1,
        "width": x2 - x1,
        "height": y2 - y1
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    ruta = os.path.join(
        CARPETA_CAPTURAS,
        f"captura_{numero_seccion}.png"
    )

    cv2.imwrite(
        ruta,
        imagen
    )

    debug(
        f"Afirmación capturada: "
        f"captura_{numero_seccion}.png"
    )

    return ruta

# ============================================================
# CAPTURAR OPCIÓN
# ============================================================
def recortar_opcion_desde_snapshot(snapshot,x_rel,y_rel,region_guardada):

    if snapshot is None:

        print(
            "[BLOCK SECCIONES] "
            "No existe snapshot limpio "
            "para esta sección."
        )

        return None

    ancho = (
        config.BLOCK_SECCIONES_OPCION_ANCHO
    )

    alto = (
        config.BLOCK_SECCIONES_OPCION_ALTO
    )

    x_local = (
        x_rel
        - region_guardada["x_inicio"]
    )

    y_local = (
        y_rel
        - region_guardada["y_inicio"]
    )

    x1 = (
        x_local
        - ancho // 2
    )

    y1 = (
        y_local
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
            "[BLOCK SECCIONES] "
            "La opción quedó fuera "
            "del snapshot limpio."
        )

        return None

    imagen = snapshot[
        y1:y2,
        x1:x2
    ].copy()

    return imagen

def guardar_imagen_opcion(imagen,numero_seccion,numero_opcion):

    if imagen is None:
        return None

    ruta = os.path.join(
        CARPETA_CAPTURAS,
        f"opcion_{numero_seccion}_{numero_opcion}.png"
    )

    cv2.imwrite(
        ruta,
        imagen
    )

    debug(
        f"Opción capturada: "
        f"opcion_{numero_seccion}_{numero_opcion}.png"
    )

    return ruta

def capturar_opcion(hwnd,mouse_x,mouse_y,numero_seccion,numero_opcion):

    ancho = config.BLOCK_SECCIONES_OPCION_ANCHO
    alto = config.BLOCK_SECCIONES_OPCION_ALTO

    margen = MARGEN_VISOR

    x1 = mouse_x - ancho // 2 + margen
    y1 = mouse_y - alto // 2 + margen

    ancho_captura = ancho - (margen * 2)
    alto_captura = alto - (margen * 2)

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

    ruta = os.path.join(
        CARPETA_CAPTURAS,
        f"opcion_{numero_seccion}_{numero_opcion}.png"
    )

    cv2.imwrite(
        ruta,
        imagen
    )

    debug(
        f"Opción capturada: "
        f"opcion_{numero_seccion}_{numero_opcion}.png"
    )

    return ruta

def capturar_afirmacion_actual(hwnd):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x1 = (
        izquierda +
        config.BLOCK_SECCIONES_AFIRMACION_X_INICIO +
        MARGEN_VISOR
    )

    x2 = (
        izquierda +
        config.BLOCK_SECCIONES_AFIRMACION_X_FIN -
        MARGEN_VISOR
    )

    y1 = (
        arriba +
        config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO +
        MARGEN_VISOR
    )

    y2 = (
        arriba +
        config.BLOCK_SECCIONES_AFIRMACION_Y_FIN -
        MARGEN_VISOR
    )

    ancho = x2 - x1
    alto = y2 - y1

    if ancho <= 0 or alto <= 0:

        print(
            "Error: región de afirmación inválida "
            f"({ancho}x{alto})"
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho,
        "height": alto
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    return imagen

def capturar_region_opciones(hwnd):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x1 = (
        izquierda
        + config.BLOCK_SECCIONES_OPCIONES_X_INICIO
        + MARGEN_VISOR
    )

    x2 = (
        izquierda
        + config.BLOCK_SECCIONES_OPCIONES_X_FIN
        - MARGEN_VISOR
    )

    y1 = (
        arriba
        + config.BLOCK_SECCIONES_OPCIONES_Y_INICIO
        + MARGEN_VISOR
    )

    y2 = (
        arriba
        + config.BLOCK_SECCIONES_OPCIONES_Y_FIN
        - MARGEN_VISOR
    )

    ancho = x2 - x1
    alto = y2 - y1

    if ancho <= 0 or alto <= 0:

        print(
            "Error: región de opciones inválida "
            f"({ancho}x{alto})"
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho,
        "height": alto
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    return imagen

def capturar_afirmacion_region(hwnd, region_guardada):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x1 = (
        izquierda
        + region_guardada["x_inicio"]
        + MARGEN_VISOR
    )

    x2 = (
        izquierda
        + region_guardada["x_fin"]
        - MARGEN_VISOR
    )

    y1 = (
        arriba
        + region_guardada["y_inicio"]
        + MARGEN_VISOR
    )

    y2 = (
        arriba
        + region_guardada["y_fin"]
        - MARGEN_VISOR
    )

    ancho = x2 - x1
    alto = y2 - y1

    if ancho <= 0 or alto <= 0:

        print(
            "Región de afirmación inválida: "
            f"{ancho}x{alto}"
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho,
        "height": alto
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    return imagen

def capturar_region_opciones_guardada(
    hwnd,
    region_guardada
):

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x1 = (
        izquierda
        + region_guardada["x_inicio"]
        + MARGEN_VISOR
    )

    x2 = (
        izquierda
        + region_guardada["x_fin"]
        - MARGEN_VISOR
    )

    y1 = (
        arriba
        + region_guardada["y_inicio"]
        + MARGEN_VISOR
    )

    y2 = (
        arriba
        + region_guardada["y_fin"]
        - MARGEN_VISOR
    )

    ancho = x2 - x1
    alto = y2 - y1

    if ancho <= 0 or alto <= 0:

        print(
            "Región de opciones inválida: "
            f"{ancho}x{alto}"
        )

        return None

    region = {
        "left": x1,
        "top": y1,
        "width": ancho,
        "height": alto
    }

    with mss.mss() as sct:

        imagen = np.array(
            sct.grab(region)
        )

    imagen = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGRA2BGR
    )

    return imagen