import win32gui
import config
import threading
import time

from pynput import keyboard
from pynput import mouse
from windows.window_manager import obtener_rectangulo
from core.debug import debug

from core.mirror import (
    cambiar_estado_manual,
    cambiar_estado_espejo,
    cambiar_estado_escritura,
    cambiar_estado_arrastre,
    cambiar_estado_block_vertical,
    espejo_esta_activo,
    escritura_esta_activa,
    escritura_teclado_esta_activa,
    registrar_tecla_escritura_teclado,
    arrastre_esta_activo,
    guardar_inicio_arrastre,
    guardar_fin_arrastre,
    block_vertical_esta_activo,
    obtener_maestra,
    procesar_evento,
    agregar_evento,
    registrar_flecha,
    registrar_zoom,
    evento_interno_activo,
    activar_espejo,
    replicar_scroll
)

from core.sound import reproducir

from capturador.manager_capturador import (
    cambiar_estado_capturador,
    capturador_esta_activo,
    mover_offset_izquierda,
    mover_offset_derecha,
    hacer_magenta_mas_alto,
    hacer_magenta_menos_alto,
    hacer_magenta_mas_ancho,
    hacer_magenta_menos_ancho,
    registrar_click_capturador,
    registrar_flecha_capturador,
    registrar_mouse_down_capturador,
    registrar_mouse_up_capturador,
    mover_offset_arriba,
    mover_offset_abajo
)

from block_secciones.manager_secciones import (
    iniciar_aprendizaje,
    detener_aprendizaje,
    aprendizaje_activo,
    registrar_click_seccion,
    hacer_magenta_bs_mas_alto,
    hacer_magenta_bs_menos_alto,
    hacer_magenta_bs_mas_ancho,
    hacer_magenta_bs_menos_ancho
)

from automata.manager_automata import (
    cambiar_estado_grabacion,
    cambiar_estado_pausa_automata,
    cambiar_estado_cronometro_video,
    cambiar_estado_intervencion_usuario,
    automata_grabando,
    automata_reproduciendo,
    automata_acepta_eventos,
    borrar_ultimo_evento_grabacion,
    detener_reproduccion
)

from automata.events import (
    CLICK_MANUAL,
    CLICK_ESPEJO,
    FLECHA_ESPEJO,
    ZOOM_ESPEJO,
    SCROLL_ESPEJO,
    ARRASTRE_MANUAL,
    INSPECTOR_AVANCE
)

from automata.asignaciones import (
    hay_asignaciones
)

from automata.player import (
    reproducir_asignaciones
)

from automata.recorder import (
    registrar_evento
)

keyboard_listener = None
mouse_listener = None
ctrl_presionado = False
shift_presionado = False
caps_lock_activo = False
scroll_acumulado = 0
ultimo_scroll = 0
scroll_timer = None

TIEMPO_AGRUPAR_SCROLL = 0.70 #Tiempo entre cada scroll o grupo de scrolls que se hace

def hay_modo_activo():

    return (
        espejo_esta_activo()
        or capturador_esta_activo()
        or block_vertical_esta_activo()
        or escritura_esta_activa()
        or aprendizaje_activo()
        or automata_grabando()
    )

def tecla_realizada_en_maestra():

    maestra = obtener_maestra()

    if maestra is None:
        return False

    ventana_activa = win32gui.GetForegroundWindow()

    return ventana_activa == maestra["hwnd"]

def ejecutar_scroll_acumulado():

    global scroll_acumulado
    global scroll_timer

    delta = scroll_acumulado

    scroll_acumulado = 0
    scroll_timer = None

    if delta == 0:
        return

    # Replicar normalmente en las esclavas.
    replicar_scroll(
        delta
    )

def on_scroll(x, y, dx, dy):

    # Ignorar scroll generado por MirrorSync
    if evento_interno_activo():
        return

    # Esta primera prueba pertenece solamente al Espejo
    if not espejo_esta_activo():
        return

    maestra = obtener_maestra()

    if maestra is None:
        return

    # Identificar la ventana bajo el mouse
    hwnd = win32gui.WindowFromPoint(
        (x, y)
    )

    raiz = hwnd

    while True:

        padre = win32gui.GetParent(
            raiz
        )

        if padre == 0:
            break

        raiz = padre

    # Solamente replicar si la rueda se usó
    # físicamente sobre la ventana maestra.
    if raiz != maestra["hwnd"]:
        return
    
    if dy != 0 and automata_grabando():

        direccion = (
            1
            if dy > 0
            else -1
        )

        cantidad = abs(
            int(dy)
        )

        for _ in range(cantidad):

            registrar_evento({
                "tipo": SCROLL_ESPEJO,
                "delta": direccion
            })

    debug(
        f"[SCROLL ESPEJO] "
        f"dx={dx} dy={dy}"
    )

    global scroll_acumulado
    global ultimo_scroll
    global scroll_timer

    scroll_acumulado += dy
    ultimo_scroll = time.time()

    if scroll_timer is not None:

        scroll_timer.cancel()

    scroll_timer = threading.Timer(
        TIEMPO_AGRUPAR_SCROLL,
        ejecutar_scroll_acumulado
    )

    scroll_timer.daemon = True
    scroll_timer.start()

