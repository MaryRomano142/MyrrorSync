import os
import time
import win32gui
import win32api
import win32con
import config

from block_vertical.capture_blockvertical import (
    capturar_ventana_block_vertical,
    capturar_block_vertical_automata
)

from block_vertical.detector_blockvertical import procesar

from block_vertical.capture_state import (
    captura_reforzada_activa
)

from block_vertical.capture_reforzada import (
    mejorar_imagen_block_vertical
)

from core.debug import debug
from core.sound import reproducir

from ui.ui_state import (
    mostrar_blockvert_clickeando,
    mostrar_blockvert_desactivado
)

from windows.window_actions import (
    traer_ventana_al_frente
)

RUTA_CONFIG = "config.py"

def guardar_config_block_vertical():

    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas = []

    for linea in lineas:

        if linea.startswith("BLOCK_VERTICAL_X_INICIO"):

            nuevas.append(
                f"BLOCK_VERTICAL_X_INICIO = "
                f"{config.BLOCK_VERTICAL_X_INICIO}\n"
            )

        elif linea.startswith("BLOCK_VERTICAL_X_FIN"):

            nuevas.append(
                f"BLOCK_VERTICAL_X_FIN = "
                f"{config.BLOCK_VERTICAL_X_FIN}\n"
            )

        elif linea.startswith("BLOCK_VERTICAL_Y_INICIO"):

            nuevas.append(
                f"BLOCK_VERTICAL_Y_INICIO = "
                f"{config.BLOCK_VERTICAL_Y_INICIO}\n"
            )

        elif linea.startswith("BLOCK_VERTICAL_Y_FIN"):

            nuevas.append(
                f"BLOCK_VERTICAL_Y_FIN = "
                f"{config.BLOCK_VERTICAL_Y_FIN}\n"
            )

        elif linea.startswith(
            "BLOCK_VERTICAL_AJUSTE_PEQUENOS"
        ):

            nuevas.append(
                f"BLOCK_VERTICAL_AJUSTE_PEQUENOS = "
                f"{config.BLOCK_VERTICAL_AJUSTE_PEQUENOS}\n"
            )

        elif linea.startswith(
            "BLOCK_VERTICAL_AJUSTE_GRANDES"
        ):

            nuevas.append(
                f"BLOCK_VERTICAL_AJUSTE_GRANDES = "
                f"{config.BLOCK_VERTICAL_AJUSTE_GRANDES}\n"
            )

        else:

            nuevas.append(linea)

    ruta_temporal = RUTA_CONFIG + ".tmp"

    with open(ruta_temporal,"w",encoding="utf-8") as f:

        f.writelines(nuevas)

        f.flush()

        os.fsync(f.fileno())

    os.replace(
        ruta_temporal,
        RUTA_CONFIG
    )

    debug("Config Block Vertical actualizada.")

def actualizar_block_vertical(maestra, esclavas):

    resultados = capturar_y_detectar_todas(
        maestra,
        esclavas
    )

    debug(
        "\n========== INICIANDO CLICS =========="
    )

    for resultado in resultados:

        ventana = resultado["ventana"]
        botones = resultado["botones"]

        debug(
            f"\nClickeando: {ventana['proceso']}"
        )

        clicar_botones(
            botones
        )

    debug(
        "\n========== BLOCK VERTICAL TERMINADO =========="
    )

    return resultados

def capturar_y_detectar_ventana(ventana):

    hwnd = ventana["hwnd"]

    imagen = capturar_ventana_block_vertical(hwnd)

    if imagen is None:
        return []

    # ========================================================
    # MODO DE IMAGEN DEL BLOCK VERTICAL
    # ========================================================

    if captura_reforzada_activa():

        debug(
            "[BLOCK VERTICAL] "
            "Aplicando captura reforzada."
        )

        imagen = mejorar_imagen_block_vertical(
            imagen
        )

    else:

        debug(
            "[BLOCK VERTICAL] "
            "Usando captura normal."
        )

    botones = procesar(imagen)

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    botones_absolutos = []

    for boton in botones:

        botones_absolutos.append({
            "x": izquierda + boton["x"] + config.BLOCK_VERTICAL_X_INICIO,
            "y": arriba + boton["y"] + config.BLOCK_VERTICAL_Y_INICIO,
            "w": boton["w"],
            "h": boton["h"],
            "marcada": boton["marcada"]
        })

    return botones_absolutos

