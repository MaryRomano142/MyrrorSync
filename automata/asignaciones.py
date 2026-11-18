MAX_ASIGNACIONES = 10

asignaciones = []


def obtener_asignaciones():

    return asignaciones.copy()


def hay_asignaciones():

    return len(asignaciones) > 0


def agregar_asignacion(grabacion,ventana):

    if len(asignaciones) >= MAX_ASIGNACIONES:

        return (
            False,
            "Se alcanzó el máximo de 10 asignaciones."
        )

    # Una esclava solamente puede tener
    # una grabación asignada.
    for asignacion in asignaciones:

        if (
            asignacion["ventana"]["hwnd"]
            == ventana["hwnd"]
        ):

            return (
                False,
                "Esta esclava ya tiene una grabación asignada."
            )

    asignaciones.append({

        "grabacion":
            grabacion,

        "ventana":
            ventana,

        "variables_escritura":
            {}
    })

    return (
        True,
        "Asignación creada."
    )

def eliminar_asignacion(indice):

    if (
        indice < 0
        or indice >= len(asignaciones)
    ):

        return False

    asignaciones.pop(
        indice
    )

    return True

def actualizar_variables_escritura(indice,valores):

    if (
        indice < 0
        or indice >= len(asignaciones)
    ):

        return False

    asignaciones[indice][
        "variables_escritura"
    ] = valores.copy()

    return True

def asignacion_sigue_existiendo(asignacion):

    hwnd = asignacion.get(
        "ventana",
        {}
    ).get(
        "hwnd"
    )

    grabacion = asignacion.get(
        "grabacion"
    )

    for asignacion_actual in asignaciones:

        ventana_actual = asignacion_actual.get(
            "ventana",
            {}
        )

        if (
            asignacion_actual.get("grabacion") == grabacion
            and ventana_actual.get("hwnd") == hwnd
        ):

            return True

    return False

def limpiar_asignaciones():

    asignaciones.clear()