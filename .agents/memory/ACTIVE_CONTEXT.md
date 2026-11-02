# Active Context — Parma (D&D Character Hub & Grimoire)

## 📅 Última Sesión
- **Fecha**: 2026-11-01 / 2026-11-02
- **Dispositivo**: Notebook Pop!_OS Linux
- **Estado General**: Fases 1 a 4 completamente implementadas mediante estrategia de worktrees departamentalizados y fusionadas con éxito en la rama **`develop`** (PRs #8 y #9).
  - **Fases 1 y 2 (Onboarding & i18n)**: Saneamiento de textos con claves dinámicas (`translate()`), despeje de colisiones visuales entre botones, contención responsiva de tarjetas y reubicación del botón `Saltar todo` para no obstruir los botones de acción del header.
  - **Fases 3 y 4 (Auto-Updater Protocol)**: Descargas nativas en segundo plano por trozos de 64KB, telemetría RPC con barra de progreso en vivo, modal no bloqueante, insignia de cero pérdida de datos (`%LOCALAPPDATA%/Parma/data`) y botón `Reiniciar para actualizar` con instalación silenciosa (`/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS`).

---

## 🛠️ Decisiones Técnicas y Cambios Recientes

### 1. Saneamiento i18n y Layout Anti-Colisión (Fases 1 y 2) — Branch `feature/onboarding-spotlight-fix`
- **Componente [`frontend/src/i18n/index.ts`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/frontend/src/i18n/index.ts)**:
  - `translate(path, defaultText)` retorna `""` cuando una clave no existe en lugar de devolver el nombre crudo de la ruta. Esto permite que expresiones `{t("key") || "Texto"}` evalúen limpiamente sus fallbacks en español e inglés sin filtrar nombres como `onboarding.global.step_batch`.
  - Agregadas todas las claves canónicas y alias planos/anidados en `es.ts` y `en.ts` (`button_next`, `btnNext`, `button_prev`, `btnPrev`, `button_skip_section`, `btnSkipSection`, `button_skip_all`, `btnSkipAll`, etc.).
- **Componente [`frontend/src/components/SpotlightTour.tsx`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/frontend/src/components/SpotlightTour.tsx)**:
  - Botón `Saltar todo el onboarding` reubicado a `fixed bottom-4 right-4 z-40`, despejando totalmente el sector superior derecho del header (`#tour-dice`, `#tour-talespire`, `#tour-settings`).
  - Tarjeta de coach marks forzada a colocarse abajo (`placement: "bottom"`) siempre que el objetivo esté en la barra superior (`y < 140`), evitando que quede fuera de pantalla.
  - Dimensionamiento elástico `w-[min(380px,calc(100vw-32px))]` y `max-h-[calc(100vh-32px)] overflow-y-auto`.
  - Contenedor de botones reestructurado con `flex-wrap gap-2 items-center justify-between` y `whitespace-nowrap flex-shrink-0 ml-auto` para erradicar cualquier desborde o solapamiento entre `Anterior`, `Siguiente` y `Saltar sección`.

### 2. Protocolo de Actualización Automática In-App (Fases 3 y 4) — Branch `feature/auto-updater-protocol`
- **Módulo [`desktop_api/auto_updater.py`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/desktop_api/auto_updater.py)**:
  - `AutoUpdateManager` descarga el binario en trozos de 64KB en un hilo secundario (`threading.Thread`) hacia `{user_data_dir}/updates/`.
  - Mide y expone `percent`, `downloaded_mb` y `total_mb` en tiempo real.
  - Ejecuta el reinicio silencioso en Windows invocando el instalador con `subprocess.Popen([installer_path, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])`, cerrando de inmediato la ventana de PyWebView para dar paso al instalador oficial de Inno Setup.
  - En Linux maneja paquetes deb / ejecutables portables o modo git en desarrollo.
  - **Cero pérdida de datos garantizada**: La base de datos SQLite y los personajes residen en `user_data_dir` (`%LOCALAPPDATA%/Parma/data` en Windows y `~/.local/share/parma/data` en Linux). Inno Setup instala exclusivamente en `{autopf}\Parma` (`C:\Program Files\Parma`) sin tocar los datos de usuario.
- **RPC PyWebView y Frontend Bridge**:
  - `desktop_api/bridge.py` expone `start_auto_update`, `get_update_progress` y `apply_update_and_restart`.
  - `frontend/src/api/client.ts` y `frontend/src/api/types.ts` incorporan los contratos `UpdateProgress` y llamadas asíncronas tipadas.
  - `frontend/src/App.tsx` realiza sondeo reactivo a intervalos de 450ms únicamente mientras haya una descarga en curso.
- **Componente [`frontend/src/components/UpdateModal.tsx`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/frontend/src/components/UpdateModal.tsx)**:
  - Reemplaza el enlace a la web de GitHub por el flujo directo in-app:
    - Barra de progreso animada con visualización de `%` y `MB / Total MB`.
    - Botón `"Descargar en segundo plano"` para cerrar el modal y seguir jugando mientras se descarga.
    - Botón verde pulsante `"Reiniciar para actualizar"` tras finalizar la descarga.
    - Botón `"Ignorar esta versión"`.
- **Componente [`frontend/src/components/UpdateNotificationPill.tsx`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/frontend/src/components/UpdateNotificationPill.tsx)**:
  - Si la descarga está activa en segundo plano, la píldora muestra el spinner y el porcentaje actual.
  - Si la descarga está completa, la píldora se torna verde esmeralda y ofrece un botón directo `"Reiniciar"`.

---

## 🔀 Integración y Estado de Ramas
- `feature/onboarding-spotlight-fix`: Mergeada en `develop` vía PR #8 (`fca495684aec2ad4b1e9b64e9ad95558ec9bd3d4`).
- `feature/auto-updater-protocol`: Mergeada en `develop` vía PR #9 (`2aea5ec4f312400720f6c57ea5c61768147262fb`).
- Rama actual de trabajo consolidada: **`develop`** (HEAD: `2aea5ec4f312400720f6c57ea5c61768147262fb`).

---

## 📋 Tareas Pendientes / Siguiente Paso (Fase 5)
1. **Revisión del usuario**: Validar que la rama `develop` cumple con todas las expectativas de UX y estabilidad.
2. **Merge de `develop` a `main`**: Una vez confirmado por el usuario, fusionar `develop` en `main`.
3. **Limpieza**: Eliminar las ramas remotas y locales `feature/onboarding-spotlight-fix` y `feature/auto-updater-protocol`.
