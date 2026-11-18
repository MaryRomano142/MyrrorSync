import queue
import threading
import time
import win32gui
import traceback
import win32clipboard

from automata.manager_automata import (
    automata_grabando,
    automata_reproduciendo,
    obtener_ventana_reproduccion
)

from automata.recorder import (
    registrar_evento
)

from automata.events import (
    CLICK_MANUAL,
    CLICK_ESPEJO,
    ESCRITURA,
    ARRASTRE_MANUAL,
    BLOCK_VERTICAL
)

from core.debug import debug

from block_vertical.manager_blockvertical import actualizar_block_vertical

from windows.window_actions import (
    obtener_punto_absoluto,
    obtener_posicion_mouse,
    restaurar_mouse,
    mover_mouse,
    click_izquierdo,
    arrastrar_mouse,
    traer_ventana_al_frente
)

import config

from config import (
    TIEMPO_ESPEJO_CLIC,
    PUNTO_FOCO_X,
    PUNTO_FOCO_Y,
    TIEMPO_FOCO,
    TIEMPO_ENTRE_FLECHAS,
    TIEMPO_RETORNO,
    TIEMPO_ESCRITURA_INICIO,
    TIEMPO_ESCRITURA_COPIAR,
    TIEMPO_ESCRITURA_CLIC,
    TIEMPO_ESCRITURA_PEGAR,
    TIEMPO_AUTOMATA_TECLA_PRESIONADA,
    TIEMPO_AUTOMATA_ENTRE_FLECHAS
)

from ui.ui_state import (
    mostrar_manual_activo,
    mostrar_manual_replicando,
    mostrar_manual_desactivado,
    mostrar_espejo_activo,
    mostrar_espejo_replicando,
    mostrar_espejo_desactivado,
    mostrar_escritura_activa,
    mostrar_escritura_replicando,
    mostrar_escritura_desactivada,
    mostrar_anticeros_activo,
    mostrar_anticeros_desactivado,
    mostrar_escritura_teclado_activa,
    mostrar_escritura_teclado_desactivada,
    mostrar_arrastre_activado,
    mostrar_arrastre_replicando,
    mostrar_arrastre_desactivado,
    mostrar_blockvert_clickeando,
    mostrar_blockvert_desactivado
)

from pynput.keyboard import (
    Controller,
    Key,
    KeyCode
)

from pynput.mouse import (
    Controller as MouseController
)

teclado = Controller()

mouse_control = MouseController()

from core.sound import (
    reproducir,
    reproducir_bucle,
    detener
)

from block_vertical.capture_state import (
    obtener_modo as obtener_modo_block
)

cola_eventos = queue.Queue()
manual_activo = False
espejo_activo = False
block_vertical_activo = False
escritura_activa = False
anticeros_activo = False
escritura_teclado_activa = False
texto_escritura_teclado = ""
x_escritura = None
y_escritura = None
arrastre_activo = False
arrastres = []
arrastre_en_progreso = False
x_inicio = None
y_inicio = None
x_fin = None
y_fin = None
evento_interno = False
maestra = None
esclavas = []
flecha_pendiente = None
cantidad_flechas = 0
ultimo_evento_flecha = 0
zoom_pendiente = None
cantidad_zoom = 0
ultimo_evento_zoom = 0
teclado = Controller()
#AUTÓMATA
#CLIC ESPEJO - rápido
TIEMPO_AUTOMATA_CLIC_ESPEJO = 0.05
TIEMPO_AUTOMATA_POST_CLICK_ESPEJO = 0.05
#CLIC MANUAL - más lento
TIEMPO_AUTOMATA_CLIC_MANUAL = 0.15
TIEMPO_AUTOMATA_POST_CLICK_MANUAL = 0.15
#FLECHAS
TIEMPO_AUTOMATA_FLECHA = 0.01
TIEMPO_AUTOMATA_POST_FLECHA = 0.03

def iniciar_evento_interno():

    global evento_interno

    evento_interno = True

def finalizar_evento_interno():

    global evento_interno

    evento_interno = False

def evento_interno_activo():

    return evento_interno

def establecer_maestra(ventana):
    global maestra
    maestra = ventana

def obtener_maestra():
    return maestra

def establecer_esclavas(lista):
    global esclavas
    esclavas = lista

def obtener_esclavas():
    return esclavas

def dar_foco_ventana(hwnd):

    debug("DAR FOCO")

    iniciar_evento_interno()

    try:

        x, y = obtener_punto_absoluto(
            hwnd,
            PUNTO_FOCO_X,
            PUNTO_FOCO_Y
        )

        mover_mouse(x, y)

        time.sleep(0.08)

        click_izquierdo()

        time.sleep(0.08)

    finally:

        finalizar_evento_interno()

