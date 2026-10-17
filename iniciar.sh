#!/usr/bin/env bash
# ==============================================================================
# D&D Sanctum — Lanzador de Escritorio Linux (WebKitGTK)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

echo "==================================================="
echo " D&D Sanctum — Character Hub & Grimoire (Linux)"
echo "==================================================="

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
