import threading
import urllib.request

# ========================================================
# CONFIGURACIÓN
# ========================================================

TOPICO_NTFY = "mirrorsync-alerts"

notificaciones_activas = False

# ========================================================
# ESTADO
# ========================================================

def notificaciones_estan_activas():
    return notificaciones_activas

def cambiar_estado_notificaciones():

    global notificaciones_activas

    notificaciones_activas = (
        not notificaciones_activas
    )

    estado = (
        "ACTIVADAS"
        if notificaciones_activas
        else "DESACTIVADAS"
    )

    print(
        f"[NOTIFICACIONES] {estado}"
    )

    return notificaciones_activas

# ========================================================
# ENVÍO
# ========================================================

def _enviar_ntfy(titulo, mensaje, prioridad):

    try:

        url = (
            f"https://ntfy.sh/"
            f"{TOPICO_NTFY}"
        )

        request = urllib.request.Request(
            url,
            data=mensaje.encode("utf-8"),
            method="POST",
            headers={
                "Title": titulo,
                "Priority": prioridad,
                "Tags": "warning",
                "Connection": "close"
            }
        )

        opener = urllib.request.build_opener()

        with opener.open(
            request,
            timeout=10
        ) as respuesta:

            respuesta.read()

        opener.close()

        print(
            "[NOTIFICACIONES] "
            "Notificación enviada."
        )

    except Exception as e:

        print(
            "[NOTIFICACIONES] "
            f"Error enviando notificación: {e}"
        )

def enviar_notificacion(
    mensaje,
    titulo="MirrorSync",
    prioridad="urgent"
):

    if not notificaciones_activas:
        return

    hilo = threading.Thread(
        target=_enviar_ntfy,
        args=(
            titulo,
            mensaje,
            prioridad
        ),
        daemon=True
    )

    hilo.start()