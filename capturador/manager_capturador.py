import win32gui
import config
import time
import pyautogui
import importlib
import threading
import os
import json
import shutil

pyautogui.PAUSE = 0.001

from automata.manager_automata import (
    automata_grabando,
    automata_acepta_eventos
)

from automata.recorder import (
    registrar_evento,
    siguiente_orden
)

from automata.storage import (
    crear_carpeta_evento
)

from automata.events import (
    CAPTURADOR
)

from capturador.capture_capturador import (
    capturar_opcion,
    capturar_imagen_opcion,
    guardar_imagen_opcion,
    capturar_region_opciones,
    recortar_opcion_desde_snapshot,
    MARGEN_VISOR,
    limpiar_capturas
)

from capturador.detector_capturador import (
    buscar_opcion_en_region
)

from capturador.capture_state import (
    obtener_modo,
    MODO_NORMAL,
    establecer_modo,
    arrastre_inteligente_activo
)

from core.mirror import (
    obtener_esclavas,
    desactivar_espejo,
    activar_espejo,
    iniciar_evento_interno,
    finalizar_evento_interno
)

from core.debug import debug

from core.sound import (
    reproducir,
    reproducir_bucle,
    detener
)

from ui.ui_state import (
    mostrar_capturador_activo,
    mostrar_capturador_replicando,
    mostrar_capturador_desactivado
)

from windows.window_actions import (
    traer_ventana_al_frente
)

RUTA_CONFIG = "config.py"
PASO_OFFSET_X = 10
PASO_OFFSET_Y = 10
activo = False
numero_seccion = 1
secciones = []
# Flechas usadas después de la región actual
movimientos_pendientes = []
click_fuera_pendiente = None
snapshot_limpio_pendiente = None
ARRASTRE_UMBRAL_SEGUNDOS = 0.50
arrastre_mouse_down = False
arrastre_inicio_tiempo = None
arrastre_inicio_x = None
arrastre_inicio_y = None
arrastre_hwnd = None
arrastre_imagen_inicial = None

# ============================================================
# VELOCIDADES CAPTURADOR
# ============================================================

# Clics normales
TIEMPO_MOVER_CLICK = 0.05
TIEMPO_ANTES_CLICK = 0.05
TIEMPO_DESPUES_CLICK = 0.10 #Pausa entre clics

# Clic de foco
TIEMPO_MOVER_FOCO = 0.03
TIEMPO_ANTES_FOCO = 0.02
TIEMPO_DESPUES_FOCO = 0.04

# Flechas
TIEMPO_ENTRE_FLECHAS_CAP = 0.001
TIEMPO_DESPUES_FLECHAS = 1.0

# Arrastre
TIEMPO_MOVER_ORIGEN = 0.10
TIEMPO_ANTES_MOUSE_DOWN = 0.01
TIEMPO_MOUSE_DOWN = 0.08
TIEMPO_ARRASTRE = 0.20
TIEMPO_ANTES_MOUSE_UP = 0.01
TIEMPO_REACOMODO = 0.40

def activar_capturador():

    global activo
    global numero_seccion
    global secciones
    global movimientos_pendientes
    global click_fuera_pendiente

    activo = True

    desactivar_espejo(
        activar_manual_al_salir=False
    )
    mostrar_capturador_activo()
    reproducir("capturador")

    numero_seccion = 1

    secciones = []

    movimientos_pendientes = []

    click_fuera_pendiente = None

    limpiar_capturas()

    debug(
        "========== CAPTURADOR =========="
    )

    debug(
        "CAPTURADOR ACTIVADO"
    )

    debug(
        "Esperando selección..."
    )

def desactivar_capturador():

    global activo
    global click_fuera_pendiente
    global movimientos_pendientes

    if not activo:
        return

    activo = False

    mostrar_capturador_replicando()
    
    # ========================================================
    # SI QUEDÓ UN CLIC FUERA PENDIENTE,
    # ESE ERA EL CLIC DE AVANZAR
    # ========================================================

    seccion = obtener_seccion_actual()

    if (
        seccion is not None
        and
        click_fuera_pendiente is not None
    ):

        seccion["click_avanzar"] = (
            click_fuera_pendiente.copy()
        )

        debug(
            f"Avance sección "
            f"{seccion['id']}: "
            f"x={click_fuera_pendiente['x_rel']} "
            f"y={click_fuera_pendiente['y_rel']}"
        )

    click_fuera_pendiente = None
    movimientos_pendientes = []

    # ============================================================
    # GUARDAR CAPTURADOR EN AUTÓMATA
    # ============================================================

    if automata_acepta_eventos():

        guardar_sesion_automata_capturador()

    debug(
        "========== CAPTURADOR =========="
    )

    debug(
        "CAPTURADOR DESACTIVADO"
    )

    # ============================================================
    # REPLICAR EN OTRO HILO
    #
    # MUY IMPORTANTE:
    # No bloquear el listener de pynput.
    # ============================================================

    hilo = threading.Thread(
        target=ejecutar_replica_capturador,
        daemon=True
    )

    hilo.start()

def ejecutar_replica_capturador():

    reproducir_bucle("capturadorreplicando")

    try:

        esclavas = obtener_esclavas()

        if not esclavas:

            print(
                "No hay esclavas configuradas."
            )

            return

        if not secciones:

            debug(
                "No hay secciones aprendidas."
            )

            return

        debug(
            "Iniciando prueba de búsqueda "
            "en esclavas..."
        )

        for ventana in esclavas:

            probar_busqueda_esclava(
                ventana
            )

        debug(
            "Prueba de búsqueda terminada."
        )

    finally:

        detener("capturadorreplicando")

        mostrar_capturador_desactivado()

        activar_espejo()

def cambiar_estado_capturador():

    if activo:
        desactivar_capturador()
    else:
        activar_capturador()

