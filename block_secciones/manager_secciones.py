import time
import win32gui
import pyautogui
import config
import threading
import os
import json
import shutil

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
    BLOCK_SECCIONES
)

from block_secciones.capture_secciones import (
    capturar_afirmacion,
    capturar_opcion,
    recortar_opcion_desde_snapshot,
    guardar_imagen_opcion,
    capturar_afirmacion_actual,
    capturar_region_opciones,
    capturar_region_opciones_guardada,
    MARGEN_VISOR
)

from block_secciones.detector_secciones import (
    buscar_seccion,
    buscar_opcion_en_region
)

from ui.ui_state import (
    mostrar_blocksecciones_activo,
    mostrar_blocksecciones_clickeando,
    mostrar_blocksecciones_desactivado
)

from core.mirror import (
    obtener_esclavas,
    desactivar_espejo,
    activar_espejo,
    iniciar_evento_interno,
    finalizar_evento_interno
)

from core.sound import (
    reproducir,
    reproducir_bucle,
    detener
)

from core.debug import debug

from windows.window_actions import (
    traer_ventana_al_frente
)

RUTA_CONFIG = "config.py"

# ESTADO DEL APRENDIZAJE
activo = False
numero_seccion = 1
esperando_opcion = True
secciones = []

# Snapshot virgen de la región marrón
# correspondiente a la sección actual.
# Las opciones seleccionadas se recortarán
# desde esta imagen y NO desde la pantalla
# en vivo, evitando hover y selección.
snapshot_limpio_seccion = None

MAX_OPCIONES_SECCION = 10 #Opciones por seccion

# INICIAR APRENDIZAJE
def iniciar_aprendizaje():

    global activo
    global numero_seccion
    global esperando_opcion
    global secciones

    activo = True

    desactivar_espejo(
        activar_manual_al_salir=False
    )
    mostrar_blocksecciones_activo()
    reproducir("secciones")

    numero_seccion = 1
    esperando_opcion = True
    secciones = []

    debug("========== BLOCK SECCIONES ==========")
    debug("Aprendizaje iniciado.")
    debug("Esperando selección de opción...")

# DETENER APRENDIZAJE
def detener_aprendizaje():

    global activo

    activo = False

    mostrar_blocksecciones_clickeando()

    debug("========== BLOCK SECCIONES ==========")
    debug("Aprendizaje terminado.")
    debug(
        f"Secciones aprendidas: {len(secciones)}"
    )

    # ========================================================
    # AUTÓMATA
    # ========================================================

    if automata_acepta_eventos():

        guardar_sesion_automata()

    # ========================================================
    # FUNCIONAMIENTO NORMAL
    # ========================================================

    hilo = threading.Thread(
        target=iniciar_reproduccion,
        daemon=True
    )

    hilo.start()

# CONSULTAR ESTADO
def aprendizaje_activo():

    return activo

def hacer_magenta_bs_mas_alto():

    config.BLOCK_SECCIONES_OPCION_ALTO += 5

def hacer_magenta_bs_menos_alto():

    config.BLOCK_SECCIONES_OPCION_ALTO = max(
        10,
        config.BLOCK_SECCIONES_OPCION_ALTO - 5
    )

def hacer_magenta_bs_menos_ancho(event=None):

    config.BLOCK_SECCIONES_OPCION_ANCHO = max(
        10,
        config.BLOCK_SECCIONES_OPCION_ANCHO - 5
    )

def hacer_magenta_bs_mas_ancho(event=None):

    config.BLOCK_SECCIONES_OPCION_ANCHO += 5

def capturar_snapshot_limpio_seccion(hwnd):

    global snapshot_limpio_seccion

    imagen = capturar_region_opciones(
        hwnd
    )

    if imagen is None:

        print(
            "[BLOCK SECCIONES] "
            "No se pudo capturar "
            "el snapshot limpio."
        )

        snapshot_limpio_seccion = None

        return False

    snapshot_limpio_seccion = (
        imagen.copy()
    )

    print(
        "[BLOCK SECCIONES] "
        "Snapshot guardado."
    )

    return True

