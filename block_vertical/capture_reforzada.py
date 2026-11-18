import cv2


def mejorar_imagen_block_vertical(
    imagen
):

    if imagen is None:
        return None

    # ========================================================
    # ESCALA DE GRISES
    # ========================================================

    if len(imagen.shape) == 3:

        gris = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGR2GRAY
        )

    else:

        gris = imagen.copy()

    # ========================================================
    # CONTRASTE LOCAL
    #
    # Queremos hacer más visibles:
    #
    # - radios muy finos
    # - checkbox
    # - bordes de celdas
    # - elementos azulados muy tenues
    # ========================================================

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(6, 6)
    )

    contraste = clahe.apply(
        gris
    )

    # ========================================================
    # ENFOQUE
    # ========================================================

    suavizada = cv2.GaussianBlur(
        contraste,
        (0, 0),
        0.8
    )

    nitida = cv2.addWeighted(
        contraste,
        1.9,
        suavizada,
        -0.9,
        0
    )

    # ========================================================
    # VOLVER A BGR
    #
    # El detector actual seguirá recibiendo una imagen
    # normal de 3 canales.
    # ========================================================

    reforzada = cv2.cvtColor(
        nitida,
        cv2.COLOR_GRAY2BGR
    )

    return reforzada