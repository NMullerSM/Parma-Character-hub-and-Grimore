#!/usr/bin/env bash
# ==============================================================================
# Parma — Lanzador de Escritorio Linux (WebKitGTK)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# 0. Compatibilidad Gráfica en Linux (Pop!_OS / Ubuntu / NVIDIA / Wayland / GStreamer)
# Evita la pantalla negra por fallo del renderizador DMABUF en WebKitGTK
export WEBKIT_DISABLE_DMABUF_RENDERER=1

echo "==================================================="
echo " Parma — Character Hub & Grimoire (Linux)"
echo "==================================================="

# 1. Verificación y compilación automática del Frontend (React + Vite)
DIST_INDEX="$SCRIPT_DIR/frontend/dist/index.html"
NEEDS_BUILD=false

if [ ! -f "$DIST_INDEX" ]; then
    echo "[Parma] Compilación de frontend no encontrada en frontend/dist."
    NEEDS_BUILD=true
else
    # Comprobar si hay archivos en frontend/src más recientes que frontend/dist/index.html
    if [ -n "$(find "$SCRIPT_DIR/frontend/src" -newer "$DIST_INDEX" 2>/dev/null | head -n 1)" ]; then
        echo "[Parma] Se detectaron cambios recientes en frontend/src. Sincronizando build..."
        NEEDS_BUILD=true
    fi
fi

if [ "$NEEDS_BUILD" = true ]; then
    if command -v npm >/dev/null 2>&1; then
        echo "[Parma] Compilando frontend automáticamente..."
        (cd "$SCRIPT_DIR/frontend" && npm run build)
        if [ $? -ne 0 ]; then
            echo "[Aviso] Falló la compilación de npm. Intentando ejecutar con la versión existente..."
        else
            echo "[Parma] Frontend compilado exitosamente."
        fi
    else
        echo "[Aviso] npm no está disponible en PATH. Se usará el build existente si existe."
    fi
fi

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_CMD="$VENV_PYTHON"
    # Habilitar paquetes del sistema en .venv para que pueda cargar WebKitGTK / PyGObject ('gi')
    if [ -f "$SCRIPT_DIR/.venv/pyvenv.cfg" ]; then
        if grep -q "include-system-site-packages = false" "$SCRIPT_DIR/.venv/pyvenv.cfg"; then
            echo "[Parma Linux] Habilitando 'include-system-site-packages = true' en .venv para WebKitGTK..."
            sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "$SCRIPT_DIR/.venv/pyvenv.cfg"
        fi
    fi
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "[Error] No se encontró Python 3 instalado en el sistema ni en .venv."
    exit 1
fi

# 3. Comprobación de dependencias nativas de PyWebView (WebKitGTK / gi)
GI_STATUS=$("$PYTHON_CMD" -c "
try:
    import gi
    gi.require_version('Gtk', '3.0')
    print('OK')
except Exception:
    print('FAIL')
" 2>/dev/null)

if [ "$GI_STATUS" != "OK" ]; then
    QT_STATUS=$("$PYTHON_CMD" -c "
try:
    import PyQt5.QtWebEngineWidgets
    print('OK')
except Exception:
    try:
        import PyQt6.QtWebEngineWidgets
        print('OK')
    except Exception:
        print('FAIL')
" 2>/dev/null)

    if [ "$QT_STATUS" != "OK" ]; then
        echo "======================================================================="
        echo " [Aviso Linux] Dependencia nativa requerida: WebKitGTK / PyGObject"
        echo "======================================================================="
        echo " PyWebView requiere el módulo 'gi' del sistema para conectar Python con"
        echo " la interfaz gráfica (fichas, tiradas y base de datos SQLite)."
        echo ""
        echo " 👉 Para instalarlo en tu distribución:"
        echo ""
        echo "   • Ubuntu / Debian / Linux Mint / Pop!_OS:"
        echo "     sudo apt update && sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1"
        echo ""
        echo "   • Arch Linux / Manjaro:"
        echo "     sudo pacman -S --needed python-gobject webkit2gtk-4.1"
        echo ""
        echo "   • Fedora:"
        echo "     sudo dnf install -y python3-gobject webkit2gtk4.1"
        echo ""
        echo "   • Alternativa rápida sin sudo (vía pip):"
        echo "     $PYTHON_CMD -m pip install PyQt5 PyQtWebEngine"
        echo "======================================================================="
        echo ""
    fi
fi

"$PYTHON_CMD" desktop_app.py "$@"
