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
7. [ADR-007: Persistencia Híbrida SQLite en Modo WAL + Documento JSON (`data_json`)](#adr-007-persistencia-híbrida-sqlite-en-modo-wal--documento-json-data_json)
8. [ADR-008: Compendio Atómico Bilingüe OKF (Open Knowledge Format en Markdown + YAML)](#adr-008-compendio-atómico-bilingüe-okf-open-knowledge-format-en-markdown--yaml)
9. [ADR-009: Arquitectura Zero-Server para Sesiones DM Online con Cloudflare Quick Tunnels y Enrutamiento Simétrico](#adr-009-arquitectura-zero-server-para-sesiones-dm-online-con-cloudflare-quick-tunnels-y-enrutamiento-simétrico)
10. [ADR-010: Daemon WebSocket Permanente para TaleSpire Symbiote y Modos Duales de Lanzamiento (`Dual Throw Modes`)](#adr-010-daemon-websocket-permanente-para-talespire-symbiote-y-modos-duales-de-lanzamiento-dual-throw-modes)
11. [ADR-011: Mitigación de Pantalla Negra en Linux WebKitGTK (`WEBKIT_DISABLE_COMPOSITING_MODE=1`)](#adr-011-mitigación-de-pantalla-negra-en-linux-webkitgtk-webkit_disable_compositing_mode1)
12. [ADR-012: Conectores Desacoplados Multi-Proveedor para Retratos con IA y Empaquetado Legal OKF](#adr-012-conectores-desacoplados-multi-proveedor-para-retratos-con-ia-y-empaquetado-legal-okf)

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

## ADR-007: Persistencia Híbrida SQLite en Modo WAL + Documento JSON (`data_json`)

### Estado
**Aceptado** (Desde v1.0.0)

### Contexto
El prototipo original almacenaba un único personaje en un archivo plano `autosave_character.json`, lo cual impedía gestionar múltiples héroes, sufría riesgo de corrupción si la app se cerraba a mitad de escritura y no permitía relacionar diarios de campaña, grafos de PNJs o sesiones de DM. Por otro lado, normalizar en decenas de tablas cada rasgo, ranura de conjuro y modificador de D&D 5e/5.5e haría que cada cambio del SRD requiriera complejas migraciones SQL (`ALTER TABLE`).

### Decisión
Implementar en `core/db.py` (`DatabaseManager`) un modelo **Híbrido Relacional-Documental** sobre SQLite3 con `PRAGMA journal_mode=WAL;`:
* Columnas relacionales indexadas en `characters` (`id`, `name`, `char_class`, `subclass`, `level`, `race`, `hp_current`, `hp_max`, `is_active`) para listados rápidos.
* Columna documental `data_json` que almacena la serialización íntegra de `CharacterSheet`, con deserialización defensiva (`CharacterSheet.from_dict`).
* Tablas relacionales satélites con `ON DELETE CASCADE` para `campaign_journals`, `network_nodes`, `network_edges`, `dm_sessions`, `dm_session_players`, `dm_session_logs` y `dm_homebrew_items`.

### Consecuencias
* Concurrencia sin bloqueos (`WAL`) entre el hilo de PyWebView y el servidor asíncrono FastAPI.
* Evolución flexible de la ficha de personaje sin romper bases de datos de versiones previas.

---

## ADR-008: Compendio Atómico Bilingüe OKF (Open Knowledge Format en Markdown + YAML)

### Estado
**Aceptado** (Desde v1.0.0)

### Contexto
Las reglas de D&D 5e/5.5e (Clases, Subclases, Especies, Conjuros, Dotes, Equipo) requieren ser consultadas tanto por humanos con formato editorial rico (tablas, listas, negritas) como por el motor matemático del Creador de Personajes y los optimizadores de IA, además de soportar cambio de idioma instantáneo entre Español e Inglés.

### Decisión
Almacenar el compendio en `okf_dnd5e/` bajo el estándar **OKF (Open Knowledge Format)**:
* Más de **570 archivos Markdown atómicos** (`.md` para español y `_en.md` para inglés) encabezados por un bloque **YAML Frontmatter** con metadatos estructurados (`id`, `nombre`, `nivel`, `escuela`, `clases`, `fuente`, `edicion`).
* Indexación en memoria al arranque mediante `core/okf_engine.py` (`OkfEngine`).

### Consecuencias
* Funcionamiento 100% offline con latencia de búsqueda sub-milisegundo.
* Trazabilidad limpia en Git y facilidad para auditar o agregar contenido Homebrew/SRD.

---

## ADR-009: Arquitectura Zero-Server para Sesiones DM Online con Cloudflare Quick Tunnels y Enrutamiento Simétrico

### Estado
**Aceptado** (Introducido en v1.0.2, Perfeccionado en v1.0.3)

### Contexto
Permitir que un DM dirija una partida online donde los jugadores sincronicen sus fichas, reciban daño/curación cinemática y objetos Homebrew normalmente requeriría costear un servidor backend central en la nube o exigir al DM abrir puertos (Port Forwarding) en su router doméstico. Adicionalmente, cuando un host Linux abría sesión y un cliente Windows se conectaba App-a-App, el WebSocket intentaba conectarse a `127.0.0.1` en lugar del host remoto.

### Decisión
1. **Servidor Embebido (`desktop_api/session_server.py`):** La máquina del DM ejecuta un servidor FastAPI + Uvicorn local que sirve tanto el SPA compilado (`frontend/dist`) como la API REST (`/api/session/info`, `/api/player/join`) y el hub WebSocket (`/ws`).
2. **Túnel Saliente Zero-Config (`desktop_api/tunnel_manager.py`):** Descarga automática del binario oficial `cloudflared` en `user_data_dir/bin` (con `chmod 0o755` automático en Linux/macOS), levantando un túnel seguro `https://<hash>.trycloudflare.com` y generando un código QR en Base64.
3. **Enrutamiento WebSocket Dinámico (`OnlinePlayerSync.tsx` & `CharacterContext.tsx`):** Al unirse mediante URL de túnel desde otra app de escritorio o navegador, se persiste `remoteTunnelUrl` en `safeStorage` y se enruta el WebSocket explícitamente hacia `wss://<hash>.trycloudflare.com/ws`.

### Consecuencias
* Costo cero de infraestructura en la nube y cero configuración de red para el DM.
* Compatibilidad bidireccional simétrica entre hosts y clientes Windows, Linux y navegadores móviles.

---

## ADR-010: Daemon WebSocket Permanente para TaleSpire Symbiote y Modos Duales de Lanzamiento (`Dual Throw Modes`)

### Estado
**Aceptado** (Introducido en v1.0.3 — PR #12)

### Contexto
Anteriormente, el servidor FastAPI/WebSocket solo se iniciaba cuando el usuario abría manualmente una sesión online de DM. Por ello, durante partidas locales de un jugador, el Symbiote dentro de TaleSpire (`ws://127.0.0.1:8765/ws/talespire`) sufría *Connection Refused* y quedaba en *"Reconectando..."*. Además, algunos usuarios preferían que Parma arrojara los dados físicamente de forma automática y otros preferían que solo los dejara listos en la bandeja de TaleSpire.

### Decisión
1. **Auto-Arranque en Segundo Plano:** `DesktopBridge.__init__` invoca `self._session_server.ensure_running()` al iniciar Parma, garantizando que el endpoint `ws://127.0.0.1:8765/ws/talespire` esté siempre activo.
2. **Estado Real del Symbiote:** `get_talespire_status()` reporta `symbiote_connected` consultando el socket activo real en `ConnectionManager`.
3. **Modos Duales (`talespire_auto_throw`):** Nueva preferencia persistente que permite alternar entre **Lanzamiento Automático** (ejecuta el micro-gesto físico calibrado `execute_throw_gesture()`) y **Modo Manual en Bandeja** (solo coloca los dados en la bandeja mediante `putDiceInTray` / Named Pipe).

### Consecuencias
* Conexión instantánea del Symbiote apenas se abre TaleSpire y control total del usuario sobre el comportamiento físico de los dados.

---

## ADR-011: Mitigación de Pantalla Negra en Linux WebKitGTK (`WEBKIT_DISABLE_COMPOSITING_MODE=1`)

### Estado
**Aceptado** (Introducido en v1.0.3)

### Contexto
En distribuciones Linux con WebKitGTK 2.40+ (Pop!_OS, Ubuntu 24.04), definir únicamente `WEBKIT_DISABLE_DMABUF_RENDERER=1` hacía que el compositor acelerado de WebKit fallara al inicializar el contexto EGL sin DMABUF, mostrando una ventana negra al iniciar. Asimismo, aplicar `backdrop-blur` sobre un elemento `<rect>` SVG con máscara en `SpotlightTour.tsx` bloqueaba el pipeline de renderizado GTK.

### Decisión
1. Declarar conjuntamente `WEBKIT_DISABLE_DMABUF_RENDERER=1` y `WEBKIT_DISABLE_COMPOSITING_MODE=1` en `desktop_app.py`, `iniciar.sh` y `ejecutables/linux/parma.sh`.
2. Eliminar `backdrop-blur-xs` sobre elementos SVG enmascarados.

### Consecuencias
* Renderizado inmediato y libre de pantallas negras en cualquier GPU (NVIDIA, AMD, Intel) bajo X11 y Wayland en Linux.

---

## ADR-012: Conectores Desacoplados Multi-Proveedor para Retratos con IA y Empaquetado Legal OKF

### Estado
**Aceptado** (Desde v1.0.1, Consolidado en v1.0.3)

### Contexto
Los jugadores desean generar retratos personalizados para sus personajes sin estar obligados a pagar suscripciones ni configurar claves de API complejas, pero los usuarios avanzados también quieren poder conectar sus propias cuentas de Google AI Studio, OpenAI o instancias locales de Stable Diffusion.

### Decisión
Implementar en `DesktopBridge.generate_ai_portrait` una arquitectura multi-conector:
1. **Proveedor Gratuito por Defecto (`pollinations` / `free`):** Conecta con Pollinations.ai (modelo `flux`) sin requerir API Key y forzando `enhance=false` y `nologo=true` para fidelidad estricta al prompt.
2. **Google AI Studio (`google` / `gemini`):** Conecta con Imagen 3 (`:predict`) con fallback automático al endpoint OpenAI-compatible de Gemini (`/v1beta/openai/images/generations`).
3. **OpenAI (`openai`):** Conecta con DALL-E 3 devolviendo `b64_json`.
4. **Stable Diffusion Local (`local`):** Conecta con `http://127.0.0.1:7860/sdapi/v1/txt2img`.

### Consecuencias
* Generación de retratos lista para usar desde el primer segundo tras instalar Parma, con extensibilidad total hacia modelos comerciales o locales.

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
