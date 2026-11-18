import os

import cv2
import mss
import numpy as np
import win32gui

from ui.mouse_coords import (
    ocultar_visor_coordenadas,
    mostrar_visor_coordenadas
)

# CONFIGURACIÓN DEL DETECTOR DE PANTALLA BLANCA
UMBRAL_PANTALLA_BLANCA = 98.0

def capturar_pantalla_actual(hwnd):

    if not hwnd:

        print(
            "[INSPECTOR DE AVANCE] "
            "No hay ventana para capturar."
        )

        return None

    try:

        izquierda, arriba, derecha, abajo = (
            win32gui.GetWindowRect(hwnd)
        )

        ancho = derecha - izquierda
        alto = abajo - arriba

        # ====================================================
        # MISMA REGIÓN QUE LA CAPTURA TESTIGO
        # ====================================================

        margen_izquierdo = 6
        margen_derecho = 6

        margen_superior = 112
        margen_inferior = 6

        x = izquierda + margen_izquierdo
        y = arriba + margen_superior

        ancho_region = (
            ancho
            - margen_izquierdo
            - margen_derecho
        )

        alto_region = (
            alto
            - margen_superior
            - margen_inferior
        )

        if ancho_region <= 0 or alto_region <= 0:

            print(
                "[INSPECTOR DE AVANCE] "
                "Región de captura inválida."
            )

            return None

        monitor = {
            "left": x,
            "top": y,
            "width": ancho_region,
            "height": alto_region
        }

        ocultar_visor_coordenadas()

        try:

            with mss.mss() as sct:
                captura = sct.grab(monitor)
                imagen = np.array(captura)

        finally:

            mostrar_visor_coordenadas()

        imagen = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGRA2BGR
        )

        return imagen

    except Exception as e:

        print(
            "[INSPECTOR DE AVANCE] "
            f"Error capturando pantalla actual: {e}"
        )

        return None

def analizar_movimiento_pantallas(imagen_1, imagen_2):

    if imagen_1 is None or imagen_2 is None:
        return None

    try:

        # Asegurar que ambas capturas tengan el mismo tamaño
        if imagen_1.shape[:2] != imagen_2.shape[:2]:

            imagen_2 = cv2.resize(
                imagen_2,
                (
                    imagen_1.shape[1],
                    imagen_1.shape[0]
                )
            )

        # Pasar ambas imágenes a escala de grises
        gris_1 = cv2.cvtColor(
            imagen_1,
            cv2.COLOR_BGR2GRAY
        )

        gris_2 = cv2.cvtColor(
            imagen_2,
            cv2.COLOR_BGR2GRAY
        )

        # Diferencia absoluta entre ambas capturas
        diferencia = cv2.absdiff(
            gris_1,
            gris_2
        )

        # ----------------------------------------------------
        # DATOS PUROS
        # Todavía NO decidimos si existe movimiento.
        # ----------------------------------------------------

        pixeles_totales = int(
            diferencia.size
        )

        pixeles_diferentes = int(
            np.count_nonzero(diferencia)
        )

        porcentaje_pixeles_diferentes = (
            pixeles_diferentes
            / pixeles_totales
            * 100.0
        )

        diferencia_media = float(
            np.mean(diferencia)
        )

        diferencia_maxima = int(
            np.max(diferencia)
        )

        similitud = (
            1.0
            - diferencia_media / 255.0
        ) * 100.0

        return {
            "similitud": similitud,
            "pixeles_diferentes": pixeles_diferentes,
            "pixeles_totales": pixeles_totales,
            "porcentaje_pixeles_diferentes":
                porcentaje_pixeles_diferentes,
            "diferencia_media": diferencia_media,
            "diferencia_maxima": diferencia_maxima,
        }

    except Exception as e:

        print(
            "[INSPECTOR DE AVANCE] "
            f"Error analizando movimiento: {e}"
        )

        return None

def calcular_similitud_pantallas(imagen_testigo,imagen_actual):

    if imagen_testigo is None:
        return None

    if imagen_actual is None:
        return None

    try:

        # ====================================================
        # ASEGURAR MISMO TAMAÑO
        # ====================================================

        if (
            imagen_testigo.shape[:2]
            != imagen_actual.shape[:2]
        ):

            imagen_actual = cv2.resize(
                imagen_actual,
                (
                    imagen_testigo.shape[1],
                    imagen_testigo.shape[0]
                )
            )

        # ====================================================
        # PASAR A ESCALA DE GRISES
        # ====================================================

        gris_testigo = cv2.cvtColor(
            imagen_testigo,
            cv2.COLOR_BGR2GRAY
        )

        gris_actual = cv2.cvtColor(
            imagen_actual,
            cv2.COLOR_BGR2GRAY
        )

        # ====================================================
        # DIFERENCIA ABSOLUTA
        # ====================================================

        diferencia = cv2.absdiff(
            gris_testigo,
            gris_actual
        )

        diferencia_media = (
            np.mean(diferencia)
        )

        # 0 diferencia = idénticas
        # 255 diferencia = totalmente distintas
        #
        # Convertimos eso en similitud 0..1

        similitud = (
            1.0
            - (
                diferencia_media
                / 255.0
            )
        )

        return float(similitud)

    except Exception as e:

        print(
            "[INSPECTOR DE AVANCE] "
            f"Error calculando similitud: {e}"
        )

        return None

def detectar_pantalla_blanca(imagen):

    if imagen is None:
        return False, 0.0

    try:

        gris = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGR2GRAY
        )

        # ====================================================
        # PIXELES MUY CLAROS
        # ====================================================

        pixeles_claros = (
            gris >= 245
        )

        porcentaje_claro = (
            np.mean(
                pixeles_claros
            )
            * 100
        )

        # ====================================================
        # CONSIDERAMOS PANTALLA BLANCA
        # SI CASI TODA LA REGIÓN ES MUY CLARA
        # ====================================================

        ES_PANTALLA_BLANCA = (
            porcentaje_claro >= UMBRAL_PANTALLA_BLANCA #criterio pantalla blanca
        )

        return (
            ES_PANTALLA_BLANCA,
            float(porcentaje_claro)
        )

    except Exception as e:

        print(
            "[INSPECTOR DE AVANCE] "
            f"Error detectando pantalla blanca: {e}"
        )

        return False, 0.0
