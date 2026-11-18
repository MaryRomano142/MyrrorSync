import os
import json
import time
import threading
import pyautogui
import win32clipboard

from windows.window_actions import (
    traer_ventana_al_frente
)

from automata.manager_automata import (
    iniciar_reproduccion,
    finalizar_reproduccion,
    automata_pausado,
    automata_reproduciendo,
    esperar_intervencion_usuario,
    preparar_lote_reproduccion,
    reproduccion_fue_detenida,
    establecer_ventana_reproduccion,
    modo_zig_zag_esta_activo
)

from automata.events import (
    CLICK_MANUAL,
    CLICK_ESPEJO,
    FLECHA_ESPEJO,
    ZOOM_ESPEJO,
    SCROLL_ESPEJO,
    ESCRITURA,
    ARRASTRE_MANUAL,
    BLOCK_VERTICAL,
    BLOCK_SECCIONES,
    CAPTURADOR,
    INSPECTOR_AVANCE,
    CRONOMETRO_VIDEO,
    INTERVENCION_USUARIO,
    VIGILAR_VULNERABILIDAD
)

from automata.asignaciones import (
    obtener_asignaciones,
    asignacion_sigue_existiendo
)

from automata.storage import (
    CARPETA_GRABACIONES
)

from automata.capture_pantalla import (
    capturar_pantalla_actual,
    calcular_similitud_pantallas,
    detectar_pantalla_blanca,
    analizar_movimiento_pantallas
)

from automata.inspector_vulnerabilidad import (
    obtener_puerto_cdp_ventana,
    detectar_vulnerabilidad_dom
)

from core.mirror import (
    obtener_esclavas,
    reproducir_click_automata,
    reproducir_flecha_automata,
    reproducir_zoom_automata,
    reproducir_scroll_automata,
    reproducir_escritura_automata,
    reproducir_arrastre_automata,
    desactivar_espejo,
    iniciar_evento_interno,
    finalizar_evento_interno,
    dar_foco_ventana
)

from core.sound import (
    reproducir,
    reproducir_bucle,
    detener
)

from core.notificaciones import enviar_notificacion

from core.debug import debug

from ui.ui_state import (
    mostrar_espejo_replicando,
    mostrar_espejo_desactivado
)

from block_vertical.manager_blockvertical import (
    reproducir_block_vertical_automata
)

from block_secciones.manager_secciones import (
    reproducir_block_secciones_automata
)

from capturador.manager_capturador import (
    reproducir_capturador_automata
)

CARPETA_AUTOMATA = os.path.dirname(
    __file__
)

CARPETA_TEMPORAL = os.path.join(
    CARPETA_AUTOMATA,
    "grabaciones",
    "_temporal"
)

RUTA_TIMELINE_TEMPORAL = os.path.join(
    CARPETA_TEMPORAL,
    "timeline.json"
)

TIEMPO_DESCALIFICACION = 200.0 #3 minutos x 60 seg = 180 = 3 minutos
INTERVALO_DESCALIFICACION = 3.0
TIEMPO_ENTRE_EVENTOS_AUTOMATA = 0.2
TIEMPO_POST_CRONOMETRO = 0.25

# CONFIGURACIÓN DE LAS ESPECIALIDADES DEL INSPECTOR DE AVANCE
UMBRAL_MISMA_PANTALLA = 99.83
TIEMPO_REINTENTO = 2.0
TIEMPO_MAXIMO_INSPECCION = 30.0

servicio_protegido_activo = (
    threading.Event()
)

pausa_descalificador = (
    threading.Event()
)

def cargar_timeline(ruta_timeline):

    if not os.path.exists(
        ruta_timeline
    ):

        print(
            "[AUTOMATA] No existe timeline:"
        )

        print(
            ruta_timeline
        )

        return None

    try:

        with open(
            ruta_timeline,
            "r",
            encoding="utf-8"
        ) as archivo:

            timeline = json.load(
                archivo
            )

    except Exception as e:

        print(
            "[AUTOMATA] Error leyendo timeline:"
        )

        print(
            e
        )

        return None

    if not isinstance(
        timeline,
        list
    ):

        print(
            "[AUTOMATA] Timeline inválida."
        )

        return None

    return timeline

def esperar_con_pausa(segundos):

    transcurrido = 0.0

    ultimo_tiempo = time.perf_counter()

    while (
        transcurrido < segundos
        and automata_reproduciendo()
    ):

        if automata_pausado() or pausa_descalificador.is_set():

            time.sleep(
                0.05
            )

            ultimo_tiempo = (
                time.perf_counter()
            )

            continue

        ahora = (
            time.perf_counter()
        )

        transcurrido += (
            ahora - ultimo_tiempo
        )

        ultimo_tiempo = ahora

        time.sleep(
            0.01
        )

def reproducir_inspector_avance(evento):

    segundos = 2.0 #tiempre entre pantallas

    debug(
        "[AUTOMATA] "
        "Inspector de avance"
    )

    debug(
        f"Esperando "
        f"{segundos} segundos..."
    )

    esperar_con_pausa(
        segundos
    )

    debug(
        "[AUTOMATA] "
        "Inspector de avance terminado."
    )

    time.sleep(
        TIEMPO_POST_CRONOMETRO
    )
 