#MANUAL

def actualizar_estado_manual():

    if (
        manual_activo
        and not espejo_activo
        and not escritura_activa
        and not arrastre_activo
    ):

        mostrar_manual_activo()

        reproducir("manual")

        debug("MANUAL ACTIVADO")

    else:

        mostrar_manual_desactivado()

        debug("MANUAL DESACTIVADO")

def activar_manual():

    global manual_activo

    manual_activo = True

    mostrar_manual_activo()

    debug("MANUAL ACTIVADO")

def desactivar_manual():

    global manual_activo

    manual_activo = False

    mostrar_manual_desactivado()

    debug("MANUAL DESACTIVADO")

def cambiar_estado_manual():

    if manual_activo:
        desactivar_manual()
    else:
        activar_manual()

def manual_esta_activo():
    return manual_activo

#ESPEJO - CLIC

def activar_espejo():

    global espejo_activo

    espejo_activo = True

    desactivar_manual()

    mostrar_espejo_activo()

    debug("ESPEJO ACTIVADO")

    reproducir("espejo")

    if maestra is not None:

        dar_foco_ventana(
            maestra["hwnd"]
        )

def desactivar_espejo(activar_manual_al_salir=True):

    global espejo_activo

    espejo_activo = False

    mostrar_espejo_desactivado()

    debug("ESPEJO DESACTIVADO")

    if activar_manual_al_salir:

        activar_manual()

        reproducir("manual")

    else:

        desactivar_manual()

def cambiar_estado_espejo():

    if espejo_activo:
        desactivar_espejo()
    else:
        activar_espejo()

def espejo_esta_activo():
    return espejo_activo

def procesar_click_espejo(evento):

    # ========================================================
    # AUTÓMATA - GUARDAR CLIC ESPEJO
    # ========================================================

    if (
        automata_grabando()
        and evento["maestra"]
    ):

        registrar_evento({

            "tipo": CLICK_ESPEJO,

            "boton": evento["boton"],

            "x_rel": evento["x_rel"],

            "y_rel": evento["y_rel"]
        })

    # ========================================================
    # FUNCIONAMIENTO NORMAL DEL ESPEJO
    # ========================================================

    time.sleep(0.10)

    posicion_original = obtener_posicion_mouse()

    mostrar_espejo_replicando()

    reproducir("espejoreplicando")

    for ventana in esclavas:

        debug("\nCLICK ESPEJO")

        debug(
            f"Destino: "
            f"{ventana['titulo']}"
        )

        x, y = obtener_punto_absoluto(

            ventana["hwnd"],

            evento["x_rel"],

            evento["y_rel"]
        )

        mover_mouse(
            x,
            y
        )

        time.sleep(
            TIEMPO_ESPEJO_CLIC
        )

        click_izquierdo()

        time.sleep(
            TIEMPO_ESPEJO_CLIC
        )

    dar_foco_ventana(
        maestra["hwnd"]
    )

    restaurar_mouse(
        posicion_original
    )

    mostrar_espejo_activo()

# ========================================================
# ESPEJO - SCROLL EXPERIMENTAL
# ========================================================

def replicar_scroll(delta):

    if not espejo_activo:
        return

    if maestra is None:
        return

    if not esclavas:
        return

    iniciar_evento_interno()

    posicion_original = obtener_posicion_mouse()

    try:

        debug(
            f"[SCROLL ESPEJO] Delta: {delta}"
        )

        for ventana in esclavas:

            dar_foco_ventana(
                ventana["hwnd"]
            )

            time.sleep(
                TIEMPO_FOCO
            )

            mouse_control.scroll(
                0,
                delta
            )

            time.sleep(0.05)

        dar_foco_ventana(
            maestra["hwnd"]
        )

        restaurar_mouse(
            posicion_original
        )

    finally:

        finalizar_evento_interno()

#ESPEJO - FLECHAS

def registrar_flecha(flecha, modo="espejo"):

    global flecha_pendiente
    global cantidad_flechas
    global ultimo_evento_flecha
    global modo_flecha

    if flecha_pendiente == flecha:

        cantidad_flechas += 1

    else:

        flecha_pendiente = flecha
        cantidad_flechas = 1
        modo_flecha = modo

    ultimo_evento_flecha = time.time()

