# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-30 13:50 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `b36c5e5a86e78e88bf580247c434ad920778a785`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Pipeline Multiplataforma CI/CD (`.github/workflows/build-and-release.yml`)**
   - **En `develop` (Test Compilation):**
     - Compila en paralelo para Windows (`windows-latest`) y Linux (`ubuntu-latest`).
     - Genera instalador Inno Setup (`.exe`), paquete portable (`.zip`), paquete Debian (`.deb`) y tarball portable (`.tar.gz`).
     - **Resguardo interno / Oculto:** Las compilaciones se guardan como artefactos de GitHub Actions (retención 14 días), sin crear releases públicos en la portada del repositorio.
   - **En `main` (Public Release):**
     - Al hacer merge a `main`, ejecuta el mismo pipeline y publica automáticamente una **Release oficial en el perfil público de GitHub** con los 4 ejecutables adjuntos y changelog de versión.

2. **Subcarpeta de Instaladores Windows (`ejecutables/windows/installer/`)**
   - `parma_setup.iss`: Script de Inno Setup con compresión LZMA2, instalador por usuario sin UAC invasivo (`privileges=lowest`), iconos y soporte multiidioma (ES/EN).
   - `build_installer.bat`: Script ejecutor local para Windows.

3. **Subcarpeta de Paquete Linux Debian (`ejecutables/linux/deb/`)**
   - `build_deb.py`: Empaquetador nativo que estructura `/opt/parma`, `/usr/bin/parma`, `/usr/share/applications/` y llama a `dpkg-deb`.
   - `parma.desktop`: Metadatos de integración con el escritorio Linux.
   - `parma-launcher.sh`: Wrapper de ejecución que inyecta `WEBKIT_DISABLE_DMABUF_RENDERER=1` para evitar pantallas negras en Pop!_OS / Ubuntu con NVIDIA.
   - `DEBIAN/control` y `DEBIAN/postinst`: Control de versión, dependencias y regeneración de caché de iconos.

4. **Iconos de Alta Visibilidad para Barra de Tareas (Escudos Sólidos)**
   - `brand/es/icon-shield-solid-dark.svg`: Escudo Negro Sólido (`#12181c`) con glifo 'P' y arco en blanco nítido para temas claros.
   - `brand/es/icon-shield-solid-light.svg`: Escudo Blanco Sólido (`#ffffff`) con glifo 'P' y arco en negro nítido para temas oscuros.
   - `scripts/generate_taskbar_icons.py`: Generador automático de iconos `.ico` multi-resolución (16x16 a 256x256) y PNGs de alto contraste.
   - `desktop_app.py`: Detección dinámica de tema tanto en Windows (`winreg`) como en Linux (`gsettings / GTK_THEME`) para asignar el escudo correspondiente.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Probar la acción en GitHub Actions desde la pestaña *Actions* en la rama `develop` usando el botón *Run workflow*.
- [ ] Verificar la descarga del instalador Windows (`Parma-Setup-v1.0.0.exe`) y paquete Linux (`parma_1.0.0_amd64.deb`) desde los artefactos de la compilación de prueba.
- [ ] Merge a `main` cuando la compilación de prueba esté validada para publicar la primera Release pública en el perfil.
