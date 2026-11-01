"""
Herramienta auxiliar para consultar la versión actual del proyecto
definida en core/version.py de forma agnóstica a la plataforma y shell.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from core.version import __version__
    print(__version__)
except Exception:
    # Respaldo de seguridad en caso de error inesperado
    print("1.0.1")
