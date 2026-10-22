"""
Parma — Lanzador Principal de Escritorio (PyWebView)
Inicia la ventana nativa ligera (WebView2 en Windows, WebKitGTK en Linux)
y expone el puente RPC hacia el frontend de React 18.
"""
import os
import sys
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


def get_taskbar_icon_path(base_dir: str) -> str:
    """
    Selecciona el icono de escudo para la barra de tareas adaptándose al tema:
    - Barra oscura: Escudo blanco (parma_taskbar_light.ico)
    - Barra clara: Escudo negro (parma_taskbar_dark.ico)
    Ambos contienen exclusivamente el blasón heráldico sin tipografía.
    """
    is_light = is_windows_taskbar_light()
    chosen_name = "parma_taskbar_dark.ico" if is_light else "parma_taskbar_light.ico"
    candidate = os.path.join(base_dir, chosen_name)
    if os.path.exists(candidate):
        print(f"[Parma] Tema de barra detectado: {'Claro' if is_light else 'Oscuro'}. Usando icono: {chosen_name}")
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


def start_app():
    parser = argparse.ArgumentParser(description="Parma Desktop")
    parser.add_argument("--dev", action="store_true", help="Usa servidor de desarrollo Vite (localhost:5173)")
    parser.add_argument("--port", type=int, default=5173, help="Puerto del servidor de desarrollo")
    args = parser.parse_args()

    # 1. Configurar identidad de proceso en Windows
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

        target_url = f"file:///{os.path.abspath(dist_path).replace(os.sep, '/')}"
        print(f"[Parma] Iniciando en Modo Producción: {target_url}")

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

    # Iniciar el bucle de eventos del WebView nativo con el icono asignado
    webview.start(func=on_app_started, debug=args.dev, icon=icon_path)


if __name__ == "__main__":
    start_app()
