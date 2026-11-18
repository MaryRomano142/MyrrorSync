import threading
import time

animacion_manual = False
color_manual = False
animacion_espejo = False
color_espejo = False
animacion_escritura = False
color_escritura = False
animacion_arrastre = False
color_arrastre = False
animacion_blocksecciones = False
color_blocksecciones = False
animacion_capturador = False
color_capturador = False
animacion_automata_grabando = False
color_automata_grabando = False
animacion_automata_reproduciendo = False
color_automata_reproduciendo = False

estado = {
    "manual": None,
    "espejo": None,
    "escritura": None,
    "anticeros": None,
    "escritura_teclado": None,
    "arrastre": None,
    "blockvert": None,
    "blocksecciones": None,
    "capturador": None,
    "automata": None,
    "notificaciones": None,
}

def animar_manual():

    global animacion_manual
    global color_manual

    while animacion_manual:

        if not animacion_manual:
            return

        if color_manual:

            estado["manual"].config(
                foreground="#FFFF00"
            )

        else:

            estado["manual"].config(
                foreground="#B57C00"
            )

        color_manual = not color_manual

        time.sleep(0.5)

def mostrar_manual_activo():

    global animacion_manual

    if estado["manual"]:

        estado["manual"].config(
            text="N",
            font=("Pokemon pixels 1", 21, "normal"),
            foreground="#FFFF00"
        )

        if not animacion_manual:

            animacion_manual = True

            threading.Thread(
                target=animar_manual,
                daemon=True
            ).start()

def mostrar_manual_replicando():

    global animacion_manual
    animacion_manual = False

    estado["manual"].config(
        text="N",
        font=("Pokemon pixels 1", 21, "normal"),
        foreground="cyan"
    )

def mostrar_manual_desactivado():

    global animacion_manual
    animacion_manual = False

    if estado["manual"]:

        estado["manual"].config(
            text="N",
            font=("Pokemon pixels 1", 21, "normal"),
            foreground="red"
        )

def animar_espejo():

    global animacion_espejo
    global color_espejo

    while animacion_espejo:

        if not animacion_espejo:
            return

        if color_espejo:

            estado["espejo"].config(
                foreground="#39FF14"
            )

        else:

            estado["espejo"].config(
                foreground="green"
            )

        color_espejo = not color_espejo

        time.sleep(0.5)

def mostrar_espejo_activo():

    global animacion_espejo

    if estado["espejo"]:

        estado["espejo"].config(
            text="Y",
            font=("Pokemon pixels 1", 20, "normal"),
            foreground="#39FF14"
        )

        if not animacion_espejo:

            animacion_espejo = True

            threading.Thread(
                target=animar_espejo,
                daemon=True
            ).start()

def mostrar_espejo_replicando():

    global animacion_espejo
    animacion_espejo = False

    estado["espejo"].config(
        text="Y",
        font=("Pokemon pixels 1", 20, "normal"),
        foreground="cyan"
    )

def mostrar_espejo_desactivado():

    global animacion_espejo
    animacion_espejo = False

    if estado["espejo"]:

        estado["espejo"].config(
            text="Y",
            font=("Pokemon pixels 1", 20, "normal"),
            foreground="red"
        )

def animar_escritura():

    global animacion_escritura
    global color_escritura

    while animacion_escritura:

        if not animacion_escritura:
            return

        if color_escritura:

            estado["escritura"].config(
                foreground="#39FF14"
            )

        else:

            estado["escritura"].config(
                foreground="green"
            )

        color_escritura = not color_escritura

        time.sleep(0.5)

def mostrar_escritura_activa():

    global animacion_escritura

    if estado["escritura"]:

        estado["escritura"].config(
            text="e",
            font=("Special Forces", 42, "normal"),
            foreground="#39FF14"
        )

        if not animacion_escritura:

            animacion_escritura = True

            threading.Thread(
                target=animar_escritura,
                daemon=True
            ).start()

def mostrar_escritura_replicando():

    global animacion_escritura
    animacion_escritura = False

    estado["escritura"].config(
        text="e",
        font=("Special Forces", 42, "normal"),
        foreground="cyan"
    )

