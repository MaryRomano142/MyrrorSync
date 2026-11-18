import os
import json
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from automata.asignaciones import (
    obtener_asignaciones,
    actualizar_variables_escritura
)

from automata.storage import (
    CARPETA_GRABACIONES
)


def obtener_variables_grabacion(
    grabacion
):

    ruta_timeline = os.path.join(
        CARPETA_GRABACIONES,
        grabacion,
        "timeline.json"
    )

    if not os.path.exists(
        ruta_timeline
    ):

        print(
            "[CONFIGURACIÓN] "
            "Timeline no encontrada:"
        )

        print(
            ruta_timeline
        )

        return []

    try:

        with open(
            ruta_timeline,
            "r",
            encoding="utf-8"
        ) as archivo:

            timeline = json.load(
                archivo
            )

    except Exception as e:

        print(
            "[CONFIGURACIÓN] "
            "No se pudo leer timeline:"
        )

        print(e)

        return []

    variables = []

    for evento in timeline:

        variable = evento.get(
            "variable_escritura"
        )

        if not variable:

            continue

        variable = (
            str(variable)
            .strip()
            .upper()
        )

        if (
            variable
            and variable not in variables
        ):

            variables.append(
                variable
            )

    print(
        "[CONFIGURACIÓN] "
        f"Variables encontradas en "
        f"{grabacion}: "
        f"{variables}"
    )

    return variables


def abrir_configurar_asignaciones(
    app
):

    asignaciones = (
        obtener_asignaciones()
    )

    if not asignaciones:

        print()
        print(
            "[CONFIGURACIÓN] "
            "No hay asignaciones disponibles."
        )

        return

    ventana = ttk.Toplevel(
        app
    )

    ventana.title(
        "Configurar Asignaciones"
    )

    ancho = 480
    alto = 500
        
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (
        pantalla_ancho - ancho
    ) // 2

    y = (
        pantalla_alto - alto
    ) // 3

    ventana.geometry(
        f"{ancho}x{alto}+{x}+{y}"
    )

    ventana.transient(
        app
    )

    # ========================================================
    # CONTENEDOR GENERAL
    # ========================================================

    frame_general = ttk.Frame(
        ventana
    )

    frame_general.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=12
    )

    entradas = {}

    # ========================================================
    # CREAR UNA SECCIÓN POR ASIGNACIÓN
    # ========================================================

    for indice, asignacion in enumerate(
        asignaciones
    ):

        grabacion = asignacion.get(
            "grabacion",
            "Desconocida"
        )

        ventana_asignada = asignacion.get(
            "ventana",
            {}
        )

        proceso = ventana_asignada.get(
            "proceso",
            "Ventana"
        )

        variables = (
            obtener_variables_grabacion(
                grabacion
            )
        )

        frame_asignacion = ttk.LabelFrame(
            frame_general,
            text=(
                f"{indice + 1}. "
                f"{proceso} — {grabacion}"
            )
        )

        frame_asignacion.pack(
            fill="x",
            pady=6
        )

        entradas[
            indice
        ] = {}

        if not variables:

            ttk.Label(
                frame_asignacion,
                text=(
                    "Sin escrituras variables."
                )
            ).pack(
                pady=8
            )

            continue

        valores_actuales = (
            asignacion.get(
                "variables_escritura",
                {}
            )
        )

        for variable in variables:

            frame_variable = ttk.Frame(
                frame_asignacion
            )

            frame_variable.pack(
                fill="x",
                padx=10,
                pady=4
            )

            ttk.Label(
                frame_variable,
                text=f"{variable}:",
                width=16
            ).pack(
                side="left"
            )

            entrada = ttk.Entry(
                frame_variable,
                width=50 #ancho cuadro texto
            )

            entrada.pack(
                side="left",
                padx=5
            )

            valor_actual = (
                valores_actuales.get(
                    variable,
                    ""
                )
            )

            if valor_actual != "":

                entrada.insert(
                    0,
                    str(valor_actual)
                )

            entradas[
                indice
            ][
                variable
            ] = entrada

    # ========================================================
    # GUARDAR
    # ========================================================

    def guardar():

        for indice, campos in (
            entradas.items()
        ):

            valores = {}

            for variable, entrada in (
                campos.items()
            ):

                valores[
                    variable
                ] = entrada.get()

            actualizar_variables_escritura(
                indice,
                valores
            )

        print()

        print(
            "[CONFIGURACIÓN] "
            "Escrituras variables guardadas:"
        )

        asignaciones_actualizadas = (
            obtener_asignaciones()
        )

        for indice, asignacion in enumerate(
            asignaciones_actualizadas,
            1
        ):

            proceso = (
                asignacion
                .get(
                    "ventana",
                    {}
                )
                .get(
                    "proceso",
                    "Ventana"
                )
            )

            print(
                f"{indice}. "
                f"{proceso}"
            )

            variables_guardadas = (
                asignacion.get(
                    "variables_escritura",
                    {}
                )
            )

            for variable, valor in (
                variables_guardadas.items()
            ):

                print(
                    f"   {variable}: "
                    f"{valor}"
                )

        messagebox.showinfo(
            "Configurar Asignaciones",
            "Configuración guardada.",
            parent=ventana
        )

        ventana.destroy()

    # ========================================================
    # BOTÓN GUARDAR
    # ========================================================

    ttk.Button(
        frame_general,
        text="Guardar",
        command=guardar,
        style="SUCCESS"
    ).pack(
        pady=12
    )