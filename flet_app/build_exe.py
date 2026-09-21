"""
Script de Compilación Automatizada PyInstaller para Visualizador D&D 5e Desktop.
Genera un ejecutable .EXE autocontenido para Windows.
"""
import os
import sys
import subprocess


def build():
    print("=" * 60)
    print(" Compilador de Visualizador & Editor D&D 5e (Flet Desktop)")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flet_dir = os.path.join(base_dir, "flet_app")
    entry_point = os.path.join(flet_dir, "main.py")
    okf_dir = os.path.join(base_dir, "okf_dnd5e")
    artanis_pdf = os.path.join(base_dir, "Artanis LVL 4.pdf")

    # Verificar existencia de archivos clave
    if not os.path.exists(entry_point):
        print(f"[Error] Punto de entrada no encontrado: {entry_point}")
        sys.exit(1)

    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    # Comando PyInstaller
    # En Windows, add-data usa separador punto y coma (;)
    add_data_okf = f"{okf_dir};okf_dnd5e"
    add_data_artanis = f"{artanis_pdf};."

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--name=Visualizador_Dnd_5e",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--clean",
        f"--add-data={add_data_okf}",
        f"--add-data={add_data_artanis}",
        "--hidden-import=flet",
        "--hidden-import=pymupdf",
        "--hidden-import=pypdf",
        "--hidden-import=yaml",
        "--hidden-import=PIL",
        entry_point
    ]

    print("\nEjecutando PyInstaller:")
    print(" ".join(cmd))
    print("\nIniciando proceso de compilación... (esto puede tardar unos minutos)")

    try:
        ret = subprocess.run(cmd, check=True)
        if ret.returncode == 0:
            print("\n" + "=" * 60)
            print(" ¡COMPILACIÓN EXITOSA!")
            print(f" El ejecutable se encuentra en: {dist_dir}\\Visualizador_Dnd_5e\\")
            print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n[Error durante la compilación]: {e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