def revisar_flechas():

    global flecha_pendiente
    global cantidad_flechas
    global ultimo_evento_flecha
    global modo_flecha

    if flecha_pendiente is None:
        return

    if time.time() - ultimo_evento_flecha < 0.70:
        return

    replicar_flechas(
        flecha_pendiente,
        cantidad_flechas,
        modo_flecha
    )

    flecha_pendiente = None
    cantidad_flechas = 0
    modo_flecha = None

def replicar_flechas(direccion, cantidad, modo="espejo"):

    iniciar_evento_interno()

    posicion_original = obtener_posicion_mouse()

    if modo == "espejo":

        mostrar_espejo_replicando()

        reproducir_bucle("espejoreplicando")

    for ventana in esclavas:

        dar_foco_ventana(
            ventana["hwnd"]
        )

        time.sleep(TIEMPO_FOCO)

        for _ in range(cantidad):

            if direccion == "down":

                teclado.press(Key.down)
                teclado.release(Key.down)

            elif direccion == "left":

                teclado.press(Key.left)
                teclado.release(Key.left)

            elif direccion == "right":

                teclado.press(Key.right)
                teclado.release(Key.right)

            else:

                teclado.press(Key.up)
                teclado.release(Key.up)

            time.sleep(
                TIEMPO_ENTRE_FLECHAS
            )

    debug(
        f"Replicando {cantidad} veces {direccion}"
    )

    if modo == "espejo":

        detener("espejoreplicando")

    time.sleep(TIEMPO_RETORNO)

    dar_foco_ventana(
        maestra["hwnd"]
    )

    restaurar_mouse(
        posicion_original
    )

    if modo == "espejo":

        mostrar_espejo_activo()

        reproducir("espejo")

    finalizar_evento_interno()

#ESPEJO - ZOOM

def registrar_zoom(zoom):

    global zoom_pendiente
    global cantidad_zoom
    global ultimo_evento_zoom

    if zoom_pendiente == zoom:

        cantidad_zoom += 1

    else:

        zoom_pendiente = zoom
        cantidad_zoom = 1

    ultimo_evento_zoom = time.time()

def revisar_zoom():

    global zoom_pendiente
    global cantidad_zoom
    global ultimo_evento_zoom

    if zoom_pendiente is None:
        return

    if time.time() - ultimo_evento_zoom < 0.10:
        return

    replicar_zoom(
        zoom_pendiente,
        cantidad_zoom
    )

    zoom_pendiente = None
    cantidad_zoom = 0

def replicar_zoom(tipo, cantidad):

    iniciar_evento_interno()

    posicion_original = obtener_posicion_mouse()

    mostrar_espejo_replicando()

    reproducir("espejoreplicando")

    for ventana in esclavas:

        dar_foco_ventana(ventana["hwnd"])

        time.sleep(TIEMPO_FOCO)

        teclado.press(Key.ctrl)

        for _ in range(cantidad):

            if tipo == "mas":

                teclado.press(KeyCode.from_vk(107))
                teclado.release(KeyCode.from_vk(107))

            else:

                teclado.press(KeyCode.from_vk(109))
                teclado.release(KeyCode.from_vk(109))

            time.sleep(0.05)

        teclado.release(Key.ctrl)

    detener("espejoreplicando")

    time.sleep(TIEMPO_RETORNO)

    dar_foco_ventana(maestra["hwnd"])

    restaurar_mouse(posicion_original)

    mostrar_espejo_activo()

    finalizar_evento_interno()

#REPRODUCIR CLIC
def reproducir_click_automata(ventana, evento):

    hwnd = ventana["hwnd"]

    x_rel = evento["x_rel"]
    y_rel = evento["y_rel"]

    tipo = evento.get(
        "tipo"
    )

    # ========================================================
    # VELOCIDAD SEGÚN TIPO DE CLIC
    # ========================================================

    if tipo == CLICK_MANUAL:

        mostrar_manual_replicando()

        reproducir("manual")

        tiempo_clic = (
            TIEMPO_AUTOMATA_CLIC_MANUAL
        )

        tiempo_post_click = (
            TIEMPO_AUTOMATA_POST_CLICK_MANUAL
        )

    else:

        tiempo_clic = (
            TIEMPO_AUTOMATA_CLIC_ESPEJO
        )

        tiempo_post_click = (
            TIEMPO_AUTOMATA_POST_CLICK_ESPEJO
        )

    x, y = obtener_punto_absoluto(
        hwnd,
        x_rel,
        y_rel
    )

    iniciar_evento_interno()

    try:

        mover_mouse(
            x,
            y
        )

        time.sleep(
            tiempo_clic
        )

        click_izquierdo()

        time.sleep(
            tiempo_post_click
        )

    finally:

        mostrar_manual_desactivado()

        finalizar_evento_interno()