def on_click(x, y, button, pressed):

    if evento_interno_activo():
        return

    if arrastre_esta_activo():

        if pressed:

            guardar_inicio_arrastre(x, y)

        else:

            guardar_fin_arrastre(x, y)

        return

    # ========================================================
    # COMPROBAR MODOS
    # ========================================================

    if not hay_modo_activo():
        return

    maestra = obtener_maestra()

    if maestra is None:
        return

    # ========================================================
    # IDENTIFICAR VENTANA DONDE ESTÁ EL MOUSE
    # ========================================================

    hwnd = win32gui.WindowFromPoint(
        (x, y)
    )

    raiz = hwnd

    while True:

        padre = win32gui.GetParent(
            raiz
        )

        if padre == 0:
            break

        raiz = padre

    es_maestra = (
        raiz == maestra["hwnd"]
    )

    # ========================================================
    # CAPTURADOR
    #
    # IMPORTANTE:
    # Tiene que ejecutarse ANTES de:
    #
    # if not pressed:
    #     return
    #
    # porque necesitamos mouse DOWN y mouse UP.
    # ========================================================

    if (
        capturador_esta_activo()
        and es_maestra
    ):

        if pressed:

            registrar_mouse_down_capturador(
                maestra["hwnd"],
                x,
                y
            )

        else:

            registrar_mouse_up_capturador(
                maestra["hwnd"],
                x,
                y
            )

        return

    # ========================================================
    # RESTO DE MODOS
    # Solo trabajan con mouse DOWN
    # ========================================================

    if not pressed:
        return

    # ========================================================
    # BLOCK SECCIONES
    # ========================================================

    if (
        aprendizaje_activo()
        and es_maestra
    ):

        registrar_click_seccion(
            maestra["hwnd"],
            x,
            y
        )

        return

    izquierda, arriba, derecha, abajo = (
        obtener_rectangulo(
            maestra["hwnd"]
        )
    )

    # ========================================================
    # AUTÓMATA - MANUAL
    # ========================================================

    if (
        automata_grabando()):

        modo_especial_activo = (

            espejo_esta_activo()
            or block_vertical_esta_activo()
            or escritura_esta_activa()
            or aprendizaje_activo()
            or capturador_esta_activo()
        )

        if not modo_especial_activo:

            registrar_evento({

                "tipo": CLICK_MANUAL,

                "boton": str(button),

                "x_rel":
                    x - izquierda,

                "y_rel":
                    y - arriba
            })

    # ========================================================
    # EVENTO NORMAL DE MIRROR
    # ========================================================

    evento = {

        "tipo": "click",

        "boton": str(button),

        "x_abs": x,
        "y_abs": y,

        "x_rel":
            x - izquierda,

        "y_rel":
            y - arriba,

        "maestra":
            es_maestra
    }

    agregar_evento(
        evento
    )

