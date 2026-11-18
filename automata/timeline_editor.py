import json
import copy

from automata.events import (
    CLICK_ESPEJO,
    CLICK_MANUAL,
    ESCRITURA,
    INSPECTOR_AVANCE,
    VIGILAR_VULNERABILIDAD,
    CRONOMETRO_VIDEO,
    INTERVENCION_USUARIO,
)

def cargar_timeline_editor(ruta):

    try:

        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as archivo:

            timeline = json.load(
                archivo
            )

        if not isinstance(
            timeline,
            list
        ):

            return None

        return timeline

    except Exception as e:

        print(
            "[EDITOR TIMELINE] "
            "Error cargando:"
        )

        print(e)

        return None

def guardar_timeline_editor(ruta,timeline):

    try:

        with open(
            ruta,
            "w",
            encoding="utf-8"
        ) as archivo:

            json.dump(
                timeline,
                archivo,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as e:

        print(
            "[EDITOR TIMELINE] "
            "Error guardando:"
        )

        print(e)

        return False

def buscar_evento(timeline,orden):

    for evento in timeline:

        if evento.get(
            "orden"
        ) == orden:

            return evento

    return None

def marcar_escritura_variable(timeline,orden,nombre_variable):

    evento = buscar_evento(
        timeline,
        orden
    )

    if evento is None:

        return "no_encontrado"

    if evento.get(
        "tipo"
    ) != ESCRITURA:

        return "no_escritura"

    nombre_variable = (
        nombre_variable
        .strip()
        .upper()
    )

    if not nombre_variable:

        return "nombre_vacio"

    evento[
        "variable_escritura"
    ] = nombre_variable

    return "ok"

def buscar_indice_evento(timeline,orden):

    for indice, evento in enumerate(
        timeline
    ):

        if evento.get(
            "orden"
        ) == orden:

            return indice

    return None

def reordenar_timeline(timeline):

    for orden, evento in enumerate(
        timeline,
        1
    ):

        evento["orden"] = orden

def modificar_evento(timeline,orden,nuevo_evento):

    indice = buscar_indice_evento(
        timeline,
        orden
    )

    if indice is None:

        return False

    # La posición de timeline manda.
    # Evitamos que editar manualmente "orden"
    # rompa la secuencia.
    nuevo_evento["orden"] = orden

    timeline[indice] = (
        nuevo_evento
    )

    return True

#Borrado individual, Ej Orden: 15; Orden: 16, etc
def eliminar_evento(timeline,orden):

    indice = buscar_indice_evento(
        timeline,
        orden
    )

    if indice is None:

        return False

    timeline.pop(
        indice
    )

    reordenar_timeline(
        timeline
    )

    return True

#Borrado colectivo, Ej Orden: 14, 15, 16; Orden: 14-16; Orden 14-16, 18, 21-25
def eliminar_eventos(timeline, ordenes):

    if not ordenes:
        return False

    ordenes = set(
        ordenes
    )

    cantidad_original = len(
        timeline
    )

    timeline[:] = [
        evento
        for evento in timeline
        if evento.get("orden") not in ordenes
    ]

    if len(timeline) == cantidad_original:
        return False

    reordenar_timeline(
        timeline
    )

    return True

def duplicar_evento(timeline,orden,cantidad):

    if cantidad <= 0:
        return False

    indice = buscar_indice_evento(
        timeline,
        orden
    )

    if indice is None:

        return False

    evento_original = (
        timeline[indice]
    )

    copias = []

    for _ in range(
        cantidad
    ):

        copia = copy.deepcopy(
            evento_original
        )

        copias.append(
            copia
        )

    posicion = (
        indice + 1
    )

    timeline[
        posicion:
        posicion
    ] = copias

    reordenar_timeline(
        timeline
    )

    return True

def modificar_inspectores_avance(timeline,segundos):

    modificados = 0

    for evento in timeline:

        if evento.get(
            "tipo"
        ) == "inspector_avance":

            evento["segundos"] = segundos

            modificados += 1

    return modificados

def insertar_vigilar_vulnerabilidad(timeline,orden):

    if orden < 1:

        return False

    if orden > len(timeline) + 1:

        return False

    nuevo_evento = {
        "orden": orden,
        "tipo": "vigilar_vulnerabilidad"
    }

    indice_insercion = (
        orden - 1
    )

    timeline.insert(
        indice_insercion,
        nuevo_evento
    )

    reordenar_timeline(
        timeline
    )

    return True

def insertar_inspector_avance(timeline,orden):

    if orden < 1:
        return False

    if orden > len(timeline) + 1:
        return False

    nuevo_evento = {
        "orden": orden,
        "tipo": INSPECTOR_AVANCE,
        "segundos": 2 #tiempo entre pantallas
    }

    indice_insercion = (
        orden - 1
    )

    timeline.insert(
        indice_insercion,
        nuevo_evento
    )

    reordenar_timeline(
        timeline
    )

    return True

def insertar_intervencion_usuario(timeline, orden):

    if orden < 1:
        return False

    if orden > len(timeline) + 1:
        return False

    nuevo_evento = {
        "orden": orden,
        "tipo": INTERVENCION_USUARIO
    }

    indice_insercion = (
        orden - 1
    )

    timeline.insert(
        indice_insercion,
        nuevo_evento
    )

    reordenar_timeline(
        timeline
    )

    return True

def insertar_cronometro_video(timeline, orden):

    if orden < 1:
        return False

    if orden > len(timeline) + 1:
        return False

    nuevo_evento = {
        "orden": orden,
        "tipo": CRONOMETRO_VIDEO,
        "segundos": 4
    }

    indice_insercion = (
        orden - 1
    )

    timeline.insert(
        indice_insercion,
        nuevo_evento
    )

    reordenar_timeline(
        timeline
    )

    return True