def reproducir_evento(ventana,evento,carpeta_eventos,variables_escritura=None):

    if variables_escritura is None:

        variables_escritura = {}

    tipo = evento.get(
        "tipo"
    )

    # ========================================================
    # CLICS
    # ========================================================

    if tipo in (
        CLICK_MANUAL,
        CLICK_ESPEJO
    ):

        reproducir_click_automata(
            ventana,
            evento
        )

        return

    # ========================================================
    # FLECHAS ESPEJO
    # ========================================================

    if tipo == FLECHA_ESPEJO:

        reproducir_flecha_automata(
            ventana,
            evento
        )

        return

    # ========================================================
    # ZOOM ESPEJO
    # ========================================================

    if tipo == ZOOM_ESPEJO:

        reproducir_zoom_automata(
            ventana,
            evento
        )

        return
    
    # ========================================================
    # SCROLL ESPEJO
    # ========================================================

    if tipo == SCROLL_ESPEJO:

        reproducir_scroll_automata(
            ventana,
            evento
        )

        return
    
    # ========================================================
    # ESCRITURA
    # ========================================================

    if tipo == ESCRITURA:

        evento_escritura = evento.copy()

        variable = evento.get(
            "variable_escritura"
        )

        if variable:

            variable = (
                str(variable)
                .strip()
                .upper()
            )

            if variable in variables_escritura:

                valor = variables_escritura[
                    variable
                ]

                evento_escritura[
                    "texto"
                ] = str(valor)

                print(
                    "[ESCRITURA VARIABLE] "
                    f"{variable} = {valor}"
                )

            else:

                print(
                    "[ESCRITURA VARIABLE] "
                    f"Sin valor para {variable}. "
                    "Se usará el texto original."
                )
            
        esperar_con_pausa(0.3) #tiempo estabilizacion

        reproducir_escritura_automata(
            ventana,
            evento_escritura
        )

        return

    # ========================================================
    # ARRASTRE MANUAL
    # ========================================================

    if tipo == ARRASTRE_MANUAL:

        reproducir_arrastre_automata(
            ventana,
            evento
        )

        return
    
    # ========================================================
    # BLOCK VERTICAL
    # ========================================================

    if tipo == BLOCK_VERTICAL:

        esperar_con_pausa(0.7) #tiempo estabilizacion

        reproducir_block_vertical_automata(
            ventana,
            evento
        )

        return
    
    # ========================================================
    # BLOCK SECCIONES
    # ========================================================

    if tipo == BLOCK_SECCIONES:

        esperar_con_pausa(1.5) #tiempo estabilizacion

        reproducir_block_secciones_automata(
            ventana,
            evento,
            carpeta_eventos
        )

        return
    
    # ========================================================
    # CAPTURADOR
    # ========================================================

    if tipo == CAPTURADOR:

        esperar_con_pausa(1.5) #tiempo estabilizacion

        reproducir_capturador_automata(
            ventana,
            evento,
            carpeta_eventos
        )

        return

    # ========================================================
    # INSPECTOR DE AVANCE
    # ========================================================

    if tipo == INSPECTOR_AVANCE:

        reproducir_inspector_avance(
            evento
        )

        return

    # ========================================================
    # INSPECTOR DE VIDEO
    # ========================================================

    if tipo == CRONOMETRO_VIDEO:

        reproducir_cronometro_video(
            evento
        )

        return

    # ========================================================
    # INTERVENCIÓN DEL USUARIO
    # ========================================================

    if tipo == INTERVENCION_USUARIO:

        reproducir_intervencion_usuario(
            evento
        )

        return

    print(
        f"[AUTOMATA] "
        f"Evento todavía no reproducible: "
        f"{tipo}"
    )

