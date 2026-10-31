# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-31 20:48 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `7295e15bd8782667786b76b3b62f8d807842e408`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Corrección de Runtime Crash en Windows (PyMuPDF FileNotFoundError)**
   - `core/pdf_engine.py`: Revertida la prioridad de importación a `import fitz as pymupdf`. El enlace en C directo `fitz` no dispara la carga de los modelos neuronales ONNX (`pymupdf.layout`), acelerando el arranque y evitando la búsqueda de `layout_rf2.4.1+imf1.yaml`.
   - `build_desktop.py`: Sustituido `--hidden-import=pymupdf` por `--collect-all=pymupdf` y `--hidden-import=fitz` para que PyInstaller empaquete todos los metadatos y librerías C de PyMuPDF dentro de `_internal/`.

2. **Arreglo del Icono de Escritorio y Acceso al Desinstalador en Inno Setup**
   - `ejecutables/windows/installer/parma_setup.iss`:
     - Copia explícita de `parma.ico` en la raíz de instalación `{app}`.
     - Los accesos directos de escritorio y menú inicio ahora apuntan directamente a `{app}\{#MyAppExeName}` para extraer el icono multi-resolución embebido en `Parma.exe`, eliminando el icono de hoja blanca.
     - Añadido acceso directo `{group}\Desinstalar Parma` (`{uninstallexe}`) en el menú inicio y registrado `UninstallDisplayName` y `CreateUninstallRegKey=yes` para desinstalación directa desde Configuración de Windows.

3. **Protección de Hojas de Personajes en `.gitignore`**
   - `.gitignore`: Ignoradas todas las fichas y exportaciones concurrentes generadas por el usuario (`data/characters/*.pdf`, `*.json`, `*.png`, `*.jpg`, carpetas `exports/`, `user_sheets/`), preservando intacta únicamente la ficha oficial de prueba `Artanis LVL 4.pdf`.

4. **Integridad de Tipos de Frontend Preservada**
   - La interfaz `SpellStatsData` en `frontend/src/api/types.ts` y el paso de verificación `npx tsc -b` se mantuvieron 100% intactos para asegurar que ambos pipelines de CI/CD continúen pasando en verde.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Monitorear la compilación del commit `7295e15` en GitHub Actions.
- [ ] Descargar los nuevos artefactos de Windows y validar el arranque sin crash de PyMuPDF, el icono correcto y el desinstalador.
- [ ] Merge de `develop` a `main` para publicar la Release oficial en el perfil público.
