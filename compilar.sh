#!/usr/bin/env bash
# ===================================================
#  Visualizador D&D 5e - Linux PyInstaller Compiler
# ===================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

echo "==================================================="
echo " Compilador PyInstaller a Ejecutable Nativo Linux"
echo "==================================================="

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[Error] No se encontró el entorno virtual en: $SCRIPT_DIR/.venv"
    echo "Por favor inicializa el entorno virtual antes de compilar."
    exit 1
fi

"$VENV_PYTHON" flet_app/build_exe.py "$@"
