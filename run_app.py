"""
Punto de entrada unificado y lanzador para empaquetado (PyInstaller) y ejecución directa.
Compatible con Linux, Windows y macOS.
"""
import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import flet as ft
from flet_app.main import main

if __name__ == "__main__":
    ft.app(target=main)
