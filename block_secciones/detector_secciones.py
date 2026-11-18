import cv2
import numpy as np
import time

from block_secciones.capture_secciones import (
    capturar_afirmacion_region
)

from core.debug import debug

from block_secciones.capture_state import (
    modo_reforzado
)

ANCHO_NORMALIZADO = 800
ALTO_NORMALIZADO = 180

def preparar_imagen(imagen):

    if imagen is None:
        return None

    # --------------------------------------------------------
    # ESCALA DE GRISES
    # --------------------------------------------------------

    gris = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # BINARIZACIÓN
    #
    # Texto = blanco
    # Fondo = negro
    # --------------------------------------------------------

    _, binaria = cv2.threshold(
        gris,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # --------------------------------------------------------
    # BUSCAR SOLAMENTE LOS PÍXELES QUE CONTIENEN INFORMACIÓN
    # --------------------------------------------------------

    puntos = cv2.findNonZero(
        binaria
    )

    if puntos is None:
        return None

    x, y, w, h = cv2.boundingRect(
        puntos
    )

    # --------------------------------------------------------
    # RECORTAR ESPACIO VACÍO
    # --------------------------------------------------------

    recorte = binaria[
        y:y + h,
        x:x + w
    ]

    if recorte.size == 0:
        return None

    # --------------------------------------------------------
    # NORMALIZAR
    #
    # De esta forma las pequeñas diferencias de tamaño entre
    # ventanas no afectan tanto.
    # --------------------------------------------------------

    normalizada = cv2.resize(
        recorte,
        (
            ANCHO_NORMALIZADO,
            ALTO_NORMALIZADO
        ),
        interpolation=cv2.INTER_AREA
    )

    return normalizada

def comparar_imagenes(imagen_actual,imagen_referencia):

    actual = preparar_imagen(
        imagen_actual
    )

    referencia = preparar_imagen(
        imagen_referencia
    )

    if actual is None or referencia is None:
        return 0.0

    # --------------------------------------------------------
    # CORRELACIÓN
    # --------------------------------------------------------

    resultado = cv2.matchTemplate(
        actual,
        referencia,
        cv2.TM_CCOEFF_NORMED
    )

    similitud = float(
        resultado[0][0]
    )

    return similitud

def buscar_seccion(hwnd, secciones):

    mejor_seccion = None
    mejor_similitud = -1.0

    debug("Comparando afirmación...")

    time.sleep(1.1) #Tiempo entre avances

    for seccion in secciones:

        imagen_actual = capturar_afirmacion_region(
            hwnd,
            seccion["region_afirmacion"]
        )

        if imagen_actual is None:
            continue

        referencia = cv2.imread(
            seccion["afirmacion"]
        )

        if referencia is None:

            debug(
                f"  Sección {seccion['id']}: "
                "no se pudo abrir referencia."
            )

            continue

        similitud = comparar_imagenes(
            imagen_actual,
            referencia
        )

        debug(
            f"  Sección {seccion['id']}: "
            f"{similitud:.4f}"
        )

        if similitud > mejor_similitud:

            mejor_similitud = similitud
            mejor_seccion = seccion

    if mejor_seccion is None:

        print(
            "No se encontró ninguna sección."
        )

        return None, 0.0

    debug(
        f"Mejor coincidencia: "
        f"SECCIÓN {mejor_seccion['id']} "
        f"({mejor_similitud:.4f})"
    )

    return mejor_seccion, mejor_similitud

def preparar_opcion_reforzada(imagen):

    if imagen is None:
        return None

    gris = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGR2GRAY
    )

    _, reforzada = cv2.threshold(
        gris,
        0,
        255,
        cv2.THRESH_BINARY_INV
        + cv2.THRESH_OTSU
    )

    return reforzada

def buscar_opcion_en_region(imagen_region,ruta_opcion):

    if imagen_region is None:
        return None

    opcion = cv2.imread(
        ruta_opcion
    )

    if opcion is None:

        print(
            f"No se pudo abrir: {ruta_opcion}"
        )

        return None

    if modo_reforzado():

        region_gris = preparar_opcion_reforzada(
            imagen_region
        )

        opcion_gris = preparar_opcion_reforzada(
            opcion
        )

    else:

        region_gris = cv2.cvtColor(
            imagen_region,
            cv2.COLOR_BGR2GRAY
        )

        opcion_gris = cv2.cvtColor(
            opcion,
            cv2.COLOR_BGR2GRAY
        )

    alto_opcion, ancho_opcion = (
        opcion_gris.shape
    )

    alto_region, ancho_region = (
        region_gris.shape
    )

    if (
        ancho_opcion > ancho_region
        or alto_opcion > alto_region
    ):

        print(
            "La opción es más grande que "
            "la región de búsqueda."
        )

        return None

    resultado = cv2.matchTemplate(
        region_gris,
        opcion_gris,
        cv2.TM_CCOEFF_NORMED
    )

    _, similitud_maxima, _, posicion = (
        cv2.minMaxLoc(resultado)
    )

    x, y = posicion

    # Centro de la coincidencia
    centro_x = x + ancho_opcion // 2
    centro_y = y + alto_opcion // 2

    return {
        "x": centro_x,
        "y": centro_y,
        "similitud": float(similitud_maxima),
        "ancho": ancho_opcion,
        "alto": alto_opcion
    }