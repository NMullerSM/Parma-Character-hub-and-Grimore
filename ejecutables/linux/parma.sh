#!/bin/bash
# ==============================================================================
# Parma — Wrapper de Lanzamiento Portable para Linux
# ==============================================================================

# Desactiva el renderizador DMABUF de WebKitGTK para evitar fallos de pantalla negra
# en GPUs NVIDIA o sesiones Wayland.
export WEBKIT_DISABLE_DMABUF_RENDERER=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

exec "$SCRIPT_DIR/Parma" "$@"
