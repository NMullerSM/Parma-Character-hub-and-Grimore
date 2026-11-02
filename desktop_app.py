"""
Parma — Lanzador Principal de Escritorio (PyWebView)
Inicia la ventana nativa ligera (WebView2 en Windows, WebKitGTK en Linux)
y expone el puente RPC hacia el frontend de React 18.
"""
import os
import sys

# ==============================================================================
# Compatibilidad Gráfica en Linux (Pop!_OS / Ubuntu / NVIDIA / Wayland / GStreamer):
# Desactiva el renderizador DMABUF de WebKitGTK que causa pantallas negras / cuelgues
# por fallos en la negociación de buffers de video y formatos DRM.
# ==============================================================================
if sys.platform.startswith("linux"):
    os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
    os.environ.setdefault("WEBKIT_DISABLE_COMPOSITING_MODE", "1")

import argparse
import webview

from desktop_api.bridge import DesktopBridge


def get_base_dir() -> str:
    """Retorna la ruta base de la aplicación (compatible con PyInstaller)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def is_windows_taskbar_light() -> bool:
    """Detecta si la barra de tareas de Windows 10/11 está en modo claro u oscuro."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        winreg.CloseKey(key)
        return val == 1
    except Exception:
        # Por defecto Windows 10/11 utiliza barra de tareas oscura
        return False


