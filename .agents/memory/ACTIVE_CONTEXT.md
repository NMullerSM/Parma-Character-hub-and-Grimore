# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-11-01 16:30 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Objetivo**: Estabilización Integral para Versión 1.0 (Forja limpia, PDFs, Compendio y Resiliencia de Permisos UAC)

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Restauración de Archivos Truncados en Git (`bridge.py` y `pdf_engine.py`)**
   - En commits anteriores de CI, `desktop_api/bridge.py` (1.868 líneas en remoto vs 2.336 reales) y `core/pdf_engine.py` (331 líneas en remoto vs 605 reales) se habían subido truncados, provocando que la Forja fallara al crear personajes y que el visor de PDFs no tuviera métodos de renderizado ni tabla de contenidos (`get_toc`, `render_page_base64`, `is_open`).
   - Se restauraron ambos archivos con sus implementaciones completas.

2. **Gestor Centralizado de Rutas (`core/paths.py`) y Resiliencia ante UAC en Windows**
   - Creado `core/paths.py` distinguiendo:
     * **Bundle Dir (Solo lectura)**: Recursos empaquetados por PyInstaller (`sys._MEIPASS` o carpeta del ejecutable).
     * **User Data Dir (Lectura y Escritura)**: Garantiza permisos de escritura en `%LOCALAPPDATA%\Parma\data` (Windows) y `~/.local/share/parma/data` (Linux), evitando errores de base de datos de solo lectura (`sqlite3.OperationalError` / `WinError 5`) cuando Parma se instala en `C:\Program Files\Parma`.
   - `core/db.py`, `desktop_api/bridge.py`, `desktop_api/tunnel_manager.py` y `core/pdf_engine.py` adaptados para utilizar `core.paths`.

3. **Carga y Visualización de Manuales PDF (`desktop_api/bridge.py`)**
   - `list_pdf_documents()` y `open_pdf_document()` ahora exploran recursivamente el directorio de instalación empaquetado (`data/manuals/es`, `data/manuals/en`, `data/manuals`) y el directorio de datos del usuario.
   - Los manuales oficiales (*Manual del Jugador 2024*, *Caldero de Tasha para Todo*, *Guía de Xanathar Para Todo*) se localizan y abren inmediatamente.

4. **Visualizador de Markdown en Compendio OKF (`core/okf_engine.py`)**
   - `read_entity_file()` normaliza separadores de ruta en Windows (`os.path.normpath`) y busca en rutas candidatas para cargar el contenido de los archivos atómicos `.md` y mostrarlos en el panel derecho del compendio sin pantallas vacías.

5. **Política de Privacidad de Personajes y Repositorio Limpio (.gitignore)**
   - Eliminadas del historial de Git las hojas personales de prueba de Artanis (`Artanis LVL 4.pdf` y `Artanis_Sheet.pdf`).
   - `.gitignore` actualizado para ignorar todo el contenido de `data/characters/*`, preservando únicamente `.gitkeep` para que la aplicación inicie con una base de datos limpia y lista para que el usuario cree nuevos héroes desde cero en la Forja.

6. **Mejora de UX en Estado Vacío de Personajes (`frontend/src/views/SheetView.tsx`)**
   - Cuando no hay personajes registrados en la base de datos, la vista principal de la ficha ofrece un botón directo y claro hacia la **Forja de Héroes** para guiar al usuario a crear su primer personaje.

7. **Documentación Técnica y README**
   - Actualizados `README.md` y `docs/BACKEND.md` documentando la arquitectura de rutas (`core/paths.py`), resiliencia UAC y badges de estado para las ramas `main` y `develop`.

---

## 📌 Observaciones Técnicas para Sesión Posterior
- **Conectividad Sesión Online (Host Linux -> Invitado Windows)**:
  - El usuario reporta que al ejecutar el juego en Windows como anfitrión, la conexión como jugador funciona adecuadamente. Sin embargo, al iniciar la sesión online como host desde Linux, los clientes invitados en Windows no logran establecer la conexión.
  - *Instrucción explícita del usuario*: No tocar este subsistema por ahora. Dejar el merge y pipeline en `main` listos para pruebas preliminares y abordar esta investigación en una sesión posterior.

---

## 🎯 Tareas Pendientes Prioritarias

- [x] Sincronizar todos los cambios locales hacia la rama `develop` mediante GitHub.
- [x] Realizar merge completo de `develop` hacia `main` mediante Pull Request.
- [ ] Verificar la ejecución automática de la pipeline de GitHub Actions en `main` (Windows Installer/Portable + Linux DEB/Portable + Release).
- [ ] Investigar conectividad de Cloudflare Tunnel / WebSockets cuando Linux actúa como anfitrión (DM) en la siguiente sesión.
