# D&D Sanctum — Plan de Arquitectura y Migración Técnica: Flet a PyWebView + React 18

> **Nombre Oficial de la Aplicación:** `D&D Sanctum` (*Desktop Character Hub & Grimoire*)  
> **Rama de Trabajo:** `pywebview-migration`  
> **Estado:** En Ejecución  
> **Objetivo:** Sustituir la capa de interfaz Flet (Flutter) por una arquitectura moderna basada en **PyWebView + React 18 + Vite + Tailwind CSS**, manteniendo el 100% de la lógica de negocio Python en local, reduciendo el consumo de RAM de ~220 MB a ~60 MB, aplicando la **Ley de Hick** y el Design System de Stitch (**Obsidian & Parchment D&D 5e Hub**), y garantizando empaquetado nativo en `.exe` (Windows) y `Flatpak` (Linux) con integración fluida para **TaleSpire**.

---

## 1. Justificación y Objetivos Técnicos

### 1.1 Problemas del Stack Actual (Flet / Flutter)
1. **Consumo de Memoria Excesivo:** Flet levanta un runtime completo de Flutter en C++ junto al intérprete de Python, promediando **140 MB a 220 MB de RAM** en reposo.
2. **Rigidez de UI / Sobrecarga Cognitiva:** Los widgets de Flet complican la personalización editorial requerida para una aplicación de rol inmersiva. El resultado actual presenta saturación de controles y dificultad para implementar una divulgación progresiva fluida.
3. **Scripts Redundantes:** Existen múltiples archivos de inicio y compilación desalineados (`iniciar.bat`, `iniciar_desktop.bat`, `iniciar.sh`, `compilar.sh`, `compilar_exe.bat`).

### 1.2 Por qué PyWebView + React (en vez de Tauri puro o Electron)
* **Frente a Electron:** PyWebView **no empaqueta Chromium** (~150 MB extra). Usa el motor web nativo del SO (**WebView2** en Windows y **WebKitGTK** en Linux). Huella de RAM: **~50-80 MB**.
* **Frente a Tauri puro (Rust):** Tauri exigiría reescribir desde cero en Rust el motor de PDFs AcroForms (`PyMuPDF`), el analizador de reglas Markdown/YAML (`okf_engine`) y la base de datos, lo que implicaría meses de trabajo improductivo. Con PyWebView, **la lógica Python se conserva íntegra**.
* **Frente a Flet:** React + Tailwind permite control milimétrico sobre el DOM, transiciones de CSS, tipografía refinada (EB Garamond, Manrope, Space Grotesk) y arquitectura de componentes desacoplada.

---

## 2. Arquitectura General del Sistema

```
+-------------------------------------------------------------------------------+
|                        VENTANA ESCRITORIO (PYWEBVIEW)                         |
|  - Windows: Microsoft Edge WebView2 (Nativo)                                  |
|  - Linux:   WebKit2GTK (Nativo / Flatpak Runtime org.gnome.Platform)          |
+---------------------------------------+---------------------------------------+
                                        |
     [IPC Bridge: window.pywebview.api] | [Evaluate JS / Custom Events]
                                        v
+-------------------------------------------------------------------------------+
|                       CAPA FRONTEND (React 18 + Vite)                         |
|  - Design System: Obsidian & Parchment (Stitch Design System Tokens)          |
|  - Principios: Ley de Hick, Anti-Icon Proliferation, Progressive Disclosure   |
|  - Layout: Header táctico minimalista, Drawer contextual, Vistas modulares   |
|  - Soporte de Temas: Dark Mode (Obsidian) / Light Mode (Parchment) / Plugins |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                    CAPA BACKEND LOCAL (Python 3.11+)                          |
|  - Entry Point: desktop_main.py (Inicia ventana PyWebView + expone API)       |
|  - core/db.py: SQLite (Personajes, notas, historial de dados)                 |
|  - core/pdf_engine.py: PyMuPDF / pypdf (AcroForms oficiales D&D 5e)           |
|  - core/okf_engine.py: Compendio Markdown/YAML (Clases, conjuros, etc.)       |
|  - core/talespire_bridge.py: IPC Named Pipe (Win) / Unix Socket (Proton)      |
|  - core/rules.py, point_buy.py, modifier_pipeline.py: Reglas 5e puras         |
+-------------------------------------------------------------------------------+
```

