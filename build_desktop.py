"""
Compilador Automatizado PyInstaller para Parma Desktop.
Genera un ejecutable autocontenido (.exe en Windows / binario nativo en Linux)
utilizando el motor web nativo del sistema (WebView2 / WebKitGTK) sin sobrecarga de Chromium.
"""
import os
import sys
import subprocess


import argparse
import shutil


def build():
    parser = argparse.ArgumentParser(description="Compilador Parma Desktop — PyWebView + React 18")
    parser.add_argument("--onefile", action="store_true", help="Genera un único archivo ejecutable autocontenido (sin carpeta _internal)")
    args = parser.parse_args()

    print("=" * 65)
    print(" Compilador Parma Desktop — PyWebView + React 18")
    print(f" Modo: {'Ejecutable Único (--onefile)' if args.onefile else 'Carpeta Portable (--onedir)'}")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    entry_point = os.path.join(base_dir, "desktop_app.py")
    frontend_dist = os.path.join(base_dir, "frontend", "dist")
    okf_dir = os.path.join(base_dir, "okf_dnd5e")
    data_dir = os.path.join(base_dir, "data")
    themes_dir = os.path.join(base_dir, "themes")
    symbiote_dir = os.path.join(base_dir, "talespire_symbiote")

    # 1. Verificar existencia del build del frontend
    if not os.path.exists(os.path.join(frontend_dist, "index.html")):
        print("[Parma] Compilando frontend en React + Vite...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.check_call([npm_cmd, "run", "build"], cwd=os.path.join(base_dir, "frontend"))

    # 2. Detección de plataforma y destino
    is_windows = sys.platform == "win32"
    platform_dir = "windows" if is_windows else "linux"
    dist_dir = os.path.join(base_dir, "ejecutables", platform_dir)
    build_dir = os.path.join(base_dir, "build", platform_dir)

    sep = os.pathsep
    add_data_args = [
        f"--add-data={frontend_dist}{sep}dist_ui",
        f"--add-data={okf_dir}{sep}okf_dnd5e",
    ]

    if os.path.exists(data_dir):
        add_data_args.append(f"--add-data={data_dir}{sep}data")

    if os.path.exists(themes_dir):
        add_data_args.append(f"--add-data={themes_dir}{sep}themes")

    if os.path.exists(symbiote_dir):
        add_data_args.append(f"--add-data={symbiote_dir}{sep}talespire_symbiote")

    for asset_file in [
        "parma.png",
        "parma.ico",
        "parma_taskbar_dark.ico",
        "parma_taskbar_light.ico",
        "parma_taskbar_dark.png",
        "parma_taskbar_light.png"
    ]:
        asset_path = os.path.join(base_dir, asset_file)
        if os.path.exists(asset_path):
            add_data_args.append(f"--add-data={asset_path}{sep}.")

    icon_name = "parma.ico" if is_windows else "parma.png"
    icon_path = os.path.join(base_dir, icon_name)

    mode_arg = "--onefile" if args.onefile else "--onedir"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        mode_arg,
        "--name=Parma",
        f"--icon={icon_path}",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={base_dir}",
        "--clean",
        "--noconfirm",
    ] + add_data_args + [
        "--collect-all=pywebview",
        "--hidden-import=pymupdf",
        "--hidden-import=pypdf",
        "--hidden-import=yaml",
        "--hidden-import=PIL",
        "--hidden-import=bottle",
        "--hidden-import=desktop_api",
        "--hidden-import=core",
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=websockets",
        "--hidden-import=starlette",
        "--hidden-import=qrcode",
        entry_point,
    ]

    print("\nEjecutando PyInstaller:")
    print(" ".join(cmd))
    print("\nIniciando proceso de compilación...\n")

    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 65)
        print(" [Éxito] Compilación completada exitosamente.")
        print(f" Binario generado en: {dist_dir}")
        print("=" * 65)

        # Generar ZIP portable para compartir fácilmente entre computadores
        if not args.onefile:
            archive_dir = os.path.join(dist_dir, "Parma")
            if os.path.exists(archive_dir):
                zip_name = "Parma-Windows-Portable" if is_windows else "Parma-Linux-Portable"
                archive_format = "zip" if is_windows else "gztar"
                ext = ".zip" if is_windows else ".tar.gz"
                print(f"\n[Parma] Generando paquete comprimido listo para compartir: {zip_name}{ext}...")
                archive_output = os.path.join(dist_dir, zip_name)
                shutil.make_archive(archive_output, archive_format, root_dir=dist_dir, base_dir="Parma")
                print(f"[Parma] ¡Paquete portable listo en: {archive_output}{ext}!")

    except subprocess.CalledProcessError as e:
        print(f"\n[Error] La compilación falló con código {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