def reproducir_timeline(
    ruta_timeline,
    ventana,
    variables_escritura=None,
    indice_inicio=0,
    detener_al_avanzar=False,
    pantalla_inicio=1,
    gestionar_reproduccion=True
):

    if variables_escritura is None:

        variables_escritura = {}

    # ========================================================
    # CARGAR TIMELINE
    # ========================================================

    timeline = cargar_timeline(
        ruta_timeline
    )

    if timeline is None:
        return False

    # ========================================================
    # OBTENER CARPETA DE EVENTOS
    # ========================================================

    carpeta_grabacion = os.path.dirname(
        ruta_timeline
    )

    carpeta_eventos = os.path.join(
        carpeta_grabacion,
        "eventos"
    )

    # ========================================================
    # VALIDAR VENTANA
    # ========================================================

    if ventana is None:

        print(
            "[AUTOMATA] "
            "No hay ventana para reproducir."
        )

        return False
    
    establecer_ventana_reproduccion(
        ventana
    )

    # ========================================================
    # INICIAR ESTADO DE REPRODUCCIÓN
    # ========================================================

    if gestionar_reproduccion:

        if not iniciar_reproduccion():
            return False

    # ========================================================
    # CONTROLES DE ESTA REPRODUCCIÓN
    # ========================================================

    detener_cronometro = (
        threading.Event()
    )

    cancelar_asignacion = (
        threading.Event()
    )

    hilo_descalificacion = None

    reproduccion_completada = False

    avance_confirmado_turno = False
    siguiente_indice = indice_inicio

    contador_pantallas = pantalla_inicio

    try:

        total = len(
            timeline
        )

        debug(
            "[AUTOMATA] Ventana objetivo:"
        )

        debug(
            ventana.get(
                "titulo",
                ventana.get(
                    "proceso",
                    "Desconocida"
                )
            )
        )

        debug(
            "[CDP] Datos de ventana:"
        )

        debug(
            ventana
        )

        # ====================================================
        # TRAER LA VENTANA AL FRENTE
        #
        # SOLO UNA VEZ:
        # antes del primer evento.
        # ====================================================

        resultado_frente = (
            traer_ventana_al_frente(
                ventana["hwnd"]
            )
        )

        if resultado_frente is False:

            print(
                "[AUTOMATA] "
                "No se pudo traer la ventana al frente."
            )

            return False

        # Pequeña espera para que Windows termine
        # de colocar la ventana correctamente.
        time.sleep(
            0.15
        )

        # ====================================================
        # DAR FOCO REAL A LA VENTANA
        #
        # Una sola vez al comenzar esta asignación.
        # El Scroll necesita que la ventana objetivo
        # conserve el foco durante toda su secuencia.
        # ====================================================

        dar_foco_ventana(
            ventana["hwnd"]
        )

        time.sleep(
            0.05
        )

        # ====================================================
        # INICIAR INSPECTOR DE DESCALIFICACIÓN
        # ====================================================

        hilo_descalificacion = (
            threading.Thread(

                target=cronometro_descalificacion,

                args=(
                    detener_cronometro,
                    cancelar_asignacion,
                    ventana
                ),

                daemon=True
            )
        )

        hilo_descalificacion.start()

        # ====================================================
        # RECORRER TIMELINE
        # ====================================================

        espejo_sonando = False

        inspector_avance_pendiente = None

        vigilar_vulnerabilidad_activa = False

        for indice, evento in enumerate(
            timeline[indice_inicio:],
            indice_inicio + 1
        ):

            # =================================================
            # REPRODUCCIÓN DETENIDA MANUALMENTE
            # =================================================

            if not automata_reproduciendo():
                break

            # =================================================
            # DESCALIFICACIÓN
            # =================================================

            if cancelar_asignacion.is_set():

                print()
                print(
                    "[AUTOMATA] "
                    "Reproducción cancelada "
                    "por descalificación."
                )

                break

            # =================================================
            # PAUSA GENERAL F5
            # =================================================

            while (
                (automata_pausado() or pausa_descalificador.is_set())
                and automata_reproduciendo()
            ):

                time.sleep(
                    0.05
                )

            if not automata_reproduciendo():
                break

            # Puede haberse detectado descalificación
            # mientras estábamos pausados.
            if cancelar_asignacion.is_set():

                print(
                    "[AUTOMATA] "
                    "Reproducción cancelada "
                    "por descalificación."
                )

                break

            print(
                f"[AUTOMATA] "
                f"Reproduciendo evento "
                f"{indice}/{total}"
            )

            print(
                f"Tipo: "
                f"{evento.get('tipo')}"
            )

            tipo_evento = evento.get(
                "tipo"
            )

            # SONIDO DE RÉPLICA DEL ESPEJO

            evento_espejo = (
                tipo_evento
                in (
                    CLICK_ESPEJO,
                    FLECHA_ESPEJO,
                    ZOOM_ESPEJO,
                    SCROLL_ESPEJO
                )
            )

            if evento_espejo:

                if not espejo_sonando:

                    reproducir_bucle(
                        "espejoreplicando"
                    )

                    mostrar_espejo_replicando()

                    espejo_sonando = True

            else:

                if espejo_sonando:

                    detener(
                        "espejoreplicando"
                    )

                    mostrar_espejo_desactivado()

                    espejo_sonando = False

            # =================================================
            # OMOTIR DESCALIFICACION
            # =================================================

            if cancelar_asignacion.is_set():

                print(
                    "[AUTOMATA] "
                    "Evento omitido por descalificación."
                )

                break

            # ============================================================
            # PROTECCIÓN CONTRA DESCALIFICADOR
            #
            # Todos los eventos están protegidos EXCEPTO:
            #
            # - Inspector de avance
            # - Cronómetro de video
            # ============================================================

            evento_protegido = (
                tipo_evento
                not in (
                    INSPECTOR_AVANCE,
                    CRONOMETRO_VIDEO
                )
            )

            if evento_protegido:

                servicio_protegido_activo.set()

            try:

                if tipo_evento == BLOCK_VERTICAL:

                    time.sleep(
                        0.1
                    )

                # ========================================================
                # INSPECTOR DE AVANCE
                #
                # Ya no espera cuando aparece en el timeline.
                # Queda armado para ejecutarse DESPUÉS
                # del evento siguiente.
                # ========================================================

                if tipo_evento == INSPECTOR_AVANCE:

                    imagen_testigo = capturar_pantalla_actual(
                        ventana["hwnd"]
                    )

                    if imagen_testigo is None:
                        print(
                            "[INSPECTOR DE AVANCE] "
                            "No se pudo capturar el testigo."
                        )

                        inspector_avance_pendiente = None

                    else:
                        inspector_avance_pendiente = {
                            "evento": evento,
                            "imagen_testigo": imagen_testigo
                        }

                        debug(
                            "[INSPECTOR DE AVANCE] "
                            "Testigo capturado."
                        )

                    continue
                
                if tipo_evento == VIGILAR_VULNERABILIDAD:

                    vigilar_vulnerabilidad_activa = True

                    print(
                        "[INSPECTOR DE AVANCE] "
                        "Vigilancia de vulnerabilidad activada."
                    )

                    continue

                else:

                    reproducir_evento(
                        ventana,
                        evento,
                        carpeta_eventos,
                        variables_escritura
                    )

                    # ====================================================
                    # SI HABÍA UN INSPECTOR PENDIENTE,
                    # ESTE ERA EL EVENTO QUE DEBÍA OCURRIR
                    # ANTES DE ESPERAR.
                    # ====================================================

                    if inspector_avance_pendiente is not None:

                        debug(
                            "[AUTOMATA] "
                            "Evento posterior al inspector ejecutado."
                        )

                        if vigilar_vulnerabilidad_activa:

                            puerto_cdp = (
                                obtener_puerto_cdp_ventana(
                                    ventana
                                )
                            )

                            if puerto_cdp is not None:

                                # ========================================================
                                # ESPERAR A QUE LA PÁGINA PROCESE EL CLIC DE AVANCE
                                #
                                # Algunos errores de validación aparecen en el DOM
                                # unas décimas después del clic.
                                # ========================================================

                                esperar_con_pausa(
                                    1.0
                                )

                                vulnerabilidad_detectada = (
                                    detectar_vulnerabilidad_dom(
                                        puerto_cdp
                                    )
                                )

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    f"Resultado vulnerabilidad: "
                                    f"{vulnerabilidad_detectada}"
                                )

                                if vulnerabilidad_detectada:

                                    print(
                                        "[INSPECTOR DE AVANCE] "
                                        "Vulnerabilidad confirmada."
                                    )

                                    print(
                                        "[INSPECTOR DE AVANCE] "
                                        "Solicitando intervención "
                                        "del usuario."
                                    )

                                    # Mientras el usuario corrige la respuesta,
                                    # el descalificador debe permanecer congelado.
                                    servicio_protegido_activo.set()

                                    try:
                                        esperar_intervencion_usuario()
                                    finally:
                                        servicio_protegido_activo.clear()

                                    print(
                                        "[INSPECTOR DE AVANCE] "
                                        "Intervención finalizada."
                                    )

                            # Si NO se detectó todavía, mantenemos la vigilancia
                            # activa durante el Inspector de Avance. En sitios como
                            # Norstat el indicador de error puede aparecer después
                            # de esta primera consulta al DOM.
                            if vulnerabilidad_detectada:
                                vigilar_vulnerabilidad_activa = False

                        debug(
                            "[AUTOMATA] "
                            "Iniciando espera de pantalla..."
                        )

                        # ============================================================
                        # EL INSPECTOR DE AVANCE NO ES UN SERVICIO PROTEGIDO
                        #
                        # El evento que produjo el avance ya terminó.
                        # Liberamos la protección para permitir que el
                        # Inspector de descalificación pueda ejecutarse
                        # durante la espera visual.
                        # ============================================================

                        if evento_protegido:
                            servicio_protegido_activo.clear()

                        reproducir_inspector_avance(
                            inspector_avance_pendiente["evento"]
                        )

                        imagen_testigo = inspector_avance_pendiente[
                            "imagen_testigo"
                        ]

                        # ============================================================
                        # BUCLE DE INSPECCIÓN
                        # ============================================================

                        inicio_inspeccion = time.time()

                        pantalla_confirmada = False

                        reintentos_inspector = 0
                        notificacion_inspector_enviada = False

                        def registrar_reintento_inspector():

                            nonlocal reintentos_inspector
                            nonlocal notificacion_inspector_enviada

                            reintentos_inspector += 1

                            print(
                                "[INSPECTOR DE AVANCE] "
                                f"Reintento {reintentos_inspector}."
                            )

                            if (
                                reintentos_inspector >= 8
                                and not notificacion_inspector_enviada
                            ):

                                reproducir("demasiadosintentos")

                                enviar_notificacion(
                                    mensaje="8 reintentos acumulados.",
                                    titulo="MirrorSync - Inspector de Avance",
                                    prioridad="urgent"
                                )

                                notificacion_inspector_enviada = True

                        while not pantalla_confirmada:

                            # ========================================================
                            # F5 Y DESCALIFICADOR PAUSAN EL INSPECTOR DE AVANCE
                            # ========================================================

                            if (
                                automata_pausado()
                                or pausa_descalificador.is_set()
                            ):

                                inicio_pausa_inspector = time.time()

                                while (
                                    (
                                        automata_pausado()
                                        or pausa_descalificador.is_set()
                                    )
                                    and automata_reproduciendo()
                                ):

                                    time.sleep(
                                        0.05
                                    )

                                # El tiempo que estuvo pausado NO debe contar
                                # para el límite máximo del Inspector.
                                inicio_inspeccion += (
                                    time.time()
                                    - inicio_pausa_inspector
                                )

                            if (
                                not automata_reproduciendo()
                                or reproduccion_fue_detenida()
                            ):

                                debug(
                                    "[INSPECTOR DE AVANCE] "
                                    "Inspección cancelada por el usuario."
                                )

                                break

                            imagen_actual = capturar_pantalla_actual(
                                ventana["hwnd"]
                            )

                            if imagen_actual is None:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No se pudo obtener la captura actual."
                                )

                                break


                            debug(
                                "[INSPECTOR DE AVANCE] "
                                "Captura actual realizada."
                            )


                            if imagen_testigo is None:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No hay captura testigo válida."
                                )

                                break
                            
                            # ========================================================
                            # ¿LA PANTALLA ESTÁ BLANCA / CARGANDO?
                            # ========================================================

                            pantalla_blanca, porcentaje_blanco = (
                                detectar_pantalla_blanca(
                                    imagen_actual
                                )
                            )

                            print(
                                "[INSPECTOR DE AVANCE] "
                                f"Pantalla blanca: "
                                f"{porcentaje_blanco:.2f}%"
                            )

                            if pantalla_blanca:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "PANTALLA EN BLANCO DETECTADA."
                                )

                                tiempo_transcurrido = (
                                    time.time()
                                    - inicio_inspeccion
                                )

                                if (
                                    tiempo_transcurrido
                                    >= TIEMPO_MAXIMO_INSPECCION
                                ):

                                    print(
                                        "[INSPECTOR DE AVANCE] "
                                        "Tiempo máximo de espera alcanzado."
                                    )

                                    break

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    f"Reintentando en "
                                    f"{TIEMPO_REINTENTO:.0f} segundos..."
                                )

                                registrar_reintento_inspector()

                                time.sleep(
                                    TIEMPO_REINTENTO
                                )

                                continue

                            # ========================================================
                            # DIAGNÓSTICO DE MOVIMIENTO
                            # ========================================================

                            captura_movimiento_1 = capturar_pantalla_actual(
                                ventana["hwnd"]
                            )

                            time.sleep(0.25)

                            captura_movimiento_2 = capturar_pantalla_actual(
                                ventana["hwnd"]
                            )

                            diagnostico_movimiento = analizar_movimiento_pantallas(
                                captura_movimiento_1,
                                captura_movimiento_2
                            )

                            if diagnostico_movimiento is None:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No se pudo comprobar el movimiento."
                                )

                                registrar_reintento_inspector()

                                time.sleep(
                                    TIEMPO_REINTENTO
                                )

                                continue

                            pixeles_diferentes = (
                                diagnostico_movimiento[
                                    "pixeles_diferentes"
                                ]
                            )

                            similitud_temporal = (
                                diagnostico_movimiento[
                                    "similitud"
                                ]
                            )

                            if pixeles_diferentes != 0:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    f"Pantalla estable: " #Similitud temporal
                                    f"{similitud_temporal:.6f}%"
                                )

                                debug(
                                    "[INSPECTOR DE AVANCE] "
                                    f"Movimiento detectado "
                                    f"({pixeles_diferentes} píxeles diferentes)."
                                )

                                debug(
                                    "[INSPECTOR DE AVANCE] "
                                    "Esperando estabilidad..."
                                )

                                registrar_reintento_inspector()

                                time.sleep(
                                    TIEMPO_REINTENTO
                                )

                                continue

                            print(
                                    "[INSPECTOR DE AVANCE] "
                                    f"Pantalla estable: " #Similitud temporal
                                    f"{similitud_temporal:.6f}%"
                                )
                            
                            # ========================================================
                            # CAPTURA PROPIA DEL CRITERIO MISMA PANTALLA
                            # ========================================================

                            captura_misma_pantalla = capturar_pantalla_actual(
                                ventana["hwnd"]
                            )

                            if captura_misma_pantalla is None:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No se pudo capturar la pantalla "
                                    "para comprobar misma pantalla."
                                )

                                registrar_reintento_inspector()

                                time.sleep(
                                    TIEMPO_REINTENTO
                                )

                                continue

                            similitud = calcular_similitud_pantallas(
                                imagen_testigo,
                                captura_misma_pantalla
                            )

                            if similitud is None:

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No se pudo calcular la similitud."
                                )

                                break

                            porcentaje = (
                                similitud * 100
                            )

                            print(
                                "[INSPECTOR DE AVANCE] "
                                f"Pantallas iguales: " #Similitud con captura testigo
                                f"{porcentaje:.2f}%"
                            )

                            # ========================================================
                            # PANTALLA DIFERENTE
                            # ========================================================

                            if porcentaje < UMBRAL_MISMA_PANTALLA:

                                # ====================================================
                                # ÚLTIMA COMPROBACIÓN DE VULNERABILIDAD
                                #
                                # La página ya está estable y parece haber cambiado,
                                # pero un error de validación también puede producir
                                # ese cambio visual. Antes de confirmar el avance (y
                                # antes de que Zig Zag ceda el turno) consultamos el
                                # DOM una vez más si la vigilancia sigue armada.
                                # ====================================================

                                if vigilar_vulnerabilidad_activa:

                                    puerto_cdp = obtener_puerto_cdp_ventana(
                                        ventana
                                    )

                                    if puerto_cdp is not None:

                                        vulnerabilidad_detectada = (
                                            detectar_vulnerabilidad_dom(
                                                puerto_cdp
                                            )
                                        )

                                        print(
                                            "[INSPECTOR DE AVANCE] "
                                            "Resultado vulnerabilidad final: "
                                            f"{vulnerabilidad_detectada}"
                                        )

                                        if vulnerabilidad_detectada:

                                            print(
                                                "[INSPECTOR DE AVANCE] "
                                                "Vulnerabilidad confirmada antes "
                                                "del avance."
                                            )

                                            print(
                                                "[INSPECTOR DE AVANCE] "
                                                "Solicitando intervención "
                                                "del usuario."
                                            )

                                            # La intervención manual también es un
                                            # servicio protegido: el descalificador
                                            # no debe verificar mientras se espera F7.
                                            servicio_protegido_activo.set()

                                            try:
                                                esperar_intervencion_usuario()
                                            finally:
                                                servicio_protegido_activo.clear()

                                            print(
                                                "[INSPECTOR DE AVANCE] "
                                                "Intervención finalizada."
                                            )

                                            # Ya se atendió esta vigilancia. El
                                            # Inspector continúa y comprobará si la
                                            # corrección realmente produjo el avance.
                                            vigilar_vulnerabilidad_activa = False

                                            inicio_inspeccion = time.time()

                                            continue

                                    # Si llegamos hasta aquí sin vulnerabilidad, la
                                    # vigilancia correspondiente a este avance termina.
                                    vigilar_vulnerabilidad_activa = False

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "AVANCE CONFIRMADO."
                                )

                                contador_pantallas += 1

                                print(
                                    f"\n~~~~~~~~~~~~~~~~~~~~ PANTALLA "
                                    f"{contador_pantallas} "
                                    f"~~~~~~~~~~~~~~~~~~~~"
                                )

                                pantalla_confirmada = True
                                avance_confirmado_turno = True

                                break

                            # ========================================================
                            # TODAVÍA ES LA MISMA PANTALLA
                            # ========================================================

                            print(
                                "[INSPECTOR DE AVANCE] "
                                "NO ES POSIBLE AVANZAR."
                            )


                            tiempo_transcurrido = (
                                time.time()
                                - inicio_inspeccion
                            )


                            # ========================================================
                            # TIEMPO MÁXIMO
                            # ========================================================

                            if (
                                tiempo_transcurrido
                                >= TIEMPO_MAXIMO_INSPECCION
                            ):

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "Tiempo máximo de espera alcanzado."
                                )

                                print(
                                    "[INSPECTOR DE AVANCE] "
                                    "No se confirmó el avance."
                                )

                                break

                            print(
                                "[INSPECTOR DE AVANCE] "
                                f"Reintentando en "
                                f"{TIEMPO_REINTENTO:.0f} segundos..."
                            )

                            registrar_reintento_inspector()

                            time.sleep(
                                TIEMPO_REINTENTO
                            )

                        else:

                            print(
                                "[INSPECTOR DE AVANCE] "
                                "No se pudo obtener la captura actual."
                            )

                        inspector_avance_pendiente = None

            finally:

                if evento_protegido:

                    servicio_protegido_activo.clear()

            if tipo_evento == FLECHA_ESPEJO:

                # ====================================================
                # MIRAR QUÉ EVENTO VIENE DESPUÉS
                # ====================================================

                siguiente_tipo = None

                if indice < total:

                    siguiente_evento = timeline[
                        indice
                    ]

                    siguiente_tipo = siguiente_evento.get(
                        "tipo"
                    )

                # ====================================================
                # SI VIENE OTRA FLECHA:
                # seguimos rapidísimo.
                #
                # SI TERMINÓ LA SECUENCIA:
                # esperamos un poco para que la página se estabilice
                # antes del clic/capturador/block/etc.
                # ====================================================

                if siguiente_tipo == FLECHA_ESPEJO:

                    time.sleep(
                        0.001
                    )

                else:

                    time.sleep(
                        0.15
                    )

            else:

                time.sleep(
                    TIEMPO_ENTRE_EVENTOS_AUTOMATA
                )
            
            siguiente_indice = indice

            if (
                detener_al_avanzar
                and avance_confirmado_turno
            ):

                break

            # =================================================
            # COMPROBAR RESULTADO DESPUÉS DEL EVENTO
            # =================================================

            if cancelar_asignacion.is_set():

                print()
                print(
                    "[AUTOMATA] "
                    "Descalificación detectada. "
                    "No se ejecutarán más eventos "
                    "en esta ventana."
                )

                break

        # ====================================================
        # RESULTADO DE ESTA ASIGNACIÓN
        # ====================================================

        if cancelar_asignacion.is_set():

            debug(
                "========== AUTÓMATA =========="
            )

            debug(
                "ASIGNACIÓN CANCELADA "
                "POR DESCALIFICACIÓN"
            )

            reproduccion_completada = False
        
        elif (
            detener_al_avanzar
            and avance_confirmado_turno
        ):

            reproduccion_completada = False

        elif automata_reproduciendo():

            debug(
                "[AUTOMATA] "
                "Timeline completada correctamente."
            )

            reproduccion_completada = True

        else:

            debug(
                "[AUTOMATA] "
                "Reproducción detenida."
            )

            reproduccion_completada = False

    except Exception as e:

        print()
        print(
            "[AUTOMATA] "
            "Error durante la reproducción:"
        )

        import traceback
        traceback.print_exc()

        print(
            e
        )

        reproduccion_completada = False

    finally:

        detener("espejoreplicando")

        # ====================================================
        # DETENER INSPECTOR DE DESCALIFICACIÓN
        # ====================================================

        detener_cronometro.set()

        if (
            hilo_descalificacion is not None
            and hilo_descalificacion.is_alive()
        ):

            hilo_descalificacion.join(
                timeout=0.5
            )

        # Asegurarnos de no dejar este estado prendido
        # entre una asignación y la siguiente.
        servicio_protegido_activo.clear()

        establecer_ventana_reproduccion(
            None
        )

        # ====================================================
        # FINALIZAR REPRODUCCIÓN
        # ====================================================

        if gestionar_reproduccion:

            finalizar_reproduccion()
    
    if detener_al_avanzar:

        return {
            "completada": reproduccion_completada,
            "avance_confirmado": avance_confirmado_turno,
            "siguiente_indice": siguiente_indice
        }

    return reproduccion_completada