---

## 3. Estructura de Directorios Propuesta

Para limpiar el proyecto y erradicar todo residuo de Flet, la estructura final será:

```
Vizualizador Dnd/
├── core/                           # Lógica pura de negocio Python (desacoplada de UI)
│   ├── __init__.py
│   ├── db.py                       # Gestor SQLite
│   ├── models.py                   # Modelos de datos (Pydantic / Dataclasses)
│   ├── modifier_pipeline.py        # Pipeline de cálculo de bonos y atributos
│   ├── okf_engine.py               # Motor del compendio Markdown
│   ├── pdf_engine.py               # Generación y lectura de PDFs AcroForms
│   ├── point_buy.py                # Reglas de compra por puntos
│   ├── quick_build.py              # Generador rápido de arquetipos
│   ├── random_generator.py         # Generador aleatorio
│   ├── rules.py                    # Descansos, reglas y mecánicas 5e
│   ├── session_ledger.py           # Auditoría de tiradas en memoria
│   └── talespire_bridge.py         # Puente IPC y simulación de dados TaleSpire
│
├── desktop_api/                    # Capa adaptadora PyWebView <-> Core
│   ├── __init__.py
│   ├── bridge.py                   # Clase PyWebViewBridge expuesta al frontend
│   └── events.py                   # Emisor de eventos push hacia React
│
├── frontend/                       # Proyecto React 18 + Vite + TypeScript / Tailwind
│   ├── package.json
│   ├── vite.config.ts              # Configuración de build estático a ../dist_ui
│   ├── tailwind.config.js          # Tokens del Design System de Stitch
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                    # Cliente tipado para window.pywebview.api (con Mock para dev)
│   │   ├── components/             # Componentes atómicos (Botones, Drawer, Modales, Inputs)
│   │   │   ├── common/
│   │   │   ├── dice/               # Bandeja flotante / drawer de dados
│   │   │   └── wizard/             # Pasos del creador progresivo
│   │   ├── views/                  # Vistas principales
│   │   │   ├── SheetView.tsx       # Hoja de personaje minimalista y editorial
│   │   │   ├── CombatView.tsx      # Rastreador de combate táctico
│   │   │   ├── SpellsView.tsx      # Grimorio y ranuras
│   │   │   ├── CompendiumView.tsx  # Visor OKF con búsqueda instantánea
│   │   │   ├── CharacterWizard.tsx # Forja de personajes por fases
│   │   │   └── SettingsView.tsx    # Ajustes, TaleSpire, rutas y selector de tema
│   │   ├── context/                # Estado global (Zustand o Context API)
│   │   └── styles/
│   │       ├── index.css
│   │       └── themes/             # CSS Variables para temas (dark, light, etc.)
│   └── dist/                       # Artefactos compilados servidos localmente
│
├── data/                           # Base de datos y personajes del usuario
│   ├── dnd_database.db
│   └── characters/
│
├── themes/                         # Carpeta extensible para temas personalizados (.json / .css)
│   ├── dark-obsidian/
│   └── light-parchment/
│
├── okf_dnd5e/                      # Archivos de compendio oficiales Markdown
├── desktop_app.py                  # Lanzador principal PyWebView
├── build_desktop.py                # Compilador unificado PyInstaller (.exe / Linux)
├── requirements.txt                # Dependencias limpias (SIN flet)
├── iniciar.bat                     # Lanzador único para Windows
└── iniciar.sh                      # Lanzador único para Linux
```

---

## 4. Diseño Visual & Ley de Hick (Stitch Design System)

