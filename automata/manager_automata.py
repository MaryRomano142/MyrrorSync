import time
import threading
import os

from automata.recorder import (
    limpiar_eventos,
    obtener_eventos,
    registrar_evento,
    eliminar_cierre_final,
    establecer_registro_habilitado,
    borrar_ultimo_evento
)

from automata.storage import (
    preparar_grabacion_temporal,
    guardar_timeline,
    CARPETA_TEMPORAL
)

from automata.events import (
    CRONOMETRO_VIDEO,
    INTERVENCION_USUARIO
)

from automata.ui_bridge import (
    solicitar_guardado_grabacion
)

from ui.ui_state import (
    mostrar_automata_reproduciendo,
    mostrar_automata_grabando,
    mostrar_automata_pausado,
    mostrar_automata_desactivado
)

from core.sound import (
    reproducir,
    detener
)

from core.debug import debug

from core.notificaciones import enviar_notificacion

grabando = False
reproduciendo = False
pausado = False
modo_zig_zag = False
ventana_reproduccion_actual = None
cronometro_video_activo = False
inicio_cronometro_video = None
intervencion_grabacion_activa = False
intervencion_reproduccion_activa = False
evento_intervencion = threading.Event()
detencion_reproduccion_solicitada = False

def automata_grabando():

    return grabando

def automata_reproduciendo():

    return reproduciendo

def establecer_ventana_reproduccion(ventana):

    global ventana_reproduccion_actual

    ventana_reproduccion_actual = ventana

def obtener_ventana_reproduccion():

    return ventana_reproduccion_actual

def automata_pausado():

    return pausado

def modo_zig_zag_esta_activo():

    return modo_zig_zag

def cambiar_estado_zig_zag():

    global modo_zig_zag

    modo_zig_zag = not modo_zig_zag

    if modo_zig_zag:

        print("[AUTOMATA] MODO ZIG ZAG ACTIVADO")

        reproducir("modozigzagactivado")

    else:

        print("[AUTOMATA] MODO ZIG ZAG DESACTIVADO")

        reproducir("modozigzagdesactivado")

    return modo_zig_zag

def automata_acepta_eventos():

    return (
        grabando
        and not pausado
    )

def iniciar_grabacion():

    global grabando
    global pausado
    global cronometro_video_activo
    global inicio_cronometro_video
    global intervencion_grabacion_activa
    cronometro_video_activo = False
    inicio_cronometro_video = None
    intervencion_grabacion_activa = False

    if grabando:
        return

    preparar_grabacion_temporal()

    limpiar_eventos()

    grabando = True
    pausado = False

    mostrar_automata_grabando()

    reproducir("automatagrabando")

    establecer_registro_habilitado(
        True
    )

    print("GRABACIÓN INICIADA")

    print("\n<<<<<<<<<<<<<<<<<<<< PANTALLA 1 >>>>>>>>>>>>>>>>>>>>")

def detener_grabacion():

    global grabando
    global pausado
    global cronometro_video_activo
    global inicio_cronometro_video
    global intervencion_grabacion_activa
    cronometro_video_activo = False
    inicio_cronometro_video = None
    intervencion_grabacion_activa = False

    if not grabando:
        return

    grabando = False
    pausado = False

    mostrar_automata_desactivado()

    establecer_registro_habilitado(
        False
    )

    # El Inspector y el clic finales corresponden
    # al intento de finalizar el cuestionario.
    eliminar_cierre_final()

    eventos = obtener_eventos()

    guardar_timeline(
        eventos
    )

    print("GRABACIÓN DETENIDA")

    print(
        f"Eventos guardados: "
        f"{len(eventos)}"
    )

    # ============================================================
    # AVISAR A LA INTERFAZ QUE DEBE PEDIR EL NOMBRE
    # ============================================================

    solicitar_guardado_grabacion()

def cambiar_estado_grabacion():

    if automata_grabando():

        detener_grabacion()

    else:

        iniciar_grabacion()
    
def pausar_automata():

    global pausado

    if (
        not grabando
        and not reproduciendo
    ):

        print(
            "[AUTOMATA] No hay grabación "
            "ni reproducción activa."
        )

        return

    if pausado:
        return

    pausado = True

    mostrar_automata_pausado()

    # Durante grabación,
    # recorder deja de aceptar eventos.
    if grabando:

        establecer_registro_habilitado(
            False
        )

    if grabando:

        reproducir("automataenpausa")

        print("GRABACIÓN PAUSADA")

    elif reproduciendo:

        detener("espejoreplicando")

        reproducir("automataenpausa")

        print("REPRODUCCIÓN PAUSADA")

def reanudar_automata():

    global pausado

    if (
        not grabando
        and not reproduciendo
    ):

        return

    if not pausado:
        return

    pausado = False

    if (
        grabando
        and not intervencion_grabacion_activa
    ):

        establecer_registro_habilitado(
            True
        )

    if grabando:

        mostrar_automata_grabando()

        reproducir("automatagrabando")

        print("GRABACIÓN REANUDADA")

    elif reproduciendo:

        mostrar_automata_reproduciendo()

        reproducir("automatareproduciendo")

        print("REPRODUCCIÓN REANUDADA")

def cambiar_estado_pausa_automata():

    if (
        not automata_grabando()
        and not automata_reproduciendo()
    ):

        print(
            "[AUTOMATA] F5 ignorado: "
            "el Autómata está inactivo."
        )

        return

    if automata_pausado():

        reanudar_automata()

    else:

        pausar_automata()

