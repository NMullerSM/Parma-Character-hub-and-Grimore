"""
Compilador Automatizado PyInstaller para Parma Desktop.
Genera un ejecutable autocontenido (.exe en Windows / binario nativo en Linux)
utilizando el motor web nativo del sistema (WebView2 / WebKitGTK) sin sobrecarga de Chromium.
"""
import os
import sys
import subprocess


def build():
    print("=" * 65)
    print(" Compilador Parma Desktop — PyWebView + React 18")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    entry_point = os.path.join(base_dir, "desktop_app.py")
    frontend_dist = os.path.join(base_dir, "frontend", "dist")
    okf_dir = os.path.join(base_dir, "okf_dnd5e")
    data_dir = os.path.join(base_dir, "data")
    themes_dir = os.path.join(base_dir, "themes")

    # 1. Verificar existencia del build del frontend
    if not os.path.exists(os.path.join(frontend_dist, "index.html")):
        print("[Parma] Compilando frontend en React + Vite...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.check_call([npm_cmd, "run", "build"], cwd=os.path.join(base_dir, "frontend"))

    # 2. Detección de plataforma
    is_windows = sys.platform == "win32"
    platform_dir = "windows" if is_windows else "linux"
    dist_dir = os.path.join(base_dir, "dist", platform_dir)
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

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--name=Parma",
        f"--icon={os.path.join(base_dir, 'parma.ico')}",
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
        "--hidden-import=desktop_api",
        "--hidden-import=core",
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
    except subprocess.CalledProcessError as e:
        print(f"\n[Error] La compilación falló con código {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
