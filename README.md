# MirrorSync

**Plataforma de automatización de navegadores y sincronización de múltiples ventanas**

MirrorSync es una aplicación de escritorio desarrollada en Python, diseñada para automatizar y sincronizar interacciones del usuario entre múltiples ventanas y pestañas de navegadores web.

La aplicación combina mecanismos de automatización de navegadores, captura y reproducción de acciones, inspección visual y gestión de errores para facilitar la ejecución de tareas web repetitivas.

## Características principales

- **Sincronización de múltiples ventanas:** coordina acciones entre distintas ventanas de navegadores.
- **Captura de acciones:** registra las interacciones del usuario para su posterior reproducción.
- **Reproducción automatizada:** ejecuta secuencias de acciones previamente registradas.
- **Integración con navegadores:** permite comunicarse con navegadores compatibles basados en Chromium mediante Chrome DevTools Protocol (CDP).
- **Inspección visual:** captura y procesa imágenes de pantalla para detectar cambios visuales.
- **Inspección del DOM:** analiza elementos de páginas web para facilitar la automatización y validación.
- **Gestión de errores:** incorpora mecanismos de reintento y recuperación ante situaciones inesperadas.
- **Múltiples modos de automatización:** ofrece diferentes modalidades para gestionar y ejecutar tareas automatizadas.
- **Interfaz gráfica:** permite administrar las funcionalidades de la aplicación desde un entorno de escritorio.

## Tecnologías utilizadas

| Tecnología | Aplicación |
|---|---|
| Python | Desarrollo principal de la aplicación |
| Tkinter | Interfaz gráfica de escritorio |
| ttkbootstrap | Estilización de la interfaz |
| CustomTkinter | Componentes visuales |
| OpenCV | Procesamiento de imágenes |
| NumPy | Procesamiento de datos e imágenes |
| MSS | Captura de pantalla |
| Pygame | Reproducción de sonidos |
| Chrome DevTools Protocol | Comunicación con navegadores |
| PyInstaller | Empaquetado de la aplicación |

## Arquitectura del proyecto

MirrorSync utiliza una arquitectura modular que permite separar sus principales componentes y responsabilidades.

El proyecto se organiza en módulos dedicados a:

- Gestión de la interfaz gráfica.
- Automatización de navegadores.
- Captura y reproducción de acciones.
- Inspección visual y captura de pantalla.
- Configuración y administración de recursos.
- Gestión de sonidos y utilidades complementarias.

## Plataforma

- Sistema operativo: Windows.
- Lenguaje de programación: Python.
- Integración con navegadores: navegadores compatibles basados en Chromium.

## Estado del proyecto

MirrorSync es un proyecto en desarrollo activo. Sus funcionalidades y arquitectura evolucionan continuamente mediante pruebas, mejoras y la incorporación de nuevas características.

## Autor

Desarrollado como proyecto independiente de desarrollo de software.
