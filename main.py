import warnings
from core.hotkeys import iniciar_hotkeys

# Oculta advertencia de pygame
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*"
)

# Oculta advertencia de PyTorch
warnings.filterwarnings(
    "ignore",
    message=".*pin_memory.*"
)

import importlib
import config

importlib.reload(config)

from ui.main_window import iniciar_app

if __name__ == "__main__":
    #Tomar el control de las F antes que cualquier otra app
    import threading

    threading.Thread(
        target=iniciar_hotkeys,
        daemon=True
    ).start()

    iniciar_app()
