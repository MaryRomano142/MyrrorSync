# ============================================================
# MODO DE IMAGEN
# ============================================================

from core.debug import debug

from core.sound import reproducir

MODO_NORMAL = "normal"
MODO_REFORZADO = "reforzado"

modo_imagen = MODO_NORMAL


def establecer_modo(
    modo
):

    global modo_imagen

    if modo not in (
        MODO_NORMAL,
        MODO_REFORZADO
    ):

        print(
            "[CAPTURADOR] "
            f"Modo de imagen inválido: {modo}"
        )

        return

    modo_imagen = modo

    debug(
        "[CAPTURADOR] "
        f"Modo de imagen: "
        f"{modo_imagen.upper()}"
    )


def obtener_modo():

    return modo_imagen


def captura_reforzada_activa():

    return (
        modo_imagen
        == MODO_REFORZADO
    )

# ============================================================
# MODO ARRASTRE INTELIGENTE
#
# Es independiente de NORMAL / REFORZADO.
#
# Por lo tanto pueden existir:
#
# NORMAL + ARRASTRE INTELIGENTE
# REFORZADO + ARRASTRE INTELIGENTE
# ============================================================

arrastre_inteligente_activo_estado = False

def activar_arrastre_inteligente():

    global arrastre_inteligente_activo_estado

    arrastre_inteligente_activo_estado = True

    print(
        "[CAPTURADOR] "
        "Arrastre Inteligente ACTIVADO"
    )

    reproducir("arrastreinteligenteactivado")


def desactivar_arrastre_inteligente():

    global arrastre_inteligente_activo_estado

    arrastre_inteligente_activo_estado = False

    print(
        "[CAPTURADOR] "
        "Arrastre Inteligente DESACTIVADO"
    )

    reproducir("arrastreinteligentedesactivado")


def cambiar_arrastre_inteligente():

    if arrastre_inteligente_activo():

        desactivar_arrastre_inteligente()

    else:

        activar_arrastre_inteligente()


def arrastre_inteligente_activo():

    return (
        arrastre_inteligente_activo_estado
    )