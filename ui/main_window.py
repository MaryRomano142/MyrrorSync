import tkinter as tk
import ttkbootstrap as ttk
import pywinstyles
import customtkinter as ctk
import threading
import time
import json
import win32console
import win32gui
import importlib
import config
import pyautogui
import os
import sys

from core.notificaciones import (
    cambiar_estado_notificaciones,
    enviar_notificacion
)

from core.debug import debug

from ui.mouse_coords import iniciar_visor_coordenadas

from tkinter import simpledialog
from tkinter import messagebox

from automata.storage import (
    guardar_grabacion_permanente,
    listar_grabaciones,
    descartar_grabacion_temporal,
    eliminar_grabacion,
    MAX_GRABACIONES,
    CARPETA_GRABACIONES
)

from automata.ui_bridge import (
    obtener_solicitud_ui
)

from automata.asignaciones import (
    obtener_asignaciones,
    agregar_asignacion,
    eliminar_asignacion,
    limpiar_asignaciones,
    MAX_ASIGNACIONES
)

from automata.manager_automata import (
    automata_reproduciendo,
    obtener_ventana_reproduccion,
    modo_zig_zag_esta_activo,
    cambiar_estado_zig_zag
)

from core.layout_manager import (
    guardar_distribucion,
    restaurar_distribucion
)

from datetime import datetime, timedelta

from ttkbootstrap.constants import *

from windows.window_manager import obtener_ventanas
from core.event_listener import iniciar_listener

from core.mirror import (
    iniciar_motor,
    obtener_maestra,
    obtener_esclavas,
    establecer_maestra,
    establecer_esclavas,
    limpiar_sesion,
    desactivar_espejo,
    cambiar_estado_anticeros,
    escritura_teclado_esta_activa,
    cambiar_estado_escritura_teclado
)

from core.sound import (
    sonido_disponible,
    reproducir,
    cambiar_modo_silencioso
)

from ui.ui_state import estado

from config import (
    BLOCK_SECCIONES_AFIRMACION_X_INICIO,
    BLOCK_SECCIONES_AFIRMACION_X_FIN,
    BLOCK_SECCIONES_AFIRMACION_Y_INICIO,
    BLOCK_SECCIONES_AFIRMACION_Y_FIN,
    BLOCK_SECCIONES_OPCIONES_X_INICIO,
    BLOCK_SECCIONES_OPCIONES_X_FIN,
    BLOCK_SECCIONES_OPCIONES_Y_INICIO,
    BLOCK_SECCIONES_OPCIONES_Y_FIN,
    BLOCK_SECCIONES_OPCION_ANCHO,
    BLOCK_SECCIONES_OPCION_ALTO
)

from block_vertical.manager_blockvertical import (
    guardar_config_block_vertical
)

from block_secciones.manager_secciones import (
    guardar_config_secciones,
    capturar_snapshot_limpio_seccion
)

from block_secciones.capture_state import (
    MODO_NORMAL as BS_MODO_NORMAL,
    MODO_REFORZADO as BS_MODO_REFORZADO,
    establecer_modo as establecer_modo_block_secciones
)

from capturador.manager_capturador import (
    guardar_config_capturador,
    capturar_snapshot_limpio_capturador
)

from ui.timeline_editor_window import (
    abrir_editor_timeline
)

from ui.configurar_asignaciones_window import (
    abrir_configurar_asignaciones,
    obtener_variables_grabacion
)

from capturador.capture_state import (
    MODO_NORMAL,
    MODO_REFORZADO,
    establecer_modo,
    obtener_modo,
    cambiar_arrastre_inteligente,
    arrastre_inteligente_activo
)

from block_vertical.capture_state import (
    MODO_NORMAL as BLOCK_MODO_NORMAL,
    MODO_REFORZADO as BLOCK_MODO_REFORZADO,
    establecer_modo as establecer_modo_block,
    obtener_modo as obtener_modo_block
)

# ---------------- VARIABLES ----------------

ventanas_detectadas = []
maestra = None
esclavas = []
borde_superior = None
borde_inferior = None
borde_izquierdo = None
borde_derecho = None
temporizador_1 = None
temporizador_2 = None
mostrar_calibracion_block_vertical = False
borde_superior_block_vertical = None
borde_inferior_block_vertical = None
borde_izquierdo_block_vertical = None
borde_derecho_block_vertical = None
mostrar_calibracion_block_secciones = False
borde_superior_afirmacion_secciones = None
borde_inferior_afirmacion_secciones = None
borde_izquierdo_afirmacion_secciones = None
borde_derecho_afirmacion_secciones = None
borde_superior_opcion_secciones = None
borde_inferior_opcion_secciones = None
borde_izquierdo_opcion_secciones = None
borde_derecho_opcion_secciones = None
borde_superior_opciones_secciones = None
borde_inferior_opciones_secciones = None
borde_izquierdo_opciones_secciones = None
borde_derecho_opciones_secciones = None
flecha_presionada = False
funcion_flecha_actual = None
mostrar_calibracion_capturador = False
borde_superior_capturador = None
borde_inferior_capturador = None
borde_izquierdo_capturador = None
borde_derecho_capturador = None
borde_superior_opcion_capturador = None
borde_inferior_opcion_capturador = None
borde_izquierdo_opcion_capturador = None
borde_derecho_opcion_capturador = None
grabacion_cargada = None

# ---------------- FUNCIONES ----------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 5
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="lightyellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def actualizar():

    global ventanas_detectadas

    lista.delete(0, tk.END)

    ventanas_detectadas = obtener_ventanas()

    for ventana in ventanas_detectadas:

        lista.insert(
            tk.END,
            ventana["proceso"]
        )

        indice = lista.size() - 1

        lista.itemconfig(
            indice,
            fg=ventana["color"]
        )

def elegir_maestra():

    global maestra

    seleccion = lista.curselection()

    if not seleccion:
        return

    indice = seleccion[0]

    maestra = ventanas_detectadas[indice]

    establecer_maestra(maestra)

    lbl_maestra.config(

        text=maestra["proceso"],

        foreground=maestra["color"]

    )

def actualizar_esclavas():

    lista_esclavas.delete(0, tk.END)

    for ventana in esclavas:

        lista_esclavas.insert(
            tk.END,
            ventana["proceso"]
        )

        indice = lista_esclavas.size() - 1

        lista_esclavas.itemconfig(

            indice,

            fg=ventana["color"]

        )

def agregar_esclava():

    seleccion = lista.curselection()

    if not seleccion:
        return

    indice = seleccion[0]

    ventana = ventanas_detectadas[indice]

    if maestra and ventana["hwnd"] == maestra["hwnd"]:
        return

    for v in esclavas:
        if v["hwnd"] == ventana["hwnd"]:
            return

    if len(esclavas) >= 10: #Trabajar hasta con 10 esclavas
        return

    esclavas.append(ventana)

    establecer_esclavas(esclavas)

    actualizar_esclavas()

    print(
        f"Maestra: {'Sí' if maestra else 'No'}"
    )

    print(
        f"Esclavas: {len(esclavas)}"
    )

def guardar_distribucion_actual():

    guardar_distribucion(

        maestra,

        esclavas[0] if len(esclavas) > 0 else None,

        esclavas[1] if len(esclavas) > 1 else None,

        esclavas[2] if len(esclavas) > 2 else None,

        esclavas[3] if len(esclavas) > 3 else None,

        esclavas[4] if len(esclavas) > 4 else None,

        esclavas[5] if len(esclavas) > 5 else None,

        esclavas[6] if len(esclavas) > 6 else None,

        esclavas[7] if len(esclavas) > 7 else None,

        esclavas[8] if len(esclavas) > 8 else None,

        esclavas[9] if len(esclavas) > 9 else None

    )

    print("Distribución guardada correctamente.")

def restaurar_distribucion_actual():

    restaurar_distribucion(

        maestra,

        esclavas[0] if len(esclavas) > 0 else None,

        esclavas[1] if len(esclavas) > 1 else None,

        esclavas[2] if len(esclavas) > 2 else None,

        esclavas[3] if len(esclavas) > 3 else None,

        esclavas[4] if len(esclavas) > 4 else None,

        esclavas[5] if len(esclavas) > 5 else None,

        esclavas[6] if len(esclavas) > 6 else None,

        esclavas[7] if len(esclavas) > 7 else None,

        esclavas[8] if len(esclavas) > 8 else None,

        esclavas[9] if len(esclavas) > 9 else None

    )

    print("Distribución restaurada.")

def restaurar_distribucion_1_maestra_1_esclava():

    restaurar_distribucion(
        maestra,
        esclavas[0] if len(esclavas) > 0 else None,
        nombre="distr2venGrab.json"
    )

    print(
        "Distribución restaurada."
    )

def restaurar_distribucion_full_esclavas():

    restaurar_distribucion(
        maestra,
        esclavas[0] if len(esclavas) > 0 else None,
        esclavas[1] if len(esclavas) > 1 else None,
        esclavas[2] if len(esclavas) > 2 else None,
        esclavas[3] if len(esclavas) > 3 else None,
        esclavas[4] if len(esclavas) > 4 else None,
        esclavas[5] if len(esclavas) > 5 else None,
        esclavas[6] if len(esclavas) > 6 else None,
        esclavas[7] if len(esclavas) > 7 else None,
        esclavas[8] if len(esclavas) > 8 else None,
        esclavas[9] if len(esclavas) > 9 else None,
        nombre="distrfullescRepr.json"
    )

    print(
        "Distribución restaurada."
    )

