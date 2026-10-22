#!/usr/bin/env bash
# ==============================================================================
# Parma — Lanzador de Escritorio Linux (WebKitGTK)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

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
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "[Error] No se encontró Python 3 instalado en el sistema ni en .venv."
    exit 1
fi

"$PYTHON_CMD" desktop_app.py "$@"