#REPRODUCIR FLECHAS
def reproducir_flecha_automata(ventana,evento):

    direccion = evento.get(
        "direccion"
    )

    cantidad = evento.get(
        "cantidad",
        1
    )

    iniciar_evento_interno()

    try:

        for _ in range(
            cantidad
        ):

            if direccion == "down":

                teclado.press(
                    Key.down
                )

                time.sleep(
                    TIEMPO_AUTOMATA_TECLA_PRESIONADA
                )

                teclado.release(
                    Key.down
                )

                time.sleep(
                    TIEMPO_AUTOMATA_ENTRE_FLECHAS
                )

            elif direccion == "up":

                teclado.press(
                    Key.up
                )

                time.sleep(
                    TIEMPO_AUTOMATA_TECLA_PRESIONADA
                )

                teclado.release(
                    Key.up
                )

                time.sleep(
                    TIEMPO_AUTOMATA_ENTRE_FLECHAS
                )

            elif direccion == "left":

                teclado.press(
                    Key.left
                )

                time.sleep(
                    TIEMPO_AUTOMATA_TECLA_PRESIONADA
                )

                teclado.release(
                    Key.left
                )

                time.sleep(
                    TIEMPO_AUTOMATA_ENTRE_FLECHAS
                )

            elif direccion == "right":

                teclado.press(
                    Key.right
                )

                time.sleep(
                    TIEMPO_AUTOMATA_TECLA_PRESIONADA
                )

                teclado.release(
                    Key.right
                )

                time.sleep(
                    TIEMPO_AUTOMATA_ENTRE_FLECHAS
                )

            time.sleep(
                TIEMPO_AUTOMATA_FLECHA
            )

        time.sleep(
            TIEMPO_AUTOMATA_POST_FLECHA
        )

    finally:

        finalizar_evento_interno()

#REPRODUCIR ZOOM
def reproducir_zoom_automata(ventana,evento):

    hwnd = ventana["hwnd"]

    direccion = evento.get(
        "direccion"
    )

    cantidad = evento.get(
        "cantidad",
        1
    )

    iniciar_evento_interno()

    try:

        teclado.press(
            Key.ctrl
        )

        try:

            for _ in range(
                cantidad
            ):

                if direccion == "mas":

                    tecla_zoom = (
                        KeyCode.from_vk(107)
                    )

                else:

                    tecla_zoom = (
                        KeyCode.from_vk(109)
                    )

                teclado.press(
                    tecla_zoom
                )

                teclado.release(
                    tecla_zoom
                )

                time.sleep(
                    0.05
                )

        finally:

            teclado.release(
                Key.ctrl
            )

    finally:

        finalizar_evento_interno()

#REPRODUCIR SCROLL
def reproducir_scroll_automata(ventana, evento):

    delta = evento.get(
        "delta",
        0
    )

    if delta == 0:
        return

    direccion = (
        1
        if delta > 0
        else -1
    )

    cantidad = abs(
        int(delta)
    )

    iniciar_evento_interno()

    try:

        for _ in range(cantidad):

            mouse_control.scroll(
                0,
                direccion
            )

            time.sleep(0.02)

    finally:

        finalizar_evento_interno()

#BLOCK VERTICAL
def activar_block_vertical():

    global block_vertical_activo

    block_vertical_activo = True

    print("BLOCK VERTICAL ACTIVADO")

    desactivar_espejo()
    desactivar_manual()

    posicion_original = (
        obtener_posicion_mouse()
    )

    mostrar_blockvert_clickeando()

    # ========================================================
    # GUARDAR CALIBRACIÓN UTILIZADA
    # ========================================================

    calibracion_usada = {

        "x_inicio":
            config.BLOCK_VERTICAL_X_INICIO,

        "x_fin":
            config.BLOCK_VERTICAL_X_FIN,

        "y_inicio":
            config.BLOCK_VERTICAL_Y_INICIO,

        "y_fin":
            config.BLOCK_VERTICAL_Y_FIN
    }

    # ========================================================
    # DURANTE REPRODUCCIÓN
    #
    # Block Vertical actúa SOLO sobre la esclava activa.
    # ========================================================

    if automata_reproduciendo():

        esclava_activa = (
            obtener_ventana_reproduccion()
        )

        if esclava_activa is None:

            print(
                "[BLOCK VERTICAL] "
                "No hay una esclava activa."
            )

            desactivar_block_vertical()

            restaurar_mouse(
                posicion_original
            )

            return

        print(
            "[BLOCK VERTICAL] "
            f"Uso manual sobre esclava: "
            f"{esclava_activa['proceso']}"
        )

        actualizar_block_vertical(
            None,
            [esclava_activa]
        )

        desactivar_block_vertical()

        dar_foco_ventana(
            esclava_activa["hwnd"]
        )

        restaurar_mouse(
            posicion_original
        )

        return

    # ========================================================
    # USO NORMAL / GRABACIÓN
    #
    # Conservamos exactamente el funcionamiento anterior:
    # maestra + esclavas.
    # ========================================================

    if maestra is None:

        desactivar_block_vertical()

        restaurar_mouse(
            posicion_original
        )

        return

    actualizar_block_vertical(
        maestra,
        esclavas
    )

    # ========================================================
    # AUTÓMATA
    # Registrar solamente durante grabación.
    # ========================================================

    if automata_grabando():

        registrar_evento({

            "tipo":
                BLOCK_VERTICAL,

            "calibracion":
                calibracion_usada
        })

    desactivar_block_vertical()

    dar_foco_ventana(
        maestra["hwnd"]
    )

    restaurar_mouse(
        posicion_original
    )