def reproducir_cronometro_video(evento):

    segundos = evento.get(
        "segundos",
        0
    )

    if segundos <= 0:

        print(
            "[AUTOMATA] "
            "Inspector de video inválido."
        )

        return

    print()
    print(
        "[AUTOMATA] "
        "Inspector de video"
    )

    print(
        f"Esperando "
        f"{segundos:.2f} segundos..."
    )

    esperar_con_pausa(
        segundos
    )

    print(
        "[AUTOMATA] "
        "Inspector de video terminado."
    )

    time.sleep(
        TIEMPO_POST_CRONOMETRO
    )

def reproducir_intervencion_usuario(evento):

    esperar_intervencion_usuario() #servicio o modo protegido

def obtener_url_actual():

    iniciar_evento_interno()

    try:

        pyautogui.hotkey(
            "ctrl",
            "l"
        )

        time.sleep(
            0.05
        )

        pyautogui.hotkey(
            "ctrl",
            "c"
        )

        time.sleep(
            0.05
        )

        url = ""

        try:

            win32clipboard.OpenClipboard()

            if win32clipboard.IsClipboardFormatAvailable(
                win32clipboard.CF_UNICODETEXT
            ):

                url = (
                    win32clipboard.GetClipboardData(
                        win32clipboard.CF_UNICODETEXT
                    )
                )

        except Exception as e:

            print(
                "[AUTOMATA] "
                "No se pudo leer la URL:"
            )

            print(e)

        finally:

            try:
                win32clipboard.CloseClipboard()
            except:
                pass

        # Salir de la barra de direcciones.
        pyautogui.press(
            "esc"
        )

        return url.strip()

    finally:

        finalizar_evento_interno()