# PRIMER CLIC
def registrar_opcion(hwnd, mouse_x, mouse_y):

    if not activo:
        return

    izquierda, arriba, _, _ = win32gui.GetWindowRect(hwnd)

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    # Buscar si ya existe el registro de la sección actual
    seccion = None

    for item in secciones:

        if item["id"] == numero_seccion:

            seccion = item
            break

    # Si todavía no existe, es la primera opción de esta sección
    if seccion is None:

        ruta_afirmacion = capturar_afirmacion(
            hwnd,
            numero_seccion
        )

        seccion = {
            "id": numero_seccion,

            "afirmacion": ruta_afirmacion,

            "region_afirmacion": {
                "x_inicio": config.BLOCK_SECCIONES_AFIRMACION_X_INICIO,
                "x_fin": config.BLOCK_SECCIONES_AFIRMACION_X_FIN,
                "y_inicio": config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO,
                "y_fin": config.BLOCK_SECCIONES_AFIRMACION_Y_FIN
            },

            "region_opciones": {
                "x_inicio": config.BLOCK_SECCIONES_OPCIONES_X_INICIO,
                "x_fin": config.BLOCK_SECCIONES_OPCIONES_X_FIN,
                "y_inicio": config.BLOCK_SECCIONES_OPCIONES_Y_INICIO,
                "y_fin": config.BLOCK_SECCIONES_OPCIONES_Y_FIN
            },

            "opcion_ancho": config.BLOCK_SECCIONES_OPCION_ANCHO,
            "opcion_alto": config.BLOCK_SECCIONES_OPCION_ALTO,

            "opciones": [],

            "click_avanzar": None
        }

        secciones.append(
            seccion
        )

    # Máximo 2 opciones
    if len(seccion["opciones"]) >= MAX_OPCIONES_SECCION:

        debug(
            f"Sección {numero_seccion}: "
            "máximo de 2 opciones alcanzado."
        )

        return

    numero_opcion = len(seccion["opciones"]) + 1

    # ========================================================
    # CAPTURAR OPCIÓN DESDE EL SNAPSHOT LIMPIO
    #
    # La pantalla en vivo puede tener:
    # - hover
    # - estado seleccionado
    #
    # Por eso la opción se recorta desde la fotografía
    # virgen tomada al guardar la calibración.
    # ========================================================

    region_guardada = (
        seccion[
            "region_opciones"
        ]
    )

    imagen_opcion = (
        recortar_opcion_desde_snapshot(
            snapshot_limpio_seccion,
            x_rel,
            y_rel,
            region_guardada
        )
    )

    if imagen_opcion is None:

        print(
            "[BLOCK SECCIONES] "
            "No se pudo extraer la opción "
            "desde el snapshot limpio."
        )

        return


    ruta_opcion = (
        guardar_imagen_opcion(
            imagen_opcion,
            numero_seccion,
            numero_opcion
        )
    )

    if ruta_opcion is None:
        return


    seccion["opciones"].append({

        "imagen": ruta_opcion,

        "x_rel": x_rel
    })

    debug(
        f"Sección {numero_seccion}: "
        f"opción {numero_opcion} registrada"
    )

    debug(
        f"X relativa: {x_rel}"
    )

# SEGUNDO CLIC
def registrar_avance(hwnd, mouse_x, mouse_y):

    global numero_seccion

    if not activo:
        return

    if not secciones:
        return

    izquierda, arriba, _, _ = win32gui.GetWindowRect(
        hwnd
    )

    # Coordenadas relativas a la ventana

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    seccion = secciones[-1]

    if seccion["id"] != numero_seccion:
        return

    if len(seccion["opciones"]) == 0:

        debug(
            f"Sección {numero_seccion}: "
            "no se registró ninguna opción."
        )

        return
    
    if seccion["click_avanzar"] is not None:
        return

    seccion["click_avanzar"] = {

        "x_rel": x_rel,

        "y_rel": y_rel

    }

    debug(
        f"Avance sección {numero_seccion}: "
        f"x={x_rel} y={y_rel}"
    )

    # Preparar siguiente sección

    numero_seccion += 1

    debug(
        f"Sección {numero_seccion}: "
        "esperando selección de opción..."
    )

# OBTENER DATOS APRENDIDOS
def obtener_secciones():

    return secciones

def registrar_click_seccion(hwnd, mouse_x, mouse_y):

    if not activo:
        return

    izquierda, arriba, _, _ = win32gui.GetWindowRect(
        hwnd
    )

    x_rel = mouse_x - izquierda
    y_rel = mouse_y - arriba

    dentro_region_opciones = (

        config.BLOCK_SECCIONES_OPCIONES_X_INICIO
        <= x_rel
        <= config.BLOCK_SECCIONES_OPCIONES_X_FIN

        and

        config.BLOCK_SECCIONES_OPCIONES_Y_INICIO
        <= y_rel
        <= config.BLOCK_SECCIONES_OPCIONES_Y_FIN
    )

    debug(
        f"[BLOCK SECCIONES] "
        f"x_rel={x_rel} "
        f"y_rel={y_rel} "
        f"dentro_opciones={dentro_region_opciones}"
    )

    # CLIC DENTRO DE LA REGIÓN AMARILLA = OPCIÓN
    if dentro_region_opciones:

        registrar_opcion(
            hwnd,
            mouse_x,
            mouse_y
        )

        return

    # CLIC FUERA = AVANZAR
    registrar_avance(
        hwnd,
        mouse_x,
        mouse_y
    )