def mostrar_escritura_desactivada():

    global animacion_escritura
    animacion_escritura = False

    if estado["escritura"]:

        estado["escritura"].config(
            text="e",
            font=("Special Forces", 42, "normal"),
            foreground="red"
        )

def mostrar_anticeros_activo():

    if estado["anticeros"]:

        estado["anticeros"].config(
            text="r",
            font=("Special Forces", 25, "normal"),
            foreground="#39FF14"
        )

def mostrar_anticeros_desactivado():

    if estado["anticeros"]:

        estado["anticeros"].config(
            text="r",
            font=("Special Forces", 25, "normal"),
            foreground="red"
        )

def mostrar_escritura_teclado_activa():

    if estado["escritura_teclado"]:

        estado["escritura_teclado"].config(
            text="v",
            font=("Special Forces", 24, "normal"),
            foreground="#39FF14"
        )

def mostrar_escritura_teclado_desactivada():

    if estado["escritura_teclado"]:

        estado["escritura_teclado"].config(
            text="v",
            font=("Special Forces", 24, "normal"),
            foreground="red"
        )

def animar_arrastre():

    global animacion_arrastre
    global color_arrastre

    while animacion_arrastre:

        if not animacion_arrastre:
            return

        if color_arrastre:

            estado["arrastre"].config(
                foreground="#39FF14"
            )

        else:

            estado["arrastre"].config(
                foreground="green"
            )

        color_arrastre = not color_arrastre

        time.sleep(0.5)

def mostrar_arrastre_activado():

    global animacion_arrastre

    if estado["arrastre"]:

        estado["arrastre"].config(
            text="A",
            font=("Barrel of Ninjas", 35, "normal"),
            foreground="#39FF14"
        )

        if not animacion_arrastre:

            animacion_arrastre = True

            threading.Thread(
                target=animar_arrastre,
                daemon=True
            ).start()

def mostrar_arrastre_replicando():

    global animacion_arrastre
    animacion_arrastre = False

    estado["arrastre"].config(
        text="A",
        font=("Barrel of Ninjas", 35, "normal"),
        foreground="cyan"
    )

def mostrar_arrastre_desactivado():

    global animacion_arrastre
    animacion_arrastre = False

    if estado["arrastre"]:

        estado["arrastre"].config(
            text="A",
            font=("Barrel of Ninjas", 35, "normal"),
            foreground="red"
        )

def mostrar_blockvert_clickeando():

    if estado["blockvert"]:

        estado["blockvert"].config(
        text="O",
        font=("Sonico", 43, "normal"),
        foreground="cyan"
    )

def mostrar_blockvert_desactivado():

    if estado["blockvert"]:

        estado["blockvert"].config(
            text="O",
            font=("Sonico", 43, "normal"),
            foreground="red"
        )

def animar_blocksecciones():

    global animacion_blocksecciones
    global color_blocksecciones

    while animacion_blocksecciones:

        if not animacion_blocksecciones:
            return

        if color_blocksecciones:

            estado["blocksecciones"].config(
                foreground="#39FF14"
            )

        else:

            estado["blocksecciones"].config(
                foreground="green"
            )

        color_blocksecciones = not color_blocksecciones

        time.sleep(0.5)

def mostrar_blocksecciones_activo():

    global animacion_blocksecciones

    if estado["blocksecciones"]:

        estado["blocksecciones"].config(
            text="5",
            font=("Super Street Fighter Hyper Font", 20, "normal"),
            foreground="#39FF14"
        )

        if not animacion_blocksecciones:

            animacion_blocksecciones = True

            threading.Thread(
                target=animar_blocksecciones,
                daemon=True
            ).start()

def mostrar_blocksecciones_clickeando():

    global animacion_blocksecciones
    animacion_blocksecciones = False

    if estado["blocksecciones"]:

        estado["blocksecciones"].config(
        text="5",
        font=("Super Street Fighter Hyper Font", 20, "normal"),
        foreground="cyan"
    )