def restaurar_consola():

    hwnd = win32console.GetConsoleWindow()

    time.sleep(0.2)

    with open('data/consola.json', 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    win32gui.MoveWindow(
        hwnd,
        cfg['x'],
        cfg['y'],
        cfg['ancho'],
        cfg['alto'],
        True
    )

    print('Consola posicionada.')

def actualizar_hora():

    ahora = datetime.now()

    hora_label.config(
        text=ahora.strftime("%H:%M:%S")
    )

    verificar_temporizadores(ahora)

    app.after(1000, actualizar_hora)

def iniciar_app():

    actualizar()

    actualizar_grabaciones()

    iniciar_motor()

    iniciar_listener()

    iniciar_visor_coordenadas(
        app
    )

    actualizar_hora()

    restaurar_consola()

    # ========================================================
    # ESCUCHAR SOLICITUDES DEL AUTÓMATA
    # ========================================================

    app.after(
        100,
        procesar_solicitudes_automata
    )

    app.mainloop()

def cmd_cambiar_modo_silencioso(event=None):

    activo = cambiar_modo_silencioso()

    if activo:

        lbl_modo_silencioso.configure(
            text="🔈",
            foreground="white"
        )

    else:

        lbl_modo_silencioso.configure(
            text="🔊",
            foreground="cyan"
        )

def cmd_cambiar_notificaciones():

    activas = cambiar_estado_notificaciones()

    if activas:

        btn_notificaciones.configure(
            fg_color="lime",
            text_color="black"
        )

        lbl_notificaciones_emojis.configure(
            text="🔔✔📱",
            font=("Segoe UI Emoji", 14, "normal"),
            foreground="lime"
        )

        reproducir("seenviaranasnotificacionesalcelular")

        enviar_notificacion(
            mensaje="Notificaciones activadas.",
            titulo="MirrorSync",
            prioridad="urgent"
        )

    else:

        btn_notificaciones.configure(
            fg_color="red",
            text_color="white"
        )

        lbl_notificaciones_emojis.configure(
            text="🔔🚫📱",
            font=("Segoe UI Emoji", 14, "normal"),
            foreground="red"
        )

def nueva_sesion():

    global maestra
    global esclavas
    global grabacion_cargada

    # ========================================================
    # LIMPIAR ESTADOS INTERNOS
    # ========================================================

    limpiar_sesion()

    limpiar_asignaciones()

    actualizar_asignaciones()

    establecer_maestra(
        None
    )

    establecer_esclavas(
        []
    )

    maestra = None

    esclavas.clear()

    grabacion_cargada = None

    # ========================================================
    # LIMPIAR INTERFAZ
    # ========================================================

    lbl_maestra.config(
        text="Ninguna"
    )

    lbl_grabacion_cargada.config(
        text="Ninguna"
    )

    lista_esclavas.delete(
        0,
        tk.END
    )

    lista_asignaciones.delete(
        0,
        tk.END
    )

    lista_grabaciones.delete(
        0,
        tk.END
    )

    lista.selection_clear(
        0,
        tk.END
    )

    # ========================================================
    # SOLO VOLVER A DETECTAR VENTANAS
    # ========================================================

    actualizar()

    actualizar_grabaciones()

    print(
        "Nueva sesión lista."
    )

    reproducir(
        "nuevo"
    )

def reiniciar_mirrorsync():

    print()
    print("Reiniciando MirrorSync...")

    time.sleep(0.2)

    # Obtener el script principal
    ruta_main = os.path.abspath(
        sys.argv[0]
    )

    carpeta_proyecto = os.path.dirname(
        ruta_main
    )

    # Asegurar que volvemos a la raíz
    # del proyecto.
    os.chdir(
        carpeta_proyecto
    )

    # Limpiar consola
    os.system(
        "cls"
        if os.name == "nt"
        else "clear"
    )

    # Reiniciar usando EL MISMO Python
    # que está ejecutando MirrorSync.
    os.execv(
        sys.executable,
        [
            sys.executable,
            ruta_main,
            *sys.argv[1:]
        ]
    )

def enviar_al_fondo():

    app.lower()

    app.after(50, lambda: app.attributes("-topmost", False))

def traer_al_frente():

    app.lift()

    app.focus_force()

def procesar_solicitudes_automata():

    while True:

        solicitud = (
            obtener_solicitud_ui()
        )

        if solicitud is None:
            break

        if solicitud == "guardar_grabacion":

            pedir_nombre_grabacion()

    # Volver a revisar la cola
    # dentro de 100 ms.
    app.after(
        100,
        procesar_solicitudes_automata
    )

def crear_borde(color):

    ventana = tk.Toplevel(app)

    ventana.overrideredirect(True)

    ventana.attributes("-topmost", True)

    ventana.configure(bg=color)

    return ventana

#VISORES DEL MODO CAPTURADOR
def cmd_mostrar_calibracion_capturador():

    enviar_al_fondo()

    global mostrar_calibracion_capturador

    mostrar_calibracion_capturador = (
        not mostrar_calibracion_capturador
    )

    if mostrar_calibracion_capturador:
        mostrar_rectangulos_capturador()
    else:
        ocultar_rectangulos_capturador()

def mostrar_rectangulos_capturador():

    global borde_superior_capturador
    global borde_inferior_capturador
    global borde_izquierdo_capturador
    global borde_derecho_capturador

    global borde_superior_opcion_capturador
    global borde_inferior_opcion_capturador
    global borde_izquierdo_opcion_capturador
    global borde_derecho_opcion_capturador

    # Verde
    borde_superior_capturador = crear_borde("lime")
    borde_inferior_capturador = crear_borde("lime")
    borde_izquierdo_capturador = crear_borde("lime")
    borde_derecho_capturador = crear_borde("lime")

    # Magenta
    borde_superior_opcion_capturador = crear_borde("#FF00FF")
    borde_inferior_opcion_capturador = crear_borde("#FF00FF")
    borde_izquierdo_opcion_capturador = crear_borde("#FF00FF")
    borde_derecho_opcion_capturador = crear_borde("#FF00FF")

    actualizar_rectangulos_capturador()
    seguir_mouse_capturador()

def actualizar_rectangulos_capturador():

    maestra = obtener_maestra()

    if maestra is None:
        return

    izquierda, arriba, _, _ = win32gui.GetWindowRect(
        maestra["hwnd"]
    )

    # ============================
    # VERDE
    # ============================

    x1 = (
        izquierda
        + config.CAPTURADOR_OPCIONES_X_INICIO
    )

    x2 = (
        izquierda
        + config.CAPTURADOR_OPCIONES_X_FIN
    )

    y1 = (
        arriba
        + config.CAPTURADOR_OPCIONES_Y_INICIO
    )

    y2 = (
        arriba
        + config.CAPTURADOR_OPCIONES_Y_FIN
    )

    ancho = max(1, x2 - x1)
    alto = max(1, y2 - y1)

    borde_superior_capturador.geometry(
        f"{ancho}x1+{x1}+{y1}"
    )

    borde_inferior_capturador.geometry(
        f"{ancho}x1+{x1}+{y2}"
    )

    borde_izquierdo_capturador.geometry(
        f"1x{alto}+{x1}+{y1}"
    )

    borde_derecho_capturador.geometry(
        f"1x{alto}+{x2}+{y1}"
    )

    # ============================
    # MAGENTA
    # ============================

    mouse_x, mouse_y = pyautogui.position()

    ancho_opcion = config.CAPTURADOR_OPCION_ANCHO
    alto_opcion = config.CAPTURADOR_OPCION_ALTO

    offset_x = config.CAPTURADOR_OPCION_OFFSET_X
    offset_y = config.CAPTURADOR_OPCION_OFFSET_Y

    centro_x = mouse_x + offset_x
    centro_y = mouse_y + offset_y

    opcion_x1 = centro_x - ancho_opcion // 2
    opcion_y1 = centro_y - alto_opcion // 2

    opcion_x2 = opcion_x1 + ancho_opcion
    opcion_y2 = opcion_y1 + alto_opcion

    borde_superior_opcion_capturador.geometry(
        f"{ancho_opcion}x1+{opcion_x1}+{opcion_y1}"
    )

    borde_inferior_opcion_capturador.geometry(
        f"{ancho_opcion}x1+{opcion_x1}+{opcion_y2}"
    )

    borde_izquierdo_opcion_capturador.geometry(
        f"1x{alto_opcion}+{opcion_x1}+{opcion_y1}"
    )

    borde_derecho_opcion_capturador.geometry(
        f"1x{alto_opcion}+{opcion_x2}+{opcion_y1}"
    )

def ocultar_rectangulos_capturador():

    global borde_superior_capturador
    global borde_inferior_capturador
    global borde_izquierdo_capturador
    global borde_derecho_capturador

    global borde_superior_opcion_capturador
    global borde_inferior_opcion_capturador
    global borde_izquierdo_opcion_capturador
    global borde_derecho_opcion_capturador

    bordes = (

        # OPCIÓN ELEGIDA
        borde_superior_capturador,
        borde_inferior_capturador,
        borde_izquierdo_capturador,
        borde_derecho_capturador,

        # OPCIONES DISPONIBLES
        borde_superior_opcion_capturador,
        borde_inferior_opcion_capturador,
        borde_izquierdo_opcion_capturador,
        borde_derecho_opcion_capturador
    )

    for borde in bordes:

        if borde is not None:
            borde.destroy()

    borde_superior_capturador = None
    borde_inferior_capturador = None
    borde_izquierdo_capturador = None
    borde_derecho_capturador = None

    borde_superior_opcion_capturador = None
    borde_inferior_opcion_capturador = None
    borde_izquierdo_opcion_capturador = None
    borde_derecho_opcion_capturador = None

def guardar_calibracion_capturador():

    reproducir("snapshot")

    enviar_al_fondo()

    guardar_config_capturador()

    importlib.reload(
        config
    )

    maestra = obtener_maestra()

    if maestra is None:

        print(
            "[CAPTURADOR] "
            "No hay maestra seleccionada."
        )

        return

    hwnd = maestra["hwnd"]

    snapshot_ok = (
        capturar_snapshot_limpio_capturador(
            hwnd
        )
    )

    if not snapshot_ok:

        print(
            "[CAPTURADOR] "
            "No se pudo guardar "
            "el snapshot limpio."
        )

        return

    debug(
        "Calibración CAPTURADOR guardada."
    )
    
def seguir_mouse_capturador():

    if not mostrar_calibracion_capturador:
        return

    actualizar_rectangulos_capturador()

    app.after(
        20,
        seguir_mouse_capturador
    )

def seleccionar_captura_normal():

    enviar_al_fondo()

    reproducir("capturanormalactivada")

    establecer_modo(
        MODO_NORMAL
    )

    btn_captura_normal.configure(
        fg_color="lime",
        text_color="black"
    )

    btn_captura_reforzada.configure(
        fg_color="#333333",
        text_color="white"
    )

def seleccionar_captura_reforzada():

    enviar_al_fondo()

    reproducir("capturareforzadaactivada")

    establecer_modo(
        MODO_REFORZADO
    )

    btn_captura_normal.configure(
        fg_color="#333333",
        text_color="white"
    )

    btn_captura_reforzada.configure(
        fg_color="magenta",
        text_color="black"
    )

def seleccionar_arrastre_inteligente():

    enviar_al_fondo()

    cambiar_arrastre_inteligente()

    if arrastre_inteligente_activo():

        btn_arrastre_inteligente.configure(
            fg_color="#D29BFD",
            text_color="black"
        )

    else:

        btn_arrastre_inteligente.configure(
            fg_color="#333333",
            text_color="white"
        )

#capturador: region de opciones
def capturador_x_inicio_menos(event=None):

    config.CAPTURADOR_OPCIONES_X_INICIO -= 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_x_inicio_mas(event=None):

    config.CAPTURADOR_OPCIONES_X_INICIO += 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_x_fin_menos(event=None):

    config.CAPTURADOR_OPCIONES_X_FIN -= 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_x_fin_mas(event=None):

    config.CAPTURADOR_OPCIONES_X_FIN += 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_y_inicio_menos(event=None):

    config.CAPTURADOR_OPCIONES_Y_INICIO -= 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_y_inicio_mas(event=None):

    config.CAPTURADOR_OPCIONES_Y_INICIO += 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_y_fin_menos(event=None):

    config.CAPTURADOR_OPCIONES_Y_FIN -= 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_y_fin_mas(event=None):

    config.CAPTURADOR_OPCIONES_Y_FIN += 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_arriba(event=None):

    config.CAPTURADOR_OPCIONES_Y_INICIO -= 5
    config.CAPTURADOR_OPCIONES_Y_FIN -= 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

def capturador_abajo(event=None):

    config.CAPTURADOR_OPCIONES_Y_INICIO += 5
    config.CAPTURADOR_OPCIONES_Y_FIN += 5
    actualizar_rectangulos_capturador()
    enviar_al_fondo()

#capturador: rectangulo del mouse
def capturador_ancho_menos(event=None):

    config.CAPTURADOR_OPCION_ANCHO = max(
        20,
        config.CAPTURADOR_OPCION_ANCHO - 5
    )

    actualizar_rectangulos_capturador()

def capturador_ancho_mas(event=None):

    config.CAPTURADOR_OPCION_ANCHO += 5

    actualizar_rectangulos_capturador()

def capturador_alto_menos(event=None):

    config.CAPTURADOR_OPCION_ALTO = max(
        20,
        config.CAPTURADOR_OPCION_ALTO - 5
    )

    actualizar_rectangulos_capturador()

def capturador_alto_mas(event=None):

    config.CAPTURADOR_OPCION_ALTO += 5

    actualizar_rectangulos_capturador()

def capturador_offset_x_menos(event=None):

    config.CAPTURADOR_OPCION_OFFSET_X -= 5

    actualizar_rectangulos_capturador()

def capturador_offset_x_mas(event=None):

    config.CAPTURADOR_OPCION_OFFSET_X += 5

    actualizar_rectangulos_capturador()

#VISOR BLOCK VERTICAL
def block_vertical_aceptar_mas_pequenos(event=None):

    enviar_al_fondo()

    config.BLOCK_VERTICAL_AJUSTE_PEQUENOS += 1

    print(
        "[BLOCK VERTICAL] "
        "Ajuste pequeños: "
        f"{config.BLOCK_VERTICAL_AJUSTE_PEQUENOS}"
    )

def block_vertical_aceptar_mas_grandes(event=None):

    enviar_al_fondo()

    config.BLOCK_VERTICAL_AJUSTE_GRANDES += 1

    print(
        "[BLOCK VERTICAL] "
        "Ajuste grandes: "
        f"{config.BLOCK_VERTICAL_AJUSTE_GRANDES}"
    )

def block_vertical_reducir_pequenos(event=None):

    enviar_al_fondo()

    config.BLOCK_VERTICAL_AJUSTE_PEQUENOS = max(
        0,
        config.BLOCK_VERTICAL_AJUSTE_PEQUENOS - 1
    )

    print(
        "[BLOCK VERTICAL] "
        "Ajuste pequeños: "
        f"{config.BLOCK_VERTICAL_AJUSTE_PEQUENOS}"
    )


def block_vertical_reducir_grandes(event=None):

    enviar_al_fondo()

    config.BLOCK_VERTICAL_AJUSTE_GRANDES = max(
        0,
        config.BLOCK_VERTICAL_AJUSTE_GRANDES - 1
    )

    print(
        "[BLOCK VERTICAL] "
        "Ajuste grandes: "
        f"{config.BLOCK_VERTICAL_AJUSTE_GRANDES}"
    )

def cmd_mostrar_calibracion_block_vertical():

    enviar_al_fondo()

    global mostrar_calibracion_block_vertical

    mostrar_calibracion_block_vertical = (
        not mostrar_calibracion_block_vertical
    )

    if mostrar_calibracion_block_vertical:

        mostrar_rectangulo_block_vertical()

    else:

        ocultar_rectangulo_block_vertical()

def mostrar_rectangulo_block_vertical():

    global borde_superior_block_vertical
    global borde_inferior_block_vertical
    global borde_izquierdo_block_vertical
    global borde_derecho_block_vertical

    borde_superior_block_vertical = crear_borde("#E7D40A")
    borde_inferior_block_vertical = crear_borde("#E7D40A")
    borde_izquierdo_block_vertical = crear_borde("#E7D40A")
    borde_derecho_block_vertical = crear_borde("#E7D40A")

    actualizar_rectangulo_block_vertical()

def actualizar_rectangulo_block_vertical():

    global borde_superior_block_vertical
    global borde_inferior_block_vertical
    global borde_izquierdo_block_vertical
    global borde_derecho_block_vertical

    maestra = obtener_maestra()

    ventana_objetivo = None

    # ========================================================
    # DURANTE REPRODUCCIÓN
    # usar EXACTAMENTE la esclava que reproduce el Autómata
    # ========================================================

    if automata_reproduciendo():

        ventana_objetivo = (
            obtener_ventana_reproduccion()
        )

    # ========================================================
    # FUERA DE REPRODUCCIÓN
    # usar la maestra como siempre
    # ========================================================

    else:

        ventana_objetivo = maestra

    # ========================================================
    # VALIDACIÓN
    # ========================================================

    if ventana_objetivo is None:

        print(
            "No hay ventana válida para Block Vertical."
        )

        return

    hwnd = ventana_objetivo["hwnd"]

    izquierda, arriba, derecha, abajo = (
        win32gui.GetWindowRect(hwnd)
    )

    x1 = (
        izquierda +
        config.BLOCK_VERTICAL_X_INICIO
    )

    x2 = (
        izquierda +
        config.BLOCK_VERTICAL_X_FIN
    )

    y1 = (
        arriba +
        config.BLOCK_VERTICAL_Y_INICIO
    )

    y2 = (
        arriba +
        config.BLOCK_VERTICAL_Y_FIN
    )

    ancho = max(1, x2 - x1)
    alto = max(1, y2 - y1)

    borde_superior_block_vertical.geometry(
        f"{ancho}x1+{x1}+{y1}"
    )

    borde_inferior_block_vertical.geometry(
        f"{ancho}x1+{x1}+{y2}"
    )

    borde_izquierdo_block_vertical.geometry(
        f"1x{alto}+{x1}+{y1}"
    )

    borde_derecho_block_vertical.geometry(
        f"1x{alto}+{x2}+{y1}"
    )

def ocultar_rectangulo_block_vertical():

    global borde_superior_block_vertical
    global borde_inferior_block_vertical
    global borde_izquierdo_block_vertical
    global borde_derecho_block_vertical

    for borde in (
        borde_superior_block_vertical,
        borde_inferior_block_vertical,
        borde_izquierdo_block_vertical,
        borde_derecho_block_vertical
    ):

        if borde is not None:

            borde.destroy()

    borde_superior_block_vertical = None
    borde_inferior_block_vertical = None
    borde_izquierdo_block_vertical = None
    borde_derecho_block_vertical = None

def guardar_calibracion_block_vertical():

    enviar_al_fondo()

    guardar_config_block_vertical()

    importlib.reload(config)

    print("Calibración BLOCK VERTICAL guardada.")

def block_vertical_x_menos(event=None):

    config.BLOCK_VERTICAL_X_INICIO -= 5
    config.BLOCK_VERTICAL_X_FIN -= 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_x_mas(event=None):

    config.BLOCK_VERTICAL_X_INICIO += 5
    config.BLOCK_VERTICAL_X_FIN += 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_x_inicio_menos(event=None):

    config.BLOCK_VERTICAL_X_INICIO -= 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_x_inicio_mas(event=None):

    config.BLOCK_VERTICAL_X_INICIO += 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_x_fin_menos(event=None):

    config.BLOCK_VERTICAL_X_FIN -= 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_x_fin_mas(event=None):

    config.BLOCK_VERTICAL_X_FIN += 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_y_inicio_menos(event=None):

    config.BLOCK_VERTICAL_Y_INICIO -= 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_y_inicio_mas(event=None):

    config.BLOCK_VERTICAL_Y_INICIO += 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_y_fin_menos(event=None):

    config.BLOCK_VERTICAL_Y_FIN -= 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def block_vertical_y_fin_mas(event=None):

    config.BLOCK_VERTICAL_Y_FIN += 5

    actualizar_rectangulo_block_vertical()
    enviar_al_fondo()

def seleccionar_block_normal():

    enviar_al_fondo()

    reproducir("capturanormalactivada")

    establecer_modo_block(
        BLOCK_MODO_NORMAL
    )

    btn_block_normal.configure(
        fg_color="lime",
        text_color="black"
    )

    btn_block_reforzado.configure(
        fg_color="#333333",
        text_color="white"
    )

def seleccionar_block_reforzado():

    enviar_al_fondo()

    reproducir("capturareforzadaactivada")

    establecer_modo_block(
        BLOCK_MODO_REFORZADO
    )

    btn_block_normal.configure(
        fg_color="#333333",
        text_color="white"
    )

    btn_block_reforzado.configure(
        fg_color="magenta",
        text_color="black"
    )

def seleccionar_block_secciones_normal():

    enviar_al_fondo()

    reproducir("capturanormalactivada")

    establecer_modo_block_secciones(
        BS_MODO_NORMAL
    )

    btn_block_secciones_normal.configure(
        fg_color="lime",
        text_color="black"
    )

    btn_block_secciones_reforzado.configure(
        fg_color="#333333",
        text_color="white"
    )

def seleccionar_block_secciones_reforzado():

    enviar_al_fondo()

    reproducir("capturareforzadaactivada")

    establecer_modo_block_secciones(
        BS_MODO_REFORZADO
    )

    btn_block_secciones_normal.configure(
        fg_color="#333333",
        text_color="white"
    )

    btn_block_secciones_reforzado.configure(
        fg_color="magenta",
        text_color="black"
    )

# VISOR BLOCK SECCIONES
def cmd_mostrar_calibracion_block_secciones():

    enviar_al_fondo()

    global mostrar_calibracion_block_secciones

    mostrar_calibracion_block_secciones = (
        not mostrar_calibracion_block_secciones
    )

    if mostrar_calibracion_block_secciones:

        mostrar_rectangulo_block_secciones()

    else:

        ocultar_rectangulo_block_secciones()

def mostrar_rectangulo_block_secciones():

    global borde_superior_afirmacion_secciones
    global borde_inferior_afirmacion_secciones
    global borde_izquierdo_afirmacion_secciones
    global borde_derecho_afirmacion_secciones

    global borde_superior_opciones_secciones
    global borde_inferior_opciones_secciones
    global borde_izquierdo_opciones_secciones
    global borde_derecho_opciones_secciones

    global borde_superior_opcion_secciones
    global borde_inferior_opcion_secciones
    global borde_izquierdo_opcion_secciones
    global borde_derecho_opcion_secciones

    # RECTÁNGULO AFIRMACIÓN

    borde_superior_afirmacion_secciones = crear_borde("cyan")
    borde_inferior_afirmacion_secciones = crear_borde("cyan")
    borde_izquierdo_afirmacion_secciones = crear_borde("cyan")
    borde_derecho_afirmacion_secciones = crear_borde("cyan")

    # RECTÁNGULO REGIÓN DE OPCIONES

    borde_superior_opciones_secciones = crear_borde("#FF7F50")
    borde_inferior_opciones_secciones = crear_borde("#FF7F50")
    borde_izquierdo_opciones_secciones = crear_borde("#FF7F50")
    borde_derecho_opciones_secciones = crear_borde("#FF7F50")

    # RECTÁNGULO OPCIÓN SELECCIONADA

    borde_superior_opcion_secciones = crear_borde("magenta")
    borde_inferior_opcion_secciones = crear_borde("magenta")
    borde_izquierdo_opcion_secciones = crear_borde("magenta")
    borde_derecho_opcion_secciones = crear_borde("magenta")

    actualizar_rectangulo_block_secciones()

    seguir_mouse_block_secciones()

def actualizar_rectangulo_block_secciones():

    maestra = obtener_maestra()

    if maestra is None:
        print("No hay maestra seleccionada.")
        return

    hwnd = maestra["hwnd"]

    izquierda, arriba, derecha, abajo = (
        win32gui.GetWindowRect(hwnd)
    )

    # ==================================================
    # FUNCIÓN PARA DIBUJAR RECTÁNGULOS FIJOS
    # ==================================================

    def dibujar_rectangulo(
        borde_superior,
        borde_inferior,
        borde_izquierdo,
        borde_derecho,
        x_inicio,
        x_fin,
        y_inicio,
        y_fin
    ):

        x1 = izquierda + x_inicio
        x2 = izquierda + x_fin
        y1 = arriba + y_inicio
        y2 = arriba + y_fin

        ancho = max(1, x2 - x1)
        alto = max(1, y2 - y1)

        borde_superior.geometry(
            f"{ancho}x1+{x1}+{y1}"
        )

        borde_inferior.geometry(
            f"{ancho}x1+{x1}+{y2}"
        )

        borde_izquierdo.geometry(
            f"1x{alto}+{x1}+{y1}"
        )

        borde_derecho.geometry(
            f"1x{alto}+{x2}+{y1}"
        )

    # ==================================================
    # 🟦 AFIRMACIÓN
    # ==================================================

    dibujar_rectangulo(

        borde_superior_afirmacion_secciones,
        borde_inferior_afirmacion_secciones,
        borde_izquierdo_afirmacion_secciones,
        borde_derecho_afirmacion_secciones,

        config.BLOCK_SECCIONES_AFIRMACION_X_INICIO,
        config.BLOCK_SECCIONES_AFIRMACION_X_FIN,
        config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO,
        config.BLOCK_SECCIONES_AFIRMACION_Y_FIN
    )

    # ==================================================
    # 🟪 OPCIÓN ELEGIDA — SIGUE AL MOUSE
    # ==================================================

    mouse_x, mouse_y = pyautogui.position()

    opcion_ancho = config.BLOCK_SECCIONES_OPCION_ANCHO
    opcion_alto = config.BLOCK_SECCIONES_OPCION_ALTO

    opcion_x1 = mouse_x - opcion_ancho // 2
    opcion_y1 = mouse_y - opcion_alto // 2

    opcion_x2 = opcion_x1 + opcion_ancho
    opcion_y2 = opcion_y1 + opcion_alto

    borde_superior_opcion_secciones.geometry(
        f"{opcion_ancho}x1+{opcion_x1}+{opcion_y1}"
    )

    borde_inferior_opcion_secciones.geometry(
        f"{opcion_ancho}x1+{opcion_x1}+{opcion_y2}"
    )

    borde_izquierdo_opcion_secciones.geometry(
        f"1x{opcion_alto}+{opcion_x1}+{opcion_y1}"
    )

    borde_derecho_opcion_secciones.geometry(
        f"1x{opcion_alto}+{opcion_x2}+{opcion_y1}"
    )

    # ==================================================
    # 🟨 OPCIONES DISPONIBLES
    # ==================================================

    dibujar_rectangulo(

        borde_superior_opciones_secciones,
        borde_inferior_opciones_secciones,
        borde_izquierdo_opciones_secciones,
        borde_derecho_opciones_secciones,

        config.BLOCK_SECCIONES_OPCIONES_X_INICIO,
        config.BLOCK_SECCIONES_OPCIONES_X_FIN,
        config.BLOCK_SECCIONES_OPCIONES_Y_INICIO,
        config.BLOCK_SECCIONES_OPCIONES_Y_FIN
    )

def ocultar_rectangulo_block_secciones():

    global borde_superior_afirmacion_secciones
    global borde_inferior_afirmacion_secciones
    global borde_izquierdo_afirmacion_secciones
    global borde_derecho_afirmacion_secciones

    global borde_superior_opcion_secciones
    global borde_inferior_opcion_secciones
    global borde_izquierdo_opcion_secciones
    global borde_derecho_opcion_secciones

    global borde_superior_opciones_secciones
    global borde_inferior_opciones_secciones
    global borde_izquierdo_opciones_secciones
    global borde_derecho_opciones_secciones

    bordes = (

        # AFIRMACIÓN
        borde_superior_afirmacion_secciones,
        borde_inferior_afirmacion_secciones,
        borde_izquierdo_afirmacion_secciones,
        borde_derecho_afirmacion_secciones,

        # OPCIÓN ELEGIDA
        borde_superior_opcion_secciones,
        borde_inferior_opcion_secciones,
        borde_izquierdo_opcion_secciones,
        borde_derecho_opcion_secciones,

        # OPCIONES DISPONIBLES
        borde_superior_opciones_secciones,
        borde_inferior_opciones_secciones,
        borde_izquierdo_opciones_secciones,
        borde_derecho_opciones_secciones
    )

    for borde in bordes:

        if borde is not None:
            borde.destroy()

    borde_superior_afirmacion_secciones = None
    borde_inferior_afirmacion_secciones = None
    borde_izquierdo_afirmacion_secciones = None
    borde_derecho_afirmacion_secciones = None

    borde_superior_opcion_secciones = None
    borde_inferior_opcion_secciones = None
    borde_izquierdo_opcion_secciones = None
    borde_derecho_opcion_secciones = None

    borde_superior_opciones_secciones = None
    borde_inferior_opciones_secciones = None
    borde_izquierdo_opciones_secciones = None
    borde_derecho_opciones_secciones = None

def seguir_mouse_block_secciones():

    if not mostrar_calibracion_block_secciones:

        return

    actualizar_rectangulo_block_secciones()

    app.after(
        20,
        seguir_mouse_block_secciones
    )

#VISOR AFIRMACION
def block_secciones_x_inicio_menos(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_X_INICIO -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_x_inicio_mas(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_X_INICIO += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_x_fin_menos(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_X_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_x_fin_mas(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_X_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_y_inicio_menos(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_y_inicio_mas(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_y_fin_menos(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_y_fin_mas(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_afirmacion_arriba(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO -= 5
    config.BLOCK_SECCIONES_AFIRMACION_Y_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_afirmacion_abajo(event=None):

    config.BLOCK_SECCIONES_AFIRMACION_Y_INICIO += 5
    config.BLOCK_SECCIONES_AFIRMACION_Y_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

#REGION OPCIONES
def block_secciones_opciones_x_inicio_menos(event=None):

    config.BLOCK_SECCIONES_OPCIONES_X_INICIO -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_x_inicio_mas(event=None):

    config.BLOCK_SECCIONES_OPCIONES_X_INICIO += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_x_fin_menos(event=None):

    config.BLOCK_SECCIONES_OPCIONES_X_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_x_fin_mas(event=None):

    config.BLOCK_SECCIONES_OPCIONES_X_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_y_inicio_menos(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_INICIO -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_y_inicio_mas(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_INICIO += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_y_fin_menos(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_y_fin_mas(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_mover_arriba(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_INICIO -= 5
    config.BLOCK_SECCIONES_OPCIONES_Y_FIN -= 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

def block_secciones_opciones_mover_abajo(event=None):

    config.BLOCK_SECCIONES_OPCIONES_Y_INICIO += 5
    config.BLOCK_SECCIONES_OPCIONES_Y_FIN += 5
    actualizar_rectangulo_block_secciones()
    enviar_al_fondo()

#OPCION MOUSE
def block_secciones_opcion_ancho_menos(event=None):

    config.BLOCK_SECCIONES_OPCION_ANCHO -= 5

    actualizar_rectangulo_block_secciones()

def block_secciones_opcion_ancho_mas(event=None):

    config.BLOCK_SECCIONES_OPCION_ANCHO += 5

    actualizar_rectangulo_block_secciones()

def block_secciones_opcion_alto_menos(event=None):

    config.BLOCK_SECCIONES_OPCION_ALTO -= 5

    actualizar_rectangulo_block_secciones()

def block_secciones_opcion_alto_mas(event=None):

    config.BLOCK_SECCIONES_OPCION_ALTO += 5

    actualizar_rectangulo_block_secciones()

def guardar_calibracion_block_secciones():

    reproducir("snapshot")

    enviar_al_fondo()

    guardar_config_secciones()

    importlib.reload(config)

    maestra = obtener_maestra()

    if maestra is None:

        print(
            "[BLOCK SECCIONES] "
            "No hay maestra seleccionada."
        )

        return

    hwnd = maestra["hwnd"]

    snapshot_ok = (
        capturar_snapshot_limpio_seccion(
            hwnd
        )
    )

    if not snapshot_ok:

        print(
            "[BLOCK SECCIONES] "
            "No se pudo guardar "
            "el snapshot limpio."
        )

        return

    debug(
        "Calibración BLOCK SECCIONES guardada."
    )

#CONFIGURAR TIEMPO LIMITE CON MINUTOS
def iniciar_temporizador(minutos,numero):

    global temporizador_1
    global temporizador_2

    # ========================================================
    # TEMPORIZADOR 1
    # ========================================================

    if numero == 1:

        # Si ya está activo con ese mismo valor,
        # se cancela.
        if (
            temporizador_1
            and temporizador_1["minutos"] == minutos
        ):

            temporizador_1 = None

            lbl_horario_1.configure(
                text="00:00",
                bootstyle="secondary"
            )

            etiquetas_minutos_1[
                minutos
            ].configure(
                bootstyle="secondary"
            )

            return

        # Si ya tiene otro tiempo activo,
        # lo reemplazamos.
        if temporizador_1:

            minutos_anterior = (
                temporizador_1["minutos"]
            )

            etiquetas_minutos_1[
                minutos_anterior
            ].configure(
                bootstyle="secondary"
            )

        destino = (
            datetime.now()
            + timedelta(
                minutes=minutos
            )
        )

        temporizador_1 = {

            "minutos":
                minutos,

            "hora":
                destino,

            "notificacion_1_minuto":
                False
        }

        lbl_horario_1.configure(
            text=destino.strftime(
                "%H:%M"
            ),
            bootstyle="success"
        )

        etiquetas_minutos_1[
            minutos
        ].configure(
            bootstyle="success"
        )

        return

    # ========================================================
    # TEMPORIZADOR 2
    # ========================================================

    if numero == 2:

        if (
            temporizador_2
            and temporizador_2["minutos"] == minutos
        ):

            temporizador_2 = None

            lbl_horario_2.configure(
                text="00:00",
                bootstyle="secondary"
            )

            etiquetas_minutos_2[
                minutos
            ].configure(
                bootstyle="secondary"
            )

            return

        if temporizador_2:

            minutos_anterior = (
                temporizador_2["minutos"]
            )

            etiquetas_minutos_2[
                minutos_anterior
            ].configure(
                bootstyle="secondary"
            )

        destino = (
            datetime.now()
            + timedelta(
                minutes=minutos
            )
        )

        temporizador_2 = {

            "minutos":
                minutos,

            "hora":
                destino,

                "notificacion_1_minuto":
                False
        }

        lbl_horario_2.configure(
            text=destino.strftime(
                "%H:%M"
            ),
            bootstyle="primary"
        )

        etiquetas_minutos_2[
            minutos
        ].configure(
            bootstyle="primary"
        )

def verificar_temporizadores(ahora):

    global temporizador_1
    global temporizador_2

    # ========================================================
    # TEMPORIZADOR 1
    # ========================================================

    if temporizador_1:

        segundos_restantes = (
            temporizador_1["hora"]
            - ahora
        ).total_seconds()

        if (
            0
            < segundos_restantes
            <= 60
        ):

            etiquetas_minutos_1[
                temporizador_1["minutos"]
            ].configure(
                bootstyle="warning"
            )

            lbl_horario_1.configure(
                bootstyle="warning"
            )

            if not temporizador_1[
                "notificacion_1_minuto"
            ]:

                enviar_notificacion(
                    mensaje="Finalizando Temporizador 1.",
                    titulo="MirrorSync - Temporizador",
                    prioridad="urgent"
                )

                temporizador_1[
                    "notificacion_1_minuto"
                ] = True

        if ahora >= temporizador_1["hora"]:

            finalizar_temporizador(
                1
            )

    # ========================================================
    # TEMPORIZADOR 2
    # ========================================================

    if temporizador_2:

        segundos_restantes = (
            temporizador_2["hora"]
            - ahora
        ).total_seconds()

        if (
            0
            < segundos_restantes
            <= 60
        ):

            etiquetas_minutos_2[
                temporizador_2["minutos"]
            ].configure(
                bootstyle="warning"
            )

            lbl_horario_2.configure(
                bootstyle="warning"
            )

            if not temporizador_2[
                "notificacion_1_minuto"
            ]:

                enviar_notificacion(
                    mensaje="Finalizando Temporizador 2.",
                    titulo="MirrorSync - Temporizador",
                    prioridad="urgent"
                )

                temporizador_2[
                    "notificacion_1_minuto"
                ] = True

        if ahora >= temporizador_2["hora"]:

            finalizar_temporizador(
                2
            )

def finalizar_temporizador(numero):

    global temporizador_1
    global temporizador_2

    if numero == 1:

        etiquetas_minutos_1[
            temporizador_1["minutos"]
        ].configure(
            bootstyle="danger"
        )

        lbl_horario_1.configure(
            bootstyle="danger"
        )

        app.after(
            1000,
            apagar_temporizador_1
        )

        reproducir(
            "tiempofuera"
        )

    else:

        etiquetas_minutos_2[
            temporizador_2["minutos"]
        ].configure(
            bootstyle="danger"
        )

        lbl_horario_2.configure(
            bootstyle="danger"
        )

        app.after(
            1000,
            apagar_temporizador_2
        )

        reproducir(
            "tiempofuera"
        )

def apagar_temporizador_1():

    global temporizador_1

    if temporizador_1 is None:
        return

    etiquetas_minutos_1[
        temporizador_1["minutos"]
    ].configure(
        bootstyle="secondary"
    )

    lbl_horario_1.configure(
        text="00:00",
        bootstyle="secondary"
    )

    temporizador_1 = None

def apagar_temporizador_2():

    global temporizador_2

    if temporizador_2 is None:
        return

    etiquetas_minutos_2[
        temporizador_2["minutos"]
    ].configure(
        bootstyle="secondary"
    )

    lbl_horario_2.configure(
        text="00:00",
        bootstyle="secondary"
    )

    temporizador_2 = None

def iniciar_repeticion_flecha(funcion):

    global flecha_presionada
    global funcion_flecha_actual

    flecha_presionada = True
    funcion_flecha_actual = funcion

    # Ejecutar una vez inmediatamente
    funcion()

    app.after(
        120,
        repetir_flecha
    )

def repetir_flecha():

    if not flecha_presionada:
        return

    if funcion_flecha_actual is None:
        return

    funcion_flecha_actual()

    app.after(
        40,
        repetir_flecha
    )

def detener_repeticion_flecha(event=None):

    global flecha_presionada
    global funcion_flecha_actual

    flecha_presionada = False
    funcion_flecha_actual = None

#GRABACION AUTOMATA
def pedir_nombre_grabacion():

    while True:

        nombre = simpledialog.askstring(
            "Guardar grabación",
            "Ingrese un nombre para la grabación:",
            parent=app
        )

        # ====================================================
        # USUARIO CANCELÓ
        # ====================================================

        if nombre is None:

            respuesta = messagebox.askyesno(
                "Cancelar guardado",
                (
                    "La grabación todavía no fue guardada.\n\n"
                    "¿Desea descartar la grabación?"
                ),
                parent=app
            )

            if respuesta:

                descartar_grabacion_temporal()

                actualizar_grabaciones()

                return False

            continue

        nombre = nombre.strip()

        # ====================================================
        # INTENTAR GUARDAR
        # ====================================================

        exito, resultado = (
            guardar_grabacion_permanente(
                nombre
            )
        )

        if exito:

            # La grabación ya fue guardada.
            # "resultado" es la ruta de su carpeta.
            ruta_instrucciones = os.path.join(
                resultado,
                "Instrucciones.txt"
            )

            try:

                # Crea el archivo vacío sin sobrescribirlo
                # si ya existiera.
                with open(
                    ruta_instrucciones,
                    "a",
                    encoding="utf-8"
                ):
                    pass

            except OSError as e:

                messagebox.showwarning(
                    "Grabación guardada",
                    (
                        f'La grabación "{nombre}" se guardó, '
                        "pero no se pudo crear Instrucciones.txt.\n\n"
                        f"{e}"
                    ),
                    parent=app
                )

            else:

                try:

                    os.startfile(
                        ruta_instrucciones
                    )

                except OSError as e:

                    messagebox.showwarning(
                        "Grabación guardada",
                        (
                            "Se creó Instrucciones.txt, "
                            "pero no se pudo abrir automáticamente.\n\n"
                            f"{e}"
                        ),
                        parent=app
                    )

            # Actualizar inmediatamente
            # la lista visible.
            actualizar_grabaciones()

            return True

        # ====================================================
        # ERROR
        # ====================================================

        messagebox.showwarning(
            "No se pudo guardar",
            resultado,
            parent=app
        )

def actualizar_grabaciones():

    lista_grabaciones.delete(
        0,
        tk.END
    )

    grabaciones = listar_grabaciones()

    for nombre in grabaciones:

        lista_grabaciones.insert(
            tk.END,
            nombre
        )

def abrir_timeline_grabacion(event=None):

    seleccion = (
        lista_grabaciones.curselection()
    )

    if not seleccion:
        return

    indice = seleccion[0]

    nombre = lista_grabaciones.get(
        indice
    )

    ruta_timeline = os.path.join(
        CARPETA_GRABACIONES,
        nombre,
        "timeline.json"
    )

    if not os.path.exists(
        ruta_timeline
    ):

        messagebox.showerror(
            "Timeline",
            (
                "No se encontró la timeline "
                "de esta grabación."
            ),
            parent=app
        )

        return

    abrir_editor_timeline(
        app,
        ruta_timeline
    )

def cargar_grabacion():

    global grabacion_cargada

    seleccion = (
        lista_grabaciones.curselection()
    )

    if not seleccion:

        messagebox.showwarning(
            "Cargar grabación",
            "Seleccione una grabación.",
            parent=app
        )

        return

    indice = seleccion[0]

    nombre = lista_grabaciones.get(
        indice
    )

    grabacion_cargada = nombre

    lbl_grabacion_cargada.config(
        text=f"{nombre}"
    )

    print(
        f"[AUTOMATA] "
        f"Grabación cargada: {nombre}"
    )

def eliminar_grabacion_seleccionada():

    global grabacion_cargada

    seleccion = (
        lista_grabaciones.curselection()
    )

    if not seleccion:

        messagebox.showwarning(
            "Eliminar grabación",
            "Seleccione una grabación.",
            parent=app
        )

        return

    indice = seleccion[0]

    nombre = lista_grabaciones.get(
        indice
    )

    confirmar = messagebox.askyesno(
        "Eliminar grabación",
        (
            f'¿Desea eliminar "{nombre}"?\n\n'
            "Esta acción no se puede deshacer."
        ),
        parent=app
    )

    if not confirmar:
        return

    exito, resultado = eliminar_grabacion(
        nombre
    )

    if not exito:

        messagebox.showerror(
            "Error",
            resultado,
            parent=app
        )

        return

    # Si justamente estaba cargada,
    # la descargamos.
    if grabacion_cargada == nombre:

        grabacion_cargada = None

        lbl_grabacion_cargada.config(
            text="Ninguna"
        )

    actualizar_grabaciones()

def asignar_grabacion_a_esclava():

    if grabacion_cargada is None:

        messagebox.showwarning(
            "Asignar grabación",
            "Primero cargue una grabación.",
            parent=app
        )

        return

    seleccion = (
        lista_esclavas.curselection()
    )

    if not seleccion:

        messagebox.showwarning(
            "Asignar grabación",
            "Seleccione una esclava.",
            parent=app
        )

        return

    indice = seleccion[0]

    ventana = esclavas[
        indice
    ]

    exito, mensaje = agregar_asignacion(
        grabacion_cargada,
        ventana
    )

    if not exito:

        messagebox.showwarning(
            "Asignar grabación",
            mensaje,
            parent=app
        )

        return

    print()
    print(
        "[AUTOMATA] "
        "Asignación creada:"
    )

    print(
        f"{grabacion_cargada} "
        f"→ {ventana['proceso']}"
    )

    actualizar_asignaciones()

def actualizar_asignaciones():

    lista_asignaciones.delete(
        0,
        tk.END
    )

    asignaciones = (
        obtener_asignaciones()
    )

    hay_variables = False

    for asignacion in asignaciones:

        grabacion = (
            asignacion["grabacion"]
        )

        ventana = (
            asignacion["ventana"]
        )

        proceso = ventana.get(
            "proceso",
            "Ventana"
        )

        lista_asignaciones.insert(
            tk.END,
            f"{grabacion} → {proceso}"
        )

    for asignacion in asignaciones:

        grabacion = asignacion.get(
            "grabacion"
        )

        variables = obtener_variables_grabacion(
            grabacion
        )

        if variables:

            hay_variables = True
            break

    if hay_variables:

        if not btn_configurar_asignaciones.winfo_manager():

            btn_configurar_asignaciones.pack(
                side="left",
                padx=3,
                before=lbl_abrir_carpeta
            )

            reproducir("escriturasvariablesdetectadas")

    else:

        if btn_configurar_asignaciones.winfo_manager():

            btn_configurar_asignaciones.pack_forget()

def eliminar_asignacion_seleccionada():

    seleccion = (
        lista_asignaciones.curselection()
    )

    if not seleccion:
        return

    indice = seleccion[0]

    eliminar_asignacion(
        indice
    )

    actualizar_asignaciones()

def abrir_carpeta_mirrorsync(event=None):

    carpeta_programa = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

    os.startfile(
        carpeta_programa
    )

def cmd_cambiar_zig_zag(event=None):

    activo = cambiar_estado_zig_zag()

    if activo:

        lbl_zig_zag.configure(
            foreground="lime"
        )

    else:

        lbl_zig_zag.configure(
            foreground="red"
        )

def cmd_cambiar_anticeros(event=None):

    cambiar_estado_anticeros()

    app.after(
        50,
        app.lower
    )

def cmd_cambiar_escritura_teclado(event=None):

    cambiar_estado_escritura_teclado()

    app.after(
        50,
        app.lower
    )

# *************INTERFAZ*****************************************************************

app = ttk.Window(themename="cyborg")

style = ttk.Style()

app.title("MirrorSync 3.5")

app.geometry("1020x361") #ancho x alto

app.update_idletasks()

ancho = app.winfo_width()
alto = app.winfo_height()

pantalla_ancho = app.winfo_screenwidth()
pantalla_alto = app.winfo_screenheight()

x = (pantalla_ancho - ancho) // 2 - 460
y = pantalla_alto - alto - 24

# Posición normal
x_normal = x
y_normal = y

app.geometry(f"+{x}+{y}")

frame_contenedor = ttk.Frame(app)
frame_contenedor.pack(padx=10, pady=10)

#FRAME UNO
frame_uno = ttk.Frame(frame_contenedor)
frame_uno.pack(side="left", padx=5)

frame_detectadas = ttk.Frame(frame_uno)
frame_detectadas.pack(pady=3)

#BOTON AGREGAR MAESTRA
lbl_elegir_maestra = ttk.Label(
    frame_detectadas,
    text="w",
    font=("Chess Maya", 20, "normal"),
    foreground="gold",
    cursor="hand2"
)

lbl_elegir_maestra.pack(
    side="left",
    padx=1
)

lbl_elegir_maestra.bind(
    "<Button-1>",
    lambda event: elegir_maestra()
)

ToolTip(lbl_elegir_maestra, "Maestra")

#LISTA DE VENTANAS DETECTADAS
lista = tk.Listbox(
    frame_detectadas,
    width=10,
    height=6, #Renglones para la lista de ventanas
    font=("Consolas", 10, "bold")
)

lista.pack(
    side="left",
    padx=2
)

#BOTON AGREGAR ESCLAVA
lbl_agregar_esclava = ttk.Label(
    frame_detectadas,
    text="o",
    font=("Chess Maya", 20, "normal"),
    foreground="#00AAE4",
    cursor="hand2"
)

lbl_agregar_esclava.pack(
    side="left",
    padx=1
)

lbl_agregar_esclava.bind(
    "<Button-1>",
    lambda event: agregar_esclava()
)

ToolTip(lbl_agregar_esclava, "Esclava")

frame_sub_inferior = ttk.Frame(frame_uno)
frame_sub_inferior.pack(pady=2)

#BOTON REINICIAR
lbl_reiniciar = ttk.Label(
    frame_sub_inferior,
    text="M",
    font=("Wingdings", 24, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_reiniciar.pack(
    side="left",
    padx=1
)

lbl_reiniciar.bind(
    "<Button-1>",
    lambda event: reiniciar_mirrorsync()
)

ToolTip(lbl_reiniciar, "Reiniciar Programa")

#BOTON GUARDAR POSICIONES DE VENTANAS
lbl_guardar = ttk.Label(
    frame_sub_inferior,
    text="<",
    font=("Wingdings", 24, "normal"),
    foreground="#F5B7B1",
    cursor="hand2"
)

lbl_guardar.pack(
    side="left",
    padx=1
)

lbl_guardar.bind(
    "<Button-1>",
    lambda event: guardar_distribucion_actual()
)

ToolTip(lbl_guardar, "Guardar Distribucion de Ventanas")

#BOTON RESTAURAR POSICIONES DE VENTANAS
lbl_restaurar = ttk.Label(
    frame_sub_inferior,
    text="q",
    font=("Webdings", 24, "normal"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_restaurar.pack(
    side="left",
    padx=1
)

lbl_restaurar.bind(
    "<Button-1>",
    lambda event: restaurar_distribucion_actual()
)

ToolTip(lbl_restaurar, "Restaurar Distribucion")

#BOTON NUEVA SESION
lbl_nueva_sesion = ttk.Label(
    frame_sub_inferior,
    text="J",
    font=("Wingdings", 24, "normal"),
    foreground="gold",
    cursor="hand2"
)

lbl_nueva_sesion.pack(
    side="left",
    padx=1
)

lbl_nueva_sesion.bind(
    "<Button-1>",
    lambda event: nueva_sesion()
)

ToolTip(lbl_nueva_sesion, "Nueva Sesion")

frame_inferior = ttk.Frame(frame_uno)
frame_inferior.pack(pady=2)

lbl_dist_2 = ttk.Label(
    frame_inferior,
    text="2",
    font=("DPoly Six-Sider", 26, "normal"),
    foreground="magenta",
    cursor="hand2"
)

lbl_dist_2.pack(
    side="left",
    padx=2
)

lbl_dist_2.bind(
    "<Button-1>",
    lambda event: restaurar_distribucion_1_maestra_1_esclava()
)

ToolTip(lbl_dist_2, "2G")

lbl_dist_3 = ttk.Label(
    frame_inferior,
    text="6",
    font=("DPoly Six-Sider", 26, "normal"),
    foreground="lime",
    cursor="hand2"
)

lbl_dist_3.pack(
    side="left",
    padx=2
)

lbl_dist_3.bind(
    "<Button-1>",
    lambda event: restaurar_distribucion_full_esclavas()
)

ToolTip(lbl_dist_3, "6R")

frame_maestra = ttk.Frame(frame_uno)
frame_maestra.pack(pady=2)

#MOSTRAR MAESTRA SELECCIONADA
ttk.Label(
    frame_maestra,
    text="M: ",
    font=("VCR OSD Mono", 10, "bold")
).pack(
    side="left",
    padx=5
)


lbl_maestra = ttk.Label(
    frame_maestra,
    text="Ninguna",
    foreground="gold",
    font=("Consolas", 11, "normal")
)

lbl_maestra.pack(
    side="left",
    padx=5
)

frame_esclavas = ttk.Frame(frame_uno)
frame_esclavas.pack(padx=10)

#MOSTRAR ESCLAVAS SELECCIONADAS
ttk.Label(
    frame_esclavas,
    text="ESCLAVAS",
    font=("VCR OSD Mono", 10, "bold")
).pack(
    side="left",
    padx= 1
)

frame_esclavas_dos = ttk.Frame(frame_uno)
frame_esclavas_dos.pack(pady=1)

lbl_asignar = ttk.Label(
    frame_esclavas_dos,
    text="E",
    font=("Wingdings 2", 24, "normal"),
    foreground="black",
    cursor="hand2"
)

lbl_asignar.pack(
    side="left",
    padx=1
)

lista_esclavas = tk.Listbox(
    frame_esclavas_dos,
    width=10,
    height=6, #Renglones para la lista de esclavas
    font=("Consolas", 10, "bold")
)

lista_esclavas.pack(
    side="left",
    padx=1
)

lbl_asignar = ttk.Label(
    frame_esclavas_dos,
    text="E",
    font=("Wingdings 2", 24, "normal"),
    foreground="magenta",
    cursor="hand2"
)

lbl_asignar.pack(
    side="left",
    padx=1
)

lbl_asignar.bind(
    "<Button-1>",
    lambda event: asignar_grabacion_a_esclava()
)

ToolTip(lbl_asignar, "Asignar Grabacion")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#FRAME DOS
frame_dos = ttk.Frame(frame_contenedor)
frame_dos.pack(side="left", padx=3)

frame_grabaciones = ttk.Frame(frame_dos)
frame_grabaciones.pack(pady=1)

ttk.Label(
    frame_grabaciones,
    text="GRABACIONES",
    font=("VCR OSD Mono", 10, "bold")
).pack()


lista_grabaciones = tk.Listbox(
    frame_grabaciones,
    width=38,
    height=6,
    font=("Consolas", 10, "bold")
)

lista_grabaciones.pack(
    pady=1
)

lista_grabaciones.bind(
    "<Double-Button-1>",
    abrir_timeline_grabacion
)

frame_botones_1 = ttk.Frame(frame_dos)
frame_botones_1.pack(pady=1)

lbl_eliminar_grabacion = ttk.Label(
    frame_botones_1,
    text="3",
    font=("Wingdings 2", 24, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_eliminar_grabacion.pack(
    side="left",
    padx=1
)

lbl_eliminar_grabacion.bind(
    "<Button-1>",
    lambda event: eliminar_grabacion_seleccionada()
)

ToolTip(lbl_eliminar_grabacion, "Eliminar Grabacion")

lbl_cargar_grabacion = ttk.Label(
    frame_botones_1,
    text="8",
    font=("Wingdings 2", 24, "normal"),
    foreground="lime",
    cursor="hand2"
)

lbl_cargar_grabacion.pack(
    side="left",
    padx=1
)

lbl_cargar_grabacion.bind(
    "<Button-1>",
    lambda event: cargar_grabacion()
)

ToolTip(lbl_cargar_grabacion, "Cargar Grabacion")

frame_cargada = ttk.Frame(frame_dos)
frame_cargada.pack(pady=1)

lbl_grabacion_cargada = ttk.Label(
    frame_cargada,
    text="Ninguna",
    font=("Consolas", 11, "normal"),
    foreground="lime"
)

lbl_grabacion_cargada.pack()

frame_asignaciones = ttk.Frame(frame_dos)
frame_asignaciones.pack(pady=1)

ttk.Label(
    frame_asignaciones,
    text="ASIGNACIONES",
    font=("VCR OSD Mono", 10, "bold")
).pack()

lista_asignaciones = tk.Listbox(
    frame_asignaciones,
    width=49,
    height=6,
    font=("Consolas", 8, "bold")
)

lista_asignaciones.pack()

frame_botones_2 = ttk.Frame(frame_dos)
frame_botones_2.pack(pady=1)

lbl_quitar_asignacion = ttk.Label(
    frame_botones_2,
    text="r",
    font=("Webdings", 23, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_quitar_asignacion.pack(
    side="left",
    padx=3
)

lbl_quitar_asignacion.bind(
    "<Button-1>",
    lambda event: eliminar_asignacion_seleccionada()
)

ToolTip(lbl_quitar_asignacion, "Quitar Asignación")

btn_configurar_asignaciones = ctk.CTkButton(
    frame_botones_2,
    text="CFG",
    command=lambda: abrir_configurar_asignaciones(app),
    font=("VCR OSD Mono", 12, "bold"),
    width=8,
    fg_color="lime",
    text_color="black",
    corner_radius=10
)

ToolTip(
    btn_configurar_asignaciones,
    "Configurar Escrituras Variables"
)

lbl_abrir_carpeta = ttk.Label(
    frame_botones_2,
    text="📁",
    font=("Segoe UI Emoji", 22),
    foreground="yellow",
    cursor="hand2"
)

lbl_abrir_carpeta.pack(
    side="left",
    padx=3
)

lbl_abrir_carpeta.bind(
    "<Button-1>",
    abrir_carpeta_mirrorsync
)

ToolTip(
    lbl_abrir_carpeta,
    "Abrir Carpeta de MirrorSync"
)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#FRAME TRES
frame_tres = ttk.Frame(frame_contenedor)
frame_tres.pack(side="left", padx=1)

frame_medio = ttk.Frame(frame_tres)
frame_medio.pack(pady=2)

#BOTON ENVIAR AL FONDO
lbl_fondo = ttk.Label(
    frame_medio,
    text="J",
    font=("Controllers", 20, "normal"),
    foreground="white",
    cursor="hand2"
)

lbl_fondo.pack(
    side="left",
    padx=5
)

lbl_fondo.bind(
    "<Button-1>",
    lambda event: enviar_al_fondo()
)

ToolTip(lbl_fondo, "Atras")

#HORA
hora_label = ttk.Label(
    frame_medio,
    text="00:00:00",
    font=("Technology", 22, "bold"),
    bootstyle=WARNING
)

hora_label.pack(
    side="left",
    padx=5
)

#BOTON ENVIAR AL FRENTE
lbl_frente = ttk.Label(
    frame_medio,
    text="L",
    font=("Controllers", 20, "normal"),
    foreground="white",
    cursor="hand2"
)

lbl_frente.pack(
    side="left",
    padx=5
)

lbl_frente.bind(
    "<Button-1>",
    lambda event: traer_al_frente()
)

ToolTip(lbl_frente, "Frente")

frame_temporizador_1 = ttk.Frame(frame_tres)
frame_temporizador_1.pack(pady=(0, 2))

etiquetas_minutos_1 = {}

for minutos in (3,5,7,10,12,15,18,20,25):

    lbl = ttk.Label(
        frame_temporizador_1,
        text=str(minutos),
        font=(
            "Technology",
            14,
            "bold"
        ),
        bootstyle=SECONDARY,
        anchor="center",
        cursor="hand2"
    )

    lbl.pack(
        side="left",
        padx=3
    )

    etiquetas_minutos_1[
        minutos
    ] = lbl

    lbl.bind(
        "<Button-1>",
        lambda e, m=minutos:
            iniciar_temporizador(
                m,
                1
            )
    )

frame_temporizador_2 = ttk.Frame(frame_tres)
frame_temporizador_2.pack(pady=(0, 2))

etiquetas_minutos_2 = {}

for minutos in (3,5,7,10,12,15,18,20,25):

    lbl = ttk.Label(
        frame_temporizador_2,
        text=str(minutos),
        font=(
            "Technology",
            14,
            "bold"
        ),
        bootstyle=SECONDARY,
        anchor="center",
        cursor="hand2"
    )

    lbl.pack(
        side="left",
        padx=3
    )

    etiquetas_minutos_2[
        minutos
    ] = lbl

    lbl.bind(
        "<Button-1>",
        lambda e, m=minutos:
            iniciar_temporizador(
                m,
                2
            )
    )

frame_horarios = ttk.Frame(frame_tres)
frame_horarios.pack(pady=(0, 2))

lbl_horario_1 = ttk.Label(
    frame_horarios,
    text="00:00",
    font=("Technology", 18, "bold"),
    bootstyle=SECONDARY,
    width=7,
    anchor="center"
)

lbl_horario_1.pack(
    side="left",
    padx=10
)

lbl_horario_2 = ttk.Label(
    frame_horarios,
    text="00:00",
    font=("Technology", 18, "bold"),
    bootstyle=SECONDARY,
    width=7,
    anchor="center"
)

lbl_horario_2.pack(
    side="left",
    padx=10
)

frame_estados = ttk.Frame(frame_tres)
frame_estados.pack(pady=0)

frame_estados_fila1 = ttk.Frame(frame_estados)
frame_estados_fila1.pack(pady=0)

#VISOR DE ESTADOS DE MODOS
lbl_estado_automata = ttk.Label(
    frame_estados_fila1,
    text="S",
    font=("ROBOTS", 38, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_automata.pack(
    side="left",
    padx=0,
    pady=0
)

ToolTip(lbl_estado_automata, "Automata")

lbl_zig_zag = ttk.Label(
    frame_estados_fila1,
    text="7",
    font=("Wingdings 3", 24, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_zig_zag.pack(
    side="left",
    padx=0
)

lbl_zig_zag.bind(
    "<Button-1>",
    cmd_cambiar_zig_zag
)

ToolTip(
    lbl_zig_zag,
    "Modo Zig Zag"
)

lbl_estado_blockvert = ttk.Label(
    frame_estados_fila1,
    text="O",
    font=("Sonico", 43, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_blockvert.pack(
    side="left",
    padx=30,
    pady=0
)

ToolTip(lbl_estado_blockvert, "Block Vertical")

frame_estados_fila2 = ttk.Frame(frame_estados)
frame_estados_fila2.pack(pady=0)

lbl_estado_manual = ttk.Label(
    frame_estados_fila2,
    text="N",
    font=("Pokemon pixels 1", 21, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_manual.pack(
    side="left",
    padx=25,
    pady=0
)

ToolTip(lbl_estado_manual, "Manual")

lbl_estado_espejo = ttk.Label(
    frame_estados_fila2,
    text="Y",
    font=("Pokemon pixels 1", 20, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_espejo.pack(
    side="left",
    padx=25,
    pady=0
)

ToolTip(lbl_estado_espejo, "Espejo")

frame_estados_fila3 = ttk.Frame(frame_estados)
frame_estados_fila3.pack(pady=0)

lbl_estado_escritura = ttk.Label(
    frame_estados_fila3,
    text="e",
    font=("Special Forces", 42, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_escritura.pack(
    side="left",
    padx=2,
    pady=0
)

ToolTip(lbl_estado_escritura, "Escritura")

lbl_estado_anticeros = ttk.Label(
    frame_estados_fila3,
    text="r",
    font=("Special Forces", 25, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_anticeros.pack(
    side="left",
    padx=0,
    pady=0
)

lbl_estado_anticeros.bind(
    "<Button-1>",
    cmd_cambiar_anticeros
)

ToolTip(lbl_estado_anticeros,"Anticeros")

lbl_escritura_teclado = ttk.Label(
    frame_estados_fila3,
    text="v",
    font=("Special Forces",24,"normal"),
    foreground="red",
    cursor="hand2"
)

lbl_escritura_teclado.pack(
    side="left",
    padx=0,
    pady=0
)

lbl_escritura_teclado.bind(
    "<Button-1>",
    cmd_cambiar_escritura_teclado
)

ToolTip(lbl_escritura_teclado,"Teclado")

lbl_estado_arrastre = ttk.Label(
    frame_estados_fila3,
    text="A",
    font=("Barrel of Ninjas", 35, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_arrastre.pack(
    side="left",
    padx=19,
    pady=0
)

ToolTip(lbl_estado_arrastre, "Arrastre")

frame_estados_fila4 = ttk.Frame(frame_estados)
frame_estados_fila4.pack(pady=0)

lbl_estado_blocksecciones = ttk.Label(
    frame_estados_fila4,
    text="5",
    font=("Super Street Fighter Hyper Font", 20, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_blocksecciones.pack(
    side="left",
    padx=30,
    pady=0
)

ToolTip(lbl_estado_blocksecciones, "Block Secciones")

lbl_estado_capturador = ttk.Label(
    frame_estados_fila4,
    text="Q",
    font=("Super Street Fighter Hyper Font", 19, "normal"),
    foreground="red",
    cursor="hand2"
)

lbl_estado_capturador.pack(
    side="left",
    padx=10,
    pady=0
)

ToolTip(lbl_estado_capturador, "Capturador")

estado["automata"] = lbl_estado_automata
estado["manual"] = lbl_estado_manual
estado["espejo"] = lbl_estado_espejo
estado["escritura"] = lbl_estado_escritura
estado["anticeros"] = lbl_estado_anticeros
estado["escritura_teclado"] = lbl_escritura_teclado
estado["arrastre"] = lbl_estado_arrastre
estado["blockvert"] = lbl_estado_blockvert
estado["blocksecciones"] = lbl_estado_blocksecciones
estado["capturador"] = lbl_estado_capturador

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#FRAME CUATRO
frame_cuatro = ttk.Frame(frame_contenedor)
frame_cuatro.pack(side="left", padx=2)

#<<<<< BLOCK VERTICAL >>>>>>
frame_block_modo_captura = ttk.Frame(frame_cuatro)
frame_block_modo_captura.pack(pady=1)

btn_block_normal = ctk.CTkButton(
    frame_block_modo_captura,
    text="N",
    command=seleccionar_block_normal,
    font=("VCR OSD Mono", 11, "bold"),
    width=28,
    height=24,
    fg_color="lime",
    text_color="black",
    corner_radius=8
)

btn_block_normal.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_block_normal,
    "Captura Normal"
)

btn_block_reforzado = ctk.CTkButton(
    frame_block_modo_captura,
    text="R+",
    command=seleccionar_block_reforzado,
    font=("VCR OSD Mono", 11, "bold"),
    width=32,
    height=24,
    fg_color="#333333",
    text_color="white",
    corner_radius=8
)

btn_block_reforzado.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_block_reforzado,
    "Captura Reforzada"
)

frame_block_vertical_superior = ttk.Frame(frame_cuatro)
frame_block_vertical_superior.pack(pady=1)

lbl_block_vertical_pequenos = ttk.Label(
    frame_block_vertical_superior,
    text="-",
    font=("Consolas", 16, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_pequenos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_y_inicio_menos = ttk.Label(
    frame_block_vertical_superior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_y_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_y_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_y_inicio_menos
    )
)

lbl_block_vertical_y_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_vertical_y_inicio_mas = ttk.Label(
    frame_block_vertical_superior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_y_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_block_vertical_y_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_y_inicio_mas
    )
)

lbl_block_vertical_y_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_vertical_grandes = ttk.Label(
    frame_block_vertical_superior,
    text="+",
    font=("Consolas", 16, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_grandes.pack(
    side="left",
    padx=1
)

# IZQUIERDO:
# aceptar más pequeños
lbl_block_vertical_pequenos.bind(
    "<Button-1>",
    block_vertical_aceptar_mas_pequenos
)

# DERECHO:
# reducir tolerancia de pequeños
lbl_block_vertical_pequenos.bind(
    "<Button-3>",
    block_vertical_reducir_pequenos
)

# IZQUIERDO:
# aceptar más grandes
lbl_block_vertical_grandes.bind(
    "<Button-1>",
    block_vertical_aceptar_mas_grandes
)

# DERECHO:
# reducir tolerancia de grandes
lbl_block_vertical_grandes.bind(
    "<Button-3>",
    block_vertical_reducir_grandes
)

frame_block_vertical_centro_sup = ttk.Frame(frame_cuatro)
frame_block_vertical_centro_sup.pack(pady=1)

lbl_block_vertical_x_menos = ttk.Label(
    frame_block_vertical_centro_sup,
    text="t",
    font=("Wingdings 3", 14, "normal"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_x_menos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_menos
    )
)

lbl_block_vertical_x_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_vertical_x_inicio_menos = ttk.Label(
    frame_block_vertical_centro_sup,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="yellow",
    cursor="hand2"
)

lbl_block_vertical_x_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_inicio_menos
    )
)

lbl_block_vertical_x_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

btn_mostrar_block_vertical = ctk.CTkButton(
    frame_block_vertical_centro_sup,
    text="M",
    width=8,
    command=cmd_mostrar_calibracion_block_vertical,
    font=("VCR OSD Mono", 12, "bold"),
    fg_color="#333333",
    text_color="white",
    corner_radius=10
)

btn_mostrar_block_vertical.pack(
    side="left",
    padx=1
)

ToolTip(btn_mostrar_block_vertical, "Mostrar Visor Block Vertical")

lbl_block_vertical_x_fin_menos = ttk.Label(
    frame_block_vertical_centro_sup,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="yellow",
    cursor="hand2"
)

lbl_block_vertical_x_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_fin_menos
    )
)

lbl_block_vertical_x_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_vertical_x_mas = ttk.Label(
    frame_block_vertical_centro_sup,
    text="u",
    font=("Wingdings 3", 14, "normal"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_x_mas.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_mas
    )
)

lbl_block_vertical_x_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

frame_block_vertical_centro_inf = ttk.Frame(frame_cuatro)
frame_block_vertical_centro_inf.pack(pady=2)

lbl_block_vertical_x_inicio_mas = ttk.Label(
    frame_block_vertical_centro_inf,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="yellow",
    cursor="hand2"
)

lbl_block_vertical_x_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_inicio_mas
    )
)

lbl_block_vertical_x_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

btn_guardar_block_vertical = ctk.CTkButton(
    frame_block_vertical_centro_inf,
    text="G",
    width=8,
    command=guardar_calibracion_block_vertical,
    font=("VCR OSD Mono", 12, "bold"),
    fg_color="#333333",
    text_color="white",
    corner_radius=10
)

btn_guardar_block_vertical.pack(
    side="left",
    padx=1
)

ToolTip(btn_guardar_block_vertical, "Guardar Calibracion Block Vertical")

lbl_block_vertical_x_fin_mas = ttk.Label(
    frame_block_vertical_centro_inf,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="yellow",
    cursor="hand2"
)

lbl_block_vertical_x_fin_mas.pack(
    side="left",
    padx=1
)

lbl_block_vertical_x_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_x_fin_mas
    )
)

lbl_block_vertical_x_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)


frame_block_vertical_inferior = ttk.Frame(frame_cuatro)
frame_block_vertical_inferior.pack(pady=1)

lbl_block_vertical_y_fin_menos = ttk.Label(
    frame_block_vertical_inferior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_y_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_vertical_y_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_y_fin_menos
    )
)

lbl_block_vertical_y_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_vertical_y_fin_mas = ttk.Label(
    frame_block_vertical_inferior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#E7D40A",
    cursor="hand2"
)

lbl_block_vertical_y_fin_mas.pack(
    side="left",
    padx=1
)

lbl_block_vertical_y_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_vertical_y_fin_mas
    )
)

lbl_block_vertical_y_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

frame_espacio = ttk.Frame(frame_cuatro)
frame_espacio.pack(pady=1)

lbl_espacio = ttk.Label(
    frame_espacio,
    text="ESPACIO",
    font=("VCR OSD Mono", 5, "bold"),
    foreground="black"
)

lbl_espacio.pack(
    side="left",
    padx=1
)

#<<<<<<< MODO CAPTURADOR >>>>>>>
#ARRIBA Y ABAJO SUPERIOR
#OPCION

frame_capturador_modo_captura = ttk.Frame(frame_cuatro)
frame_capturador_modo_captura.pack(pady=1)

btn_captura_normal = ctk.CTkButton(
    frame_capturador_modo_captura,
    text="N",
    command=seleccionar_captura_normal,
    font=("VCR OSD Mono", 11, "bold"),
    width=28,
    height=24,
    fg_color="lime",
    text_color="black",
    corner_radius=8
)

btn_captura_normal.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_captura_normal,
    "Captura Normal"
)

btn_captura_reforzada = ctk.CTkButton(
    frame_capturador_modo_captura,
    text="R+",
    command=seleccionar_captura_reforzada,
    font=("VCR OSD Mono", 11, "bold"),
    width=32,
    height=24,
    fg_color="#333333",
    text_color="white",
    corner_radius=8
)

btn_captura_reforzada.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_captura_reforzada,
    "Captura Reforzada"
)

btn_arrastre_inteligente = ctk.CTkButton(
    frame_capturador_modo_captura,
    text="AI",
    command=seleccionar_arrastre_inteligente,
    font=("VCR OSD Mono", 11, "bold"),
    width=32,
    height=24,
    fg_color="#333333",
    text_color="white",
    corner_radius=8
)

btn_arrastre_inteligente.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_arrastre_inteligente,
    "Arrastre Inteligente"
)

frame_capturador_superior = ttk.Frame(frame_cuatro)
frame_capturador_superior.pack(pady=1)

#OPCIONES
lbl_capturador_region_opciones_y_inicio_menos = ttk.Label(
    frame_capturador_superior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_y_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_y_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_y_inicio_menos
    )
)

lbl_capturador_region_opciones_y_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_capturador_arriba = ttk.Label(
    frame_capturador_superior,
    text="🔺",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_arriba.pack(
    side="left",
    padx=1
)

lbl_capturador_arriba.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_arriba
    )
)

lbl_capturador_arriba.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_capturador_region_opciones_y_inicio_mas = ttk.Label(
    frame_capturador_superior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_y_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_y_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_y_inicio_mas
    )
)

lbl_capturador_region_opciones_y_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

frame_capturador_centro_superior = ttk.Frame(frame_cuatro)
frame_capturador_centro_superior.pack(pady=1)

#IZQUIERDA INICIO CENTRO SUPERIOR
#OPCIONES
lbl_capturador_region_opciones_x_inicio_menos = ttk.Label(
    frame_capturador_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_x_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_x_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_x_inicio_menos
    )
)

lbl_capturador_region_opciones_x_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

btn_mostrar_capturador = ctk.CTkButton(
    frame_capturador_centro_superior,
    text="M",
    width=8,
    command=cmd_mostrar_calibracion_capturador,
    font=("VCR OSD Mono", 12, "bold"),
    fg_color="#333333",
    text_color="white",
    corner_radius=10
)

btn_mostrar_capturador.pack(
    side="left",
    padx=1
)

ToolTip(
    btn_mostrar_capturador,
    "Mostrar Visor del Capturador"
)

#IZQUIERDA FIN CENTRO SUPERIOR

#OPCIONES
lbl_capturador_region_opciones_x_fin_menos = ttk.Label(
    frame_capturador_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_x_fin_menos.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_x_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_x_fin_menos
    )
)

lbl_capturador_region_opciones_x_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

frame_capturador_centro_inferior = ttk.Frame(frame_cuatro)
frame_capturador_centro_inferior.pack(pady=0)

#DERECHA INICIO CENTRO INFERIOR
#OPCIONES
lbl_capturador_region_opciones_x_inicio_mas = ttk.Label(
    frame_capturador_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_x_inicio_mas.pack(
    side="left",
    padx=0
)

lbl_capturador_region_opciones_x_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_x_inicio_mas
    )
)

lbl_capturador_region_opciones_x_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

lbl_guardar_capturador = ttk.Label(
    frame_capturador_centro_inferior,
    text="Ó",
    font=("Webdings", 22, "normal"),
    foreground="white",
    cursor="hand2"
)

lbl_guardar_capturador.pack(
    side="left",
    padx=0
)

lbl_guardar_capturador.bind(
    "<Button-1>",
    lambda event: guardar_calibracion_capturador()
)

ToolTip(
    lbl_guardar_capturador,
    "Capturador SNAPSHOT")

#DERECHA FIN CENTRO INFERIOR

#OPCIONES
lbl_capturador_region_opciones_x_fin_mas = ttk.Label(
    frame_capturador_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_x_fin_mas.pack(
    side="left",
    padx=0
)

lbl_capturador_region_opciones_x_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_x_fin_mas
    )
)

lbl_capturador_region_opciones_x_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

#ARRIBA Y ABAJO INFERIOR
frame_capturador_inferior = ttk.Frame(frame_cuatro)
frame_capturador_inferior.pack(pady=0)

#OPCIONES
lbl_capturador_region_opciones_y_fin_menos = ttk.Label(
    frame_capturador_inferior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_y_fin_menos.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_y_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_y_fin_menos
    )
)

lbl_capturador_region_opciones_y_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_capturador_abajo = ttk.Label(
    frame_capturador_inferior,
    text="🔻",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_abajo.pack(
    side="left",
    padx=1
)

lbl_capturador_abajo.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_abajo
    )
)

lbl_capturador_abajo.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_capturador_region_opciones_y_fin_mas = ttk.Label(
    frame_capturador_inferior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="lime",
    cursor="hand2"
)

lbl_capturador_region_opciones_y_fin_mas.pack(
    side="left",
    padx=1
)

lbl_capturador_region_opciones_y_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        capturador_y_fin_mas
    )
)

lbl_capturador_region_opciones_y_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#FRAME CINCO
frame_cinco = ttk.Frame(frame_contenedor)
frame_cinco.pack(side="left", padx=5)

#<<<<<<<< MODO SILENCIOSO >>>>>>>>
frame_modo_silencioso  = ttk.Frame(frame_cinco)
frame_modo_silencioso .pack(pady=0)

lbl_modo_silencioso = ttk.Label(
    frame_modo_silencioso,
    text="🔊",
    font=("Segoe UI Emoji", 25),
    foreground="cyan",
    cursor="hand2"
)

lbl_modo_silencioso.pack()

lbl_modo_silencioso.bind(
    "<Button-1>",
    cmd_cambiar_modo_silencioso
)

ToolTip(
    lbl_modo_silencioso,
    "Modo Silencioso"
)

#<<<<<<< NOTIFICACIONES >>>>>>>
frame_notificaciones = ttk.Frame(frame_cinco)
frame_notificaciones.pack(pady=5)

lbl_notificaciones_emojis = ttk.Label(
    frame_notificaciones,
    text="🔔🚫📱",
    font=("Segoe UI Emoji", 14, "normal"),
    foreground="#AA0000",
    cursor="hand2"
)

lbl_notificaciones_emojis.pack(
    padx=3,
    pady=3
)

btn_notificaciones = ctk.CTkButton(
    frame_notificaciones,
    text="NOTIFICACIONES",
    font=("VCR OSD Mono", 13, "bold"),
    width=45,
    height=28,
    corner_radius=8,
    fg_color="red",
    text_color="white",
    command=cmd_cambiar_notificaciones
)

btn_notificaciones.pack(
    side="left",
    padx=3
)

estado["notificaciones"] = btn_notificaciones

frame_espacio_dos = ttk.Frame(frame_cinco)
frame_espacio_dos.pack(pady=1)

lbl_espacio = ttk.Label(
    frame_espacio_dos,
    text="ESPACIO",
    font=("VCR OSD Mono", 4, "bold"),
    foreground="black"
)

lbl_espacio.pack(
    side="left",
    padx=1
)
#<<<<<<<< BLOCK SECCIONES >>>>>>>>
frame_block_secciones_modo_captura = ttk.Frame(frame_cinco)
frame_block_secciones_modo_captura.pack(pady=1)

btn_block_secciones_normal = ctk.CTkButton(
    frame_block_secciones_modo_captura,
    text="N",
    command=seleccionar_block_secciones_normal,
    font=("VCR OSD Mono", 11, "bold"),
    width=28,
    height=24,
    fg_color="lime",
    text_color="black",
    corner_radius=8
)

btn_block_secciones_normal.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_block_secciones_normal,
    "Captura Normal"
)

btn_block_secciones_reforzado = ctk.CTkButton(
    frame_block_secciones_modo_captura,
    text="R+",
    command=seleccionar_block_secciones_reforzado,
    font=("VCR OSD Mono", 11, "bold"),
    width=32,
    height=24,
    fg_color="#333333",
    text_color="white",
    corner_radius=8
)

btn_block_secciones_reforzado.pack(
    side="left",
    padx=2
)

ToolTip(
    btn_block_secciones_reforzado,
    "Captura Reforzada"
)

#ARRIBA Y ABAJO SUPERIOR
#OPCION

frame_block_secciones_superior_dos = ttk.Frame(frame_cinco)
frame_block_secciones_superior_dos.pack(pady=1)

#OPCIONES
lbl_block_opciones_secciones_y_inicio_menos = ttk.Label(
    frame_block_secciones_superior_dos,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_y_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_y_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_y_inicio_menos
    )
)

lbl_block_opciones_secciones_y_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_opciones_secciones_arriba = ttk.Label(
    frame_block_secciones_superior_dos,
    text="🔺",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_arriba.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_arriba.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_mover_arriba
    )
)

lbl_block_opciones_secciones_arriba.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_opciones_secciones_y_inicio_mas = ttk.Label(
    frame_block_secciones_superior_dos,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_y_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_y_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_y_inicio_mas
    )
)

lbl_block_opciones_secciones_y_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

frame_block_secciones_superior = ttk.Frame(frame_cinco)
frame_block_secciones_superior.pack(pady=1)

#AFIRMACION
lbl_block_afirmacion_secciones_y_inicio_menos = ttk.Label(
    frame_block_secciones_superior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_y_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_y_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_y_inicio_menos
    )
)

lbl_block_afirmacion_secciones_y_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_afirmacion_secciones_arriba = ttk.Label(
    frame_block_secciones_superior,
    text="🔺",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_arriba.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_arriba.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_afirmacion_arriba
    )
)

lbl_block_afirmacion_secciones_arriba.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_afirmacion_secciones_y_inicio_mas = ttk.Label(
    frame_block_secciones_superior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_y_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_y_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_y_inicio_mas
    )
)

lbl_block_afirmacion_secciones_y_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

frame_block_secciones_centro_superior = ttk.Frame(frame_cinco)
frame_block_secciones_centro_superior.pack(pady=1)

#IZQUIERDA INICIO CENTRO SUPERIOR
#OPCIONES
lbl_block_opciones_secciones_x_inicio_menos = ttk.Label(
    frame_block_secciones_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_x_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_x_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_x_inicio_menos
    )
)

lbl_block_opciones_secciones_x_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

#AFIRMACION
lbl_block_afirmacion_secciones_x_inicio_menos = ttk.Label(
    frame_block_secciones_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_x_inicio_menos.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_x_inicio_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_x_inicio_menos
    )
)

lbl_block_afirmacion_secciones_x_inicio_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

btn_mostrar_block_secciones = ctk.CTkButton(
    frame_block_secciones_centro_superior,
    text="M",
    width=8,
    command=cmd_mostrar_calibracion_block_secciones,
    font=("VCR OSD Mono", 12, "bold"),
    fg_color="#333333",
    text_color="white",
    corner_radius=10
)

btn_mostrar_block_secciones.pack(
    side="left",
    padx=1
)

ToolTip(
    btn_mostrar_block_secciones,
    "Mostrar Visor Block Secciones"
)

#IZQUIERDA FIN CENTRO SUPERIOR
#AFIRMACION
lbl_block_afirmacion_secciones_x_fin_menos = ttk.Label(
    frame_block_secciones_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_x_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_x_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_x_fin_menos
    )
)

lbl_block_afirmacion_secciones_x_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

#OPCIONES
lbl_block_opciones_secciones_x_fin_menos = ttk.Label(
    frame_block_secciones_centro_superior,
    text="⬅",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_x_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_x_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_x_fin_menos
    )
)

lbl_block_opciones_secciones_x_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

frame_block_secciones_centro_inferior = ttk.Frame(frame_cinco)
frame_block_secciones_centro_inferior.pack(pady=0)

#DERECHA INICIO CENTRO INFERIOR
#OPCIONES
lbl_block_opciones_secciones_x_inicio_mas = ttk.Label(
    frame_block_secciones_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_x_inicio_mas.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_x_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_x_inicio_mas
    )
)

lbl_block_opciones_secciones_x_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

#AFIRMACION
lbl_block_afirmacion_secciones_x_inicio_mas = ttk.Label(
    frame_block_secciones_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_x_inicio_mas.pack(
    side="left",
    padx=0
)

lbl_block_afirmacion_secciones_x_inicio_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_x_inicio_mas
    )
)

lbl_block_afirmacion_secciones_x_inicio_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

lbl_guardar_block_secciones = ttk.Label(
    frame_block_secciones_centro_inferior,
    text="Ó",
    font=("Webdings", 22, "normal"),
    foreground="white",
    cursor="hand2"
)

lbl_guardar_block_secciones.pack(
    side="left",
    padx=0
)

lbl_guardar_block_secciones.bind(
    "<Button-1>",
    lambda event: guardar_calibracion_block_secciones()
)

ToolTip(
    lbl_guardar_block_secciones,
    "BlockSecciones SNAPSHOT")

#DERECHA FIN CENTRO INFERIOR
#AFIRMACION
lbl_block_afirmacion_secciones_x_fin_mas = ttk.Label(
    frame_block_secciones_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_x_fin_mas.pack(
    side="left",
    padx=0
)

lbl_block_afirmacion_secciones_x_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_x_fin_mas
    )
)

lbl_block_afirmacion_secciones_x_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

#OPCIONES
lbl_block_opciones_secciones_x_fin_mas = ttk.Label(
    frame_block_secciones_centro_inferior,
    text="➡",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_x_fin_mas.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_x_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_x_fin_mas
    )
)

