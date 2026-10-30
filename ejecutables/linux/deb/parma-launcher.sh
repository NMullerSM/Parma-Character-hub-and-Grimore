#!/bin/bash
# ==============================================================================
# Parma — Wrapper de Lanzamiento para Linux (Debian / Pop!_OS / Ubuntu)
# ==============================================================================

# Desactiva el renderizador DMABUF de WebKitGTK para evitar fallos de pantalla negra
# en GPUs NVIDIA o sesiones Wayland.
export WEBKIT_DISABLE_DMABUF_RENDERER=1

APP_DIR="/opt/parma"
cd "$APP_DIR" || exit 1

exec "$APP_DIR/Parma" "$@"
