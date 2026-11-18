MODO_NORMAL = "normal"
MODO_REFORZADO = "reforzado"

modo_actual = MODO_NORMAL

def obtener_modo():

    return modo_actual

def establecer_modo(modo):

    global modo_actual

    if modo not in (
        MODO_NORMAL,
        MODO_REFORZADO
    ):
        return

    modo_actual = modo

    print(
        "[BLOCK SECCIONES] "
        f"Modo captura: {modo_actual.upper()}"
    )

def modo_reforzado():

    return (
        modo_actual
        == MODO_REFORZADO
    )