def url_es_descalificacion(url):

    if not url:
        return False

    url = url.lower()

    return (
        "/qualscreen/" in url
        or
        "/quotafull/" in url
        or
        "/screened/" in url
    )

def cronometro_descalificacion(detener_cronometro,cancelar_asignacion,ventana):

    transcurrido = 0.0

    siguiente_revision = (
        INTERVALO_DESCALIFICACION
    )

    ultimo_tiempo = (
        time.perf_counter()
    )

    debug(
        "[INSPECTOR DE DESCALIFICACION] "
        "Inspeccion iniciada."
    )

    while (
        automata_reproduciendo()
        and not detener_cronometro.is_set()
        and transcurrido < TIEMPO_DESCALIFICACION
    ):

        # ====================================================
        # F5 CONGELA TAMBIÉN ESTE INSPECTOR
        # ====================================================

        if automata_pausado():

            time.sleep(
                0.05
            )

            ultimo_tiempo = (
                time.perf_counter()
            )

            continue

        # ====================================================
        # ÚNICOS SERVICIOS PROTEGIDOS:
        #
        # - Todos los Modos
        # - Intervención del usuario
        #
        # El Inspector de avance y el cronómetro de video NO bloquean la verificación.
        # ====================================================

        if servicio_protegido_activo.is_set():

            time.sleep(
                0.05
            )

            ultimo_tiempo = (
                time.perf_counter()
            )

            continue

        ahora = (
            time.perf_counter()
        )

        transcurrido += (
            ahora - ultimo_tiempo
        )

        ultimo_tiempo = ahora

        # ====================================================
        # TODAVÍA NO TOCA REVISAR
        # ====================================================

        if transcurrido < siguiente_revision:

            time.sleep(
                0.05
            )

            continue

        # La siguiente revisión será
        # dentro de otro intervalo.
        siguiente_revision += (
            INTERVALO_DESCALIFICACION
        )

        # ====================================================
        # COMPROBAR URL
        # ====================================================

        debug(
            "[INSPECTOR DE DESCALIFICACION] "
            "Pausando reproducción "
            "para verificar descalificación..."
        )

        pausa_descalificador.set()

        try:

            time.sleep(
                0.05
            )

            print(
                "[INSPECTOR DE DESCALIFICACION] "
                "Verificando URL..."
            )

            reproducir("inspectordescalificacion")

            url = obtener_url_actual()

            debug(
                "[INSPECTOR DE DESCALIFICACION] URL actual:"
            )

            debug(
                url
            )

            if url_es_descalificacion(
                url
            ):

                print(
                    "[INSPECTOR DE DESCALIFICACION] "
                    "DESCALIFICACIÓN DETECTADA."
                )

                enviar_notificacion(
                    mensaje="Descalificacion Detectada.",
                    titulo="MirrorSync - Descalificacion",
                    prioridad="urgent"
                )

                reproducir("descalificaciondetectada")

                time.sleep(1.9)

                reproducir("informardescalificaciondetectada")

                cancelar_asignacion.set()

                return

            debug(
                "[INSPECTOR DE DESCALIFICACION] "
                "URL normal. Continuando."
            )

        finally:

            if ventana is not None:

                hwnd = ventana.get(
                    "hwnd"
                )

                if hwnd:

                    dar_foco_ventana(
                        hwnd
                    )
            
            time.sleep(
                0.05
            )

            pausa_descalificador.clear()

            debug(
                "[AUTOMATA] "
                "Reproducción reanudada."
            )

    debug(
        "[AUTOMATA] "
        "Inspector de descalificación terminado."
    )

    reproducir("fininspectordescalificacion")

