# Active Context — Parma (D&D Character Hub & Grimoire)

## 📅 Última Sesión
- **Fecha**: 2026-11-01
- **Dispositivo**: Notebook Pop!_OS Linux
- **Estado General**: Reemplazo total del sistema de onboarding anterior por un **motor cinemático de foco visual (Spotlight Tour & Telón Borroso)**, guías contextuales progresivas por sección, demostración interactiva de tirada de dados d20 en vivo y control absoluto de omisión (Heurística de Nielsen & Ley de Hick). Versión promovida a **`1.0.2`**.

---

## 🛠️ Decisiones Técnicas y Cambios Recientes

### 1. Sistema de Onboarding Visual por Foco (Spotlight Tour) — v1.0.2
- **Componente [`SpotlightTour.tsx`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/frontend/src/components/SpotlightTour.tsx)**:
  - Telón de fondo con desenfoque cinematográfico (`backdrop-blur-xs` y `rgba(5, 7, 10, 0.78)`).
  - Máscara SVG dinámica con recorte redondeado (`rx="14"`) que ilumina con precisión quirúrgica el elemento real activo en la interfaz.
  - Halo y borde pulsante dorado (`ring-4 ring-gold/20 shadow-[0_0_24px_rgba(201,164,92,0.6)]`) que se desplaza fluidamente entre secciones con transiciones CSS bezier.
  - Tarjeta táctica auto-posicionable arriba/abajo con flecha, contador de pasos, barra de puntos interactiva y soporte completo de teclado (`Escape` para salir, `←` y `→` para navegar).
  - **Tirada de prueba interactiva en vivo**: El paso de dados incluye un botón `¡Probar tirada d20!` que acciona la animación 3D de dados en el centro de la pantalla.
  - **Heurística de Nielsen (Libertad del Usuario)**: Botón omnipresente en la esquina superior derecha `[ Saltar todo el onboarding ]` y botón secundario `Saltar sección`.

### 2. Guías Contextuales Progresivas por Sección
- Al navegar entre pestañas, si el usuario no ha completado la guía de esa sección y no ha saltado todo el onboarding, se activa un mini-tour especializado:
  - **Grimorio (`spells`)**: Filtros por nivel de conjuro, ranuras mágicas gastables y gestor de compendio/homebrew.
  - **Ficha de Personaje (`sheet`)**: Barra de vida animada, matriz de atributos/salvaciones con tirada automática y acciones de ataque.
  - **Compendio (`compendium`)**: Búsqueda atómica instantánea e índice de categorías oficiales OKF.
  - **Forja de Héroes (`forge`)**: Selector de los 3 métodos de creación (Paso a paso, 60s rápido o 4d6 al azar).
- Botón de reinicio en `SettingsView.tsx`: "Reiniciar guías de secciones" para poder revisarlas a demanda.

### 3. Versionado SemVer v1.0.2 y Automatización CI/CD
- Bump de versión a `1.0.2` en:
  - `core/version.py`: `__version__ = "1.0.2"`
  - `frontend/src/version.ts`: `export const APP_VERSION = "1.0.2"`
  - `ejecutables/windows/installer/parma_setup.iss`: `#define MyAppVersion "1.0.2"`
  - `scripts/get_version.py`: utilizado para resolución multiplataforma agnóstica.

### 2. Notificador y Modal de Actualizaciones GitHub
- **Píldora Flotante `UpdateNotificationPill.tsx`**:
  - Ubicación: `fixed bottom-4 left-4 z-40`.
  - Texto exacto: `¡Nueva versión!` junto con la insignia de versión `vX.Y.Z`.
  - Botón directo `"Actualizar"` y botón descartar `✕`.
  - Sin iconos invasivos de estrella; emplea `ArrowUpCircle`.
- **Modal de Descargas `UpdateModal.tsx`**:
  - Muestra las notas del parche (`body`) obtenidas desde GitHub Releases API (`/releases/latest`).
  - Detección nativa del sistema operativo:
    - En Windows: Acceso prioritario al instalador Inno Setup (`.exe`) y versión portable (`.zip`).
    - En Linux: Acceso prioritario al paquete Debian (`.deb`) y tarball portable (`.tar.gz`).
  - Enlace directo a GitHub Releases.

### 3. Persistencia de Versión y Ajustes
- **Tipado estricto**: `AppSettings` en `frontend/src/api/types.ts` extendido con `last_seen_version?: string` y `has_completed_onboarding?: boolean`. Nuevos tipos `GitHubReleaseInfo` y `GitHubReleaseAsset`.
- **Backend SQLite**: `desktop_api/bridge.py` (`get_settings`) expone `last_seen_version` y `has_completed_onboarding`. Al cerrar el onboarding se invoca `api.setSetting` garantizando persistencia en SQLite y fallback en `localStorage`.
- **Control de Versiones SemVer**: `core/version.py` y `frontend/src/version.ts` fijados en `1.0.1`.
- **CI/CD Dinámico**: `.github/workflows/build-and-release.yml` actualizado para extraer la versión dinámicamente desde `core/version.py` (`TAG_NAME=v1.0.1`).

---

## 📋 Tareas Pendientes / Siguiente Equipo
1. Subir los cambios a `develop` y sincronizar/mergear con `main`.
2. Verificar el workflow de GitHub Actions en `main` para la publicación de la release `v1.0.1` con los instaladores `.exe`, `.deb`, `.zip` y `.tar.gz`.
3. Disfrutar de la nueva funcionalidad de onboarding y notificaciones en las próximas ejecuciones de Parma.
