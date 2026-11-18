import cv2

UMBRAL_SIMILITUD = 0.66

def buscar_opcion_en_region(
    imagen_region,
    ruta_opcion,
    max_candidatos=8
):

    if imagen_region is None:
        return []

    opcion = cv2.imread(
        ruta_opcion
    )

    if opcion is None:

        print(
            f"No se pudo abrir: "
            f"{ruta_opcion}"
        )

        return []

    region_gris = cv2.cvtColor(
        imagen_region,
        cv2.COLOR_BGR2GRAY
    )

    opcion_gris = cv2.cvtColor(
        opcion,
        cv2.COLOR_BGR2GRAY
    )

    alto_opcion, ancho_opcion = (
        opcion_gris.shape
    )

    alto_region, ancho_region = (
        region_gris.shape
    )

    if (
        ancho_opcion > ancho_region
        or alto_opcion > alto_region
    ):

        return []

    resultado = cv2.matchTemplate(
        region_gris,
        opcion_gris,
        cv2.TM_CCOEFF_NORMED
    )

    candidatos = []

    # Copia porque vamos a "borrar"
    # coincidencias después de seleccionarlas.
    mapa = resultado.copy()

    for _ in range(max_candidatos):

        _, similitud, _, posicion = (
            cv2.minMaxLoc(mapa)
        )

        if similitud < UMBRAL_SIMILITUD:
            break

        x, y = posicion

        centro_x = (
            x + ancho_opcion // 2
        )

        centro_y = (
            y + alto_opcion // 2
        )

        candidatos.append({

            "x": centro_x,

            "y": centro_y,

            "similitud": float(
                similitud
            ),

            "ancho": ancho_opcion,

            "alto": alto_opcion
        })

        # ==========================================
        # ANULAR ESTA ZONA PARA BUSCAR OTRO MATCH
        # ==========================================

        margen_x = max(
            10,
            ancho_opcion // 2
        )

        margen_y = max(
            10,
            alto_opcion // 2
        )

        x1 = max(
            0,
            x - margen_x
        )

        y1 = max(
            0,
            y - margen_y
        )

        x2 = min(
            mapa.shape[1],
            x + margen_x
        )

        y2 = min(
            mapa.shape[0],
            y + margen_y
        )

        mapa[
            y1:y2,
            x1:x2
        ] = -1.0

    return candidatos

