import tkinter as tk
import win32api
import win32con
import win32gui

ventana_coords = None
label_coords = None

# Distancia respecto de la punta del mouse
OFFSET_X = 16
OFFSET_Y = 18

# Velocidad de actualización
ACTUALIZACION_MS = 20

def hacer_click_through(ventana):

    # Forzar a Tkinter a crear completamente la ventana
    ventana.update_idletasks()
    ventana.update()

    # HWND interno de Tkinter
    hwnd_tk = ventana.winfo_id()

    # HWND real de la ventana superior de Windows
    hwnd = win32gui.GetParent(hwnd_tk)

    # Por seguridad, si no tiene padre usamos el original
    if hwnd == 0:
        hwnd = hwnd_tk

    estilo = win32gui.GetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE
    )

    estilo |= win32con.WS_EX_TRANSPARENT
    estilo |= win32con.WS_EX_TOOLWINDOW
    estilo |= win32con.WS_EX_NOACTIVATE

    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        estilo
    )

def iniciar_visor_coordenadas(root):

    global ventana_coords
    global label_coords

    # Evitar crear dos visores
    if ventana_coords is not None:
        return

    ventana_coords = tk.Toplevel(root)

    # Sin marco ni barra de título
    ventana_coords.overrideredirect(True)

    # Siempre encima
    ventana_coords.attributes(
        "-topmost",
        True
    )

    # Un poco transparente, bajar el valor para mas transparencia
    ventana_coords.attributes(
        "-alpha",
        0.78
    )

    # Fondo
    ventana_coords.configure(
        bg="#111111"
    )

    label_coords = tk.Label(
        ventana_coords,

        text="X: 0  Y: 0",

        font=(
            "Consolas",
            9,
            "bold"
        ),

        bg="#111111",
        fg="#00FFFF",

        padx=6,
        pady=2
    )

    label_coords.pack()

    # Hacer que no intercepte clics
    hacer_click_through(
        ventana_coords
    )

    actualizar_coordenadas()

def actualizar_coordenadas():

    if ventana_coords is None:
        return

    try:

        x, y = win32api.GetCursorPos()

        label_coords.config(
            text=f"X:{x}  Y:{y}"
        )

        ventana_coords.geometry(
            f"+{x + OFFSET_X}+{y + OFFSET_Y}"
        )

        ventana_coords.after(
            ACTUALIZACION_MS,
            actualizar_coordenadas
        )

    except tk.TclError:
        return

def ocultar_visor_coordenadas():

    if ventana_coords is not None:

        try:
            ventana_coords.withdraw()
        except tk.TclError:
            pass

def mostrar_visor_coordenadas():

    if ventana_coords is not None:

        try:
            ventana_coords.deiconify()
            ventana_coords.attributes(
                "-topmost",
                True
            )
        except tk.TclError:
            pass