def guardar_config_secciones():

    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas = []

    for linea in lineas:

        if linea.startswith("BLOCK_SECCIONES_AFIRMACION_X_INICIO"):

            nuevas.append(
                f"BLOCK_SECCIONES_AFIRMACION_X_INICIO = "
                f"{config.BLOCK_SECCIONES_AFIRMACION_X_INICIO}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_AFIRMACION_X_FIN"):

            nuevas.append(
                f"BLOCK_SECCIONES_AFIRMACION_X_FIN = "
                f"{config.BLOCK_SECCIONES_AFIRMACION_X_FIN}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_AFIRMACION_Y_INICIO"):

            nuevas.append(
                f"BLOCK_SECCIONES_AFIRMACION_Y_INICIO = "
                f"{config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_AFIRMACION_Y_FIN"):

            nuevas.append(
                f"BLOCK_SECCIONES_AFIRMACION_Y_FIN = "
                f"{config.BLOCK_SECCIONES_AFIRMACION_Y_FIN}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCIONES_X_INICIO"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCIONES_X_INICIO = "
                f"{config.BLOCK_SECCIONES_OPCIONES_X_INICIO}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCIONES_X_FIN"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCIONES_X_FIN = "
                f"{config.BLOCK_SECCIONES_OPCIONES_X_FIN}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCIONES_Y_INICIO"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCIONES_Y_INICIO = "
                f"{config.BLOCK_SECCIONES_OPCIONES_Y_INICIO}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCIONES_Y_FIN"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCIONES_Y_FIN = "
                f"{config.BLOCK_SECCIONES_OPCIONES_Y_FIN}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCION_ANCHO"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCION_ANCHO = "
                f"{config.BLOCK_SECCIONES_OPCION_ANCHO}\n"
            )

        elif linea.startswith("BLOCK_SECCIONES_OPCION_ALTO"):

            nuevas.append(
                f"BLOCK_SECCIONES_OPCION_ALTO = "
                f"{config.BLOCK_SECCIONES_OPCION_ALTO}\n"
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
        "Config Block Secciones actualizada."
    )

