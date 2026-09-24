#!/usr/bin/env bash
# ===================================================
#  Visualizador & Editor D&D 5e - Linux Launcher
# ===================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

echo "==================================================="
echo " Visualizador & Editor D&D 5e - Linux Desktop Edition"
echo "==================================================="

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[Error] No se encontró el entorno virtual en: $SCRIPT_DIR/.venv"
    echo "Por favor inicializa el entorno virtual con:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements.txt"
    exit 1
fi

echo "Iniciando aplicación de escritorio..."
"$VENV_PYTHON" -m flet_app.main "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[Aviso] La aplicación finalizó con código de salida $EXIT_CODE."
fi

exit $EXIT_CODE
