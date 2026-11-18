import mss
import numpy as np
import cv2
import win32gui

import config

def capturar_ventana_block_vertical(hwnd):

    izquierda, arriba, derecha, abajo = win32gui.GetWindowRect(hwnd)

    x1 = izquierda + config.BLOCK_VERTICAL_X_INICIO
    y1 = arriba + config.BLOCK_VERTICAL_Y_INICIO

    x2 = izquierda + config.BLOCK_VERTICAL_X_FIN
    y2 = arriba + config.BLOCK_VERTICAL_Y_FIN

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

    return imagen

def capturar_block_vertical_automata(hwnd,calibracion):

    izquierda, arriba, derecha, abajo = (
        win32gui.GetWindowRect(hwnd)
    )

    x1 = (
        izquierda
        + calibracion["x_inicio"]
    )

    y1 = (
        arriba
        + calibracion["y_inicio"]
    )

    x2 = (
        izquierda
        + calibracion["x_fin"]
    )

    y2 = (
        arriba
        + calibracion["y_fin"]
    )

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

    return imagen