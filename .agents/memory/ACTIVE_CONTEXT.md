# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-31 15:52 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `eeeb2db399dbbbae4868b7178fa29796d499df5a`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Estabilización de Pipelines CI/CD (`build-windows` y `build-linux`)**
   - `.github/workflows/build-and-release.yml`:
     - Subida de versión a **Node.js 22** en ambos runners (compatibilidad nativa con Vite 8 y `@tailwindcss/vite` v4).
     - Reemplazo de `npm ci` por `npm install --include=optional --no-audit` para descargar binarios nativos cruzados (`win32-x64-msvc` en Windows y `linux-x64-gnu` en Linux).
     - Windows: Variables de entorno `PYTHONUTF8: '1'` y `PYTHONIOENCODING: 'utf-8'`, detección inteligente de `ISCC.exe` preinstalado.
     - Linux: Python 3.12 unificado con el sistema `ubuntu-24.04`, instalación de paquetes de cabeceras C (`meson`, `ninja-build`, `pkg-config`, `libgirepository1.0-dev`, `libcairo2-dev`, `python3-dev`) y compilación nativa de `PyGObject`/`pycairo`.
   - `requirements.txt`:
     - Incorporadas dependencias reales de backend: `fastapi>=0.110.0`, `uvicorn>=0.27.0`, `starlette>=0.36.0`, `websockets>=12.0`, `qrcode>=7.4.2`.
   - `build_desktop.py`:
     - Incorporada la carpeta `talespire_symbiote/` en `add_data_args` para auto-instalación del symbiote en tiempo de ejecución.
     - Añadidos hidden imports para `fastapi`, `uvicorn`, `websockets`, `starlette` y `qrcode`.
   - `ejecutables/windows/installer/parma_setup.iss`:
     - Cambiada directiva a `ArchitecturesAllowed=x64` y `ArchitecturesInstallIn64BitMode=x64` (compatibilidad universal Inno Setup 6.x).
   - `ejecutables/linux/deb/DEBIAN/control` y `ejecutables/linux/deb/build_deb.py`:
     - Garantizado salto de línea final `\n` obligatorio por Debian Policy en `control`.
     - Forzados recursivamente permisos `0o755` en la jerarquía de directorios para evitar rechazo de `dpkg-deb`.

2. **Pipeline Multiplataforma CI/CD (`.github/workflows/build-and-release.yml`)**
   - **En `develop` (Test Compilation):**
     - Compila en paralelo para Windows (`windows-latest`) y Linux (`ubuntu-latest`).
     - Genera instalador Inno Setup (`.exe`), paquete portable (`.zip`), paquete Debian (`.deb`) y tarball portable (`.tar.gz`).
     - **Resguardo interno / Oculto:** Las compilaciones se guardan como artefactos de GitHub Actions (retención 14 días), sin crear releases públicos en la portada del repositorio.
   - **En `main` (Public Release):**
     - Al hacer merge a `main`, ejecuta el mismo pipeline y publica automáticamente una **Release oficial en el perfil público de GitHub** con los 4 ejecutables adjuntos y changelog de versión.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Monitorear la ejecución del workflow en GitHub Actions sobre la rama `develop`.
- [ ] Validar la generación de artefactos en Windows y Linux.
- [ ] Merge a `main` cuando esté validado.
