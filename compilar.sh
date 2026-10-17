#!/usr/bin/env bash
# ==============================================================================
# D&D Sanctum — Compilador PyInstaller Linux Standalone
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

echo "==================================================="
echo " Compilador D&D Sanctum (Binario Nativo Linux)"
echo "==================================================="

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_CMD="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "[Error] No se encontró Python 3 instalado en el sistema."
    exit 1
fi

"$PYTHON_CMD" build_desktop.py "$@"
