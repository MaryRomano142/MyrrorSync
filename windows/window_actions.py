import win32api
import win32con
import win32gui
import time

from config import (
    PASOS_ARRASTRE,
    TIEMPO_ENTRE_PASOS
)

def obtener_punto_absoluto(hwnd, x_rel, y_rel):

    izquierda, arriba, derecha, abajo = win32gui.GetWindowRect(hwnd)

    return (
        izquierda + x_rel,
        arriba + y_rel
    )

def mover_mouse(x, y):

    win32api.SetCursorPos((x, y))

def click_izquierdo():

    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTDOWN,
        0,
        0
    )

    time.sleep(0.01)

    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTUP,
        0,
        0
    )

def presionar_izquierdo():

    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTDOWN,
        0,
        0
    )

def soltar_izquierdo():

    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTUP,
        0,
        0
    )

def obtener_posicion_mouse():
    return win32api.GetCursorPos()

def restaurar_mouse(posicion):
    win32api.SetCursorPos(posicion)

def traer_ventana_al_frente(hwnd):

    if not win32gui.IsWindow(hwnd):
        return False

    # Si está minimizada, restaurarla.
    if win32gui.IsIconic(hwnd):

        win32gui.ShowWindow(
            hwnd,
            win32con.SW_RESTORE
        )

        time.sleep(0.1)

    # Mostrarla normalmente.
    win32gui.ShowWindow(
        hwnd,
        win32con.SW_SHOW
    )

    # Colocarla arriba.
    win32gui.BringWindowToTop(
        hwnd
    )

    try:

        win32gui.SetForegroundWindow(
            hwnd
        )

    except Exception:

        pass

    time.sleep(0.15)

    return True

def arrastrar_mouse(x1, y1, x2, y2):

    mover_mouse(x1, y1)

    time.sleep(0.05)

    presionar_izquierdo()

    for i in range(PASOS_ARRASTRE + 1):

        t = i / PASOS_ARRASTRE

        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)

        mover_mouse(x, y)

        time.sleep(TIEMPO_ENTRE_PASOS)

    soltar_izquierdo()