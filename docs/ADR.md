# 📋 Parma — Registros de Decisiones de Arquitectura (ADR) & Convenciones

Este documento consolida los **Architecture Decision Records (ADRs)** y las **Convenciones de Desarrollo** de **Parma (Character Hub & Grimoire)**. Todo cambio estructural, de backend, de frontend o de empaquetado debe respetar los lineamientos y decisiones aquí documentados.

---

## 📑 Índice de Decisiones (ADRs)

1. [ADR-001: Adopción de PyWebView sobre Electron](#adr-001-adopción-de-pywebview-sobre-electron)
2. [ADR-002: Estrategia Dual de Ramas en CI/CD (`develop` vs `main`)](#adr-002-estrategia-dual-de-ramas-en-cicd-develop-vs-main)
3. [ADR-003: Aislamiento de Datos de Usuario para Garantía de Cero Pérdida (`core.paths`)](#adr-003-aislamiento-de-datos-de-usuario-para-garantía-de-cero-pérdida-corepaths)
4. [ADR-004: Protocolo de Actualización In-App con Descarga Asíncrona por Trozos e Instalación Silenciosa](#adr-004-protocolo-de-actualización-in-app-con-descarga-asíncrona-por-trozos-e-instalación-silenciosa)
5. [ADR-005: Abstracción de Almacenamiento Seguro (`safeStorage`) y Polyfill Síncrono para WebKitGTK](#adr-005-abstracción-de-almacenamiento-seguro-safestorage-y-polyfill-síncrono-para-webkitgtk)
6. [ADR-006: Onboarding Táctico Enfocado (Ley de Hick), Diseño Anti-Colisión y Resguardo con `ErrorBoundary`](#adr-006-onboarding-táctico-enfocado-ley-de-hick-diseño-anti-colisión-y-resguardo-con-errorboundary)

---

## ADR-001: Adopción de PyWebView sobre Electron

### Estado
**Aceptado** (Desde v1.0.0)

### Contexto
Parma requiere ser una aplicación de escritorio distribuible para jugadores y DM que habitualmente ejecutan herramientas de alta demanda gráfica simultáneamente (como TaleSpire 3D, Discord, Spotify y navegadores con streaming). Un runtime basado en Chromium empaquetado (Electron) añade una huella de memoria en reposo de 250MB–400MB y un instalador superior a 150MB.

### Decisión
Utilizar **PyWebView** con bindings nativos al motor de renderizado del sistema operativo:
* **Windows:** Microsoft Edge WebView2 (`winforms`).
* **Linux:** WebKitGTK 4.1 (`gir1.2-webkit2-4.1`).

### Consecuencias
* **Positivas:**
  * Binario portable ligero (~45MB–60MB comprimido).
  * Consumo de memoria RAM en reposo inferior a 75MB.
  * Tiempo de inicio inferior a 1.2 segundos.
* **Desafíos & Mitigaciones:**
  * Diferencias de motor entre WebKitGTK y WebView2 requirieron estandarizar scripts de inicialización (`WEBKIT_DISABLE_DMABUF_RENDERER=1`, `WEBKIT_DISABLE_COMPOSITING_MODE=1` en Linux) y abstracciones de almacenamiento seguro.

---

## ADR-002: Estrategia Dual de Ramas en CI/CD (`develop` vs `main`)

### Estado
**Aceptado** (Desde v1.0.2)

### Contexto
Previamente, las ejecuciones de compilación en GitHub Actions publicaban o pisaban releases públicas con instaladores en etapas preliminares o inestables, generando confusión entre los usuarios.

### Decisión
Separar taxativamente los pipelines en `.github/workflows/build-and-release.yml`:
1. **Rama `develop` (Test Compilation / Oculto):**
   * Compila `Parma-Setup-*.exe`, `Parma-Windows-Portable.zip`, `parma_*_amd64.deb` y `Parma-Linux-Portable.tar.gz`.
   * Los artefactos se almacenan temporalmente en GitHub Actions (retención 14 días) para pruebas internas.
   * El paso `publish-release` se omite estrictamente.
2. **Rama `main` (Public Release Oficial):**
   * Se activa únicamente tras pruebas satisfactorias en `develop` y validación de merges.
   * Compila los binarios finales, genera el tag de versión y publica la **Release pública oficial** en GitHub con los 4 paquetes descargables adjuntos.

### Consecuencias
* Ningún cambio inestable o en progreso ensucia el repositorio público de releases.
* Los desarrolladores pueden descargar y probar instaladores generados en la nube antes de liberar una versión oficial.

---

## ADR-003: Aislamiento de Datos de Usuario para Garantía de Cero Pérdida (`core.paths`)

### Estado
**Aceptado** (Desde v1.0.0, Formalizado en v1.0.3)

### Contexto
Al instalar la aplicación en directorios protegidos de Windows (`C:\Program Files\Parma`) o Linux (`/usr/lib/parma`), intentar escribir bases de datos o configuraciones en la carpeta del ejecutable provoca errores de acceso denegado (`PermissionError: [WinError 5]` o `sqlite3.OperationalError: attempt to write a readonly database`). Además, actualizar la aplicación reinstalando el paquete corría el riesgo de sobrescribir los personajes creados por el usuario.

### Decisión
Diseñar el módulo `core/paths.py` con una división estricta:
* **`bundle_dir` (Solo Lectura):** Carpeta donde residen los recursos estáticos empaquetados (assets web compilados, compendio OKF del SRD, manuales PDF oficiales de sólo lectura).
* **`user_data_dir` (Lectura y Escritura):** Ubicado en el estándar del sistema operativo del usuario:
  * **Windows:** `%LOCALAPPDATA%\Parma\data\`
  * **Linux:** `~/.local/share/parma/data/`
  Contiene `characters.db` (SQLite), retratos personalizados, exportaciones, bitácoras y binarios de actualización.

### Consecuencias
* **Cero Pérdida de Datos Garantizada:** Los instaladores de Windows (Inno Setup) y Linux (Debian) instalan y actualizan exclusivamente en las carpetas de programa (`{autopf}\Parma` o `/opt/parma`). Los datos de usuario jamás son sobreescritos ni eliminados durante una actualización.

---

## ADR-004: Protocolo de Actualización In-App con Descarga Asíncrona por Trozos e Instalación Silenciosa

### Estado
**Aceptado** (Introducido en v1.0.3)

### Contexto
En la versión 1.0.2, el modal de actualización dirigía a los usuarios a la página de releases de GitHub para que descargaran e instalaran el binario manualmente. Esto interrumpía el flujo de juego, obligaba a abandonar la aplicación y resultaba engorroso.

### Decisión
Implementar un protocolo de actualización automática nativo e interactivo:
1. **Backend (`desktop_api/auto_updater.py`):**
   * Descarga asíncrona en trozos (chunks) de 64KB en un hilo de fondo (`threading.Thread`) hacia `{user_data_dir}/updates/`.
   * Expone telemetría reactiva en tiempo real (`percent`, `downloaded_mb`, `total_mb`, `status`).
   * Al completarse, ejecuta el reinicio silencioso en Windows:
     `subprocess.Popen([installer, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])`, cerrando inmediatamente PyWebView.
2. **Frontend (`UpdateModal.tsx` & `UpdateNotificationPill.tsx`):**
   * Posibilidad de descargar en segundo plano mientras el usuario continúa jugando.
   * Barra de progreso animada con visualización de datos y porcentaje.
   * Botón animado de "Reiniciar para actualizar" una vez descargado el paquete.
   * Píldora de estado en la barra superior con opción directa de reinicio.

### Consecuencias
* Actualizaciones fluidas en 1 clic sin salir al navegador.
* Instalación silenciosa en Windows que cierra la app vieja, reemplaza los archivos de programa y vuelve a iniciar la app automáticamente.

---

## ADR-005: Abstracción de Almacenamiento Seguro (`safeStorage`) y Polyfill Síncrono para WebKitGTK

### Estado
**Aceptado** (Introducido en v1.0.3)

### Contexto
En distribuciones Linux modernas con WebKitGTK 2.40+ bajo PyWebView, al cargar la interfaz mediante el servidor local de desarrollo o producción en `127.0.0.1`, `window.localStorage` puede estar bloqueado o no instanciado en el ciclo inicial de evaluación de scripts, lanzando un `ReferenceError: Can't find variable: localStorage` fatal que dejaba la pantalla completamente en negro.

### Decisión
Construir una arquitectura de resguardo en cuatro capas:
1. **Polyfill Síncrono en `frontend/index.html`:** Ejecutado antes de cualquier script o módulo Vite; si `window.localStorage` falla o no existe, inyecta un mock completo en memoria con soporte de `getItem`, `setItem`, `removeItem`, `clear`, `key` y `length`.
2. **Módulo Central `frontend/src/utils/storage.ts`:** Expone `safeStorage`, envolviendo cada operación en bloques `try / catch` con un almacén dual en memoria (`fallbackMap`).
3. **Erradicación de Accesos Desprotegidos:** Prohibición y reemplazo de cualquier llamada cruda a `localStorage` en toda la base de código.
4. **Activación de Almacenamiento en Backend:** Configuración nativa en `desktop_app.py` mediante `settings.set_enable_html5_local_storage(True)` y `settings.set_enable_html5_database(True)`.

### Consecuencias
* Inmunidad total contra caídas por fallos de cuota, modo incógnito o restricciones de sandboxing en WebKitGTK.

---

## ADR-006: Onboarding Táctico Enfocado (Ley de Hick), Diseño Anti-Colisión y Resguardo con `ErrorBoundary`

### Estado
**Aceptado** (Introducido en v1.0.3)

### Contexto
El sistema de tutoriales iniciales presentaba problemas de usabilidad:
* El botón "Saltar todo" flotaba sobre los controles tácticos principales de la barra superior.
* Las tarjetas de explicación se salían del viewport cuando los elementos objetivo estaban pegados arriba (`y < 140`).
* Los textos largos o nombres de botones se desbordaban y colisionaban entre sí.
* Claves i18n inexistentes se mostraban como cadenas crudas (`onboarding.global.step_batch`).

### Decisión
1. **Ley de Hick & Foco Visual Táctico:**
   * Rediseño del componente `SpotlightTour.tsx` con un área de atención clara y opciones reducidas a lo esencial.
   * Auto-posicionamiento inteligente: elementos en `y < 140` fuerzan la tarjeta hacia abajo (`placement: "bottom"`).
   * Despeje absoluto de la cabecera: botón "Saltar todo" anclado en la esquina inferior derecha (`fixed bottom-4 right-4 z-40`).
   * Contenedor de botones con flexión responsiva (`flex-wrap gap-2 items-center justify-between`) y `whitespace-nowrap flex-shrink-0 ml-auto`.
2. **Saneamiento del Motor de Traducción (`frontend/src/i18n/index.ts`):**
   * `translate(path, defaultText)` devuelve `""` en lugar de la clave cruda cuando no existe coincidencia, permitiendo que la expresión `t("key") || "Fallback"` evalúe correctamente su texto legible.
3. **Resguardo de Renderizado (`ErrorBoundary.tsx`):**
   * Envoltura de nivel superior en `main.tsx` que atrapa cualquier excepción de renderizado y presenta una interfaz de recuperación elegante con opción de recargar.

### Consecuencias
* Experiencia de onboarding visualmente pulida, sin solapamientos en ninguna resolución de pantalla.
* Prevención de bloqueos completos de pantalla si un componente secundario falla al renderizar.

---

## 📐 Convenciones de Código y Arquitectura

### 1. Convenciones de Backend (Python 3.12)
* **Tipado:** Todo método nuevo en `desktop_api/` o `core/` debe incluir type hints de Python (`typing`).
* **Manejo de Rutas:** Prohibido concatenar cadenas de texto para rutas. Usar siempre `core.paths.get_user_data_path()` o `core.paths.get_bundle_path()` junto a `os.path.join` y `os.path.normpath`.
* **Persistencia:** Cualquier escritura debe residir en `user_data_dir`. El directorio del ejecutable se considera estrictamente de solo lectura.
* **Hilos:** Tareas de red o descarga pesada deben ejecutarse en hilos secundarios desacoplados (`threading.Thread(daemon=True)`).

### 2. Convenciones de Frontend (React 18 + TypeScript)
* **Importaciones de Tipos:** Con `verbatimModuleSyntax: true` activado, todos los tipos e interfaces deben importarse explícitamente mediante `import type { ... } from "..."`.
* **Almacenamiento:** Prohibido el uso directo de `localStorage`. Usar exclusivamente `safeStorage` de `frontend/src/utils/storage.ts`.
* **Internacionalización:**
  * Toda cadena mostrable al usuario debe admitir traducción vía `useTranslation()`.
  * Toda llamada a `t("clave")` debe proveer un fallback legible o clave canónica válida en `es.ts` y `en.ts`.
* **Control de Nulos:** En formularios y vistas, usar coalescencia nula explícita (`?? ""`, `?? 0`, `?? null`) para evitar componentes descontrolados en React.

### 3. Convenciones de CI/CD y Versionado
* **Versionado Semántico (SemVer):** El número de versión se define de manera canónica en `core/version.py` (`__version__ = "X.Y.Z"`).
* **Sincronización:** Al incrementar versión, se debe actualizar en:
  1. `core/version.py`
  2. `frontend/src/version.ts`
  3. `frontend/package.json`
* **Flujo de Trabajo Git:**
  * Trabajo activo y pruebas: rama **`develop`**.
  * Despliegue de release oficial: merge a **`main`**.
  * Ramas de características (`feature/*`): se eliminan una vez consolidadas en `develop`.