# REPRODUCCIÓN / IDENTIFICACIÓN
def procesar_esclava(ventana):

    hwnd = ventana["hwnd"]

    debug(
        f"Procesando esclava: "
        f"{ventana['proceso']}"
    )

    # Guardamos qué secciones ya fueron reproducidas
    secciones_reproducidas = set()

    # La esclava debe completar exactamente
    # la cantidad de secciones aprendidas en la maestra
    total_secciones = len(secciones)

    while len(secciones_reproducidas) < total_secciones:

        # ====================================================
        # IDENTIFICAR SECCIÓN
        # ====================================================

        secciones_pendientes = [
            seccion
            for seccion in secciones
            if seccion["id"] not in secciones_reproducidas
        ]

        seccion, similitud = buscar_seccion(
            hwnd,
            secciones_pendientes
        )

        if seccion is None:

            print(
                "No se pudo identificar la sección."
            )

            break

        id_seccion = seccion["id"]

        # ====================================================
        # EVITAR REPETIR UNA SECCIÓN
        # ====================================================

        if id_seccion in secciones_reproducidas:

            print(
                f"[BLOCK SECCIONES] "
                f"{ventana['proceso']} "
                f"→ Sección {id_seccion} "
                "ya fue reproducida."
            )

            print(
                "[BLOCK SECCIONES] "
                "Deteniendo para evitar repetición."
            )

            break

        debug(
            f"{ventana['proceso']} "
            f"→ sección {id_seccion}"
        )

        debug(
            f"Similitud: {similitud:.4f}"
        )

        debug(
            f"Opciones aprendidas: "
            f"{len(seccion['opciones'])}"
        )

        # ====================================================
        # CAPTURAR REGIÓN AMARILLA
        # ====================================================

        imagen_region = capturar_region_opciones_guardada(
            hwnd,
            seccion["region_opciones"]
        )

        if imagen_region is None:

            print(
                "No se pudo capturar "
                "la región de opciones."
            )

            break

        izquierda, arriba, _, _ = (
            win32gui.GetWindowRect(hwnd)
        )

        debug("Buscando opciones...")

        # ====================================================
        # BUSCAR Y CLICKEAR OPCIONES APRENDIDAS
        # ====================================================

        opciones_correctas = True

        for indice, opcion in enumerate(
            seccion["opciones"],
            1
        ):

            resultado = buscar_opcion_en_region(
                imagen_region,
                opcion["imagen"]
            )

            if resultado is None:

                print(
                    f"[BLOCK SECCIONES] "
                    f"{ventana['proceso']} "
                    f"→ Sección {id_seccion} "
                    f"→ Opción {indice} NO ENCONTRADA."
                )

                opciones_correctas = False
                break

            debug(
                f"  Opción {indice}: "
                f"x={resultado['x']} "
                f"y={resultado['y']} "
                f"similitud="
                f"{resultado['similitud']:.4f}"
            )

            x_abs = (
                izquierda
                + seccion["region_opciones"]["x_inicio"]
                + MARGEN_VISOR
                + resultado["x"]
            )

            y_abs = (
                arriba
                + seccion["region_opciones"]["y_inicio"]
                + MARGEN_VISOR
                + resultado["y"]
            )

            debug(
                f"  Clic opción {indice}: "
                f"x={x_abs} y={y_abs}"
            )

            iniciar_evento_interno()

            try:

                pyautogui.click(
                    x_abs,
                    y_abs
                )

                time.sleep(
                    0.20
                )

            finally:

                finalizar_evento_interno()

        # Si alguna opción no fue encontrada,
        # no avanzamos de sección.
        if not opciones_correctas:
            break

        # ====================================================
        # CLIC AVANZAR
        # ====================================================

        avance = seccion["click_avanzar"]

        if avance is None:

            print(
                f"Sección {id_seccion} "
                "no tiene clic de avance registrado."
            )

            break

        x_avance = (
            izquierda
            + avance["x_rel"]
        )

        y_avance = (
            arriba
            + avance["y_rel"]
        )

        debug(
            f"Clic avanzar: "
            f"x={x_avance} y={y_avance}"
        )

        iniciar_evento_interno()

        try:

            pyautogui.click(
                x_avance,
                y_avance
            )

            time.sleep(0.20)

        finally:

            finalizar_evento_interno()

        # ====================================================
        # MARCAR SECCIÓN COMO COMPLETADA
        # ====================================================

        secciones_reproducidas.add(
            id_seccion
        )

        debug(
            f"Secciones completadas: "
            f"{len(secciones_reproducidas)}/"
            f"{total_secciones}"
        )

        # ====================================================
        # ESPERAR CAMBIO DE SECCIÓN
        # ====================================================

        if len(secciones_reproducidas) < total_secciones:

            time.sleep(0.35)

    # ========================================================
    # FINAL
    # ========================================================

    if len(secciones_reproducidas) == total_secciones:

        debug(
            f"{ventana['proceso']}: "
            "todas las secciones fueron reproducidas."
        )

    else:

        debug(
            f"{ventana['proceso']}: "
            "reproducción detenida antes de completar "
            "todas las secciones."
        )

def iniciar_reproduccion():

    reproducir_bucle(
        "seccionesreplicando"
    )

    try:

        esclavas = obtener_esclavas()

        debug(
            "========== BLOCK SECCIONES =========="
        )

        debug(
            "Iniciando comparación en esclavas..."
        )

        if not esclavas:

            print(
                "No hay esclavas configuradas."
            )

            return

        if not secciones:

            print(
                "No hay secciones aprendidas."
            )

            return

        for ventana in esclavas:

            procesar_esclava(
                ventana
            )

        debug(
            "Comparación de esclavas terminada."
        )

    finally:

        detener(
            "seccionesreplicando"
        )

        mostrar_blocksecciones_desactivado()

        activar_espejo()