def capturador_esta_activo():

    return activo

def guardar_config_capturador():

    with open(RUTA_CONFIG,"r",encoding="utf-8") as f:

        lineas = f.readlines()

    nuevas = []

    for linea in lineas:

        if linea.startswith(
            "CAPTURADOR_OPCIONES_X_INICIO"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCIONES_X_INICIO = "
                f"{config.CAPTURADOR_OPCIONES_X_INICIO}\n"
            )

        elif linea.startswith(
            "CAPTURADOR_OPCIONES_X_FIN"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCIONES_X_FIN = "
                f"{config.CAPTURADOR_OPCIONES_X_FIN}\n"
            )

        elif linea.startswith(
            "CAPTURADOR_OPCIONES_Y_INICIO"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCIONES_Y_INICIO = "
                f"{config.CAPTURADOR_OPCIONES_Y_INICIO}\n"
            )

        elif linea.startswith(
            "CAPTURADOR_OPCIONES_Y_FIN"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCIONES_Y_FIN = "
                f"{config.CAPTURADOR_OPCIONES_Y_FIN}\n"
            )

        elif linea.startswith(
            "CAPTURADOR_OPCION_ANCHO"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCION_ANCHO = "
                f"{config.CAPTURADOR_OPCION_ANCHO}\n"
            )

        elif linea.startswith(
            "CAPTURADOR_OPCION_ALTO"
        ):

            nuevas.append(
                f"CAPTURADOR_OPCION_ALTO = "
                f"{config.CAPTURADOR_OPCION_ALTO}\n"
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

    debug(
        "Config Capturador actualizada."
    )

def capturar_snapshot_limpio_capturador(hwnd):

    global snapshot_limpio_pendiente

    imagen = capturar_region_opciones(
        hwnd
    )

    if imagen is None:

        print(
            "[CAPTURADOR] "
            "No se pudo capturar "
            "el snapshot limpio."
        )

        snapshot_limpio_pendiente = None

        return False

    snapshot_limpio_pendiente = (
        imagen.copy()
    )

    print(
        "[CAPTURADOR] "
        "Snapshot guardado."
    )

    return True

#funcion para la tecla asignada en event_listener
def guardar_calibracion_capturador():

    guardar_config_capturador()

    importlib.reload(
        config
    )

    debug(
        "Calibración CAPTURADOR guardada."
    )

def mover_offset_izquierda():

    config.CAPTURADOR_OPCION_OFFSET_X -= PASO_OFFSET_X

    debug(
        f"[CAPTURADOR] Offset X: "
        f"{config.CAPTURADOR_OPCION_OFFSET_X}"
    )

def mover_offset_derecha():

    config.CAPTURADOR_OPCION_OFFSET_X += PASO_OFFSET_X

    debug(
        f"[CAPTURADOR] Offset X: "
        f"{config.CAPTURADOR_OPCION_OFFSET_X}"
    )

def mover_offset_arriba():

    config.CAPTURADOR_OPCION_OFFSET_Y -= PASO_OFFSET_Y

    debug(
        f"[CAPTURADOR] Offset Y: "
        f"{config.CAPTURADOR_OPCION_OFFSET_Y}"
    )

def mover_offset_abajo():

    config.CAPTURADOR_OPCION_OFFSET_Y += PASO_OFFSET_Y

    debug(
        f"[CAPTURADOR] Offset Y: "
        f"{config.CAPTURADOR_OPCION_OFFSET_Y}"
    )

def hacer_magenta_mas_alto():

    config.CAPTURADOR_OPCION_ALTO += 5

def hacer_magenta_menos_alto():

    config.CAPTURADOR_OPCION_ALTO = max(
        10,
        config.CAPTURADOR_OPCION_ALTO - 5
    )

def hacer_magenta_menos_ancho(event=None):

    config.CAPTURADOR_OPCION_ANCHO = max(
        10,
        config.CAPTURADOR_OPCION_ANCHO - 5
    )

def hacer_magenta_mas_ancho(event=None):

    config.CAPTURADOR_OPCION_ANCHO += 5

def registrar_opcion(hwnd,mouse_x,mouse_y):

    global secciones
    global movimientos_pendientes
    global click_fuera_pendiente

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    seccion = obtener_seccion_actual()

    # ========================================================
    # CREAR SECCIÓN SI TODAVÍA NO EXISTE
    # ========================================================

    if seccion is None:

        seccion = {

            "id": numero_seccion,

            "opciones": [],

            "regiones": [],

            "click_avanzar": None
        }

        secciones.append(
            seccion
        )

    # ========================================================
    # CREAR PRIMERA REGIÓN
    # ========================================================

    if not seccion["regiones"]:

        region = crear_region_actual()

        seccion["regiones"].append(
            region
        )

    # ========================================================
    # SI HUBO NAVEGACIÓN, ESTE CLIC CONFIRMA NUEVA REGIÓN
    # ========================================================

    elif movimientos_pendientes:

        region_anterior = (
            seccion["regiones"][-1]
        )

        region_anterior[
            "movimientos_despues"
        ] = movimientos_pendientes.copy()

        movimientos_pendientes = []

        region = crear_region_actual()

        seccion["regiones"].append(
            region
        )

        debug(
            f"Nueva región creada en "
            f"sección {numero_seccion}"
        )

        debug(
            f"Región actual: "
            f"{len(seccion['regiones'])}"
        )

    else:

        region = (
            seccion["regiones"][-1]
        )

    # ========================================================
    # CAPTURAR OPCIÓN GLOBAL
    # ========================================================

    numero_opcion = (
        len(seccion["opciones"]) + 1
    )

    numero_region = (
        len(seccion["regiones"])
    )

    # ========================================================
    # CAPTURAR OPCIÓN DESDE EL SNAPSHOT LIMPIO
    #
    # La pantalla en vivo puede estar afectada por:
    # - hover
    # - estado seleccionado
    #
    # Por eso el patrón se extrae de la fotografía virgen
    # tomada al guardar la calibración.
    # ========================================================

    snapshot_limpio = (
        region.get(
            "snapshot_limpio"
        )
    )

    region_guardada = (
        region[
            "region_opciones"
        ]
    )

    imagen = (
        recortar_opcion_desde_snapshot(
            snapshot_limpio,
            x_rel,
            y_rel,
            region_guardada
        )
    )

    if imagen is None:

        print(
            "[CAPTURADOR] "
            "No se extrajo la opción "
            "desde el snapshot limpio."
        )

        return

    ruta = guardar_imagen_opcion(
        imagen,
        numero_seccion,
        numero_region,
        numero_opcion
    )

    if ruta is None:
        return

    seccion["opciones"].append({

        "id": numero_opcion,

        "tipo": "click",

        "imagen": ruta,

        "x_rel": x_rel,

        "y_rel": y_rel,

        "offset_x":
            config.CAPTURADOR_OPCION_OFFSET_X,

        "offset_y":
            config.CAPTURADOR_OPCION_OFFSET_Y,

        "opcion_ancho":
            config.CAPTURADOR_OPCION_ANCHO,

        "opcion_alto":
            config.CAPTURADOR_OPCION_ALTO
    })

    # Si había un clic fuera pendiente pero
    # después vino una opción sin flechas,
    # ya no nos sirve como avance.
    if click_fuera_pendiente is not None:

        click_fuera_pendiente = None

    debug(
        f"Sección {numero_seccion} | "
        f"Región {numero_region} | "
        f"Opción global {numero_opcion}"
    )

    debug(
        f"Clic real: "
        f"x={x_rel} y={y_rel}"
    )

def registrar_avance(hwnd, mouse_x, mouse_y):

    global movimientos_pendientes
    global numero_seccion

    seccion = obtener_seccion_actual()

    if seccion is None:

        print(
            "No se registraron opciones "
            "en esta sección."
        )

        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    seccion["click_avanzar"] = {
        "x_rel": x_rel,
        "y_rel": y_rel
    }

    debug(
        f"Avance sección {numero_seccion}: "
        f"x={x_rel} y={y_rel}"
    )

    # Si quedaron flechas pero nunca hubo otra opción,
    # no existe realmente otra región.

    movimientos_pendientes = []

    numero_seccion += 1

    print(
        f"Sección {numero_seccion}: "
        "esperando opciones..."
    )

    print()

def registrar_click_capturador(hwnd,mouse_x,mouse_y):

    global click_fuera_pendiente

    if not activo:
        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    dentro_region = (

        config.CAPTURADOR_OPCIONES_X_INICIO
        <= x_rel
        <= config.CAPTURADOR_OPCIONES_X_FIN

        and

        config.CAPTURADOR_OPCIONES_Y_INICIO
        <= y_rel
        <= config.CAPTURADOR_OPCIONES_Y_FIN
    )

    debug(
        f"[CAPTURADOR] "
        f"x={x_rel} "
        f"y={y_rel} "
        f"dentro_region={dentro_region}"
    )

    # ========================================================
    # CLIC DENTRO = OPCIÓN
    # ========================================================

    if dentro_region:

        registrar_opcion(
            hwnd,
            mouse_x,
            mouse_y
        )

        return

    # ========================================================
    # CLIC FUERA = TODAVÍA NO SABEMOS QUÉ ES
    # ========================================================

    click_fuera_pendiente = {

        "x_rel": x_rel,

        "y_rel": y_rel
    }

    debug(
        "[CAPTURADOR] "
        "Clic fuera pendiente de clasificación."
    )

def registrar_flecha_capturador(direccion):

    global movimientos_pendientes
    global click_fuera_pendiente

    if not activo:
        return

    if direccion not in (
        "up",
        "down",
        "left",
        "right"
    ):
        return

    seccion = obtener_seccion_actual()

    if seccion is None:
        return

    if not seccion["regiones"]:
        return

    region_actual = (
        seccion["regiones"][-1]
    )

    # ========================================================
    # SI HABÍA CLIC FUERA PENDIENTE,
    # AHORA SABEMOS QUE ERA CLIC DE FOCO
    # ========================================================

    if click_fuera_pendiente is not None:

        region_actual["click_foco"] = (
            click_fuera_pendiente.copy()
        )

        debug(
            "[CAPTURADOR] "
            "Clic pendiente convertido "
            "en clic de foco."
        )

        click_fuera_pendiente = None

    # ========================================================
    # AGRUPAR FLECHAS
    # ========================================================

    if (
        movimientos_pendientes
        and
        movimientos_pendientes[-1][
            "direccion"
        ] == direccion
    ):

        movimientos_pendientes[-1][
            "cantidad"
        ] += 1

    else:

        movimientos_pendientes.append({

            "direccion": direccion,

            "cantidad": 1
        })

    debug(
        f"[CAPTURADOR] "
        f"Flecha {direccion} | "
        f"movimientos pendientes: "
        f"{movimientos_pendientes}"
    )

def obtener_seccion_actual():

    if not secciones:
        return None

    seccion = secciones[-1]

    if seccion["id"] != numero_seccion:
        return None

    return seccion

def probar_busqueda_esclava(ventana):

    hwnd = ventana["hwnd"]

    debug(
        f"Probando Capturador en: "
        f"{ventana['proceso']}"
    )

    if not secciones:

        debug(
            "No hay secciones aprendidas."
        )

        return

    seccion = secciones[0]

    regiones = seccion.get(
        "regiones",
        []
    )

    opciones_globales = seccion.get(
        "opciones",
        []
    )

    if not regiones:

        print(
            "La sección no tiene regiones."
        )

        return

    if not opciones_globales:

        print(
            "La sección no tiene opciones."
        )

        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    opciones_completadas = set()

    total_opciones = len(
        opciones_globales
    )

    debug(
        f"Opciones globales: "
        f"{total_opciones}"
    )

    # ========================================================
    # RECORRER REGIONES
    # ========================================================

    for numero_region, region in enumerate(
        regiones,
        1
    ):

        debug(
            f"========== REGIÓN "
            f"{numero_region} =========="
        )

        puntos_usados = []

        nuevas_en_region = 0

        # ====================================================
        # CLICS NORMALES
        # ====================================================

        opciones_click = [

            opcion

            for opcion in opciones_globales

            if opcion.get(
                "tipo",
                "click"
            ) == "click"
        ]

        if opciones_click:

            imagen_region = (
                capturar_region_opciones(
                    hwnd,
                    region["region_opciones"]
                )
            )

            if imagen_region is None:

                print(
                    "No se pudo capturar "
                    "la región."
                )

                return

            for opcion in opciones_click:

                if procesar_click_capturador(
                    hwnd,
                    region,
                    opcion,
                    imagen_region,
                    puntos_usados,
                    opciones_completadas
                ):

                    nuevas_en_region += 1
        
        # ====================================================
        # ARRASTRE INTELIGENTE
        # ====================================================

        opciones_arrastre_inteligente = [

            opcion

            for opcion in opciones_globales

            if opcion.get(
                "tipo"
            ) == "arrastre_inteligente"
        ]

        for opcion in opciones_arrastre_inteligente:

            if procesar_arrastre_inteligente_capturador(
                hwnd,
                region,
                opcion,
                opciones_completadas
            ):

                nuevas_en_region += 1

        debug(
            f"Nuevas completadas "
            f"en región {numero_region}: "
            f"{nuevas_en_region}"
        )

        debug(
            f"Total completadas: "
            f"{len(opciones_completadas)}/"
            f"{total_opciones}"
        )

        # ====================================================
        # CLIC DE FOCO + FLECHAS
        # ====================================================

        movimientos = region.get(
            "movimientos_despues",
            []
        )

        if movimientos:

            click_foco = region.get(
                "click_foco"
            )

            if click_foco is None:

                print(
                    "Hay movimientos pero "
                    "no existe clic de foco."
                )

                return

            x_foco = (
                izquierda
                + click_foco["x_rel"]
            )

            y_foco = (
                arriba
                + click_foco["y_rel"]
            )

            debug(
                f"Clic de foco: "
                f"x={x_foco} "
                f"y={y_foco}"
            )

            iniciar_evento_interno()

            try:

                pyautogui.moveTo(
                    x_foco,
                    y_foco,
                    duration=TIEMPO_MOVER_FOCO
                )

                time.sleep(
                    TIEMPO_ANTES_FOCO
                )

                pyautogui.click()

                time.sleep(
                    TIEMPO_DESPUES_FOCO
                )

            finally:

                finalizar_evento_interno()

            iniciar_evento_interno()

            try:

                for movimiento in movimientos:

                    direccion = (
                        movimiento[
                            "direccion"
                        ]
                    )

                    cantidad = (
                        movimiento[
                            "cantidad"
                        ]
                    )

                    debug(
                        f"Replicando: "
                        f"{direccion} "
                        f"x{cantidad}"
                    )

                    for _ in range(
                        cantidad
                    ):

                        if direccion == "down":

                            pyautogui.press(
                                "down"
                            )

                        elif direccion == "up":

                            pyautogui.press(
                                "up"
                            )
                        
                        elif direccion == "left":

                            pyautogui.press(
                                "left"
                            )

                        elif direccion == "right":

                            pyautogui.press(
                                "right"
                            )

                        time.sleep(
                            TIEMPO_ENTRE_FLECHAS_CAP
                        )

                # Dejamos un instante para que pynput
                # termine de recibir las teclas artificiales.
                time.sleep(
                    0.05
                )

            finally:

                finalizar_evento_interno()

            time.sleep(TIEMPO_DESPUES_FLECHAS)

    # ========================================================
    # RESULTADO
    # ========================================================

    debug(
        "========== RESULTADO =========="
    )

    debug(
        f"Opciones completadas: "
        f"{len(opciones_completadas)}/"
        f"{total_opciones}"
    )

    faltantes = [

        opcion["id"]

        for opcion in opciones_globales

        if opcion["id"]
        not in opciones_completadas
    ]

    if faltantes:

        debug(
            f"No encontradas: "
            f"{faltantes}"
        )

    # ========================================================
    # AVANZAR
    # ========================================================

    click_avanzar = seccion.get(
        "click_avanzar"
    )

    if click_avanzar is None:

        print(
            "No existe clic de avance."
        )

        return

    x_avanzar = (
        izquierda
        + click_avanzar["x_rel"]
    )

    y_avanzar = (
        arriba
        + click_avanzar["y_rel"]
    )

    debug(
        f"Clic avanzar: "
        f"x={x_avanzar} "
        f"y={y_avanzar}"
    )

    iniciar_evento_interno()

    try:

        pyautogui.moveTo(
            x_avanzar,
            y_avanzar,
            duration=0.15
        )

        time.sleep(
            0.08
        )

        pyautogui.click()

    finally:

        finalizar_evento_interno()

    debug(
        "Sección del Capturador terminada."
    )

def crear_region_actual():

    global snapshot_limpio_pendiente

    return {

        "region_opciones": {

            "x_inicio":
                config.CAPTURADOR_OPCIONES_X_INICIO,

            "x_fin":
                config.CAPTURADOR_OPCIONES_X_FIN,

            "y_inicio":
                config.CAPTURADOR_OPCIONES_Y_INICIO,

            "y_fin":
                config.CAPTURADOR_OPCIONES_Y_FIN
        },

        # ====================================================
        # SNAPSHOT LIMPIO DE LA REGIÓN
        #
        # Se captura antes de seleccionar opciones.
        # Los recortes de cada opción saldrán de esta imagen,
        # no de la pantalla ya afectada por hover/selección.
        # ====================================================

        "snapshot_limpio": (
            snapshot_limpio_pendiente
        ),

        "click_foco": None,

        "movimientos_despues": []
    }

def registrar_mouse_down_capturador(hwnd,mouse_x,mouse_y):

    global arrastre_mouse_down
    global arrastre_inicio_tiempo
    global arrastre_inicio_x
    global arrastre_inicio_y
    global arrastre_hwnd
    global arrastre_imagen_inicial
    global snapshot_limpio_pendiente

    if not activo:
        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    x_rel = (
        mouse_x - izquierda
    )

    y_rel = (
        mouse_y - arriba
    )

    dentro_region = (

        config.CAPTURADOR_OPCIONES_X_INICIO
        <= x_rel
        <= config.CAPTURADOR_OPCIONES_X_FIN

        and

        config.CAPTURADOR_OPCIONES_Y_INICIO
        <= y_rel
        <= config.CAPTURADOR_OPCIONES_Y_FIN
    )

    if not dentro_region:

        arrastre_mouse_down = False
        arrastre_imagen_inicial = None

        return

    arrastre_mouse_down = True

    arrastre_inicio_tiempo = (
        time.perf_counter()
    )

    arrastre_inicio_x = mouse_x
    arrastre_inicio_y = mouse_y

    arrastre_hwnd = hwnd

    # ========================================================
    # ARRASTRE INTELIGENTE
    # ========================================================

    if arrastre_inteligente_activo():

        if snapshot_limpio_pendiente is None:

            print(
                "[CAPTURADOR] "
                "AI: no hay snapshot limpio. "
                "Tomá un snapshot antes de arrastrar."
            )

            arrastre_mouse_down = False
            arrastre_imagen_inicial = None

            return

        region_guardada = {

            "x_inicio":
                config.CAPTURADOR_OPCIONES_X_INICIO,

            "x_fin":
                config.CAPTURADOR_OPCIONES_X_FIN,

            "y_inicio":
                config.CAPTURADOR_OPCIONES_Y_INICIO,

            "y_fin":
                config.CAPTURADOR_OPCIONES_Y_FIN
        }

        arrastre_imagen_inicial = (
            recortar_opcion_desde_snapshot(
                snapshot_limpio_pendiente,
                x_rel,
                y_rel,
                region_guardada
            )
        )

        if arrastre_imagen_inicial is None:

            print(
                "[CAPTURADOR] "
                "AI: no se pudo extraer "
                "el objeto desde el snapshot limpio."
            )

            arrastre_mouse_down = False

            return

    else:

        arrastre_imagen_inicial = None

def registrar_mouse_up_capturador(hwnd,mouse_x,mouse_y):

    global arrastre_mouse_down
    global arrastre_inicio_tiempo
    global arrastre_inicio_x
    global arrastre_inicio_y
    global arrastre_hwnd
    global arrastre_imagen_inicial

    if not activo:
        return

    # ========================================================
    # EL DOWN EMPEZÓ FUERA DE LA REGIÓN
    # ========================================================

    if not arrastre_mouse_down:

        registrar_click_capturador(
            hwnd,
            mouse_x,
            mouse_y
        )

        return

    duracion = (
        time.perf_counter()
        - arrastre_inicio_tiempo
    )

    x_inicio = arrastre_inicio_x
    y_inicio = arrastre_inicio_y

    imagen_inicial = (
        arrastre_imagen_inicial
    )

    # ========================================================
    # LIMPIAR ESTADO TEMPORAL
    # ========================================================

    arrastre_mouse_down = False

    arrastre_inicio_tiempo = None

    arrastre_inicio_x = None
    arrastre_inicio_y = None

    arrastre_hwnd = None

    arrastre_imagen_inicial = None

    # ========================================================
    # AI DESACTIVADO
    #
    # El Capturador funciona normalmente.
    # Todo mouseDown + mouseUp dentro de su flujo
    # se interpreta como selección de opción.
    # ========================================================

    if not arrastre_inteligente_activo():

        registrar_opcion(
            hwnd,
            x_inicio,
            y_inicio
        )

        debug(
            f"[CAPTURADOR] "
            f"Clic normal "
            f"({duracion:.2f}s)"
        )

        return

    # ========================================================
    # AI ACTIVADO
    #
    # Un clic rápido sigue siendo una selección normal.
    # Un mouse mantenido y desplazado se procesa como
    # Arrastre Inteligente.
    # ========================================================

    if (
        duracion
        < ARRASTRE_UMBRAL_SEGUNDOS
    ):

        registrar_opcion(
            hwnd,
            x_inicio,
            y_inicio
        )

        debug(
            f"[CAPTURADOR] "
            f"Clic normal "
            f"({duracion:.2f}s)"
        )

        return

    # ========================================================
    # ARRASTRE INTELIGENTE
    # ========================================================

    if imagen_inicial is None:

        print(
            "[CAPTURADOR] "
            "AI: no existe imagen inicial "
            "del objeto arrastrado."
        )

        return

    registrar_arrastre_capturador(
        hwnd,
        x_inicio,
        y_inicio,
        mouse_x,
        mouse_y,
        imagen_inicial
    )

    debug(
        f"[CAPTURADOR] "
        f"Arrastre Inteligente detectado "
        f"({duracion:.2f}s)"
    )

def registrar_arrastre_capturador(hwnd,inicio_x,inicio_y,destino_x,destino_y,imagen_inicial):

    global movimientos_pendientes

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    destino_x_rel = (
        destino_x - izquierda
    )

    destino_y_rel = (
        destino_y - arriba
    )

    seccion = obtener_seccion_actual()

    # ========================================================
    # CREAR SECCIÓN
    # ========================================================

    if seccion is None:

        seccion = {

            "id": numero_seccion,

            "opciones": [],

            "regiones": [],

            "click_avanzar": None
        }

        secciones.append(
            seccion
        )

    # ========================================================
    # CREAR REGIÓN
    # ========================================================

    if not seccion["regiones"]:

        region = crear_region_actual()

        seccion["regiones"].append(
            region
        )

    elif movimientos_pendientes:

        region_anterior = (
            seccion["regiones"][-1]
        )

        region_anterior[
            "movimientos_despues"
        ] = movimientos_pendientes.copy()

        movimientos_pendientes.clear()

        region = crear_region_actual()

        seccion["regiones"].append(
            region
        )

    else:

        region = (
            seccion["regiones"][-1]
        )

    numero_region = len(
        seccion["regiones"]
    )

    numero_opcion = (
        len(seccion["opciones"]) + 1
    )

    # ========================================================
    # GUARDAR LA IMAGEN CAPTURADA EN MOUSE DOWN
    # ========================================================

    ruta = guardar_imagen_opcion(
        imagen_inicial,
        numero_seccion,
        numero_region,
        numero_opcion
    )

    if ruta is None:

        print(
            "No se pudo guardar "
            "la imagen inicial del arrastre."
        )

        return

    # ========================================================
    # GUARDAR ARRASTRE
    # ========================================================

    if arrastre_inteligente_activo():

        # ====================================================
        # ARRASTRE INTELIGENTE
        #
        # Guardamos el objeto visual de origen y el punto
        # exacto donde el usuario soltó el mouse.
        #
        # El origen NO se guarda como coordenada fija:
        # durante la reproducción se buscará visualmente
        # en su posición actual.
        # ====================================================

        seccion["opciones"].append({

            "id":
                numero_opcion,

            "tipo":
                "arrastre_inteligente",

            "imagen":
                ruta,

            "opcion_ancho":
                config.CAPTURADOR_OPCION_ANCHO,

            "opcion_alto":
                config.CAPTURADOR_OPCION_ALTO,

            "destino": {

                "x_rel":
                    destino_x_rel,

                "y_rel":
                    destino_y_rel
            }
        })

        print()

        print(
            f"Sección {numero_seccion} | "
            f"Región {numero_region} | "
            f"Arrastre Inteligente global "
            f"{numero_opcion}"
        )

        print(
            f"Destino guardado: "
            f"x={destino_x_rel} "
            f"y={destino_y_rel}"
        )

def procesar_click_capturador(hwnd,region,opcion,imagen_region,puntos_usados,opciones_completadas):

    id_opcion = opcion["id"]

    # Si ya fue seleccionada en otra región,
    # no hay que volver a clicar.
    if id_opcion in opciones_completadas:
        return False

    candidatos = buscar_opcion_en_region(
        imagen_region,
        opcion["imagen"]
    )

    if not candidatos:

        debug(
            f"Opción global {id_opcion}: "
            "sin candidatos válidos"
        )

        return False

    debug(
        f"Opción global {id_opcion}: "
        f"{len(candidatos)} candidatos"
    )

    candidato_elegido = None

    # ========================================================
    # ELEGIR CANDIDATO LIBRE
    # Solo se usa para CLIC NORMAL
    # ========================================================

    for candidato in candidatos:

        x = candidato["x"]
        y = candidato["y"]

        ocupado = False

        for punto in puntos_usados:

            distancia_x = abs(
                x - punto["x"]
            )

            distancia_y = abs(
                y - punto["y"]
            )

            if (
                distancia_x < 25
                and
                distancia_y < 25
            ):

                ocupado = True
                break

        if ocupado:
            continue

        candidato_elegido = candidato
        break

    if candidato_elegido is None:

        debug(
            "  No quedó ningún "
            "candidato libre."
        )

        return False

    debug(
        f"  Mejor libre: "
        f"{candidato_elegido['similitud']:.4f}"
    )

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    # ========================================================
    # RECONSTRUIR EL PUNTO REAL DEL CLIC
    # ========================================================

    x_click_region = (
        candidato_elegido["x"]
        - opcion.get(
            "offset_x",
            0
        )
    )

    y_click_region = (
        candidato_elegido["y"]
        - opcion.get(
            "offset_y",
            0
        )
    )

    x_abs = (
        izquierda
        + region["region_opciones"]["x_inicio"]
        + MARGEN_VISOR
        + x_click_region
    )

    y_abs = (
        arriba
        + region["region_opciones"]["y_inicio"]
        + MARGEN_VISOR
        + y_click_region
    )

    debug(
        f"  Clic opción {id_opcion}: "
        f"x={x_abs} y={y_abs}"
    )

    iniciar_evento_interno()

    try:

        pyautogui.moveTo(
            x_abs,
            y_abs,
            duration=TIEMPO_MOVER_CLICK
        )

        time.sleep(
            TIEMPO_ANTES_CLICK
        )

        pyautogui.click()

        time.sleep(
            TIEMPO_DESPUES_CLICK
        )

    finally:

        finalizar_evento_interno()

    opciones_completadas.add(
        id_opcion
    )

    puntos_usados.append({

        "x": candidato_elegido["x"],

        "y": candidato_elegido["y"]
    })

    return True

def procesar_arrastre_inteligente_capturador(hwnd,region,opcion,opciones_completadas):

    id_opcion = opcion["id"]

    # ========================================================
    # CAPTURAR REGIÓN ACTUAL
    # ========================================================

    imagen_region = capturar_region_opciones(
        hwnd,
        region["region_opciones"]
    )

    if imagen_region is None:

        print(
            f"Arrastre Inteligente {id_opcion}: "
            "no se pudo capturar la región."
        )

        return False

    # ========================================================
    # BUSCAR EL OBJETO EN SU POSICIÓN ACTUAL
    # ========================================================

    candidatos = buscar_opcion_en_region(
        imagen_region,
        opcion["imagen"]
    )

    if not candidatos:

        print(
            f"Arrastre Inteligente {id_opcion}: "
            "opción no encontrada."
        )

        return False

    candidato = candidatos[0]

    print(
        f"Arrastre Inteligente {id_opcion}: "
        f"similitud="
        f"{candidato['similitud']:.4f}"
    )

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(hwnd)
    )

    # ========================================================
    # ORIGEN ACTUAL
    #
    # El objeto puede estar en cualquier posición dentro
    # de la región. Siempre usamos su posición ACTUAL.
    # ========================================================

    origen_x = (
        izquierda
        + region["region_opciones"]["x_inicio"]
        + MARGEN_VISOR
        + candidato["x"]
    )

    origen_y = (
        arriba
        + region["region_opciones"]["y_inicio"]
        + MARGEN_VISOR
        + candidato["y"]
    )

    # ========================================================
    # DESTINO APRENDIDO
    #
    # X e Y son relativas a la ventana, por lo que funcionan
    # aunque la ventana esclava esté en otra posición.
    # ========================================================

    destino = opcion.get(
        "destino",
        {}
    )

    destino_x_rel = destino.get(
        "x_rel"
    )

    destino_y_rel = destino.get(
        "y_rel"
    )

    if (
        destino_x_rel is None
        or destino_y_rel is None
    ):

        print(
            f"Arrastre Inteligente {id_opcion}: "
            "no tiene destino X/Y guardado."
        )

        return False

    destino_x = (
        izquierda
        + destino_x_rel
    )

    destino_y = (
        arriba
        + destino_y_rel
    )

    print(
        f"  Origen encontrado: "
        f"x={origen_x} y={origen_y}"
    )

    print(
        f"  Destino aprendido: "
        f"x={destino_x} y={destino_y}"
    )

    # ========================================================
    # ARRASTRE FÍSICO REAL
    # ========================================================

    iniciar_evento_interno()

    try:

        # ----------------------------------------------------
        # IR AL OBJETO
        # ----------------------------------------------------

        pyautogui.moveTo(
            origen_x,
            origen_y,
            duration=TIEMPO_MOVER_CLICK
        )

        time.sleep(
            TIEMPO_ANTES_CLICK
        )

        # ----------------------------------------------------
        # AGARRAR
        # ----------------------------------------------------

        pyautogui.mouseDown()

        time.sleep(0.10)

        # ----------------------------------------------------
        # ARRASTRAR
        # ----------------------------------------------------

        pyautogui.moveTo(
            destino_x,
            destino_y,
            duration=0.35
        )

        time.sleep(0.10)

        # ----------------------------------------------------
        # SOLTAR
        # ----------------------------------------------------

        pyautogui.mouseUp()

        time.sleep(
            TIEMPO_DESPUES_CLICK
        )

    finally:

        # Seguridad:
        # si ocurre una excepción durante el arrastre,
        # nos aseguramos de no dejar el mouse presionado.

        pyautogui.mouseUp()

        finalizar_evento_interno()

    print(
        f"  Arrastre realizado: "
        f"({origen_x}, {origen_y}) "
        f"-> "
        f"({destino_x}, {destino_y})"
    )

    return True

