import os
import json
import shutil

from core.debug import debug

from core.sound import reproducir

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CARPETA_GRABACIONES = os.path.join(
    BASE_DIR,
    "grabaciones"
)

CARPETA_TEMPORAL = os.path.join(
    CARPETA_GRABACIONES,
    "_temporal"
)

MAX_GRABACIONES = 56

def listar_grabaciones():

    os.makedirs(
        CARPETA_GRABACIONES,
        exist_ok=True
    )

    grabaciones = []

    for nombre in os.listdir(
        CARPETA_GRABACIONES
    ):

        if nombre == "_temporal":
            continue

        ruta = os.path.join(
            CARPETA_GRABACIONES,
            nombre
        )

        if os.path.isdir(
            ruta
        ):

            grabaciones.append(
                nombre
            )

    grabaciones.sort(
        key=str.lower
    )

    return grabaciones

def nombre_grabacion_valido(nombre):

    if not nombre:
        return False

    nombre = nombre.strip()

    if not nombre:
        return False

    caracteres_invalidos = (
        '<>:"/\\|?*'
    )

    for caracter in caracteres_invalidos:

        if caracter in nombre:
            return False

    if nombre.endswith(
        "."
    ):

        return False

    return True

def guardar_grabacion_permanente(nombre):

    nombre = nombre.strip()

    if not nombre_grabacion_valido(
        nombre
    ):

        return (
            False,
            "Nombre inválido."
        )

    grabaciones = listar_grabaciones()

    if len(grabaciones) >= MAX_GRABACIONES:

        return (
            False,
            "Se alcanzó el máximo de 56 grabaciones por semana."
        )

    destino = os.path.join(
        CARPETA_GRABACIONES,
        nombre
    )

    if os.path.exists(
        destino
    ):

        return (
            False,
            "Ya existe una grabación con ese nombre."
        )

    timeline = os.path.join(
        CARPETA_TEMPORAL,
        "timeline.json"
    )

    if not os.path.exists(
        timeline
    ):

        return (
            False,
            "No existe una grabación temporal."
        )

    try:

        os.rename(
            CARPETA_TEMPORAL,
            destino
        )

    except OSError:

        # Por si Windows no permite el rename
        # directamente en alguna situación.
        try:

            shutil.move(
                CARPETA_TEMPORAL,
                destino
            )

        except Exception as e:

            return (
                False,
                f"No se pudo guardar la grabación: {e}"
            )

    print(
        "[AUTOMATA] Grabación guardada:"
    )

    print(
        destino
    )

    reproducir("automatagrabando")

    return (
        True,
        destino
    )

def descartar_grabacion_temporal():

    if not os.path.isdir(
        CARPETA_TEMPORAL
    ):
        return

    try:

        shutil.rmtree(
            CARPETA_TEMPORAL
        )

        print(
            "[AUTOMATA] "
            "Grabación temporal descartada."
        )

    except Exception as e:

        print(
            "[AUTOMATA] "
            "No se pudo descartar la temporal:"
        )

        print(e)

def eliminar_grabacion(nombre):

    if not nombre:
        return (
            False,
            "Grabación inválida."
        )

    ruta = os.path.join(
        CARPETA_GRABACIONES,
        nombre
    )

    if not os.path.isdir(
        ruta
    ):

        return (
            False,
            "La grabación no existe."
        )

    try:

        shutil.rmtree(
            ruta
        )

    except Exception as e:

        return (
            False,
            f"No se pudo eliminar: {e}"
        )

    print(
        f"[AUTOMATA] "
        f"Grabación eliminada: {nombre}"
    )

    return (
        True,
        nombre
    )

def preparar_grabacion_temporal():

    # ========================================================
    # ASEGURAR CARPETA GENERAL DE GRABACIONES
    # ========================================================

    os.makedirs(
        CARPETA_GRABACIONES,
        exist_ok=True
    )

    # ========================================================
    # LIMPIAR TEMPORAL ANTERIOR
    # ========================================================

    if os.path.isdir(
        CARPETA_TEMPORAL
    ):

        shutil.rmtree(
            CARPETA_TEMPORAL
        )

    # ========================================================
    # CREAR NUEVA GRABACIÓN TEMPORAL
    # ========================================================

    os.makedirs(
        CARPETA_TEMPORAL,
        exist_ok=True
    )

    carpeta_eventos = os.path.join(
        CARPETA_TEMPORAL,
        "eventos"
    )

    os.makedirs(
        carpeta_eventos,
        exist_ok=True
    )

    print(
        "[AUTOMATA] "
        "Carpeta temporal preparada."
    )

def guardar_timeline(eventos):

    # ========================================================
    # ASEGURAR CARPETA TEMPORAL
    # ========================================================

    os.makedirs(
        CARPETA_TEMPORAL,
        exist_ok=True
    )

    # ========================================================
    # RUTA DEL TIMELINE
    # ========================================================

    ruta_timeline = os.path.join(
        CARPETA_TEMPORAL,
        "timeline.json"
    )

    # ========================================================
    # GUARDAR EVENTOS
    # ========================================================

    try:

        with open(
            ruta_timeline,
            "w",
            encoding="utf-8"
        ) as archivo:

            json.dump(
                eventos,
                archivo,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:

        print()
        print(
            "[AUTOMATA] "
            "Error guardando timeline:"
        )

        print(e)

        return False

    debug(
        "[AUTOMATA] Timeline guardada:"
    )

    debug(
        ruta_timeline
    )

    return True

def crear_carpeta_evento(tipo_evento,orden):

    # ========================================================
    # ASEGURAR CARPETA TEMPORAL
    # ========================================================

    os.makedirs(
        CARPETA_TEMPORAL,
        exist_ok=True
    )

    # ========================================================
    # CARPETA GENERAL DE EVENTOS
    # ========================================================

    carpeta_eventos = os.path.join(
        CARPETA_TEMPORAL,
        "eventos"
    )

    os.makedirs(
        carpeta_eventos,
        exist_ok=True
    )

    # ========================================================
    # NOMBRE DEL EVENTO
    # ========================================================

    nombre_carpeta = (
        f"{tipo_evento}_"
        f"{orden:04d}"
    )

    ruta_evento = os.path.join(
        carpeta_eventos,
        nombre_carpeta
    )

    # ========================================================
    # CREAR CARPETA
    # ========================================================

    os.makedirs(
        ruta_evento,
        exist_ok=True
    )

    return ruta_evento