def capturar_y_detectar_todas(maestra, esclavas):

    ventanas = []

    if maestra is not None:
        ventanas.append(maestra)
    

    ventanas.extend(esclavas)

    resultados = []

    debug("\n========== BLOCK VERTICAL ==========")
    debug("Capturando y detectando...\n")

    for ventana in ventanas:

        debug(
            f"Ventana: {ventana['proceso']}"
        )

        botones = capturar_y_detectar_ventana(
            ventana
        )

        resultados.append({
            "ventana": ventana,
            "botones": botones
        })

        debug(
            f"Botones/casillas detectados: "
            f"{len(botones)}"
        )

        for i, boton in enumerate(botones, 1):

            debug(
                f"  {i}. "
                f"x={boton['x']} "
                f"y={boton['y']} "
                f"({boton['w']}x{boton['h']})"
            )

    debug(
        "Todas las ventanas fueron procesadas."
    )

    return resultados

def clicar_botones(botones):

    botones_para_clicar = [
        boton
        for boton in botones
        if not boton["marcada"]
    ]

    debug(
        f"Detectados: {len(botones)} | "
        f"Marcados: {len(botones) - len(botones_para_clicar)} | "
        f"Para clicar: {len(botones_para_clicar)}"
    )

    reproducir("clicksblockvertical")

    for boton in botones_para_clicar:

        x = boton["x"]
        y = boton["y"]

        debug(
            f"Clic: x={x} y={y}"
        )

        win32api.SetCursorPos(
            (x, y)
        )

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTDOWN,
            0,
            0,
            0,
            0
        )

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0
        )

        time.sleep(0.01) #velocidad en que se hace cada clic 0.02

def reproducir_block_vertical_automata(ventana,evento):

    mostrar_blockvert_clickeando()

    hwnd = ventana["hwnd"]

    calibracion = evento.get(
        "calibracion"
    )

    modo_evento = evento.get(
        "modo_captura",
        "normal"
    )

    if calibracion is None:

        debug(
            "[AUTOMATA] "
            "Block Vertical sin calibración."
        )

        return

    debug(
        "========== BLOCK VERTICAL AUTÓMATA =========="
    )

    debug(
        f"Ventana: "
        f"{ventana['proceso']}"
    )

    # ========================================================
    # CAPTURAR CON LA CALIBRACIÓN DE LA GRABACIÓN
    # ========================================================

    imagen = capturar_block_vertical_automata(
        hwnd,
        calibracion
    )

    if imagen is None:

        print(
            "[AUTOMATA] "
            "No se pudo capturar Block Vertical."
        )

        return
    
    # ========================================================
    # MODO DE IMAGEN GUARDADO EN LA GRABACIÓN
    # ========================================================

    if modo_evento == "reforzado":

        debug(
            "[BLOCK VERTICAL AUTÓMATA] "
            "Aplicando captura reforzada."
        )

        imagen = mejorar_imagen_block_vertical(
            imagen
        )

    else:

        debug(
            "[BLOCK VERTICAL AUTÓMATA] "
            "Usando captura normal."
        )

    # ========================================================
    # DETECTAR BOTONES
    # ========================================================

    botones = procesar(
        imagen
    )

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    botones_absolutos = []

    for boton in botones:

        botones_absolutos.append({

            "x":
                izquierda
                + boton["x"]
                + calibracion["x_inicio"],

            "y":
                arriba
                + boton["y"]
                + calibracion["y_inicio"],

            "w":
                boton["w"],

            "h":
                boton["h"],

            "marcada":
                boton["marcada"]
        })

    debug(
        f"Botones detectados: "
        f"{len(botones_absolutos)}"
    )

    # ========================================================
    # CLICKEAR LOS QUE NO ESTÁN MARCADOS
    # ========================================================

    clicar_botones(
        botones_absolutos
    )

    debug(
        "========== BLOCK VERTICAL TERMINADO =========="
    )

    mostrar_blockvert_desactivado()