def is_linux_system_light() -> bool:
    """Detecta si el entorno de escritorio Linux (GNOME/Pop!_OS/KDE/XFCE) está en tema claro."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        import subprocess
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().lower()
        if "prefer-dark" in out:
            return False
        if "default" in out or "prefer-light" in out:
            return True
    except Exception:
        pass

    gtk_theme = os.environ.get("GTK_THEME", "").lower()
    if "dark" in gtk_theme:
        return False

    # Pop!_OS y distros orientadas a gaming usan tema oscuro por defecto
    return False


def get_taskbar_icon_path(base_dir: str) -> str:
    """
    Selecciona el icono de la ventana adaptándose al sistema operativo y tema:
    - En Linux (WebKitGTK): Utiliza PNGs nativos con escudo sólido:
      * Tema Claro: Escudo Negro Sólido (parma_taskbar_dark.png)
      * Tema Oscuro: Escudo Blanco Sólido (parma_taskbar_light.png)
    - En Windows: Iconos .ico multi-resolución con escudo sólido:
      * Barra Clara: Escudo Negro Sólido (parma_taskbar_dark.ico)
      * Barra Oscura: Escudo Blanco Sólido (parma_taskbar_light.ico)
    """
    if sys.platform != "win32":
        is_light = is_linux_system_light()
        chosen_name = "parma_taskbar_dark.png" if is_light else "parma_taskbar_light.png"
        theme_str = "Claro" if is_light else "Oscuro"

        candidate = os.path.join(base_dir, chosen_name)
        if os.path.exists(candidate):
            print(f"[Parma Linux] Tema del sistema detectado: {theme_str}. Usando icono de alto contraste: {chosen_name}")
            return candidate

        # Fallbacks si no se han generado los específicos
        for png_candidate in [
            os.path.join(base_dir, "parma.png"),
            os.path.join(base_dir, "brand", "es", "icon-shield-solid-light.svg"),
            os.path.join(base_dir, "brand", "es", "icon-256.png"),
        ]:
            if os.path.exists(png_candidate):
                print(f"[Parma Linux] Usando icono de fallback para GTK: {os.path.basename(png_candidate)}")
                return png_candidate
        return None

    is_light = is_windows_taskbar_light()
    chosen_name = "parma_taskbar_dark.ico" if is_light else "parma_taskbar_light.ico"
    candidate = os.path.join(base_dir, chosen_name)
    if os.path.exists(candidate):
        print(f"[Parma Windows] Barra de tareas detectada: {'Clara' if is_light else 'Oscura'}. Usando icono de alto contraste: {chosen_name}")
        return candidate

    # Fallbacks si no se encuentra el específico
    for fallback in ["parma.ico", os.path.join("frontend", "public", "favicon.ico")]:
        full_path = os.path.join(base_dir, fallback)
        if os.path.exists(full_path):
            return full_path

    return None


def setup_windows_app_id():
    """Configura el App ID explícito en Windows para que la barra de tareas use el icono de la app y no el de Python."""
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = "parma.dnd.characterhub.grimoire.v1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"[Parma] Warning: No se pudo registrar AppUserModelID: {e}")


def apply_win32_icon(window, icon_path: str):
    """
    Asegura que la ventana Win32 y la barra de tareas muestren el icono oficial
    incluso ejecutando en modo no compilado (python desktop_app.py).
    """
    if sys.platform != "win32" or not icon_path or not os.path.exists(icon_path):
        return

    try:
        import ctypes
        user32 = ctypes.windll.user32

        # Esperar a que la ventana esté inicializada
        window.events.shown.wait(5.0)

        form = getattr(window, "native", None)
        if not form:
            return

        hwnd = form.Handle.ToInt64() if hasattr(form.Handle, "ToInt64") else int(form.Handle)
        if not hwnd:
            return

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        # Cargar icono pequeño (16x16 / titlebar izquierda) y grande (32x32 / taskbar)
        hicon_small = user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        hicon_big = user32.LoadImageW(None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)

        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)

        GCLP_HICON = -14
        GCLP_HICONSM = -34
        set_class_long = getattr(user32, "SetClassLongPtrW", getattr(user32, "SetClassLongW", None))
        if set_class_long:
            if hicon_big:
                set_class_long(hwnd, GCLP_HICON, hicon_big)
            if hicon_small:
                set_class_long(hwnd, GCLP_HICONSM, hicon_small)

        print(f"[Parma] Icono de barra y título aplicado a ventana Win32 (HWND: {hwnd})")
    except Exception as e:
        print(f"[Parma] Warning al asignar icono Win32 nativo: {e}")


def check_linux_gui_backend():
    """Verifica si el entorno Linux cuenta con los enlaces nativos WebKitGTK / Qt para PyWebView."""
    if not sys.platform.startswith("linux"):
        return

    has_gtk = False
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        has_gtk = True
    except Exception:
        has_gtk = False

    has_qt = False
    if not has_gtk:
        try:
            import PyQt5.QtWebEngineWidgets
            has_qt = True
        except ImportError:
            try:
                import PyQt6.QtWebEngineWidgets
                has_qt = True
            except ImportError:
                has_qt = False

    if not has_gtk and not has_qt:
        print("\n" + "=" * 68)
        print(" [AVISO IMPORTANTE - PARMA EN LINUX]")
        print(" PyWebView necesita el motor nativo WebKitGTK (PyGObject / 'gi')")
        print(" para comunicar la interfaz con las funciones de Python (SQLite/Tiradas).")
        print(" ")
        print(" Para activarlo, ejecuta en tu terminal:")
        print("   sudo apt update && sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1")
        print("=" * 68 + "\n")


def start_app():
    parser = argparse.ArgumentParser(description="Parma Desktop")
    parser.add_argument("--dev", action="store_true", help="Usa servidor de desarrollo Vite (localhost:5173)")
    parser.add_argument("--port", type=int, default=5173, help="Puerto del servidor de desarrollo")
    parser.add_argument("--debug", action="store_true", help="Habilita herramientas de desarrollo (F12) e inspección de consola")
    args = parser.parse_args()

    # 1. Comprobar entorno gráfico en Linux y configurar identidad en Windows
    check_linux_gui_backend()
    setup_windows_app_id()

    base_dir = get_base_dir()
    bridge = DesktopBridge(base_dir)

    # 2. Localizar icono oficial adaptado a la barra de tareas (solo escudo)
    icon_path = get_taskbar_icon_path(base_dir)

    # Determinar URL objetivo: dev server o build estático
    if args.dev:
        target_url = f"http://localhost:{args.port}"
        print(f"[Parma] Iniciando en Modo Desarrollo: {target_url}")
    else:
        dist_path = os.path.join(base_dir, "frontend", "dist", "index.html")
        if not os.path.exists(dist_path):
            alt_dist = os.path.join(base_dir, "dist_ui", "index.html")
            if os.path.exists(alt_dist):
                dist_path = alt_dist

        target_url = os.path.abspath(dist_path)
        print(f"[Parma] Iniciando en Modo Producción (Servidor Local Seguro): {target_url}")

    # Crear la ventana de escritorio
    window = webview.create_window(
        title="Parma — Character Hub & Grimoire",
        url=target_url,
        js_api=bridge,
        width=1320,
        height=880,
        min_size=(960, 640),
        background_color="#12181c",
        easy_drag=False,
    )
    bridge.set_window(window)

    def on_app_started():
        apply_win32_icon(window, icon_path)

    # Iniciar el bucle de eventos del WebView nativo
    # http_server=True activa el servidor Bottle interno para servir ES Modules de Vite sin bloqueos CORS en Linux
    debug_mode = bool(args.dev or args.debug or os.environ.get("PARMA_DEBUG", "0") == "1")
    start_kwargs = {
        "func": on_app_started,
        "debug": debug_mode,
        "http_server": True,
    }
    if icon_path:
        start_kwargs["icon"] = icon_path

    try:
        webview.start(**start_kwargs)
    except Exception as e:
        if "icon" in start_kwargs:
            print(f"[Parma] Aviso: Falló al inicializar ventana con icono ({e}). Reintentando sin icono...")
            start_kwargs.pop("icon", None)
            webview.start(**start_kwargs)
        else:
            raise


if __name__ == "__main__":
    start_app()
