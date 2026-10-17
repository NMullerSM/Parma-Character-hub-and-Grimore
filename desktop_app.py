"""
D&D Sanctum — Lanzador Principal de Escritorio (PyWebView)
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


def start_app():
    parser = argparse.ArgumentParser(description="D&D Sanctum Desktop")
    parser.add_argument("--dev", action="store_true", help="Usa servidor de desarrollo Vite (localhost:5173)")
    parser.add_argument("--port", type=int, default=5173, help="Puerto del servidor de desarrollo")
    args = parser.parse_args()

    base_dir = get_base_dir()
    bridge = DesktopBridge(base_dir)

    # Determinar URL objetivo: dev server o build estático
    if args.dev:
        target_url = f"http://localhost:{args.port}"
        print(f"[D&D Sanctum] Iniciando en Modo Desarrollo: {target_url}")
    else:
        dist_path = os.path.join(base_dir, "frontend", "dist", "index.html")
        if not os.path.exists(dist_path):
            alt_dist = os.path.join(base_dir, "dist_ui", "index.html")
            if os.path.exists(alt_dist):
                dist_path = alt_dist

        target_url = f"file:///{os.path.abspath(dist_path).replace(os.sep, '/')}"
        print(f"[D&D Sanctum] Iniciando en Modo Producción: {target_url}")

    # Crear la ventana de escritorio
    window = webview.create_window(
        title="D&D Sanctum — Character Hub & Grimoire",
        url=target_url,
        js_api=bridge,
        width=1320,
        height=880,
        min_size=(960, 640),
        background_color="#12181c",
        easy_drag=False,
    )
    bridge.set_window(window)

    # Iniciar el bucle de eventos del WebView nativo
    webview.start(debug=args.dev)


if __name__ == "__main__":
    start_app()
