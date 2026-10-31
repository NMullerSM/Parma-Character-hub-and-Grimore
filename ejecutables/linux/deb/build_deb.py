"""
Generador Automatizado de Paquetes Debian (.deb) para Parma.
Empaqueta el binario compilado por PyInstaller en un paquete .deb oficial
instalable con un clic en Pop!_OS, Ubuntu, Debian y derivadas.
"""
import os
import sys
import shutil
import subprocess


def build_deb(version: str = "1.0.0"):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    linux_dist = os.path.join(base_dir, "ejecutables", "linux")
    source_app_dir = os.path.join(linux_dist, "Parma")
    deb_dir = os.path.join(base_dir, "ejecutables", "linux", "deb")
    staging_dir = os.path.join(base_dir, "build", "deb_staging")
    output_deb = os.path.join(linux_dist, f"parma_{version}_amd64.deb")

    print("=" * 65)
    print(f" Empaquetador Parma .deb (Linux amd64) — v{version}")
    print("=" * 65)

    if not os.path.exists(source_app_dir) or not os.path.isfile(os.path.join(source_app_dir, "Parma")):
        print(f"[Error] No se encontró la carpeta compilada en: {source_app_dir}")
        print("Compila primero la aplicación ejecutando: python build_desktop.py")
        sys.exit(1)

    # 1. Limpiar o preparar carpeta temporal de staging
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    # 2. Estructura de carpetas Linux estándar
    opt_parma = os.path.join(staging_dir, "opt", "parma")
    usr_bin = os.path.join(staging_dir, "usr", "bin")
    usr_apps = os.path.join(staging_dir, "usr", "share", "applications")
    usr_icons_svg = os.path.join(staging_dir, "usr", "share", "icons", "hicolor", "scalable", "apps")
    usr_icons_256 = os.path.join(staging_dir, "usr", "share", "icons", "hicolor", "256x256", "apps")
    debian_dir = os.path.join(staging_dir, "DEBIAN")

    for d in [opt_parma, usr_bin, usr_apps, usr_icons_svg, usr_icons_256, debian_dir]:
        os.makedirs(d, exist_ok=True)

    # 3. Copiar archivos de la aplicación a /opt/parma
    print("[Parma .deb] Copiando binarios a /opt/parma...")
    for item in os.listdir(source_app_dir):
        s = os.path.join(source_app_dir, item)
        d = os.path.join(opt_parma, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Copiar launcher con guardrails de WebKitGTK
    launcher_src = os.path.join(deb_dir, "parma-launcher.sh")
    launcher_dst = os.path.join(opt_parma, "parma-launcher.sh")
    shutil.copy2(launcher_src, launcher_dst)
    os.chmod(launcher_dst, 0o755)

    # 4. Crear enlace simbólico /usr/bin/parma -> /opt/parma/parma-launcher.sh
    print("[Parma .deb] Configurando acceso directo en /usr/bin/parma...")
    symlink_target = "/opt/parma/parma-launcher.sh"
    symlink_path = os.path.join(usr_bin, "parma")
    try:
        os.symlink(symlink_target, symlink_path)
    except OSError:
        # Fallback en caso de sistemas de archivos que no soporten symlink relativo
        with open(symlink_path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\nexec /opt/parma/parma-launcher.sh \"$@\"\n")
        os.chmod(symlink_path, 0o755)

    # 5. Copiar archivo .desktop
    desktop_src = os.path.join(deb_dir, "parma.desktop")
    desktop_dst = os.path.join(usr_apps, "parma.desktop")
    shutil.copy2(desktop_src, desktop_dst)
    os.chmod(desktop_dst, 0o644)

    # 6. Copiar iconos de alta resolución (SVG y PNG)
    icon_svg = os.path.join(base_dir, "brand", "es", "icon-shield-solid-light.svg")
    if os.path.exists(icon_svg):
        shutil.copy2(icon_svg, os.path.join(usr_icons_svg, "parma.svg"))

    icon_png = os.path.join(base_dir, "parma_taskbar_light.png")
    if not os.path.exists(icon_png):
        icon_png = os.path.join(base_dir, "parma.png")
    if os.path.exists(icon_png):
        shutil.copy2(icon_png, os.path.join(usr_icons_256, "parma.png"))

    # 7. Copiar archivos de control DEBIAN
    control_src = os.path.join(deb_dir, "DEBIAN", "control")
    control_dst = os.path.join(debian_dir, "control")
    with open(control_src, "r", encoding="utf-8") as f:
        content = f.read().replace("Version: 1.0.0", f"Version: {version}")
    content = content.strip() + "\n"
    with open(control_dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    os.chmod(control_dst, 0o644)

    postinst_src = os.path.join(deb_dir, "DEBIAN", "postinst")
    postinst_dst = os.path.join(debian_dir, "postinst")
    shutil.copy2(postinst_src, postinst_dst)
    os.chmod(postinst_dst, 0o755)

    # Asegurar permisos de ejecución en binarios de /opt/parma
    parma_bin = os.path.join(opt_parma, "Parma")
    if os.path.exists(parma_bin):
        os.chmod(parma_bin, 0o755)

    # Forzar recursivamente permisos 0o755 en TODOS los directorios del árbol Debian (Debian Policy)
    os.chmod(staging_dir, 0o755)
    for root, dirs, _ in os.walk(staging_dir):
        os.chmod(root, 0o755)
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)

    # 8. Empaquetar con dpkg-deb
    print("[Parma .deb] Ejecutando dpkg-deb...")
    if not shutil.which("dpkg-deb"):
        print("[Error] dpkg-deb no está instalado en el sistema. Instálalo con: sudo apt install dpkg")
        sys.exit(1)

    cmd = ["dpkg-deb", "--build", "--root-owner-group", staging_dir, output_deb]
    subprocess.check_call(cmd)

    print("\n" + "=" * 65)
    print(f" [Éxito] Paquete .deb generado exitosamente en:")
    print(f" {output_deb}")
    print(" Para instalarlo en tu equipo ejecuta:")
    print(f"   sudo apt install ./{os.path.basename(output_deb)}")
    print("=" * 65)


if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    build_deb(ver)
