import os
import shutil

from automata.events import (
    TIPOS_CLICK,
    INSPECTOR_AVANCE,
)

from automata.storage import (
    CARPETA_TEMPORAL
)

eventos = []
registro_habilitado = False
contador_pantallas_grabacion = 1

def limpiar_eventos():

    global eventos
    global contador_pantallas_grabacion

    eventos = []

    contador_pantallas_grabacion = 1

def registrar_evento(evento):

    global contador_pantallas_grabacion

    if not registro_habilitado:
        return

    avanzar_pantalla = False

    if eventos:

        ultimo_evento = eventos[-1]

        avanzar_pantalla = (
            ultimo_evento.get("tipo")
            == INSPECTOR_AVANCE
            and evento.get("tipo")
            in TIPOS_CLICK
        )

    evento["orden"] = (
        len(eventos) + 1
    )

    eventos.append(
        evento
    )

    if evento["tipo"] == "scroll_espejo":

        print(
            f"[AUTOMATA] "
            f"EVENTO {evento['orden']} "
            f"→ {evento['tipo']} "
            f"| delta={evento.get('delta', 0)}"
        )

    else:

        print(
            f"[AUTOMATA] "
            f"EVENTO {evento['orden']} "
            f"→ {evento['tipo']}"
        )

    if avanzar_pantalla:

        contador_pantallas_grabacion += 1

        print(
            f"\n<<<<<<<<<<<<<<<<<<<< PANTALLA "
            f"{contador_pantallas_grabacion} "
            f">>>>>>>>>>>>>>>>>>>>"
        )

def obtener_eventos():

    return eventos

def eliminar_ultimo_click():

    if not eventos:
        return

    ultimo = eventos[-1]

    if ultimo.get("tipo") in TIPOS_CLICK:

        eliminado = eventos.pop()

        print(
            "[AUTOMATA] Último clic descartado",
            #eliminado
        )

def eliminar_cierre_final():

    if not eventos:
        return

    # ========================================================
    # CASO 1
    # Inspector de avance + clic final
    #
    # Ambos pertenecen al intento de finalizar
    # el cuestionario y deben descartarse.
    # ========================================================

    if len(eventos) >= 2:

        penultimo = eventos[-2]
        ultimo = eventos[-1]

        es_inspector = (
            penultimo.get("tipo")
            == INSPECTOR_AVANCE
        )

        es_click_final = (
            ultimo.get("tipo")
            in TIPOS_CLICK
        )

        if (
            es_inspector
            and es_click_final
        ):

            eventos.pop()
            eventos.pop()

            print(
                "[AUTOMATA] "
                "Cierre final descartado: "
                "Inspector + clic."
            )

            return

    # ========================================================
    # CASO 2
    # Solamente quedó un clic al final
    # ========================================================

    ultimo = eventos[-1]

    if ultimo.get("tipo") in TIPOS_CLICK:

        eventos.pop()

        print(
            "[AUTOMATA] "
            "Cierre final descartado: "
            "último clic."
        )

def siguiente_orden():

    return len(eventos) + 1

def establecer_registro_habilitado(habilitado):

    global registro_habilitado

    registro_habilitado = habilitado

def borrar_ultimo_evento():

    if not eventos:

        print(
            "[AUTOMATA] "
            "No hay eventos para borrar."
        )

        return None

    evento = eventos[-1]

    print(
        "[AUTOMATA] "
        f"Borrando evento "
        f"{evento.get('orden')}: "
        f"{evento.get('tipo')}"
    )

    # ========================================================
    # BORRAR CARPETA ASOCIADA SI EXISTE
    # ========================================================

    carpeta = evento.get(
        "carpeta"
    )

    if carpeta:

        ruta_carpeta = os.path.join(
            CARPETA_TEMPORAL,
            "eventos",
            carpeta
        )

        if os.path.isdir(
            ruta_carpeta
        ):

            try:

                shutil.rmtree(
                    ruta_carpeta
                )

                print(
                    "[AUTOMATA] "
                    f"Carpeta eliminada: "
                    f"{carpeta}"
                )

            except Exception as e:

                print(
                    "[AUTOMATA] "
                    "No se pudo eliminar "
                    "la carpeta:"
                )

                print(
                    e
                )

    # ========================================================
    # BORRAR EVENTO
    # ========================================================

    evento_borrado = eventos.pop()

    # ========================================================
    # RENUMERAR
    # ========================================================

    for indice, evento_actual in enumerate(
        eventos,
        1
    ):

        evento_actual["orden"] = (
            indice
        )

    print(
        "[AUTOMATA] "
        f"Eventos restantes: "
        f"{len(eventos)}"
    )

    return evento_borrado