def guardar_sesion_automata_capturador():

    if not automata_grabando():
        return

    if not secciones:

        print(
            "[AUTOMATA] Capturador sin datos. "
            "No se guardará evento."
        )

        return

    orden = siguiente_orden()

    carpeta_evento = crear_carpeta_evento(
        "capturador",
        orden
    )

    datos_guardados = []

    # ========================================================
    # RECORRER SECCIONES
    # ========================================================

    for seccion in secciones:

        nueva_seccion = {

            "id":
                seccion["id"],

            "opciones": [],

            "regiones": [],

            "click_avanzar":
                seccion.get(
                    "click_avanzar"
                )
        }

        # ====================================================
        # REGIONES
        # ====================================================

        for region in seccion.get(
            "regiones",
            []
        ):

            nueva_region = {

                "region_opciones":
                    region[
                        "region_opciones"
                    ],

                "click_foco":
                    region.get(
                        "click_foco"
                    ),

                "movimientos_despues":
                    region.get(
                        "movimientos_despues",
                        []
                    )
            }

            nueva_seccion[
                "regiones"
            ].append(
                nueva_region
            )

        # ====================================================
        # OPCIONES GLOBALES
        # ====================================================

        for opcion in seccion.get(
            "opciones",
            []
        ):

            ruta_original = opcion[
                "imagen"
            ]

            nombre_imagen = (
                os.path.basename(
                    ruta_original
                )
            )

            ruta_destino = os.path.join(
                carpeta_evento,
                nombre_imagen
            )

            # Copiar captura al evento del Autómata
            shutil.copy2(
                ruta_original,
                ruta_destino
            )

            nueva_opcion = {

                "id":
                    opcion["id"],

                "tipo":
                    opcion.get(
                        "tipo",
                        "click"
                    ),

                # En datos.json guardamos solamente
                # el nombre, no la ruta temporal vieja.
                "imagen":
                    nombre_imagen,

                "offset_x":
                    opcion.get(
                        "offset_x",
                        0
                    ),

                "offset_y":
                    opcion.get(
                        "offset_y",
                        0
                    ),

                "opcion_ancho":
                    opcion.get(
                        "opcion_ancho"
                    ),

                "opcion_alto":
                    opcion.get(
                        "opcion_alto"
                    )
            }

            # -----------------------------------------------
            # CLIC NORMAL
            # -----------------------------------------------

            if (
                opcion.get(
                    "tipo",
                    "click"
                )
                == "click"
            ):

                if "x_rel" in opcion:

                    nueva_opcion[
                        "x_rel"
                    ] = opcion[
                        "x_rel"
                    ]

                if "y_rel" in opcion:

                    nueva_opcion[
                        "y_rel"
                    ] = opcion[
                        "y_rel"
                    ]
            
            # -----------------------------------------------
            # ARRASTRE INTELIGENTE
            # -----------------------------------------------

            elif (
                opcion.get("tipo")
                == "arrastre_inteligente"
            ):

                nueva_opcion[
                    "destino"
                ] = opcion.get(
                    "destino"
                )

            nueva_seccion[
                "opciones"
            ].append(
                nueva_opcion
            )

        datos_guardados.append(
            nueva_seccion
        )

    # ========================================================
    # GUARDAR DATOS.JSON
    # ========================================================

    ruta_datos = os.path.join(
        carpeta_evento,
        "datos.json"
    )

    with open(
        ruta_datos,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos_guardados,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # REGISTRAR EVENTO EN TIMELINE
    # ========================================================

    registrar_evento({

        "tipo": CAPTURADOR,

        "carpeta":
            os.path.basename(
                carpeta_evento
            ),
        
        "modo_captura": obtener_modo()
    })

    debug(
        "[AUTOMATA] "
        "Capturador guardado:"
    )

    print(
        carpeta_evento
    )

def cargar_sesion_automata_capturador(carpeta_evento):

    ruta_datos = os.path.join(
        carpeta_evento,
        "datos.json"
    )

    if not os.path.exists(
        ruta_datos
    ):

        print(
            "[AUTOMATA] "
            "No existe datos.json del Capturador."
        )

        return None

    try:

        with open(
            ruta_datos,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

    except Exception as e:

        print(
            "[AUTOMATA] "
            "Error cargando Capturador:"
        )

        print(
            e
        )

        return None

    if not isinstance(
        datos,
        list
    ):

        print(
            "[AUTOMATA] "
            "datos.json del Capturador inválido."
        )

        return None

    # ========================================================
    # RECONSTRUIR RUTAS DE LAS IMÁGENES
    # ========================================================

    for seccion in datos:

        for opcion in seccion.get(
            "opciones",
            []
        ):

            nombre_imagen = opcion.get(
                "imagen"
            )

            if not nombre_imagen:
                continue

            ruta_imagen = os.path.join(
                carpeta_evento,
                nombre_imagen
            )

            if not os.path.exists(
                ruta_imagen
            ):

                print(
                    "[AUTOMATA] "
                    "No existe imagen del Capturador:"
                )

                print(
                    ruta_imagen
                )

                return None

            opcion["imagen"] = (
                ruta_imagen
            )

    return datos

def reproducir_capturador_automata(ventana,evento,carpeta_eventos):

    reproducir_bucle(
        "capturadorreplicando"
    )

    mostrar_capturador_replicando()

    global secciones

    # Guardamos el modo que estaba seleccionado
    # antes de reproducir este evento.
    modo_anterior = obtener_modo()

    try:

        nombre_carpeta = evento.get(
            "carpeta"
        )

        # ========================================================
        # RECUPERAR MODO DE CAPTURA DEL EVENTO
        # ========================================================

        modo_evento = evento.get(
            "modo_captura",
            MODO_NORMAL
        )

        establecer_modo(
            modo_evento
        )

        debug(
            "[CAPTURADOR] "
            f"Modo de imagen: "
            f"{modo_evento.upper()}"
        )

        # ========================================================
        # VALIDAR CARPETA
        # ========================================================

        if not nombre_carpeta:

            print(
                "[AUTOMATA] "
                "Evento Capturador sin carpeta."
            )

            return

        carpeta_evento = os.path.join(
            carpeta_eventos,
            nombre_carpeta
        )

        if not os.path.isdir(
            carpeta_evento
        ):

            print(
                "[AUTOMATA] "
                "No existe la carpeta del Capturador:"
            )

            print(
                carpeta_evento
            )

            return

        # ========================================================
        # CARGAR APRENDIZAJE
        # ========================================================

        secciones_cargadas = (
            cargar_sesion_automata_capturador(
                carpeta_evento
            )
        )

        if not secciones_cargadas:

            print(
                "[AUTOMATA] "
                "No se pudo cargar el Capturador."
            )

            return

        # ========================================================
        # CONSERVAR EL APRENDIZAJE ACTUAL
        # ========================================================

        secciones_anteriores = (
            secciones
        )

        try:

            # ====================================================
            # USAR EL APRENDIZAJE DE ESTA GRABACIÓN
            # ====================================================

            secciones = (
                secciones_cargadas
            )

            debug(
                "========== "
                "CAPTURADOR AUTÓMATA "
                "=========="
            )

            debug(
                f"Secciones cargadas: "
                f"{len(secciones)}"
            )

            debug(
                f"Ventana: "
                f"{ventana['proceso']}"
            )

            # ====================================================
            # REUTILIZAR MOTOR DEL CAPTURADOR
            # ====================================================

            probar_busqueda_esclava(
                ventana
            )

            debug(
                "========== "
                "CAPTURADOR TERMINADO "
                "=========="
            )

        finally:

            # Devolver las secciones que había
            # antes de reproducir este evento.
            secciones = (
                secciones_anteriores
            )

    finally:

        # ========================================================
        # RESTAURAR MODO DE CAPTURA ANTERIOR
        # ========================================================

        establecer_modo(
            modo_anterior
        )

        detener(
            "capturadorreplicando"
        )

        mostrar_capturador_desactivado()

    






