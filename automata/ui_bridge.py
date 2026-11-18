import queue

cola_ui_automata = queue.Queue()

def solicitar_guardado_grabacion():

    cola_ui_automata.put(
        "guardar_grabacion"
    )

def obtener_solicitud_ui():

    try:

        return cola_ui_automata.get_nowait()

    except queue.Empty:

        return None