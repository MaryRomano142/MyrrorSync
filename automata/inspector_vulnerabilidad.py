import json
import urllib.request
import urllib.error
import websocket

PUERTO_CDP = 9222

PUERTOS_CDP_POR_PROCESO = {
    "Chrome": 9222,
    "Chromium": 9223,
    "Aloha": 9224,
    "Comodo": 9225,
    "Avast": 9226,
    "Norton": 9227,
    "Canary": 9228,
    "Thorium": 9229,
    "AVG": 9230,
    "UC": 9231
}

# ============================================================
# INSPECTOR DE VULNERABILIDAD
# ============================================================

INDICADORES_VULNERABILIDAD = (
    "error",
    "danger",
    "invalid",
    #"alert", en linea 188 tambien estaba "alert"
    "warn",
    "warning",
)

def obtener_indicadores_vulnerabilidad():

    return INDICADORES_VULNERABILIDAD

def obtener_paginas_cdp(puerto=PUERTO_CDP):

    url = (
        f"http://127.0.0.1:"
        f"{puerto}/json"
    )

    try:

        with urllib.request.urlopen(
            url,
            timeout=2
        ) as respuesta:

            paginas = json.loads(
                respuesta.read().decode(
                    "utf-8"
                )
            )

    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError
    ) as error:

        print(
            "[VULNERABILIDAD] "
            "No se pudo conectar con CDP."
        )

        print(
            f"[VULNERABILIDAD] {error}"
        )

        return []

    paginas_web = []

    for pagina in paginas:

        if pagina.get(
            "type"
        ) != "page":

            continue

        paginas_web.append(
            pagina
        )

    print(
        "[VULNERABILIDAD] "
        f"Páginas detectadas por CDP: "
        f"{len(paginas_web)}"
    )

    for indice, pagina in enumerate(paginas_web,start=1):

        print()
        print(
            "[VULNERABILIDAD] "
            f"Página {indice}"
        )

        print(
            "[VULNERABILIDAD] "
            f"Título: "
            f"{pagina.get('title', '')}"
        )

        print(
            "[VULNERABILIDAD] "
            f"URL: "
            f"{pagina.get('url', '')}"
        )

        print(
            "[VULNERABILIDAD] "
            f"ID: "
            f"{pagina.get('id', '')}"
        )

        print(
            "[VULNERABILIDAD] "
            f"WebSocket: "
            f"{pagina.get('webSocketDebuggerUrl', '')}"
        )

    return paginas_web

def obtener_websocket_pagina(
    puerto=PUERTO_CDP
):

    paginas = obtener_paginas_cdp(
        puerto
    )

    if not paginas:
        return None

    pagina_activa = paginas[0]

    websocket_url = (
        pagina_activa.get(
            "webSocketDebuggerUrl"
        )
    )

    if websocket_url:

        print(
            "[VULNERABILIDAD] "
            "Página activa encontrada."
        )

        print(
            "[VULNERABILIDAD] "
            f"Título activo: "
            f"{pagina_activa.get('title', '')}"
        )

        return websocket_url

    print(
        "[VULNERABILIDAD] "
        "La página activa no tiene WebSocket."
    )

    return None

def detectar_vulnerabilidad_dom(puerto=PUERTO_CDP):

    websocket_url = (
        obtener_websocket_pagina(puerto)
    )

    if not websocket_url:

        print(
            "[VULNERABILIDAD] "
            "No hay página disponible."
        )

        return False

    expresion = """
    (() => {

        const indicadores = [
            "error",
            "danger",
            "invalid",
            "warn",
            "warning"
        ];

        const elementos = Array.from(
            document.querySelectorAll("*")
        );

        for (const elemento of elementos) {

            const estilo =
                window.getComputedStyle(
                    elemento
                );

            const visible = (
                estilo.display !== "none" &&
                estilo.visibility !== "hidden" &&
                estilo.opacity !== "0" &&
                elemento.getClientRects().length > 0
            );

            if (!visible) {
                continue;
            }

            const atributos = Array.from(
                elemento.attributes
            );

            for (const atributo of atributos) {

                const nombre =
                    atributo.name.toLowerCase();

                const valor =
                    String(
                        atributo.value
                    ).toLowerCase();

                for (
                    const indicador
                    of indicadores
                ) {

                    if (
                        nombre.includes(
                            indicador
                        ) ||
                        valor.includes(
                            indicador
                        )
                    ) {

                        return {
                            detectado: true,
                            indicador: indicador,
                            atributo: atributo.name,
                            valor: atributo.value,
                            etiqueta:
                                elemento.tagName
                        };
                    }
                }
            }
        }

        return {
            detectado: false
        };

    })()
    """

    conexion = None

    try:

        conexion = websocket.create_connection(
            websocket_url,
            timeout=3
        )

        mensaje = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expresion,
                "returnByValue": True
            }
        }

        conexion.send(
            json.dumps(
                mensaje
            )
        )

        while True:

            respuesta = json.loads(
                conexion.recv()
            )

            if respuesta.get(
                "id"
            ) == 1:

                break

        resultado = (
            respuesta
            .get(
                "result",
                {}
            )
            .get(
                "result",
                {}
            )
            .get(
                "value",
                {}
            )
        )

        if resultado.get(
            "detectado"
        ):

            print()
            print(
                "[VULNERABILIDAD] "
                "⚠ INDICADOR DETECTADO"
            )

            print(
                "[VULNERABILIDAD] "
                f"Indicador: "
                f"{resultado.get('indicador')}"
            )

            print(
                "[VULNERABILIDAD] "
                f"Elemento: "
                f"{resultado.get('etiqueta')}"
            )

            print(
                "[VULNERABILIDAD] "
                f"Atributo: "
                f"{resultado.get('atributo')}"
            )

            print(
                "[VULNERABILIDAD] "
                f"Valor: "
                f"{resultado.get('valor')}"
            )

            return True

        print()
        print(
            "[VULNERABILIDAD] "
            "No se detectó vulnerabilidad."
        )

        return False

    except Exception as error:

        print(
            "[VULNERABILIDAD] "
            "Error inspeccionando el DOM."
        )

        print(
            f"[VULNERABILIDAD] {error}"
        )

        return False

    finally:

        if conexion:

            conexion.close()

def obtener_puerto_cdp_ventana(
    ventana
):

    proceso = ventana.get(
        "proceso",
        ""
    )

    puerto = (
        PUERTOS_CDP_POR_PROCESO
        .get(
            proceso
        )
    )

    if puerto is None:

        print(
            "[VULNERABILIDAD] "
            f"Navegador no reconocido: "
            f"{proceso}"
        )

        return None

    print(
        "[VULNERABILIDAD] "
        f"Navegador: {proceso}"
    )

    print(
        "[VULNERABILIDAD] "
        f"Puerto CDP: {puerto}"
    )

    return puerto