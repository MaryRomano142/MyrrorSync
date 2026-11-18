import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312

VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_TAB = 0x09
VK_ESCAPE = 0x1B

def iniciar_hotkeys():

    hotkeys = [

        (1, VK_F1),
        (2, VK_F2),
        (3, VK_F3),
        (4, VK_F4),
        (5, VK_F5),
        (6, VK_F6),
        (7, VK_F7),
        (8, VK_F8),
        (9, VK_F9),
        (10, VK_ESCAPE),
        (11, VK_TAB)

    ]

    for identificador, tecla in hotkeys:

        if not user32.RegisterHotKey(
            None,
            identificador,
            0,
            tecla
        ):

            print(f"No se pudo registrar F{identificador}")

    print("Hotkeys iniciadas.")

    msg = wintypes.MSG()

    while user32.GetMessageW(
        ctypes.byref(msg),
        None,
        0,
        0
    ) != 0:

        if msg.message == WM_HOTKEY:

            pass