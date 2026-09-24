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
    entry_point = os.path.join(base_dir, "run_app.py")
    okf_dir = os.path.join(base_dir, "okf_dnd5e")
    artanis_pdf = os.path.join(base_dir, "Artanis LVL 4.pdf")

    # Verificar existencia de archivos clave
    if not os.path.exists(entry_point):
        print(f"[Error] Punto de entrada no encontrado: {entry_point}")
        sys.exit(1)

    # Detección de plataforma
    is_windows = sys.platform == "win32"
    platform_label = "Windows (.EXE)" if is_windows else "Linux (Binario Nativo)"
    platform_dir = "windows" if is_windows else "linux"

    dist_dir = os.path.join(base_dir, "dist", platform_dir)
    build_dir = os.path.join(base_dir, "build", platform_dir)

    print(f"-> Plataforma detectada: {platform_label}")
    print(f"-> Carpeta de distribución: {dist_dir}")

    # Separador de PyInstaller (--add-data usa ';' en Windows y ':' en Linux/Unix)
    sep = os.pathsep
    add_data_args = [f"--add-data={okf_dir}{sep}okf_dnd5e"]

    # Ficha de ejemplo si existe
    if os.path.exists(artanis_pdf):
        add_data_args.append(f"--add-data={artanis_pdf}{sep}.")

    # Carpeta data si existe
    data_dir = os.path.join(base_dir, "data")
    if os.path.exists(data_dir):
        add_data_args.append(f"--add-data={data_dir}{sep}data")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--name=Visualizador_Dnd_5e",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={base_dir}",
        "--clean",
        "--noconfirm",
    ] + add_data_args + [
        "--collect-all=flet",
        "--collect-all=flet_desktop_light",
        "--collect-all=flet_app",
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
            exe_name = "Visualizador_Dnd_5e.exe" if is_windows else "Visualizador_Dnd_5e"
            output_path = os.path.join(dist_dir, "Visualizador_Dnd_5e", exe_name)
            print("\n" + "=" * 60)
            print(f" ¡COMPILACIÓN EXITOSA ({platform_label})!")
            print(f" Ejecutable generado en: {output_path}")
            print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n[Error durante la compilación]: {e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
