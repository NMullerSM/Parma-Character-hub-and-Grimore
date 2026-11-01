"""
Módulo de Gestión Centralizada de Rutas para Parma D&D.
Distingue claramente entre:
1. Bundle Dir (Solo lectura): Recursos empaquetados por PyInstaller (manuales, okf_dnd5e, frontend, etc.).
2. User Data Dir (Lectura y Escritura): Base de datos SQLite, retratos, descargas de binarios, configuraciones.
   - En Windows instalado (Program Files): %LOCALAPPDATA%/Parma/data
   - En Linux instalado (/opt/parma): ~/.local/share/parma/data
   - En Modo Desarrollo (no frozen): <repo_root>/data
"""
import os
import sys
import platform
from pathlib import Path


def get_bundle_dir() -> str:
    """
    Retorna la ruta base de recursos empaquetados de solo lectura.
    En modo PyInstaller frozen retorna sys._MEIPASS o la carpeta del ejecutable.
    En modo desarrollo retorna la raíz del proyecto.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    current = os.path.abspath(__file__)
    base = os.path.dirname(os.path.dirname(current))
    if os.path.exists(os.path.join(base, "okf_dnd5e")):
        return base
    return os.path.dirname(base)


def get_user_data_dir() -> str:
    """
    Retorna la ruta absoluta al directorio de datos con permisos de escritura garantizados.
    Evita bloqueos de permisos en Windows UAC (C:\\Program Files) y Linux (/opt/parma).
    """
    if not getattr(sys, "frozen", False):
        dev_dir = os.path.join(get_bundle_dir(), "data")
        os.makedirs(dev_dir, exist_ok=True)
        return dev_dir

    exe_dir = os.path.dirname(sys.executable)
    is_installed = False

    if sys.platform == "win32":
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files").lower()
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)").lower()
        exe_lower = exe_dir.lower()
        if exe_lower.startswith(prog_files) or exe_lower.startswith(prog_files_x86) or "program files" in exe_lower:
            is_installed = True
    elif sys.platform.startswith("linux"):
        if exe_dir.startswith("/opt") or exe_dir.startswith("/usr"):
            is_installed = True

    if not is_installed:
        test_file = os.path.join(exe_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            portable_data = os.path.join(exe_dir, "data")
            os.makedirs(portable_data, exist_ok=True)
            return portable_data
        except (OSError, PermissionError):
            pass

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
        user_dir = os.path.join(local_app_data, "Parma", "data")
    elif sys.platform.startswith("darwin"):
        user_dir = os.path.expanduser("~/Library/Application Support/Parma/data")
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        user_dir = os.path.join(xdg_data, "parma", "data")

    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_default_db_path() -> str:
    """Retorna la ruta absoluta a dnd_database.db en el directorio escribible."""
    return os.path.join(get_user_data_dir(), "dnd_database.db")