def desactivar_block_vertical():

    global block_vertical_activo

    block_vertical_activo = False

    print("BLOCK VERTICAL DESACTIVADO")

    mostrar_blockvert_desactivado()

    # Durante reproducción el Espejo
    # debe permanecer apagado.
    if not automata_reproduciendo():

        activar_espejo()

def cambiar_estado_block_vertical():

    if block_vertical_esta_activo():

        desactivar_block_vertical()

    else:

        activar_block_vertical()

def block_vertical_esta_activo():

    return block_vertical_activo

#ESCRITURA
def anticeros_esta_activo():

    return anticeros_activo

def escritura_teclado_esta_activa():

    return escritura_teclado_activa

def registrar_tecla_escritura_teclado(key,shift_presionado=False,caps_lock_activo=False):

    global texto_escritura_teclado

    if not escritura_teclado_activa:
        return

    if not escritura_activa:
        return

    if key == Key.backspace:

        texto_escritura_teclado = (
            texto_escritura_teclado[:-1]
        )

        return

    if key == Key.space:

        texto_escritura_teclado += " "

        return

    try:

        caracter = key.char

    except AttributeError:

        return

    if caracter is None:
        return

    if caracter.isalpha():

        usar_mayuscula = (
            shift_presionado
            != caps_lock_activo
        )

        if usar_mayuscula:

            caracter = caracter.upper()

        else:

            caracter = caracter.lower()

    texto_escritura_teclado += caracter

def limpiar_texto_escritura_teclado():

    global texto_escritura_teclado

    texto_escritura_teclado = ""

def obtener_texto_escritura_teclado():

    return texto_escritura_teclado

def cambiar_estado_escritura_teclado():

    global escritura_teclado_activa
    global anticeros_activo

    escritura_teclado_activa = (
        not escritura_teclado_activa
    )

    if escritura_teclado_activa:

        anticeros_activo = False

        mostrar_anticeros_desactivado()
        mostrar_escritura_teclado_activa()

        print(
            "[ESCRITURA] "
            "TECLADO ACTIVADO"
        )

    else:

        mostrar_escritura_teclado_desactivada()

        print(
            "[ESCRITURA] "
            "TECLADO DESACTIVADO"
        )

def cambiar_estado_anticeros():

    global anticeros_activo
    global escritura_teclado_activa

    anticeros_activo = not anticeros_activo

    if anticeros_activo:

        escritura_teclado_activa = False
        mostrar_escritura_teclado_desactivada()

        mostrar_anticeros_activo()

        print(
            "[ESCRITURA] "
            "ANTICEROS ACTIVADO"
        )

    else:

        mostrar_anticeros_desactivado()

        print(
            "[ESCRITURA] "
            "ANTICEROS DESACTIVADO"
        )

def activar_escritura():

    global escritura_activa
    global texto_escritura_teclado

    escritura_activa = True

    if escritura_teclado_activa:

        texto_escritura_teclado = ""

    desactivar_espejo(
        activar_manual_al_salir=False
    )

    mostrar_escritura_activa()

    debug("ESCRITURA ACTIVADO")

    reproducir("escritura")

def desactivar_escritura():

    global escritura_activa

    escritura_activa = False

    mostrar_escritura_desactivada()

    debug("ESCRITURA DESACTIVADO")

    activar_espejo()

def escritura_esta_activa():

    return escritura_activa

def cambiar_estado_escritura():

    if escritura_activa:

        finalizar_modo_escritura()

    else:

        activar_escritura()

