# Active Context — Parma (D&D Character Hub & Grimoire)

## 📅 Última Sesión
- **Fecha**: 2026-11-01
- **Dispositivo**: Notebook Pop!_OS Linux
- **Estado General**: Implementación completa del sistema de Onboarding interactivo inteligente (5 pasos y What's New post-update) y Notificador de Actualizaciones desde GitHub Releases para Parma Desktop (versión `1.0.1`).

---

## 🛠️ Decisiones Técnicas y Cambios Recientes

### 1. Sistema de Onboarding Interactivo Multilingüe
- **Componente `OnboardingModal.tsx`**:
  - Modal accesible con soporte de teclado (Escape para cerrar, flechas izquierda/derecha para navegar).
  - Dos modos de ejecución:
    - `mode: "initial"`: Tutorial guiado de 5 pasos para nuevos usuarios (Offline-First, Forja de Héroes, Combate y Estadísticas, Compendio OKF y TaleSpire 3D). Con barra de progreso por puntos y botón de saltar.
    - `mode: "whats_new"`: Tarjeta condensada con los cambios principales de la nueva versión cuando el usuario actualiza desde una versión anterior.
  - Adaptabilidad total de temas: diseñado con tokens semánticos de Tailwind (`bg-surface`, `bg-card`, `border-iron`, `border-accent`, `text-main`, `text-muted`, `text-accent`) asegurando alto contraste en Obsidian, Parchment, Amethyst y Mithril (variantes claras y oscuras).
  - Replayable desde `SettingsView.tsx`: botón "Repetir tutorial de bienvenida" en sección dedicada con icono `BookOpen`.
  - Traducciones completas y sincronizadas en `frontend/src/i18n/es.ts` y `frontend/src/i18n/en.ts`.

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