def reproducir_asignaciones():

    asignaciones = (
        obtener_asignaciones()
    )

    if not asignaciones:

        print(
            "[AUTOMATA] "
            "No existen asignaciones."
        )

        return

    if modo_zig_zag_esta_activo():

        objetivo_reproduccion = (
            _reproducir_asignaciones_zig_zag
        )

    else:

        objetivo_reproduccion = (
            _reproducir_asignaciones
        )

    hilo = threading.Thread(

        target=objetivo_reproduccion,

        args=(
            asignaciones,
        ),

        daemon=True
    )

    hilo.start()

def _reproducir_asignaciones_zig_zag(asignaciones):

    preparar_lote_reproduccion()

    if not iniciar_reproduccion():
        return

    estados = []

    # ========================================================
    # PREPARAR ESTADO INDEPENDIENTE DE CADA ASIGNACIÓN
    # ========================================================

    for asignacion in asignaciones:

        grabacion = asignacion.get(
            "grabacion"
        )

        ventana = asignacion.get(
            "ventana"
        )

        variables_escritura = asignacion.get(
            "variables_escritura",
            {}
        )

        if (
            not grabacion
            or ventana is None
        ):

            continue

        ruta_grabacion = os.path.join(
            CARPETA_GRABACIONES,
            grabacion
        )

        ruta_timeline = os.path.join(
            ruta_grabacion,
            "timeline.json"
        )

        if not os.path.exists(
            ruta_timeline
        ):

            print(
                "[ZIG ZAG] "
                "No existe timeline:"
            )

            print(
                ruta_timeline
            )

            continue

        estados.append({
            "asignacion": asignacion,
            "grabacion": grabacion,
            "ventana": ventana,
            "variables_escritura": variables_escritura,
            "ruta_timeline": ruta_timeline,
            "indice": 0,
            "pantalla": 1,
            "activa": True
        })

    if not estados:

        print(
            "[ZIG ZAG] "
            "No existen asignaciones válidas."
        )

        finalizar_reproduccion()

        return

    print()

    print(
        "[ZIG ZAG] "
        f"Asignaciones: {len(estados)}"
    )

    print(
        "[ZIG ZAG] "
        "REPRODUCCIÓN POR PANTALLAS"
    )

    # ========================================================
    # RONDAS ZIG ZAG
    # ========================================================

    while any(
        estado["activa"]
        for estado in estados
    ):

        if reproduccion_fue_detenida():
            break

        for estado in estados:

            if reproduccion_fue_detenida():
                break

            if not estado["activa"]:
                continue

            asignacion = estado[
                "asignacion"
            ]

            # =================================================
            # LA ASIGNACIÓN PUEDE HABER SIDO ELIMINADA
            # DURANTE UNA PAUSA
            # =================================================

            if not asignacion_sigue_existiendo(
                asignacion
            ):

                print(
                    "[ZIG ZAG] "
                    "Asignación eliminada. "
                    "Se omite."
                )

                estado["activa"] = False

                continue

            ventana = estado[
                "ventana"
            ]

            proceso = ventana.get(
                "proceso",
                "Desconocida"
            )

            print()

            print(
                f"[ZIG ZAG] *** {proceso} ***"
            )

            print(
                f"<<<<<<<<<<<<<<<<<<<< PANTALLA "
                f"{estado['pantalla']} "
                f">>>>>>>>>>>>>>>>>>>>"
            )

            resultado = reproducir_timeline(
                estado["ruta_timeline"],
                ventana,
                estado["variables_escritura"],
                indice_inicio=estado["indice"],
                detener_al_avanzar=True,
                pantalla_inicio=estado["pantalla"],
                gestionar_reproduccion=False
            )

            if reproduccion_fue_detenida():
                break

            if not isinstance(
                resultado,
                dict
            ):

                estado["activa"] = False

                continue

            # =================================================
            # TIMELINE COMPLETADA
            # =================================================

            if resultado.get(
                "completada"
            ):

                estado["activa"] = False

                print(
                    f"[ZIG ZAG] "
                    f"{proceso} completada."
                )

                continue

            # =================================================
            # AVANCE CONFIRMADO:
            # GUARDAR PUNTO Y CEDER TURNO
            # =================================================

            if resultado.get(
                "avance_confirmado"
            ):

                estado["indice"] = (
                    resultado.get(
                        "siguiente_indice",
                        estado["indice"]
                    )
                )

                estado["pantalla"] += 1

                continue

            # =================================================
            # TERMINÓ SIN AVANCE NI FINAL NORMAL
            # Ejemplo: descalificación
            # =================================================

            estado["activa"] = False

            print(
                f"[ZIG ZAG] "
                f"{proceso} salió de la ronda."
            )

            time.sleep(
                0.15
            )

    establecer_ventana_reproduccion(
        None
    )

    finalizar_reproduccion()

    print()

    if reproduccion_fue_detenida():

        print(
            "[AUTOMATA] "
            "LOTE DE REPRODUCCIÓN DETENIDO"
        )

        reproducir(
            "reproducciondetenidaporelusuario"
        )

        mostrar_espejo_desactivado()

    else:

        print(
            "[ZIG ZAG] "
            "LOTE DE REPRODUCCIÓN TERMINADO"
        )

        time.sleep(
            0.4
        )

        reproducir(
            "todaslasasignacionesfueroncompletadas"
        )

        mostrar_espejo_desactivado()