def guardar_posicion_escritura(x, y):

    global x_escritura
    global y_escritura

    x_escritura = x
    y_escritura = y

    debug(f"Posición guardada: ({x}, {y})")

def finalizar_modo_escritura():

    time.sleep(TIEMPO_ESCRITURA_INICIO)

    global x_escritura
    global y_escritura
    global texto_escritura_teclado

    if x_escritura is None or y_escritura is None:

        print("No se seleccionó ningún cuadro de texto.")

        desactivar_escritura()

        return

    # ============================================================
    # OBTENER TEXTO SEGÚN MODO
    # ============================================================

    if escritura_teclado_activa:

        texto_copiado = (
            texto_escritura_teclado
        )

        debug(
            "[ESCRITURA TECLADO] "
            f"Texto capturado: "
            f"{texto_copiado!r}"
        )

    else:

        teclado.press(
            Key.ctrl
        )

        teclado.press(
            "a"
        )

        teclado.release(
            "a"
        )

        teclado.release(
            Key.ctrl
        )

        time.sleep(
            TIEMPO_ESCRITURA_INICIO
        )

        teclado.press(
            Key.ctrl
        )

        teclado.press(
            "c"
        )

        teclado.release(
            "c"
        )

        teclado.release(
            Key.ctrl
        )

        time.sleep(
            TIEMPO_ESCRITURA_COPIAR
        )

        texto_copiado = (
            obtener_texto_portapapeles()
        )

    # ============================================================
    # AUTÓMATA - GUARDAR ESCRITURA
    # ============================================================

    if automata_grabando():

        if texto_copiado is not None:

            registrar_evento({

                "tipo": ESCRITURA,

                "texto": texto_copiado,

                "x_rel": x_escritura,

                "y_rel": y_escritura,

                "modo_escritura": (
                    "teclado"
                    if escritura_teclado_activa
                    else (
                        "anticeros"
                        if anticeros_activo
                        else "normal"
                    )
                )
            })

    iniciar_evento_interno()

    posicion_original = obtener_posicion_mouse()

    mostrar_escritura_replicando()

    reproducir_bucle("escriturareplicando")

    for ventana in esclavas:

        x, y = obtener_punto_absoluto(
            ventana["hwnd"],
            x_escritura,
            y_escritura
        )

        mover_mouse(x, y)

        time.sleep(TIEMPO_ESCRITURA_CLIC)

        click_izquierdo()

        time.sleep(
            TIEMPO_ESCRITURA_PEGAR
        )

        if escritura_teclado_activa:

            if texto_copiado  is not None:

                escribir_texto_teclado(
                    texto_copiado
                )

        else:

            if anticeros_activo:

                teclado.press(
                    Key.ctrl
                )

                teclado.press(
                    "a"
                )

                teclado.release(
                    "a"
                )

                teclado.release(
                    Key.ctrl
                )

                time.sleep(
                    TIEMPO_ESCRITURA_PEGAR
                )

            teclado.press(
                Key.ctrl
            )

            teclado.press(
                "v"
            )

            teclado.release(
                "v"
            )

            teclado.release(
                Key.ctrl
            )

            time.sleep(
                TIEMPO_ESCRITURA_PEGAR
            )
    
    debug("texto copiado")
    
    detener("escriturareplicando")
    
    dar_foco_ventana(maestra["hwnd"])

    finalizar_evento_interno()

    desactivar_escritura()

    x_escritura = None
    y_escritura = None

def obtener_texto_portapapeles():

    try:

        win32clipboard.OpenClipboard()

        texto = win32clipboard.GetClipboardData(
            win32clipboard.CF_UNICODETEXT
        )

        win32clipboard.CloseClipboard()

        return texto

    except Exception as e:

        try:
            win32clipboard.CloseClipboard()
        except:
            pass

        print(
            f"No se pudo leer el portapapeles: {e}"
        )

        return None

def escribir_texto_teclado(texto):

    for caracter in texto:

        teclado.press(
            caracter
        )

        time.sleep(0.02)

        teclado.release(
            caracter
        )

        time.sleep(0.02)