El frontend implementará el sistema de diseño extraído del proyecto Stitch **"Obsidian & Parchment D&D 5e Hub"** (`projects/15335208518407567827`), adaptado estrictamente a la **Ley de Hick** según la directriz en [`hicks-law-ui/SKILL.md`](file:///c:/Users/natha/Documents/Repos/Vizualizador%20Dnd/.agents/skills/hicks-law-ui/SKILL.md).

### 4.1 Principios de la Ley de Hick aplicados a la Interfaz
1. **Anti-Icon Proliferation (Restricción Severa de Iconos):**
   - **Prohibido:** Poner iconos a cada etiqueta de texto (ej. no llenar la pantalla de 🛡️, ⚔️, 📜, ❤️, ⚡ al lado de cada número).
   - **Permitido:** Solo iconos funcionales universales: `✕` (Cerrar), `⚙` (Ajustes), `◄` (Atrás), y acción de tirar dado en la bandeja.
   - **Prioridad a la Tipografía:** Se jerarquiza con peso de fuentes: `Space Grotesk Bold` para modificadores y números grandes; `EB Garamond` para títulos; `Manrope` para textos descriptivos.
2. **Divulgación Progresiva (Progressive Disclosure):**
   - En lugar de mostrar 50 campos de hechizos, si el personaje es un Guerrero no mágico, la sección de conjuros se oculta o sintetiza en un badge discreto.
   - En el Creador de Personajes: primero Raza; una vez elegida, aparecen las Subrazas; primero Clase; el Arquetipo/Subclase solo aparece si el nivel configurado es igual o superior al umbral oficial (Nivel 1 para Clérigos/Brujos, Nivel 2 para Magos/Druidas, Nivel 3 para Guerreros/Pícaros).
3. **Ergonomía Espacial & Salidas Claras:**
   - La bandeja de dados (`DiceTray`) no ocupa un tercio fijo de la pantalla: es un **Drawer colapsable lateral o panel flotante** accesible con la tecla `Espacio` o un clic sutil.
   - Todo modal o asistente tiene 3 formas obligatorias de cierre: botón `✕` superior, botón `Cancelar` inferior, y tecla `Escape`.

### 4.2 Paleta de Colores y Tokens (Tailwind CSS)

#### Modo Oscuro: *Obsidian Sanctum* (Por defecto)
* **Canvas de fondo (`surface-canvas`):** `#12181c` (Negro obsidiana profundo, descanso visual en partidas nocturnas).
* **Superficie de tarjetas (`surface-card`):** `#232b2f` (Gris carbón arquitectónico).
* **Bordes estructurales (`border-iron`):** `#323d42` (1px, sutil, delimitador sin estridencias).
* **Acento Primario (`accent-crimson`):** `#c50009` (Rojo carmesí para botones de acción crítica, HP y daño).
* **Acento Secundario (`accent-gold`):** `#c9a45c` (Oro envejecido para bonificadores, estrellas de competencia e inspiración).
* **Texto Principal (`text-parchment`):** `#ede3d2` (Pergamino iluminado de alta legibilidad).
* **Texto Secundario (`text-muted`):** `#8c979e` (Gris rúnico para etiquetas y descripciones).

#### Modo Claro: *Illuminated Grimoire*
* **Canvas de fondo (`surface-canvas`):** `#f4efe6` (Pergamino antiguo cálido).
* **Superficie de tarjetas (`surface-card`):** `#ffffff` (Blanco hueso con sombra de contacto suave).
* **Bordes estructurales (`border-iron`):** `#d8ccba` (Borde tono papiro).
* **Acento Primario (`accent-crimson`):** `#a80007` (Carmesí profundo).
* **Acento Secundario (`accent-gold`):** `#8c6b2d` (Oro bronce antiguo).
* **Texto Principal (`text-parchment`):** `#1c1917` (Tinta negra cálida).
* **Texto Secundario (`text-muted`):** `#6b6357` (Tinta sepia atenuada).

#### Extensibilidad de Temas (Plugins / Custom Themes)
El frontend cargará dinámicamente variables CSS definidas en archivos JSON/CSS ubicados en la carpeta raíz `themes/`. Una pantalla de **Configuración (Settings)** permitirá seleccionar el tema activo sin requerir reinicios.

---

## 5. Especificación del Puente IPC (Python <-> PyWebView <-> React)

PyWebView inyecta un objeto global `window.pywebview.api` en el contexto del navegador. Todas las llamadas devuelven `Promise` en JavaScript y se resuelven en hilos concurrentes en Python.

### 5.1 Interfaz TypeScript (`frontend/src/api/types.ts`)

```typescript
export interface CharacterSummary {
  id: number;
  name: string;
  class_name: string;
  level: number;
  hp_current: number;
  hp_max: number;
  ac: number;
  passive_perception: number;
  updated_at: string;
}

export interface TaleSpireStatus {
  is_installed: boolean;
  is_running: boolean;
  is_connected: boolean;
  state_label: string;
}

export interface RollRequest {
  dice: { [sides: number]: number }; // ej: { 20: 1, 6: 2 }
  modifier: number;
  label: string;
  send_to_talespire: boolean;
}

export interface RollResult {
  total: number;
  dice_rolls: { sides: number; roll: number }[];
  modifier: number;
  label: string;
  timestamp: string;
  talespire_sent: boolean;
}

export interface AppSettings {
  theme: string;
  talespire_enabled: boolean;
  talespire_mode: "dm" | "player";
  custom_data_path: string;
}

export interface PyWebViewApi {
  // Personajes & Fichas
  list_characters(): Promise<CharacterSummary[]>;
  get_character(id: number): Promise<any>;
  save_character(character_data: any): Promise<{ success: boolean; id: number }>;
  import_character_pdf(file_path?: string): Promise<{ success: boolean; data?: any; error?: string }>;
  export_character_pdf(character_id: number): Promise<{ success: boolean; path?: string }>;

  // Compendio OKF
  search_compendium(query: string, category?: string): Promise<any[]>;
  get_compendium_entry(category: string, id: string): Promise<any>;

  // TaleSpire & Dados
  get_talespire_status(): Promise<TaleSpireStatus>;
  connect_talespire(): Promise<{ success: boolean; message: string }>;
  disconnect_talespire(): Promise<void>;
  roll_dice(request: RollRequest): Promise<RollResult>;
  trigger_talespire_gesture(): Promise<boolean>;

  // Reglas & Utilidades
  validate_point_buy(scores: Record<string, number>): Promise<{ valid: boolean; points_spent: number; error?: string }>;
  perform_rest(character_id: number, rest_type: "short" | "long", hit_dice_spent?: number): Promise<any>;

  // Configuración & Temas
  get_settings(): Promise<AppSettings>;
  save_settings(settings: AppSettings): Promise<boolean>;
  get_available_themes(): Promise<{ id: string; name: string; is_dark: boolean }[]>;
}
```

### 5.2 Implementación Backend (`desktop_api/bridge.py`)

```python
"""
Puente PyWebView para coordinar peticiones entre React y los módulos core.
"""
from typing import Dict, Any, List
import pywebview
from core.db import DatabaseManager
from core.okf_engine import OkfEngine
from core.pdf_engine import UniversalAcroFormHandler
from core.talespire_bridge import TaleSpireBridge
from core.point_buy import validate_point_buy_budget
from core.rules import perform_short_rest, perform_long_rest

class PyWebViewBridge:
    def __init__(self, db: DatabaseManager, okf: OkfEngine, ts_bridge: TaleSpireBridge):
        self.db = db
        self.okf = okf
        self.ts = ts_bridge
        self.window = None

    def set_window(self, window):
        self.window = window

    # --- Personajes ---
    def list_characters(self) -> List[Dict[str, Any]]:
        return self.db.list_characters_summary()

    def get_character(self, char_id: int) -> Dict[str, Any]:
        return self.db.load_character(char_id)

    def save_character(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        char_id = self.db.save_character(character_data)
        return {"success": True, "id": char_id}

    # --- TaleSpire & Dados ---
    def get_talespire_status(self) -> Dict[str, Any]:
        return {
            "is_installed": self.ts.is_installed,
            "is_running": self.ts.is_process_running(),
            "is_connected": self.ts.is_session_connected(),
            "state_label": self.ts.state.value
        }

    def connect_talespire(self) -> Dict[str, Any]:
        success, msg = self.ts.connect()
        return {"success": success, "message": msg}

    def disconnect_talespire(self) -> None:
        self.ts.disconnect()

    def roll_dice(self, request: Dict[str, Any]) -> Dict[str, Any]:
        import random
        from datetime import datetime
        pool = request.get("dice", {20: 1})
        modifier = int(request.get("modifier", 0))
        label = str(request.get("label", "Tirada"))
        send_ts = bool(request.get("send_to_talespire", True))

        rolls = []
        total = modifier
        for sides, count in pool.items():
            for _ in range(count):
                val = random.randint(1, int(sides))
                rolls.append({"sides": int(sides), "roll": val})
                total += val

        ts_sent = False
        if send_ts and self.ts.is_session_connected():
            url = self.ts.build_pool_url({int(k): v for k, v in pool.items()}, modifier=modifier, label=label)
            ts_sent = self.ts.send_roll(url)
            self.ts.execute_throw_gesture()

        return {
            "total": total,
            "dice_rolls": rolls,
            "modifier": modifier,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "talespire_sent": ts_sent
        }
```

---

## 6. Depuración y Eliminación de Código Obsoleto (Legacy Cleanup)

En esta migración se eliminarán por completo todos los elementos acoplados a Flet y los scripts antiguos redundantes:

1. **Eliminación de la Capa UI de Flet:**
   * Borrar la carpeta [`flet_app/ui/`](file:///c:/Users/natha/Documents/Repos/Vizualizador%20Dnd/flet_app/ui) completa.
   * Borrar [`flet_app/main.py`](file:///c:/Users/natha/Documents/Repos/Vizualizador%20Dnd/flet_app/main.py) y [`flet_app/build_exe.py`](file:///c:/Users/natha/Documents/Repos/Vizualizador%20Dnd/flet_app/build_exe.py).
   * Mover `flet_app/core/` a la raíz `core/`.
2. **Eliminación de Scripts Redundantes:**
   * Eliminar `iniciar.bat`, `iniciar_desktop.bat`, `iniciar.sh`, `compilar.sh`, `compilar_exe.bat`, `run_app.py`.
   * Crear dos únicos scripts limpios y actualizados:
     * `iniciar.bat` (Windows: ejecuta `python desktop_app.py`).
     * `iniciar.sh` (Linux: ejecuta `python3 desktop_app.py`).
3. **Limpieza de `requirements.txt`:**
   * Retirar `flet[all]==0.26.0`.
   * Agregar `pywebview>=5.1` y dependencias de servidor local liviano si aplica.

---

## 7. Estrategia de Empaquetado (.exe Windows y Flatpak Linux)

### 7.1 Windows (.EXE Nativo con PyInstaller)
* **Ventaja:** Como PyWebView utiliza `WebView2Loader.dll` y el runtime de Edge ya preinstalado en Windows 10 y 11, PyInstaller no tiene que empaquetar ningún navegador.
* **Tamaño final:** Un único archivo `.exe` o carpeta de ~45 a 60 MB.
* **Comando PyInstaller:**
  ```bash
  pyinstaller --noconsole --name=Visualizador_Dnd_5e \
    --add-data="frontend/dist;dist_ui" \
    --add-data="okf_dnd5e;okf_dnd5e" \
    --add-data="data;data" \
    --collect-all=pywebview \
    --hidden-import=pymupdf \
    desktop_app.py
  ```

### 7.2 Linux (Flatpak Nativo)
* **Runtime:** `org.gnome.Platform//46` (Freedesktop SDK).
* **Compatibilidad:** El runtime de GNOME ya incluye `WebKit2GTK 4.1` y soporte Wayland/X11 nativo con aceleración por hardware.
* **TaleSpire en Linux:** Se mantiene el soporte para detectar y conectar con TaleSpire ejecutado a través de Proton/Steam mediante el mapeo del socket de Wine.

---

## 8. Plan de Ejecución por Fases

| Fase | Tareas Principales | Entregables |
| :--- | :--- | :--- |
| **Fase 1: Preparación del Núcleo** | - Reubicar `flet_app/core` a `core/`.<br>- Crear `desktop_api/bridge.py` y `desktop_app.py`.<br>- Actualizar `requirements.txt` con `pywebview`. | `core/` desacoplado, ventana PyWebView funcional levantando un HTML de prueba. |
| **Fase 2: Infraestructura Frontend** | - Inicializar proyecto React 18 + Vite en `frontend/`.<br>- Configurar Tailwind CSS con tokens de Stitch (Obsidian & Parchment).<br>- Implementar Theme Provider (Modo Claro / Modo Oscuro) y Mock API para desarrollo en browser. | Estructura frontend lista con hot-reload en `localhost:5173` y build en `frontend/dist`. |
| **Fase 3: Diseño UI con Ley de Hick** | - Maquetar Header táctico minimalista (sin saturación de iconos).<br>- Implementar Bandeja de Dados (`DiceTray`) como Drawer colapsable.<br>- Crear Vistas: Hoja de Personaje, Rastreador de Combate, Grimorio y Compendio OKF.<br>- Crear Asistente de Creación de Personaje por etapas progresivas. | Vistas completas navegables con componentes ergonómicos. |
| **Fase 4: Integración TaleSpire & PDF** | - Conectar el puente `talespire_bridge.py` con los botones de tirada de la UI.<br>- Integrar importación/exportación de PDF con PyMuPDF. | Tiradas enviándose a TaleSpire y sincronización de ficha PDF. |
| **Fase 5: Depuración Legacy** | - Eliminar código de Flet (`flet_app/`).<br>- Borrar scripts antiguos (`iniciar_desktop.bat`, `compilar.sh`, etc.).<br>- Dejar `iniciar.bat`, `iniciar.sh` y `build_desktop.py` unificados. | Repositorio limpio y libre de dependencias huérfanas. |
| **Fase 6: Compilación y Validación** | - Probar build de PyInstaller en Windows (.exe).<br>- Validar consumo de memoria RAM (<80 MB).<br>- Configurar manifiesto Flatpak para Linux. | Ejecutable standalone funcional y verificado. |

---

## 9. Anexo A: Compactación de Páginas y Aislamiento de OKF (Ley de Hick)

Para evitar la sobrecarga cognitiva durante la partida:
1. **Compendio de Consulta vs Administración de Archivos:**
   - La pantalla de juego contará con un buscador rápido flotante o pestaña aislada `Compendio` enfocada exclusivamente en lectura y búsqueda instantánea (sin botones de gestión de archivos, recarga o indexación técnica).
   - Toda la **gestión de fuentes de datos OKF** (añadir carpetas, recargar índice, re-escanear metadatos) se traslada a la pantalla de **Configuración (Settings)**.
2. **Navegación Unificada Táctica:**
   - Barra superior minimalista: Nombre del personaje activo, selector rápido de modo (Hoja / Combate / Grimorio / Compendio / Ajustes), y botón de dados (que abre el Drawer colapsable).

---

## 10. Anexo B: Propuesta de Integración Externa con AideDD.org

* **Objetivo:** Permitir en futuras iteraciones la sincronización y actualización del compendio de conjuros, invocaciones, trasfondos y objetos mágicos desde [AideDD](https://www.aidedd.org/dnd-filters/spells.php).
* **Enfoque Arquitectónico:**
  1. **Módulo Conector (`core/importers/aidedd_crawler.py`):**
     - Cliente HTTP asíncrono con `httpx` que consulta el catálogo oficial de AideDD.
     - Extracción y normalización de campos (nivel, escuela, tiempo de lanzamiento, alcance, componentes, duración, descripción en español e inglés).
  2. **Pipeline de Transformación a OKF:**
     - El conector convertirá los conjuros obtenidos en archivos Markdown individuales con Frontmatter YAML compatibles con el formato estándar del `OkfEngine` (`okf_dnd5e/conjuros/...`).
  3. **Activador en UI:**
     - Botón en `Configuración > Fuentes de Datos`: *"Sincronizar Conjuros desde AideDD (Beta)"*, que operará en segundo plano sin congelar la interfaz y reportará el progreso mediante eventos en la barra de estado.
