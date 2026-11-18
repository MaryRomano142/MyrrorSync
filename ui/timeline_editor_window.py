import os
import json
import tkinter as tk
from tkinter import (
    ttk,
    filedialog,
    messagebox
)

from automata.timeline_editor import (
    cargar_timeline_editor,
    guardar_timeline_editor,
    buscar_evento,
    modificar_evento,
    eliminar_evento,
    eliminar_eventos,
    duplicar_evento,
    modificar_inspectores_avance,
    insertar_vigilar_vulnerabilidad,
    insertar_inspector_avance,
    marcar_escritura_variable,
    insertar_intervencion_usuario,
    insertar_cronometro_video
)

def abrir_editor_timeline(app,ruta_inicial=None):

    ventana = tk.Toplevel(
        app
    )

    ventana.title(
        "Editor de Timeline"
    )

    ancho = 550
    alto = 520
        
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

    timeline = []
    ruta_timeline = {
        "ruta": None
    }

    def cargar_desde_ruta(ruta):

        datos = cargar_timeline_editor(
            ruta
        )

        if datos is None:

            messagebox.showerror(
                "Error",
                "No se pudo cargar la timeline."
            )

            return False

        timeline.clear()

        timeline.extend(
            datos
        )

        ruta_timeline["ruta"] = ruta

        lbl_archivo.config(
            text=ruta
        )

        return True

    # ========================================================
    # CARGAR
    # ========================================================

    def cargar():

        ruta = filedialog.askopenfilename(

            title="Seleccionar timeline",

            filetypes=[
                (
                    "Timeline JSON",
                    "*.json"
                )
            ]
        )

        if not ruta:
            return

        cargar_desde_ruta(
            ruta
        )
    
    # ========================================================
    # ABRIR INSTRUCCIONES DE LA GRABACIÓN
    # ========================================================

    def abrir_instrucciones():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Instrucciones",
                "Primero cargá una timeline.",
                parent=ventana
            )

            return

        carpeta_grabacion = os.path.dirname(
            ruta_timeline["ruta"]
        )

        ruta_instrucciones = os.path.join(
            carpeta_grabacion,
            "Instrucciones.txt"
        )

        if not os.path.isfile(
            ruta_instrucciones
        ):

            messagebox.showwarning(
                "Instrucciones",
                (
                    "Esta grabación todavía no tiene "
                    "un archivo Instrucciones.txt."
                ),
                parent=ventana
            )

            return

        try:

            os.startfile(
                ruta_instrucciones
            )

        except OSError as e:

            messagebox.showerror(
                "Instrucciones",
                f"No se pudo abrir el archivo:\n\n{e}",
                parent=ventana
            )

    # ========================================================
    # BUSCAR
    # ========================================================

    def buscar():

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Orden",
                "Ingresá un número válido."
            )

            return

        evento = buscar_evento(
            timeline,
            orden
        )

        if evento is None:

            messagebox.showwarning(
                "No encontrado",
                f"No existe la orden {orden}."
            )

            return

        txt_evento.delete(
            "1.0",
            tk.END
        )

        txt_evento.insert(
            tk.END,
            json.dumps(
                evento,
                indent=4,
                ensure_ascii=False
            )
        )
    
    # ========================================================
    # NAVEGAR ENTRE EVENTOS
    # ========================================================

    def evento_anterior():

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            return

        if orden <= 1:
            return

        orden -= 1

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

    def evento_siguiente():

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            return

        if orden >= len(timeline):
            return

        orden += 1

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

    # ========================================================
    # ESCRITURA VARIABLE
    # ========================================================

    def convertir_escritura_variable():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Escritura Variable",
                "Primero cargá una timeline."
            )

            return

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Escritura Variable",
                "Ingresá una orden válida."
            )

            return

        nombre_variable = (
            txt_variable_escritura
            .get()
            .strip()
        )

        resultado = (
            marcar_escritura_variable(
                timeline,
                orden,
                nombre_variable
            )
        )

        if resultado == "no_encontrado":

            messagebox.showwarning(
                "Escritura Variable",
                f"No existe la orden {orden}."
            )

            return

        if resultado == "no_escritura":

            messagebox.showwarning(
                "Escritura Variable",
                "La orden seleccionada "
                "no es un evento de escritura."
            )

            return

        if resultado == "nombre_vacio":

            messagebox.showwarning(
                "Escritura Variable",
                "Ingresá un nombre para "
                "la variable."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        buscar()

        txt_variable_escritura.delete(
            0,
            tk.END
        )

        messagebox.showinfo(
            "Escritura Variable",
            "Evento marcado como "
            "escritura variable."
        )

    # ========================================================
    # GUARDAR MODIFICACIÓN
    # ========================================================

    def guardar():

        if not ruta_timeline["ruta"]:
            return

        try:

            orden = int(
                txt_orden.get()
            )

            nuevo_evento = json.loads(
                txt_evento.get(
                    "1.0",
                    tk.END
                )
            )

        except Exception as e:

            messagebox.showerror(
                "JSON inválido",
                str(e)
            )

            return

        if not modificar_evento(
            timeline,
            orden,
            nuevo_evento
        ):

            messagebox.showwarning(
                "Error",
                "No se encontró el evento."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        buscar()

        messagebox.showinfo(
            "Timeline",
            "Evento modificado."
        )
    
    def interpretar_ordenes_eliminar(texto):

        ordenes = set()

        partes = texto.split(",")

        for parte in partes:

            parte = parte.strip()

            if not parte:
                continue

            if "-" in parte:

                limites = parte.split("-")

                if len(limites) != 2:
                    return None

                try:

                    inicio = int(
                        limites[0].strip()
                    )

                    fin = int(
                        limites[1].strip()
                    )

                except ValueError:

                    return None

                if inicio < 1 or fin < inicio:
                    return None

                for orden in range(
                    inicio,
                    fin + 1
                ):

                    ordenes.add(
                        orden
                    )

            else:

                try:

                    orden = int(
                        parte
                    )

                except ValueError:

                    return None

                if orden < 1:
                    return None

                ordenes.add(
                    orden
                )

        return sorted(
            ordenes
        )

    # ========================================================
    # ELIMINAR
    # ========================================================

    def eliminar():

        texto_ordenes = (
            txt_orden.get().strip()
        )

        ordenes = interpretar_ordenes_eliminar(
            texto_ordenes
        )

        if not ordenes:

            messagebox.showwarning(
                "Eliminar",
                (
                    "Ingresá una orden, varias órdenes "
                    "separadas por comas o un rango.\n\n"
                    "Ejemplos:\n"
                    "25\n"
                    "25, 31, 44\n"
                    "25-40\n"
                    "10, 15-20, 27"
                )
            )

            return

        ordenes_validas = [
            orden
            for orden in ordenes
            if 1 <= orden <= len(timeline)
        ]

        if not ordenes_validas:

            messagebox.showwarning(
                "Eliminar",
                "No hay órdenes válidas para eliminar."
            )

            return

        if len(ordenes_validas) == 1:

            mensaje = (
                f"¿Eliminar la orden "
                f"{ordenes_validas[0]}?"
            )

        else:

            mensaje = (
                f"¿Eliminar {len(ordenes_validas)} "
                "eventos?\n\n"
                f"Órdenes: {texto_ordenes}"
            )

        if not messagebox.askyesno(
            "Eliminar",
            mensaje
        ):

            return

        if eliminar_eventos(
            timeline,
            ordenes_validas
        ):

            guardar_timeline_editor(
                ruta_timeline["ruta"],
                timeline
            )

            txt_orden.delete(
                0,
                tk.END
            )

            txt_evento.delete(
                "1.0",
                tk.END
            )

            messagebox.showinfo(
                "Timeline",
                (
                    f"{len(ordenes_validas)} "
                    "evento(s) eliminado(s) y "
                    "timeline reordenada."
                )
            )

    # ========================================================
    # DUPLICAR
    # ========================================================

    def duplicar():

        try:

            orden = int(
                txt_orden.get()
            )

            cantidad = int(
                txt_cantidad.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Duplicar",
                "Ingresá valores numéricos."
            )

            return

        if cantidad <= 0:
            return

        if duplicar_evento(
            timeline,
            orden,
            cantidad
        ):

            guardar_timeline_editor(
                ruta_timeline["ruta"],
                timeline
            )

            messagebox.showinfo(
                "Timeline",
                f"Orden {orden} duplicada "
                f"{cantidad} veces.\n\n"
                f"Total actual: "
                f"{len(timeline)} eventos."
            )
    
    # ========================================================
    # VIGILAR VULNERABILIDAD
    # ========================================================

    def agregar_vigilar_vulnerabilidad():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Vigilar Vulnerabilidad",
                "Ingresá en Orden la posición "
                "donde querés insertar el evento."
            )

            return

        if not insertar_vigilar_vulnerabilidad(
            timeline,
            orden
        ):

            messagebox.showwarning(
                "Vigilar Vulnerabilidad",
                f"El orden debe estar entre "
                f"1 y {len(timeline) + 1}."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

        messagebox.showinfo(
            "Vigilar Vulnerabilidad",
            f"Evento agregado en la "
            f"orden {orden}.\n\n"
            "Los eventos posteriores "
            "fueron reordenados."
        )
    
    # INSERTAR INSPECTOR DE AVANCE

    def agregar_inspector_avance():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Inspector de Avance",
                "Ingresá en Orden la posición "
                "donde querés insertar el evento."
            )

            return

        if not insertar_inspector_avance(
            timeline,
            orden
        ):

            messagebox.showwarning(
                "Inspector de Avance",
                f"El orden debe estar entre "
                f"1 y {len(timeline) + 1}."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

        messagebox.showinfo(
            "Inspector de Avance",
            f"Inspector agregado en la "
            f"orden {orden}.\n\n"
            "Los eventos posteriores "
            "fueron reordenados."
        )
    
    # ========================================================
    # INSERTAR INTERVENCIÓN DE USUARIO
    # ========================================================

    def agregar_intervencion_usuario():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Intervención de Usuario",
                "Ingresá en Orden la posición "
                "donde querés insertar el evento."
            )

            return

        if not insertar_intervencion_usuario(
            timeline,
            orden
        ):

            messagebox.showwarning(
                "Intervención de Usuario",
                f"El orden debe estar entre "
                f"1 y {len(timeline) + 1}."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

        messagebox.showinfo(
            "Intervención de Usuario",
            f"Intervención agregada en la "
            f"orden {orden}.\n\n"
            "Los eventos posteriores "
            "fueron reordenados."
        )

    # ========================================================
    # INSERTAR CRONÓMETRO DE VIDEO
    # ========================================================

    def agregar_cronometro_video():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        try:

            orden = int(
                txt_orden.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Cronómetro de Video",
                "Ingresá en Orden la posición "
                "donde querés insertar el evento."
            )

            return

        if not insertar_cronometro_video(
            timeline,
            orden
        ):

            messagebox.showwarning(
                "Cronómetro de Video",
                f"El orden debe estar entre "
                f"1 y {len(timeline) + 1}."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        txt_orden.delete(
            0,
            tk.END
        )

        txt_orden.insert(
            0,
            str(orden)
        )

        buscar()

        messagebox.showinfo(
            "Cronómetro de Video",
            f"Cronómetro de Video agregado "
            f"en la orden {orden}.\n\n"
            "Duración: 4 segundos.\n\n"
            "Los eventos posteriores "
            "fueron reordenados."
        )
    
    # MODIFICAR ESPERA DEL INSPECTOR DE AVANCE

    def aplicar_inspector_global():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        try:

            segundos = float(
                txt_inspector_global.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Inspector",
                "Ingresá una cantidad válida "
                "de segundos."
            )

            return

        if segundos <= 0:

            messagebox.showwarning(
                "Inspector",
                "Los segundos deben ser "
                "mayores a 0."
            )

            return

        cantidad = (
            modificar_inspectores_avance(
                timeline,
                segundos
            )
        )

        if cantidad == 0:

            messagebox.showwarning(
                "Inspector",
                "La timeline no contiene "
                "inspectores de avance."
            )

            return

        guardar_timeline_editor(
            ruta_timeline["ruta"],
            timeline
        )

        messagebox.showinfo(
            "Inspector",
            f"Se modificaron "
            f"{cantidad} inspectores "
            f"de avance a "
            f"{segundos:g} segundos."
        )
    
    # VER TIMELINE

    def ver_timeline():

        if not ruta_timeline["ruta"]:

            messagebox.showwarning(
                "Timeline",
                "Primero cargá una timeline."
            )

            return

        ventana_timeline = tk.Toplevel(
            ventana
        )

        ventana_timeline.title(
            "Ver Timeline"
        )

        ancho = 850
        alto = 650

        pantalla_ancho = (
            ventana_timeline.winfo_screenwidth()
        )

        pantalla_alto = (
            ventana_timeline.winfo_screenheight()
        )

        x = (
            pantalla_ancho - ancho
        ) // 2

        y = (
            pantalla_alto - alto
        ) // 2

        ventana_timeline.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

        # ========================================================
        # FRAME DEL TEXTO + SCROLL
        # ========================================================

        frame_texto = ttk.Frame(ventana_timeline)

        frame_texto.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        frame_contenido = ttk.Frame(
            frame_texto
        )

        frame_contenido.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll = ttk.Scrollbar(
            frame_contenido,
            orient="vertical"
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        txt_timeline = tk.Text(
            frame_contenido,
            font=("Consolas", 10),
            wrap="none",
            yscrollcommand=scroll.set
        )

        txt_timeline.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.config(
            command=txt_timeline.yview
        )

        # ========================================================
        # PANEL DE FILTROS
        # ========================================================

        frame_filtros = ttk.Frame(
            frame_texto
        )

        frame_filtros.pack(
            side="right",
            fill="y",
            padx=(10, 5),
            pady=2
        )

        tipos_eventos = sorted({
            evento.get("tipo")
            for evento in timeline
            if evento.get("tipo")
        })

        variables_filtro = {}

        for tipo in tipos_eventos:

            variable = tk.BooleanVar(
                value=False
            )

            variables_filtro[tipo] = variable

            ttk.Checkbutton(
                frame_filtros,
                text=tipo,
                variable=variable
            ).pack(
                anchor="w",
                padx=5,
                pady=2
            )

        # ========================================================
        # MOSTRAR / FILTRAR TIMELINE
        # ========================================================

        def mostrar_timeline(tipos_filtrar=None):

            if not tipos_filtrar:

                eventos_mostrar = timeline

            else:

                eventos_mostrar = [
                    evento
                    for evento in timeline
                    if evento.get("tipo")
                    in tipos_filtrar
                ]

            contenido = json.dumps(
                eventos_mostrar,
                indent=4,
                ensure_ascii=False
            )

            txt_timeline.config(
                state="normal"
            )

            txt_timeline.delete(
                "1.0",
                tk.END
            )

            txt_timeline.insert(
                "1.0",
                contenido
            )

            txt_timeline.config(
                state="disabled"
            )

        def aplicar_filtro():

            seleccionados = {
                tipo
                for tipo, variable
                in variables_filtro.items()
                if variable.get()
            }

            mostrar_timeline(
                seleccionados
            )

        def mostrar_todos():

            for variable in (
                variables_filtro.values()
            ):

                variable.set(
                    False
                )

            mostrar_timeline()
        
        frame_botones_filtro = ttk.Frame(frame_filtros)
        frame_botones_filtro.pack(pady=(10, 5))

        ttk.Button(
            frame_botones_filtro,
            text="Todos",
            command=mostrar_todos
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame_botones_filtro,
            text="Filtrar",
            command=aplicar_filtro
        ).pack(
            side="left",
            padx=5
        )
    
        mostrar_timeline()

    # ========================================================
    # INTERFAZ
    # ========================================================

    frame_timeline = ttk.Frame(ventana)
    frame_timeline.pack(pady=10)

    ttk.Button(
        frame_timeline,
        text="Cargar Timeline",
        command=cargar
    ).pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_timeline,
        text="Ver Timeline",
        command=ver_timeline
    ).pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_timeline,
        text="Instrucciones",
        command=abrir_instrucciones
    ).pack(
        side="left",
        padx=5
    )

    lbl_archivo = ttk.Label(
        ventana,
        text="Ninguna timeline cargada"
    )

    lbl_archivo.pack(
        pady=5
    )

    frame_buscar = ttk.Frame(ventana)
    frame_buscar.pack(pady=10)

    ttk.Label(
        frame_buscar,
        text="Orden:"
    ).pack(
        side="left",
        padx=5
    )

    txt_orden = ttk.Entry(
        frame_buscar,
        width=10
    )

    txt_orden.pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_buscar,
        text="Buscar",
        command=buscar,
        style="INFO"
    ).pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_buscar,
        text="<",
        command=evento_anterior,
        width=3
    ).pack(
        side="left",
        padx=2
    )

    ttk.Button(
        frame_buscar,
        text=">",
        command=evento_siguiente,
        width=3
    ).pack(
        side="left",
        padx=2
    )

    frame_escritura_variable = ttk.Frame(ventana)
    frame_escritura_variable.pack(pady=5)

    ttk.Label(
        frame_escritura_variable,
        text="Variable:"
    ).pack(
        side="left",
        padx=5
    )

    txt_variable_escritura = ttk.Entry(
        frame_escritura_variable,
        width=15
    )

    txt_variable_escritura.pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_escritura_variable,
        text="Escritura Variable",
        command=convertir_escritura_variable,
        style="SECONDARY"
    ).pack(
        side="left",
        padx=5
    )

    frame_insertar_eventos = ttk.Frame(ventana)
    frame_insertar_eventos.pack(pady=5)

    btn_vigilar_vulnerabilidad = ttk.Button(
        frame_insertar_eventos,
        text="Vigilar Vulnerabilidad",
        command=agregar_vigilar_vulnerabilidad,
        style="WARNING"
    )

    btn_vigilar_vulnerabilidad.pack(
        side="left",
        padx=5
    )

    btn_insertar_inspector = ttk.Button(
        frame_insertar_eventos,
        text="Inspector de Avance",
        command=agregar_inspector_avance,
    )

    btn_insertar_inspector.pack(
        side="left",
        padx=5
    )

    frame_insertar_eventos2 = ttk.Frame(ventana)
    frame_insertar_eventos2.pack(pady=5)

    btn_intervencion_usuario = ttk.Button(
        frame_insertar_eventos2,
        text="Intervención de Usuario",
        command=agregar_intervencion_usuario
    )

    btn_intervencion_usuario.pack(
        side="left",
        padx=5
    )

    btn_cronometro_video = ttk.Button(
        frame_insertar_eventos2,
        text="Cronómetro de Video",
        command=agregar_cronometro_video
    )

    btn_cronometro_video.pack(
        side="left",
        padx=5
    )

    frame_inspector = ttk.Frame(ventana)
    frame_inspector.pack(pady=5)

    ttk.Label(
        frame_inspector,
        text="Inspectores avance:"
    ).pack(
        side="left",
        padx=5
    )

    txt_inspector_global = ttk.Entry(
        frame_inspector,
        width=7
    )

    txt_inspector_global.insert(
        0,
        "2"
    )

    txt_inspector_global.pack(
        side="left",
        padx=5
    )

    ttk.Label(
        frame_inspector,
        text="seg."
    ).pack(
        side="left"
    )

    ttk.Button(
        frame_inspector,
        text="Aplicar a todos",
        command=aplicar_inspector_global
    ).pack(
        side="left",
        padx=10
    )

    txt_evento = tk.Text(
        ventana,
        width=65,
        height=9,
        font=(
            "Consolas",
            10
        )
    )

    txt_evento.pack(
        padx=10,
        pady=10
    )

    frame_acciones = ttk.Frame(ventana)
    frame_acciones.pack(pady=5)

    ttk.Button(
        frame_acciones,
        text="Eliminar",
        command=eliminar,
        style="DANGER"
    ).pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_acciones,
        text="Guardar",
        command=guardar,
        style="SUCCESS"
    ).pack(
        side="left",
        padx=5
    )

    ttk.Label(
        frame_acciones,
        text="Copias:"
    ).pack(
        side="left",
        padx=(20, 5)
    )

    txt_cantidad = ttk.Entry(
        frame_acciones,
        width=5
    )

    txt_cantidad.insert(
        0,
        "1"
    )

    txt_cantidad.pack(
        side="left",
        padx=5
    )

    ttk.Button(
        frame_acciones,
        text="Duplicar",
        command=duplicar
    ).pack(
        side="left",
        padx=5
    )

    if ruta_inicial:

        cargar_desde_ruta(
            ruta_inicial
        )