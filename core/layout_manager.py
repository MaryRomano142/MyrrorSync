import win32gui
import win32con
import json
import os

def obtener_distribucion(hwnd):

    if not hwnd:
        return None

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    return {
        "x": left,
        "y": top,
        "ancho": right - left,
        "alto": bottom - top
    }

def guardar_json(datos,nombre="distribucion.json"):

    ruta = os.path.join(
        "data",
        nombre
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            indent=4,
            ensure_ascii=False
        )

def guardar_distribucion(
    maestra=None,
    esclava1=None,
    esclava2=None,
    esclava3=None,
    esclava4=None,
    esclava5=None,
    esclava6=None,
    esclava7=None,
    esclava8=None,
    esclava9=None,
    esclava10=None,
    nombre="distribucion.json"
):

    datos = {}

    ventanas = {
        "maestra": maestra,
        "esclava1": esclava1,
        "esclava2": esclava2,
        "esclava3": esclava3,
        "esclava4": esclava4,
        "esclava5": esclava5,
        "esclava6": esclava6,
        "esclava7": esclava7,
        "esclava8": esclava8,
        "esclava9": esclava9,
        "esclava10": esclava10
    }

    for nombre_ventana, ventana in ventanas.items():

        if ventana:

            datos[nombre_ventana] = obtener_distribucion(
                ventana["hwnd"]
            )

    guardar_json(
        datos,
        nombre
    )

    print(
        "Distribución guardada."
    )

def mover_ventana(hwnd, datos):

    if not hwnd or not datos:
        return

    # ========================================================
    # RESTAURAR SI ESTÁ MINIMIZADA
    # ========================================================

    if win32gui.IsIconic(hwnd):

        win32gui.ShowWindow(
            hwnd,
            win32con.SW_RESTORE
        )

    # ========================================================
    # APLICAR DISTRIBUCIÓN GUARDADA
    # ========================================================

    win32gui.MoveWindow(
        hwnd,
        datos["x"],
        datos["y"],
        datos["ancho"],
        datos["alto"],
        True
    )

def leer_json(nombre="distribucion.json"):

    ruta = os.path.join(
        "data",
        nombre
    )

    if not os.path.exists(
        ruta
    ):
        return None

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )

def restaurar_distribucion(
    maestra=None,
    esclava1=None,
    esclava2=None,
    esclava3=None,
    esclava4=None,
    esclava5=None,
    esclava6=None,
    esclava7=None,
    esclava8=None,
    esclava9=None,
    esclava10=None,
    nombre="distribucion.json"
):

    datos = leer_json(
        nombre
    )

    if not datos:

        print(
            "No existe una distribución guardada."
        )

        return

    ventanas = {
        "maestra": maestra,
        "esclava1": esclava1,
        "esclava2": esclava2,
        "esclava3": esclava3,
        "esclava4": esclava4,
        "esclava5": esclava5,
        "esclava6": esclava6,
        "esclava7": esclava7,
        "esclava8": esclava8,
        "esclava9": esclava9,
        "esclava10": esclava10
    }

    for nombre_ventana, ventana in ventanas.items():

        if (
            ventana
            and nombre_ventana in datos
        ):

            mover_ventana(
                ventana["hwnd"],
                datos[nombre_ventana]
            )

            print(
                f"{nombre_ventana} restaurada."
            )

        else:

            print(
                f"{nombre_ventana} omitida."
            )