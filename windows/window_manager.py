import win32gui
import win32process
import psutil

NAVEGADORES = {
    #Como el nombre de algunos nevegadores es el mismo
    #en la lista de ventanas detectadas, es dificil saber
    #cual es la maestra y cuales las esclavas.
    #Buscar "esenombre" en la ruta del exe: escribirlo bien
    #y renombrar el exe con ese nombre solo para MS
    "chromium": "Chromium",
    "aloha": "Aloha",
    "avast software": "Avast",
    "avg": "AVG",
    "norton": "Norton",
    "chrome sxs": "Canary",
    "thorium": "Thorium",
    "chrome": "Chrome",
    "comodo": "Comodo",
    "ucbrowser": "UC"
}

COLORES_NAVEGADORES = {

    "Chromium": "#FFCC66",
    "Aloha": "#53A9FF",
    "Comodo": "#FF99CC",
    "Avast": "#8DC36B",
    "Canary": "#B5B5B5",
    "Thorium": "#FF6C3C",
    "Chrome": "#41CFCF",
    "AVG": "#983CFF",
    "Norton": "#FF2D37",
    "UC": "#9F6342"

}


def obtener_nombre_proceso(nombre_proceso, ruta):

    ruta = ruta.lower()

    for clave, nombre in NAVEGADORES.items():

        if clave in ruta:
            return nombre

    return nombre_proceso

def obtener_ventanas():

    ventanas = []

    procesos_ocultos = {
        "SystemSettings.exe",
        "ApplicationFrameHost.exe",
        "ShellExperienceHost.exe",
        "WinStore.App.exe",
        "explorer.exe",
        "Code.exe",
        "python.exe",
        "cmd.exe",
        "mspaint.exe",
        "ONENOTE.EXE",
        "cronometro.exe",
        "wmplayer.exe",
        "win32calc.exe",
        "notepad.exe",
        "dllhost.exe",
        "dwm.exe",
        "firefox.exe",
        "cleanmgr.exe",
        "WINWORD.EXE"
    }

    titulos_ocultos = {
        "Configuración",
        "Microsoft Store",
        "Program Manager"
    }

    def callback(hwnd, extra):

        if not win32gui.IsWindowVisible(hwnd):
            return

        titulo = win32gui.GetWindowText(hwnd).strip()

        if titulo == "":
            return

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            proceso_info = psutil.Process(pid)

            proceso = proceso_info.name()

            ruta = proceso_info.exe()

            proceso = obtener_nombre_proceso(
                proceso,
                ruta
            )

            if proceso in procesos_ocultos:
                return

            if titulo in titulos_ocultos:
                return

            ventanas.append({
                "hwnd": hwnd,
                "titulo": titulo,
                "proceso": proceso,
                "color": COLORES_NAVEGADORES.get(
                    proceso,
                    "#FFFFFF"
                )
            })

        except Exception:
            pass

    win32gui.EnumWindows(callback, None)

    return ventanas

def obtener_rectangulo(hwnd):
    return win32gui.GetWindowRect(hwnd)