#REPRODUCIR ESCRITURA
def reproducir_escritura_automata(ventana,evento):

    mostrar_escritura_replicando()

    reproducir("escriturareplicando")

    hwnd = ventana["hwnd"]

    texto = evento.get(
        "texto"
    )

    modo_escritura = evento.get(
        "modo_escritura",
        "normal"
    )

    x_rel = evento.get(
        "x_rel"
    )

    y_rel = evento.get(
        "y_rel"
    )

    if (
        texto is None
        or x_rel is None
        or y_rel is None
    ):

        print(
            "[AUTOMATA] "
            "Evento de escritura inválido."
        )

        return

    # ========================================================
    # RECONSTRUIR POSICIÓN EN LA ESCLAVA
    # ========================================================

    x, y = obtener_punto_absoluto(
        hwnd,
        x_rel,
        y_rel
    )

    iniciar_evento_interno()

    try:

        mover_mouse(
            x,
            y
        )

        time.sleep(
            TIEMPO_ESCRITURA_CLIC
        )

        click_izquierdo()

        time.sleep(
            TIEMPO_ESCRITURA_PEGAR
        )

        # ====================================================
        # MODO ANTICEROS
        #
        # Normal:
        #     pega directamente.
        #
        # Anticeros:
        #     selecciona el contenido existente antes de pegar.
        # ====================================================

        if modo_escritura == "anticeros":

            teclado.press(
                Key.ctrl
            )

            teclado.press(
                "a"
            )

            teclado.release(
                "a"
            )

            teclado.release(
                Key.ctrl
            )

            time.sleep(
                TIEMPO_ESCRITURA_PEGAR
            )

        # ====================================================
        # INTRODUCIR TEXTO
        # ====================================================

        if modo_escritura == "teclado":

            escribir_texto_teclado(
                texto
            )

        else:

            # ================================================
            # NORMAL / ANTICEROS
            # ================================================

            win32clipboard.OpenClipboard()

            try:

                win32clipboard.EmptyClipboard()

                win32clipboard.SetClipboardText(
                    texto,
                    win32clipboard.CF_UNICODETEXT
                )

            finally:

                win32clipboard.CloseClipboard()

            teclado.press(
                Key.ctrl
            )

            teclado.press(
                "v"
            )

            teclado.release(
                "v"
            )

            teclado.release(
                Key.ctrl
            )

        time.sleep(
            TIEMPO_ESCRITURA_PEGAR
        )

        debug(
            "[AUTOMATA] "
            "Escritura reproducida."
        )

    finally:

        mostrar_escritura_desactivada()

        finalizar_evento_interno()

#ARRASTRE
def activar_arrastre():

    global arrastre_activo

    arrastre_activo = True

    desactivar_espejo(
        activar_manual_al_salir=False
    )

    mostrar_arrastre_activado()

    debug("ARRASTRE ACTIVADO")

    reproducir("arrastre")

def desactivar_arrastre():

    global arrastre_activo

    arrastre_activo = False

    debug("ARRASTRE DESACTIVADO")

    replicar_arrastres()

    mostrar_arrastre_desactivado()

    detener("arrastrereplicando")

    activar_espejo()

def replicar_arrastres():

    mostrar_arrastre_replicando()

    reproducir_bucle("arrastrereplicando")

    global arrastres

    if not arrastres:

        print("No hay arrastres para replicar.")

        return

    debug("\nReplicando arrastre")

    for ventana in obtener_esclavas():

        debug("\nDestino:", ventana["titulo"])

        for arrastre in arrastres:

            replicar_arrastre(arrastre, ventana)
    
    maestra = obtener_maestra()

    if maestra:

        dar_foco_ventana(maestra["hwnd"])

    arrastres.clear()

    detener("arrastrereplicando")

def replicar_arrastre(arrastre, ventana):

    realizar_arrastre(

        ventana["hwnd"],

        arrastre["inicio"][0],
        arrastre["inicio"][1],

        arrastre["fin"][0],
        arrastre["fin"][1]

    )

def realizar_arrastre(hwnd, x1, y1, x2, y2):

    posicion_original = obtener_posicion_mouse()

    # dar_foco_ventana ya se protege internamente
    dar_foco_ventana(hwnd)

    time.sleep(TIEMPO_FOCO)

    x_inicio_abs, y_inicio_abs = obtener_punto_absoluto(
        hwnd,
        x1,
        y1
    )

    x_fin_abs, y_fin_abs = obtener_punto_absoluto(
        hwnd,
        x2,
        y2
    )

    # ========================================================
    # PROTEGER EL ARRASTRE ARTIFICIAL DEL LISTENER
    # ========================================================

    iniciar_evento_interno()

    try:

        arrastrar_mouse(
            x_inicio_abs,
            y_inicio_abs,
            x_fin_abs,
            y_fin_abs
        )

    finally:

        finalizar_evento_interno()

    restaurar_mouse(
        posicion_original
    )

def arrastre_esta_activo():

    return arrastre_activo

def cambiar_estado_arrastre():

    if arrastre_activo:

        desactivar_arrastre()

    else:

        activar_arrastre()