lbl_block_opciones_secciones_x_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

##################

frame_block_secciones_inferior = ttk.Frame(frame_cinco)
frame_block_secciones_inferior.pack(pady=0)

#ARRIBA Y ABAJO INFERIOR
#AFIRMACION
lbl_block_afirmacion_secciones_y_fin_menos = ttk.Label(
    frame_block_secciones_inferior,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_y_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_y_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_y_fin_menos
    )
)

lbl_block_afirmacion_secciones_y_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_afirmacion_secciones_abajo = ttk.Label(
    frame_block_secciones_inferior,
    text="🔻",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_abajo.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_abajo.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_afirmacion_abajo
    )
)

lbl_block_afirmacion_secciones_abajo.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_afirmacion_secciones_y_fin_mas = ttk.Label(
    frame_block_secciones_inferior,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="cyan",
    cursor="hand2"
)

lbl_block_afirmacion_secciones_y_fin_mas.pack(
    side="left",
    padx=1
)

lbl_block_afirmacion_secciones_y_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_y_fin_mas
    )
)

lbl_block_afirmacion_secciones_y_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

frame_block_secciones_inferior_dos = ttk.Frame(frame_cinco)
frame_block_secciones_inferior_dos.pack(pady=1)

#OPCIONES
lbl_block_opciones_secciones_y_fin_menos = ttk.Label(
    frame_block_secciones_inferior_dos,
    text="⬆",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_y_fin_menos.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_y_fin_menos.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_y_fin_menos
    )
)

lbl_block_opciones_secciones_y_fin_menos.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_opciones_secciones_abajo = ttk.Label(
    frame_block_secciones_inferior_dos,
    text="🔻",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_abajo.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_abajo.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_mover_abajo
    )
)

lbl_block_opciones_secciones_abajo.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)

lbl_block_opciones_secciones_y_fin_mas = ttk.Label(
    frame_block_secciones_inferior_dos,
    text="⬇",
    font=("Segoe UI Emoji", 12, "bold"),
    foreground="#FF7F50",
    cursor="hand2"
)

lbl_block_opciones_secciones_y_fin_mas.pack(
    side="left",
    padx=1
)

lbl_block_opciones_secciones_y_fin_mas.bind(
    "<ButtonPress-1>",
    lambda event: iniciar_repeticion_flecha(
        block_secciones_opciones_y_fin_mas
    )
)

lbl_block_opciones_secciones_y_fin_mas.bind(
    "<ButtonRelease-1>",
    detener_repeticion_flecha
)