def on_press(key):

    global ctrl_presionado
    global shift_presionado
    global caps_lock_activo

    if evento_interno_activo():
        return
    
    if key in (
        keyboard.Key.shift,
        keyboard.Key.shift_l,
        keyboard.Key.shift_r
    ):

        shift_presionado = True

        return

    if key == keyboard.Key.caps_lock:

        caps_lock_activo = (
            not caps_lock_activo
        )

        return
    
    #Teclas asigandas a cada modo o servicio del automata
    
    if key == keyboard.Key.esc:

        if automata_acepta_eventos():

            registrar_evento({

                "tipo":
                    INSPECTOR_AVANCE,

                "segundos":
                    2 #tiempo entre pantallas
            })

            reproducir("inspectordeavance")

            debug(
                "[AUTOMATA] "
                "Inspector de avance registrado."
            )

        return

    try:

        if key.char == "|":

            cambiar_estado_block_vertical()

            return
    
    except AttributeError:
        pass

    if key == keyboard.Key.tab:

        if aprendizaje_activo():

            detener_aprendizaje()

        else:

            iniciar_aprendizaje()

        return

    if key == keyboard.Key.f1:
        cambiar_estado_espejo()
        return
    
    if key == keyboard.Key.f2:
        cambiar_estado_escritura()
        return
    
    if (
        escritura_esta_activa()
        and escritura_teclado_esta_activa()
        and tecla_realizada_en_maestra()
    ):

        registrar_tecla_escritura_teclado(
            key,
            shift_presionado,
            caps_lock_activo
        )

        return
    
    if key == keyboard.Key.f3:
        cambiar_estado_arrastre()
        return
    
    if key == keyboard.Key.f4:
        cambiar_estado_capturador()
        return
    
    if key == keyboard.Key.f9:

        # ========================================================
        # SI ESTÁ GRABANDO:
        # F9 DETIENE GRABACIÓN
        # ========================================================

        if automata_grabando():

            cambiar_estado_grabacion()

            return

        # ========================================================
        # SI ESTÁ REPRODUCIENDO:
        # F9 DETIENE REPRODUCCIÓN
        # ========================================================

        if automata_reproduciendo():

            detener_reproduccion()

            return

        # ========================================================
        # SI HAY ASIGNACIONES:
        # F9 COMIENZA REPRODUCCIÓN
        # ========================================================

        if hay_asignaciones():

            reproducir_asignaciones()

            return

        # ========================================================
        # SIN ASIGNACIONES:
        # F9 COMIENZA GRABACIÓN
        # ========================================================

        activar_espejo()

        cambiar_estado_grabacion()

        return
    
    if key == keyboard.Key.f5:
        cambiar_estado_pausa_automata()
        return
    
    if key == keyboard.Key.f6:
        cambiar_estado_cronometro_video()
        reproducir("cronometrovideo")
        return
    
    if key == keyboard.Key.f7:
        cambiar_estado_intervencion_usuario()
        return
    
    if key == keyboard.Key.f8:
        borrar_ultimo_evento_grabacion()
        return
    
    if capturador_esta_activo():

        if key == keyboard.Key.down:

            registrar_flecha_capturador(
                "down"
            )

            return

        elif key == keyboard.Key.up:

            registrar_flecha_capturador(
                "up"
            )

            return
        
        elif key == keyboard.Key.left:

            registrar_flecha_capturador(
                "left"
            )

            return  

        elif key == keyboard.Key.right:

            registrar_flecha_capturador(
                "right"
            )

            return      
        
        elif key == keyboard.Key.insert:

            mover_offset_arriba()

            return

        elif key == keyboard.Key.delete:

            mover_offset_abajo()

            return

        try:

            if key.char == "'":

                mover_offset_izquierda()

                return

            elif key.char == "¿":

                mover_offset_derecha()

                return
            
            elif key.char == "+":

                hacer_magenta_mas_alto()

                return
            
            elif key.char == "}":

                hacer_magenta_menos_alto()

                return
            
            elif key.char == "´":

                hacer_magenta_mas_ancho()

                return
            
            elif key.char == "{":

                hacer_magenta_menos_ancho()

                return

        except AttributeError:
            pass

    if aprendizaje_activo():

        try:

            if key.char == "+":

                hacer_magenta_bs_mas_alto()

                return

            elif key.char == "}":

                hacer_magenta_bs_menos_alto()

                return

            elif key.char == "´":

                hacer_magenta_bs_mas_ancho()

                return

            elif key.char == "{":

                hacer_magenta_bs_menos_ancho()

                return

        except AttributeError:
            pass

    if key in (
        keyboard.Key.ctrl,
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r
    ):
        ctrl_presionado = True
        return
    
    if espejo_esta_activo():

        if key == keyboard.Key.down:

            registrar_flecha(
                "down",
                "espejo"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": FLECHA_ESPEJO,
                    "direccion": "down"
                })
            
            return


        elif key == keyboard.Key.left:

            registrar_flecha(
                "left",
                "espejo"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": FLECHA_ESPEJO,
                    "direccion": "left"
                })
            
            return

        elif key == keyboard.Key.right:

            registrar_flecha(
                "right",
                "espejo"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": FLECHA_ESPEJO,
                    "direccion": "right"
                })
            
            return

        elif key == keyboard.Key.up:

            registrar_flecha(
                "up",
                "espejo"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": FLECHA_ESPEJO,
                    "direccion": "up"
                })
            
            return
        
        elif (
            ctrl_presionado
            and hasattr(key, "vk")
            and key.vk == 107
        ):

            registrar_zoom(
                "mas"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": ZOOM_ESPEJO,
                    "direccion": "mas"
                })
            
            return

        elif (
            ctrl_presionado
            and hasattr(key, "vk")
            and key.vk == 109
        ):

            registrar_zoom(
                "menos"
            )

            if (
                automata_grabando()
                and tecla_realizada_en_maestra()
            ):

                registrar_evento({
                    "tipo": ZOOM_ESPEJO,
                    "direccion": "menos"
                })
            
            return

def on_release(key):

    global ctrl_presionado
    global shift_presionado

    if key in (
        keyboard.Key.shift,
        keyboard.Key.shift_l,
        keyboard.Key.shift_r
    ):

        shift_presionado = False

        return

    if key in (
        keyboard.Key.ctrl,
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r
    ):
        ctrl_presionado = False
        return

    debug("↑", key)

def iniciar_listener():

    global keyboard_listener
    global mouse_listener

    keyboard_listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    keyboard_listener.daemon = True
    keyboard_listener.start()

    mouse_listener = mouse.Listener(
        on_click=on_click,
        on_scroll=on_scroll
    )

    mouse_listener.daemon = True
    mouse_listener.start()