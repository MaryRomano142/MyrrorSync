MODO_NORMAL = "normal"
MODO_REFORZADO = "reforzado"

modo_actual = MODO_NORMAL

def establecer_modo(
    modo
):

    global modo_actual

    if modo not in (
        MODO_NORMAL,
        MODO_REFORZADO
    ):

        print(
            "[BLOCK VERTICAL] "
            f"Modo inválido: {modo}"
        )

        return

    modo_actual = modo

    print(
        "[BLOCK VERTICAL] "
        f"Modo de imagen: "
        f"{modo_actual.upper()}"
    )

def obtener_modo():

    return modo_actual

def captura_reforzada_activa():

    return (
        modo_actual
        == MODO_REFORZADO
    )