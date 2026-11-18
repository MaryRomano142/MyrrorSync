import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*"
)

import pygame

sonido_disponible = False
modo_silencioso = False

try:

    pygame.mixer.init()

    pygame.mixer.set_num_channels(20)

    sonido_disponible = True

except pygame.error as e:

    print(f"No se pudo inicializar el sonido: {e}")

if sonido_disponible:

    sonidos = {

        "manual": pygame.mixer.Sound("assets/sounds/manual.mp3"),

        "espejo": pygame.mixer.Sound("assets/sounds/espejo.mp3"),

        "espejoreplicando": pygame.mixer.Sound("assets/sounds/espejoreplicando.mp3"),

        "escritura": pygame.mixer.Sound("assets/sounds/escritura.mp3"),

        "escriturareplicando": pygame.mixer.Sound("assets/sounds/escriturareplicando.mp3"),

        "arrastre": pygame.mixer.Sound("assets/sounds/arrastre.mp3"),

        "arrastrereplicando": pygame.mixer.Sound("assets/sounds/arrastrereplicando.mp3"),

        "clicksblockvertical": pygame.mixer.Sound("assets/sounds/clicksblockvertical.mp3"),

        "secciones": pygame.mixer.Sound("assets/sounds/secciones.mp3"),

        "seccionesreplicando": pygame.mixer.Sound("assets/sounds/seccionesreplicando.mp3"),

        "capturador": pygame.mixer.Sound("assets/sounds/capturador.mp3"),

        "capturadorreplicando": pygame.mixer.Sound("assets/sounds/capturadorreplicando.mp3"),

        "automatagrabando": pygame.mixer.Sound("assets/sounds/automatagrabando.mp3"),

        "automatareproduciendo": pygame.mixer.Sound("assets/sounds/automatareproduciendo.mp3"),

        "inspectordescalificacion": pygame.mixer.Sound("assets/sounds/inspectordescalificacion.mp3"),

        "fininspectordescalificacion": pygame.mixer.Sound("assets/sounds/fininspectordescalificacion.mp3"),

        "descalificaciondetectada": pygame.mixer.Sound("assets/sounds/descalificaciondetectada.mp3"),

        "intervencionusuario": pygame.mixer.Sound("assets/sounds/intervencionusuario.mp3"),

        "nuevo": pygame.mixer.Sound("assets/sounds/nuevo.mp3"),

        "snapshot": pygame.mixer.Sound("assets/sounds/snapshot.mp3"),

        "tiempofuera": pygame.mixer.Sound("assets/sounds/tiempofuera.mp3"),

        "inspectordeavance": pygame.mixer.Sound("assets/sounds/inspectordeavance.mp3"),

        "cronometrovideo": pygame.mixer.Sound("assets/sounds/cronometrovideo.mp3"),

        #AUTOMATA SPEAK

        "automataenpausa": pygame.mixer.Sound("assets/sounds/automataenpausa.mp3"),

        "demasiadosintentos": pygame.mixer.Sound("assets/sounds/demasiadosintentos.mp3"),

        "informardescalificaciondetectada": pygame.mixer.Sound("assets/sounds/informardescalificaciondetectada.mp3"),

        "reproducciondetenidaporelusuario": pygame.mixer.Sound("assets/sounds/reproducciondetenidaporelusuario.mp3"),

        "senecesitalaintervenciondelusuario": pygame.mixer.Sound("assets/sounds/senecesitalaintervenciondelusuario.mp3"),

        "todaslasasignacionesfueroncompletadas": pygame.mixer.Sound("assets/sounds/todaslasasignacionesfueroncompletadas.mp3"),

        "arrastreinteligenteactivado": pygame.mixer.Sound("assets/sounds/arrastreinteligenteactivado.mp3"),

        "arrastreinteligentedesactivado": pygame.mixer.Sound("assets/sounds/arrastreinteligentedesactivado.mp3"),

        "capturanormalactivada": pygame.mixer.Sound("assets/sounds/capturanormalactivada.mp3"),

        "capturareforzadaactivada": pygame.mixer.Sound("assets/sounds/capturareforzadaactivada.mp3"),

        "seenviaranasnotificacionesalcelular": pygame.mixer.Sound("assets/sounds/seenviaranasnotificacionesalcelular.mp3"),

        "escriturasvariablesdetectadas": pygame.mixer.Sound("assets/sounds/escriturasvariablesdetectadas.mp3"),

        "modozigzagactivado": pygame.mixer.Sound("assets/sounds/modozigzagactivado.mp3"),

        "modozigzagdesactivado": pygame.mixer.Sound("assets/sounds/modozigzagdesactivado.mp3")

    }

def modo_silencioso_esta_activo():

    return modo_silencioso

def cambiar_modo_silencioso():

    global modo_silencioso

    modo_silencioso = not modo_silencioso

    if modo_silencioso:

        if sonido_disponible:
            pygame.mixer.stop()

        print(
            "[SONIDO] MODO SILENCIOSO ACTIVADO"
        )

    else:

        print(
            "[SONIDO] MODO SILENCIOSO DESACTIVADO"
        )

    return modo_silencioso

#FUNCIONES PARA LOS EFECTOS DE SONIDO

def reproducir(nombre):

    if (
        not sonido_disponible
        or modo_silencioso
    ):
        return

    sonido = sonidos.get(nombre)

    if sonido:

        sonido.play()

def reproducir_bucle(nombre):

    if (
        not sonido_disponible
        or modo_silencioso
    ):
        return

    sonido = sonidos.get(nombre)

    if sonido:

        sonido.play(loops=-1)

def detener(nombre):

    if not sonido_disponible:
        return

    sonido = sonidos.get(nombre)

    if sonido:

        sonido.stop()