def mostrar_blocksecciones_desactivado():

    global animacion_blocksecciones
    animacion_blocksecciones = False

    if estado["blocksecciones"]:

        estado["blocksecciones"].config(
            text="5",
            font=("Super Street Fighter Hyper Font", 20, "normal"),
            foreground="red"
        )

def animar_capturador():

    global animacion_capturador
    global color_capturador

    while animacion_capturador:

        if not animacion_capturador:
            return

        if color_capturador:

            estado["capturador"].config(
                foreground="#39FF14"
            )

        else:

            estado["capturador"].config(
                foreground="green"
            )

        color_capturador = not color_capturador

        time.sleep(0.5)

def mostrar_capturador_activo():

    global animacion_capturador

    if estado["capturador"]:

        estado["capturador"].config(
            text="Q",
            font=("Super Street Fighter Hyper Font", 19, "normal"),
            foreground="#39FF14"
        )

        if not animacion_capturador:

            animacion_capturador = True

            threading.Thread(
                target=animar_capturador,
                daemon=True
            ).start()

def mostrar_capturador_replicando():

    global animacion_capturador
    animacion_capturador = False

    if estado["capturador"]:

        estado["capturador"].config(
        text="Q",
        font=("Super Street Fighter Hyper Font", 19, "normal"),
        foreground="cyan"
    )

def mostrar_capturador_desactivado():

    global animacion_capturador
    animacion_capturador = False

    if estado["capturador"]:

        estado["capturador"].config(
            text="Q",
            font=("Super Street Fighter Hyper Font", 19, "normal"),
            foreground="red"
        )

def animar_automata_reproduciendo():

    global animacion_automata_reproduciendo
    global color_automata_reproduciendo

    while animacion_automata_reproduciendo:

        if not animacion_automata_reproduciendo:
            return

        if color_automata_reproduciendo:

            estado["automata"].config(
                foreground="#39FF14"
            )

        else:

            estado["automata"].config(
                foreground="green"
            )

        color_automata_reproduciendo = not color_automata_reproduciendo

        time.sleep(0.5)

def mostrar_automata_reproduciendo():

    global animacion_automata_grabando
    animacion_automata_grabando = False
    global animacion_automata_reproduciendo

    if estado["automata"]:

        estado["automata"].config(
            text="S",
            font=("ROBOTS", 38, "normal"),
            foreground="#39FF14"
        )

        if not animacion_automata_reproduciendo:

            animacion_automata_reproduciendo = True

            threading.Thread(
                target=animar_automata_reproduciendo,
                daemon=True
            ).start()

def animar_automata_grabando():

    global animacion_automata_grabando
    global color_automata_grabando

    while animacion_automata_grabando:

        if not animacion_automata_grabando:
            return

        if color_automata_grabando:

            estado["automata"].config(
                foreground="MAGENTA"
            )

        else:

            estado["automata"].config(
                foreground="#9C27B0"
            )

        color_automata_grabando = not color_automata_grabando

        time.sleep(0.5)

def mostrar_automata_grabando():

    global animacion_automata_grabando
    global animacion_automata_reproduciendo
    animacion_automata_reproduciendo = False

    if estado["automata"]:

        estado["automata"].config(
            text="S",
            font=("ROBOTS", 38, "normal"),
            foreground="MAGENTA"
        )

        if not animacion_automata_grabando:

            animacion_automata_grabando = True

            threading.Thread(
                target=animar_automata_grabando,
                daemon=True
            ).start()

def mostrar_automata_pausado():

    global animacion_automata_grabando
    animacion_automata_grabando = False
    global animacion_automata_reproduciendo
    animacion_automata_reproduciendo = False

    if estado["automata"]:

        estado["automata"].config(
        text="S",
        font=("ROBOTS", 38, "normal"),
        foreground="white"
    )

def mostrar_automata_desactivado():

    global animacion_automata_grabando
    animacion_automata_grabando = False
    global animacion_automata_reproduciendo
    animacion_automata_reproduciendo = False

    if estado["automata"]:

        estado["automata"].config(
            text="S",
            font=("ROBOTS", 38, "normal"),
            foreground="red"
        )