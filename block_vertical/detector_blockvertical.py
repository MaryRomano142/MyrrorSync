import cv2
import numpy as np
import config

from core.debug import debug

from block_vertical.capture_state import (
    captura_reforzada_activa
)

def esta_marcada(imagen, x, y, w, h):

    # Dejamos afuera el borde del botón/casilla.
    margen = 4

    x1 = max(0, x + margen)
    y1 = max(0, y + margen)

    x2 = min(
        imagen.shape[1],
        x + w - margen
    )

    y2 = min(
        imagen.shape[0],
        y + h - margen
    )

    interior = imagen[
        y1:y2,
        x1:x2
    ]

    if interior.size == 0:
        return False

    # Convertir el interior a HSV.
    hsv = cv2.cvtColor(
        interior,
        cv2.COLOR_BGR2HSV
    )

    # Saturación alta = color fuerte.
    saturacion = hsv[:, :, 1]

    # Contamos píxeles con bastante color.
    pixeles_coloreados = np.sum(
        saturacion > 80
    )

    total_pixeles = saturacion.size

    porcentaje_coloreado = (
        pixeles_coloreados /
        total_pixeles
    )

    # Si una cantidad apreciable del interior
    # tiene color, consideramos que está marcada.
    return porcentaje_coloreado > 0.05

def es_casilla(contorno):

    perimetro = cv2.arcLength(
        contorno,
        True
    )

    if perimetro == 0:
        return False

    aproximado = cv2.approxPolyDP(
        contorno,
        0.04 * perimetro,
        True
    )

    return len(aproximado) == 4

def procesar(imagen):

    # Escala de grises

    gris = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGR2GRAY
    )

    cv2.imwrite(
        "block_vertical_gris.png",
        gris
    )

    # ========================================================
    # UMBRAL NORMAL / REFORZADO
    # ========================================================

    if captura_reforzada_activa():

        debug(
            "[BLOCK VERTICAL] "
            "Detector REFORZADO."
        )

        # El umbral se calcula localmente.
        # Esto ayuda con radios/casillas muy tenues
        # sobre fondos claros similares.

        umbral = cv2.adaptiveThreshold(
            gris,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            15,
            4
        )

    else:

        debug(
            "[BLOCK VERTICAL] "
            "Detector NORMAL."
        )

        _, umbral = cv2.threshold(
            gris,
            180,
            255,
            cv2.THRESH_BINARY_INV
        )

    cv2.imwrite(
        "block_vertical_umbral.png",
        umbral
    )

    # Dilatación

    kernel = np.ones(
        (3, 3),
        np.uint8
    )

    dilatada = cv2.dilate(
        umbral,
        kernel,
        iterations=1
    )

    cv2.imwrite(
        "block_vertical_dilatada.png",
        dilatada
    )

    # Buscar contornos

    contornos, _ = cv2.findContours(
        dilatada,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    botones = []

    for contorno in contornos:

        x, y, w, h = cv2.boundingRect(contorno)

        area = cv2.contourArea(contorno)

        # ====================================================
        # FILTRO GEOMÉTRICO CALIBRABLE
        # ====================================================

        ajuste_pequenos = (
            config.BLOCK_VERTICAL_AJUSTE_PEQUENOS
        )

        ajuste_grandes = (
            config.BLOCK_VERTICAL_AJUSTE_GRANDES
        )

        # Valores originales del detector:
        #
        # ancho mínimo: 15
        # alto mínimo:   9
        # ancho máximo: 22
        # alto máximo:  22
        # área mínima: 180
        # diferencia máxima w/h: 5

        ancho_minimo = max(
            3,
            15 - ajuste_pequenos
        )

        alto_minimo = max(
            3,
            9 - ajuste_pequenos
        )

        area_minima = max(
            20,
            180 - (
                ajuste_pequenos * 20
            )
        )

        ancho_maximo = (
            22
            + ajuste_grandes
        )

        alto_maximo = (
            22
            + ajuste_grandes
        )

        diferencia_maxima = (
            5
            + ajuste_grandes
        )

        if w < ancho_minimo:
            continue

        if h < alto_minimo:
            continue

        if w > ancho_maximo:
            continue

        if h > alto_maximo:
            continue

        if abs(w - h) > diferencia_maxima:
            continue

        if area < area_minima:
            continue

        # Centro del botón

        centro_x = x + w // 2
        centro_y = y + h // 2

        if es_casilla(contorno):

            marcada = esta_marcada(
                imagen,
                x,
                y,
                w,
                h
            )

        else:

            marcada = False

        botones.append({

            "x": centro_x,

            "y": centro_y,

            "w": w,

            "h": h,

            "marcada": marcada

        })

    # Ordenar de arriba hacia abajo

    botones.sort(
        key=lambda boton: boton["y"]
    )

    debug(
        f"\nBotones detectados: {len(botones)}"
    )

    for i, boton in enumerate(botones, 1):

        estado = (
            "MARCADA"
            if boton["marcada"]
            else "VACIA"
        )

        debug(
            f"{i}. "
            f"x={boton['x']} "
            f"y={boton['y']} "
            f"({boton['w']}x{boton['h']}) "
            f"-> {estado}"
        )
    
    imagen_detectados = imagen.copy()

    for boton in botones:

        x = boton["x"]
        y = boton["y"]
        w = boton["w"]
        h = boton["h"]

        cv2.rectangle(
            imagen_detectados,
            (
                x - w // 2,
                y - h // 2
            ),
            (
                x + w // 2,
                y + h // 2
            ),
            (0, 255, 0),
            2
        )

        cv2.circle(
            imagen_detectados,
            (x, y),
            2,
            (0, 0, 255),
            -1
        )

    cv2.imwrite(
        "block_vertical_detectados.png",
        imagen_detectados
    )

    return botones