def iniciar_reproduccion():

    global reproduciendo
    global pausado

    if grabando:

        print(
            "[AUTOMATA] No se puede reproducir "
            "mientras se está grabando."
        )

        return False

    if reproduciendo:

        print(
            "[AUTOMATA] Ya hay una "
            "reproducción activa."
        )

        return False

    reproduciendo = True
    pausado = False

    mostrar_automata_reproduciendo()

    reproducir("automatareproduciendo")

    debug("========== AUTÓMATA ==========")
    print("REPRODUCCIÓN INICIADA")

    return True

def finalizar_reproduccion():

    global reproduciendo
    global pausado

    reproduciendo = False
    pausado = False

    mostrar_automata_desactivado()

    debug("REPRODUCCIÓN TERMINADA")

def detener_reproduccion():

    global reproduciendo
    global pausado
    global detencion_reproduccion_solicitada

    if not reproduciendo:

        return

    detencion_reproduccion_solicitada = True

    reproduciendo = False
    pausado = False

    mostrar_automata_desactivado()

    print()

    print(
        "REPRODUCCIÓN DETENIDA "
        "POR EL USUARIO"
    )

def reproduccion_fue_detenida():

    return detencion_reproduccion_solicitada

def preparar_lote_reproduccion():

    global detencion_reproduccion_solicitada

    detencion_reproduccion_solicitada = False

def cambiar_estado_cronometro_video():

    global cronometro_video_activo
    global inicio_cronometro_video

    if not automata_acepta_eventos():

        print(
            "[AUTOMATA] F6 ignorado: "
            "la grabación no está activa."
        )

        return

    # ========================================================
    # INICIAR INSPECTOR
    # ========================================================

    if not cronometro_video_activo:

        cronometro_video_activo = True

        inicio_cronometro_video = (
            time.perf_counter()
        )

        print(
            "[AUTOMATA] "
            "Inspector de video iniciado."
        )

        return

    # ========================================================
    # DETENER INSPECTOR
    # ========================================================

    fin = time.perf_counter()

    segundos = (
        fin
        - inicio_cronometro_video
    )

    cronometro_video_activo = False
    inicio_cronometro_video = None

    registrar_evento({

        "tipo": CRONOMETRO_VIDEO,

        "segundos": segundos
    })

    debug(
        "[AUTOMATA] "
        "Inspector de video detenido."
    )

    print(
        f"[AUTOMATA] "
        f"Tiempo video: "
        f"{segundos:.2f} segundos"
    )

def cambiar_estado_intervencion_usuario():

    global intervencion_grabacion_activa
    global intervencion_reproduccion_activa

    # ========================================================
    # DURANTE GRABACIÓN
    # ========================================================

    if automata_grabando():

        # ----------------------------------------------------
        # PRIMER F7
        # Guardar evento y pausar registro
        # ----------------------------------------------------

        if not intervencion_grabacion_activa:

            # Primero guardamos el evento,
            # mientras el recorder todavía acepta eventos.
            registrar_evento({

                "tipo": INTERVENCION_USUARIO
            })

            intervencion_grabacion_activa = True

            establecer_registro_habilitado(
                False
            )

            print()
            print("<<<<<<<<<<INTERVENCIÓN DEL USUARIO>>>>>>>>>>")
            print("GRABACIÓN EN ESPERA")

            return

        # ----------------------------------------------------
        # SEGUNDO F7
        # Terminar intervención y reanudar
        # ----------------------------------------------------

        intervencion_grabacion_activa = False

        # Si además F5 dejó al Autómata pausado,
        # NO habilitamos todavía el recorder.
        if not automata_pausado():

            establecer_registro_habilitado(
                True
            )

        print()
        print("<<<<<<<<<<INTERVENCIÓN TERMINADA>>>>>>>>>>")
        print("GRABACIÓN CONTINÚA")

        return

    # ========================================================
    # DURANTE REPRODUCCIÓN
    # ========================================================

    if automata_reproduciendo():

        if not intervencion_reproduccion_activa:

            print(
                "[AUTOMATA] F7 ignorado: "
                "no se está esperando intervención."
            )

            return

        print()
        print("INTERVENCIÓN TERMINADA")
        print("REPRODUCCIÓN CONTINÚA")

        # Desbloquea al hilo del reproductor.
        evento_intervencion.set()

        return

    print(
        "[AUTOMATA] F7 ignorado: "
        "el Autómata está inactivo."
    )

def iniciar_espera_intervencion():

    global intervencion_reproduccion_activa

    intervencion_reproduccion_activa = True

    evento_intervencion.clear()

def finalizar_espera_intervencion():

    global intervencion_reproduccion_activa

    intervencion_reproduccion_activa = False

    evento_intervencion.clear()

def esperar_intervencion_usuario():

    iniciar_espera_intervencion()

    reproducir("intervencionusuario")

    print()
    print("INTERVENCIÓN DEL USUARIO NECESARIA:")
    print("Usuario debe corregir respuesta y")
    print("clicar en botón de avance.")
    print("Esperando F7 para continuar...")

    time.sleep(0.3)

    detener("espejoreplicando")

    reproducir("senecesitalaintervenciondelusuario")

    enviar_notificacion(
        mensaje="Intervención del usuario.",
        titulo="MirrorSync - F7",
        prioridad="urgent"
    )

    while (
        automata_reproduciendo()
        and not evento_intervencion.is_set()
    ):

        time.sleep(
            0.05
        )

    finalizar_espera_intervencion()

def borrar_ultimo_evento_grabacion():

    if not automata_grabando():

        print(
            "[AUTOMATA] F8 ignorado: "
            "no hay grabación activa."
        )

        return

    if automata_pausado():

        print(
            "[AUTOMATA] F8 ignorado: "
            "la grabación está pausada."
        )

        return

    borrar_ultimo_evento()



