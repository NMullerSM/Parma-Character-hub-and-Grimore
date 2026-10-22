#!/usr/bin/env bash
# ==============================================================================
# Parma — Lanzador de Binario Nativo Linux Compilado (ELF)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# Compatibilidad Gráfica en Linux (Pop!_OS / Ubuntu / NVIDIA / Wayland)
export WEBKIT_DISABLE_DMABUF_RENDERER=1

BIN_PATH="$SCRIPT_DIR/Parma/Parma"
if [ ! -f "$BIN_PATH" ]; then
    echo "[Error] No se encontró el binario compilado en: $BIN_PATH"
    echo "Ejecuta './compilar.sh' en la raíz del proyecto para generarlo."
    exit 1
fi

chmod +x "$BIN_PATH"
exec "$BIN_PATH" "$@"