def _reproducir_asignaciones(asignaciones):

    preparar_lote_reproduccion()

    total = len(
        asignaciones
    )

    print()

    print(
        "[AUTOMATA] "
        f"Asignaciones a reproducir: {total}"
    )

    for indice, asignacion in enumerate(
        asignaciones,
        1
    ):

        if reproduccion_fue_detenida():
            break
        
        # ====================================================
        # COMPROBAR QUE LA ASIGNACIÓN SIGUE EXISTIENDO
        # ====================================================

        if not asignacion_sigue_existiendo(
            asignacion
        ):

            print(
                "[AUTOMATA] "
                "Asignación eliminada durante la reproducción. "
                "Se omite."
            )

            continue

        grabacion = asignacion.get(
            "grabacion"
        )

        ventana = asignacion.get(
            "ventana"
        )

        variables_escritura = asignacion.get(
            "variables_escritura",
            {}
        )

        if (
            not grabacion
            or ventana is None
        ):

            print(
                "[AUTOMATA] "
                "Asignación inválida."
            )

            continue

        ruta_grabacion = os.path.join(
            CARPETA_GRABACIONES,
            grabacion
        )

        ruta_timeline = os.path.join(
            ruta_grabacion,
            "timeline.json"
        )

        if not os.path.exists(
            ruta_timeline
        ):

            print()
            print(
                "[AUTOMATA] "
                "No existe timeline:"
            )

            print(
                ruta_timeline
            )

            continue

        print()

        print(
            f"[AUTOMATA] "
            f"Asignación {indice}/{total}"
        )

        print(
            f"Grabación: "
            f"{grabacion}"
        )

        print(
            f"Esclava: "
            f"{ventana.get('proceso', 'Desconocida')}"
        )

        resultado = reproducir_timeline(
            ruta_timeline,
            ventana,
            variables_escritura
        )

        if reproduccion_fue_detenida():

            debug(
                "[AUTOMATA] "
                "Lote detenido por el usuario."
            )

            break

        # ----------------------------------------------------
        # La timeline puede terminar normalmente
        # o por descalificación.
        #
        # En ambos casos pasamos a la siguiente asignación.
        # ----------------------------------------------------

        if resultado:

            debug(
                "[AUTOMATA] "
                "Asignación completada."
            )

        else:

            debug(
                "[AUTOMATA] "
                "Asignación terminada "
                "sin completar."
            )

        time.sleep(
            0.15
        )

    print()

    if reproduccion_fue_detenida():

        print(
            "[AUTOMATA] "
            "LOTE DE REPRODUCCIÓN DETENIDO"
        )

        reproducir("reproducciondetenidaporelusuario")

        mostrar_espejo_desactivado()

    else:

        print(
            "[AUTOMATA] "
            "LOTE DE REPRODUCCIÓN TERMINADO"
        )

        time.sleep(0.4)

        reproducir("todaslasasignacionesfueroncompletadas")

        mostrar_espejo_desactivado()