def guardar_sesion_automata():

    if not automata_grabando():
        return

    if not secciones:
        return

    orden = siguiente_orden()

    carpeta_evento = crear_carpeta_evento(
        "block_secciones",
        orden
    )

    # ========================================================
    # COPIAR CAPTURAS
    # ========================================================

    datos_guardados = []

    for seccion in secciones:

        nueva_seccion = {
            "id": seccion["id"],
            "region_afirmacion": seccion["region_afirmacion"],
            "region_opciones": seccion["region_opciones"],
            "opcion_ancho": seccion["opcion_ancho"],
            "opcion_alto": seccion["opcion_alto"],
            "opciones": [],
            "click_avanzar": seccion["click_avanzar"]
        }

        # ----------------------------------------------------
        # AFIRMACIÓN
        # ----------------------------------------------------

        ruta_afirmacion_original = seccion["afirmacion"]

        nombre_afirmacion = os.path.basename(
            ruta_afirmacion_original
        )

        ruta_afirmacion_destino = os.path.join(
            carpeta_evento,
            nombre_afirmacion
        )

        shutil.copy2(
            ruta_afirmacion_original,
            ruta_afirmacion_destino
        )

        nueva_seccion["afirmacion"] = nombre_afirmacion

        # ----------------------------------------------------
        # OPCIONES
        # ----------------------------------------------------

        for opcion in seccion["opciones"]:

            ruta_opcion_original = opcion["imagen"]

            nombre_opcion = os.path.basename(
                ruta_opcion_original
            )

            ruta_opcion_destino = os.path.join(
                carpeta_evento,
                nombre_opcion
            )

            shutil.copy2(
                ruta_opcion_original,
                ruta_opcion_destino
            )

            nueva_seccion["opciones"].append({

                "imagen": nombre_opcion,

                "x_rel": opcion["x_rel"]
            })

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
    ) as f:

        json.dump(
            datos_guardados,
            f,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # REGISTRAR EN TIMELINE
    # ========================================================

    ruta_relativa = os.path.relpath(
        carpeta_evento,
        os.path.dirname(
            os.path.join(
                carpeta_evento,
                ".."
            )
        )
    )

    registrar_evento({

        "tipo": BLOCK_SECCIONES,

        "carpeta": os.path.basename(
            carpeta_evento
        )
    })

    debug(
        "[AUTOMATA] Block Secciones guardado:"
    )

    print(
        carpeta_evento
    )

def cargar_sesion_automata(carpeta_evento):

    ruta_datos = os.path.join(
        carpeta_evento,
        "datos.json"
    )

    if not os.path.exists(
        ruta_datos
    ):

        print(
            "[AUTOMATA] "
            "No existe datos.json de Block Secciones."
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
            "Error cargando Block Secciones:"
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
            "datos.json de Block Secciones inválido."
        )

        return None

    # ========================================================
    # RECONSTRUIR RUTAS DE LAS IMÁGENES
    # ========================================================

    for seccion in datos:

        nombre_afirmacion = seccion.get(
            "afirmacion"
        )

        if nombre_afirmacion:

            seccion["afirmacion"] = os.path.join(
                carpeta_evento,
                nombre_afirmacion
            )

        for opcion in seccion.get(
            "opciones",
            []
        ):

            nombre_imagen = opcion.get(
                "imagen"
            )

            if nombre_imagen:

                opcion["imagen"] = os.path.join(
                    carpeta_evento,
                    nombre_imagen
                )

    return datos

def reproducir_block_secciones_automata(ventana,evento,carpeta_eventos):

    reproducir_bucle(
        "seccionesreplicando"
    )

    mostrar_blocksecciones_clickeando()

    try:

        global secciones

        nombre_carpeta = evento.get(
            "carpeta"
        )

        if not nombre_carpeta:

            print(
                "[AUTOMATA] "
                "Evento Block Secciones sin carpeta."
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
                "No existe la carpeta de Block Secciones:"
            )

            print(
                carpeta_evento
            )

            return

        secciones_cargadas = cargar_sesion_automata(
            carpeta_evento
        )

        if not secciones_cargadas:

            print(
                "[AUTOMATA] "
                "No se pudieron cargar las secciones."
            )

            return

        # Guardamos temporalmente el aprendizaje
        # cargado para reutilizar procesar_esclava().
        secciones_anteriores = secciones

        try:

            secciones = secciones_cargadas

            debug(
                "========== BLOCK SECCIONES AUTÓMATA =========="
            )

            debug(
                f"Secciones cargadas: "
                f"{len(secciones)}"
            )

            debug(
                f"Ventana: "
                f"{ventana['proceso']}"
            )

            procesar_esclava(
                ventana
            )

            debug(
                "========== BLOCK SECCIONES TERMINADO =========="
            )

        finally:

            secciones = secciones_anteriores

    finally:

        detener(
            "seccionesreplicando"
        )

        mostrar_blocksecciones_desactivado()

    