#REPRODUCIR ARRASTRE
def reproducir_arrastre_automata(ventana,evento):

    mostrar_arrastre_replicando()

    reproducir("arrastrereplicando")

    realizar_arrastre(

        ventana["hwnd"],

        evento["x_inicio"],
        evento["y_inicio"],

        evento["x_fin"],
        evento["y_fin"]
    )

    detener("arrastrereplicando")

    mostrar_arrastre_desactivado()

def guardar_inicio_arrastre(x, y):

    global arrastre_en_progreso
    global x_inicio
    global y_inicio

    if not arrastre_activo:
        return

    maestra = obtener_maestra()

    if maestra is None:
        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(
            maestra["hwnd"]
        )
    )

    arrastre_en_progreso = True

    x_inicio = x - izquierda
    y_inicio = y - arriba

    debug(
        f"Inicio arrastre relativo: "
        f"({x_inicio}, {y_inicio})"
    )

def guardar_fin_arrastre(x, y):

    global arrastre_en_progreso
    global x_fin
    global y_fin
    global arrastres

    if not arrastre_activo:
        return

    if not arrastre_en_progreso:
        return

    maestra = obtener_maestra()

    if maestra is None:
        return

    izquierda, arriba, _, _ = (
        win32gui.GetWindowRect(
            maestra["hwnd"]
        )
    )

    arrastre_en_progreso = False

    x_fin = x - izquierda
    y_fin = y - arriba

    # Evitar registrar un clic como si fuera arrastre
    dx = abs(
        x_fin - x_inicio
    )

    dy = abs(
        y_fin - y_inicio
    )

    if (
        dx < 10
        and dy < 10
    ):

        print(
            "Movimiento demasiado pequeño. "
            "No se registra como arrastre."
        )

        return

    arrastres.append({

        "inicio": (
            x_inicio,
            y_inicio
        ),

        "fin": (
            x_fin,
            y_fin
        )
    })

    debug(
        f"Fin arrastre relativo: "
        f"({x_fin}, {y_fin})"
    )

    debug(
        "Arrastres guardados:",
        len(arrastres)
    )

    # ========================================================
    # AUTÓMATA - REGISTRAR ARRASTRE
    # ========================================================

    if automata_grabando():

        registrar_evento({

            "tipo":
                ARRASTRE_MANUAL,

            "x_inicio":
                x_inicio,

            "y_inicio":
                y_inicio,

            "x_fin":
                x_fin,

            "y_fin":
                y_fin
        })

def procesar_evento(evento):

    debug("procesar_evento() fue llamado")

    debug("\n========================")

    for clave, valor in evento.items():
        debug(f"{clave}: {valor}")

    debug("========================")

    if evento["tipo"] != "click":
        return

    if not evento["maestra"]:
        return
    
    debug("Modo escritura:", escritura_esta_activa())
    
    if escritura_esta_activa():
        debug("Entró al modo escritura")
        guardar_posicion_escritura(
            evento["x_rel"],
            evento["y_rel"]
        )

        return
    
    if evento["tipo"] == "zoom":

        procesar_zoom(
            evento["zoom"]
        )

        return

    if espejo_activo:

        procesar_click_espejo(evento)

        return

def agregar_evento(evento):
    cola_eventos.put(evento)

def motor():

    debug("Motor de eventos iniciado")

    while True:

        try:

            evento = cola_eventos.get(
                timeout=0.05
            )

            debug(
                "Evento recibido:",
                evento["tipo"]
            )

            procesar_evento(
                evento
            )

            cola_eventos.task_done()

        except queue.Empty:

            pass

        revisar_flechas()
        revisar_zoom()

def iniciar_motor():

    debug(
        "Creando hilo del motor de eventos"
    )

    hilo = threading.Thread(
        target=motor,
        daemon=True
    )

    hilo.start()

    print(
        "Motor de eventos listo."
    )

    reproducir(
        "nuevo"
    )

def limpiar_sesion():

    global manual_activo
    global espejo_activo
    global escritura_activa
    global anticeros_activo
    global arrastre_activo
    global arrastres
    global flecha_pendiente
    global cantidad_flechas

    manual_activo = False
    espejo_activo = False
    escritura_activa = False
    anticeros_activo = False
    arrastre_activo = False

    arrastres.clear()
    flecha_pendiente = None
    cantidad_flechas = 0

    mostrar_manual_desactivado()
    mostrar_espejo_desactivado()
    mostrar_escritura_desactivada()
    mostrar_anticeros_desactivado()
    mostrar_arrastre_desactivado()

    debug("Mirror limpio.")
