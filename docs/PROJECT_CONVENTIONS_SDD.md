# Especificación del Proyecto y Convenciones de Arquitectura (SDD - Spec-Driven Development)

Este documento es la **Fuente Única de Verdad (Single Source of Truth)** para el desarrollo del **Visualizador & Editor D&D 5e**. Define las convenciones de ingeniería permanentes y el estado de avance de cada especificación funcional del prototipo.

---

## 📊 Estado de Requisitos y Módulos (SDD Tracker)

| # | Módulo / Requisito | Estado | Plataformas | Descripción Breve |
| :-: | :--- | :-: | :-: | :--- |
| **01** | **Arquitectura Multiplataforma & Paridad de Lanzadores** | `✅ COMPLETADO` | Linux / Windows | Base de código única (`main`), scripts nativos (`.bat` / `.sh`) y compilador PyInstaller dual. |
| **02** | **Jerarquía de Datos & Reorganización de PDFs** | `✅ COMPLETADO` | Linux / Windows | Separación en `data/manuals/` y `data/characters/`, empaquetado y resolución dinámica de rutas. |
| **03** | **Persistencia Local con SQLite (`dnd_database.db`)** | `✅ COMPLETADO` | Linux / Windows | Migración desde JSON plano a base relacional SQLite en modo WAL con esquema multi-personaje. |
| **04** | **Árbol Atómico OKF: Renderizado Markdown & Buscador** | `✅ COMPLETADO` | Linux / Windows | Reemplazo de `ft.Text` por `ft.Markdown`, limpieza de escapes y buscador en vivo en cabecera. |
| **05** | **Visor de Manuales: Modo Inmersivo & Controles Ergonómicos** | `✅ COMPLETADO` | Linux / Windows | Zen Reader (100% altura), controles en barra superior y botón de importación externa. |
| **06** | **Visualización de Personaje: Retrato & Avatar Gráfico** | `✅ COMPLETADO` | Linux / Windows | Componente `CharacterPortraitCard` con marco dorado, subida de foto local y fallback visual. |

---

## 🏛️ PARTE I: Convenciones Obligatorias de Arquitectura (Reglas Permanentes)

Cualquier nuevo desarrollo, dependencia, refactorización o corrección dentro de este repositorio debe someterse estrictamente a las siguientes directrices:

### 1. Paridad Dual Obligatoria (Dual-Platform Core)
* La aplicación se desarrolla sobre una **Base de Código Única (Single Codebase)** en la rama `main`.
* No existen ramas permanentes separadas para Linux o Windows: el 100% de la lógica de negocio, reglas de D&D 5e y vistas Flet son compartidas.
* Queda estrictamente prohibido introducir llamadas o comportamientos exclusivos de un solo sistema operativo sin proveer una abstracción multiplataforma equivalente.

### 2. Política Estricta de Dependencias ([requirements.txt](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/requirements.txt))
* Todo paquete que se incorpore **debe contar con soporte oficial tanto en Linux x86_64 como en Windows x86_64** (vía Python puro o disponibilidad de *wheels* binarios precompilados).
* Si una librería es indispensable pero exclusiva de Windows (o Linux), **debe declararse obligatoriamente con marcadores de entorno PEP 508** (por ejemplo: `paquete; sys_platform == 'win32'`). De este modo, `pip install -r requirements.txt` nunca arrojará error en la otra plataforma.
* Versión fijada de Flet: `flet[all]==0.26.0` (o dentro de la serie 0.26.x compatible) para asegurar paridad de la API de widgets y disponer de los runners de escritorio nativos (`flet-desktop-light`).

### 3. Paridad Total de UX/UI y Motores Python
* La experiencia de usuario, diseño visual dorado, paleta de colores, componentes interactivos y diálogos deben lucir y funcionar de manera idéntica en ambos sistemas operativos.
* Ningún componente visual puede depender de fuentes o widgets que existan solo en Windows o solo en Linux.

### 4. Lanzadores y Compilación Sincronizados
* **Modo Desarrollo**:
  * Windows: `iniciar_desktop.bat` o `iniciar.bat`.
  * Linux: `iniciar.sh` (permisos de ejecución `chmod +x`).
  * Agnóstico por terminal: `python run_app.py` o `python -m flet_app.main`.
* **Modo Compilación**:
  * Windows: `compilar_exe.bat` ➔ genera `dist/windows/Visualizador_Dnd_5e/Visualizador_Dnd_5e.exe`.
  * Linux: `compilar.sh` ➔ genera `dist/linux/Visualizador_Dnd_5e/Visualizador_Dnd_5e`.
  * El script unificado [flet_app/build_exe.py](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/flet_app/build_exe.py) gestiona ambas compilaciones con `sys.platform`, `os.pathsep` y el flag `--noconfirm`.

### 5. Agnosticismo en Manejo de Rutas y Modo Empaquetado (`sys.frozen`)
* Nunca utilizar barras duras (`/` o `\`) ni separadores de sistema (`;` o `:`) en cadenas de texto. Utilizar siempre `os.path.join()`, `os.pathsep` y `os.sep`.
* Toda clase o módulo que cargue recursos en disco (datos, PDFs, compendios OKF) debe soportar detección de ejecución empaquetada:
  ```python
  if getattr(sys, "frozen", False):
      base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
  else:
      base_dir = ... # Directorio relativo al código fuente
  ```

---

## 📋 PARTE II: Especificación Detallada de Módulos (SDD Specifications)

### Módulo 01: Arquitectura Multiplataforma & Paridad de Lanzadores
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * `iniciar.sh` y `compilar.sh` operativos con permisos de ejecución.
  * `run_app.py` como punto de entrada raíz que abstrae la importación del paquete `flet_app`.
  * `requirements.txt` estandarizado a UTF-8 con dependencias condicionales PEP 508.
  * `build_exe.py` adaptado con `os.pathsep` y subdirectorios `dist/linux/` y `dist/windows/`.
* **Criterio de Aceptación**: La aplicación arranca sin errores tanto en modo dev como empaquetada en ambos sistemas operativos.

---

### Módulo 02: Jerarquía de Datos & Reorganización de PDFs
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * `data/manuals/`: Alberga los manuales oficiales (`Manual del Jugador 2024.pdf`, `Guia de Xanathar Para Todo.pdf`, `Caldero de Tasha para Todo.pdf`).
  * `data/characters/`: Alberga fichas de personaje (`Artanis LVL 4.pdf`), exportaciones de partidas y futuros avatares.
  * `flet_app/ui/views/pdf_viewer.py`: Motor de búsqueda en cascada (`data/manuals/` ➔ `data/characters/` ➔ raíz).
  * `flet_app/main.py`: Resolución de ficha de ejemplo vinculada a `data/characters/`.
* **Criterio de Aceptación**: Todos los manuales y fichas abren correctamente sin duplicar archivos en la raíz.

---

### Módulo 03: Persistencia Local con SQLite (`dnd_database.db`)
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Implementado en `flet_app/core/db.py` con clase `DatabaseManager`.
  * SQLite con `PRAGMA journal_mode=WAL`, `synchronous=NORMAL` y `foreign_keys=ON`.
  * Tablas relacionales: `characters`, `network_nodes`, `network_edges`, `campaign_journals`, `app_settings`.
  * Migración automática e imperceptible desde `autosave_character.json` a `dnd_database.db`.
  * Copia y almacenamiento de retratos en `data/characters/portraits/`.
* **Criterio de Aceptación**: Los cambios de ficha, combate y retratos persisten entre reinicios en la base de datos SQLite y mantienen compatibilidad hacia atrás.

---

### Módulo 04: Árbol Atómico OKF: Renderizado Markdown Real y Buscador en Índice
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Implementado en `flet_app/ui/views/okf_view.py`.
  * Sustitución de `ft.Text` por `ft.Markdown(extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)`.
  * Sanitización de descripciones crudas YAML/OCR (limpieza de comillas escapadas, saltos innecesarios y formato legible).
  * Buscador reactivo en la cabecera del panel maestro para filtrar entidades en tiempo real.
* **Criterio de Aceptación**: Las entradas del compendio se leen con formato Markdown auténtico, negritas, listas y tablas sin artefactos de escape crudo.

---

### Módulo 05: Visor de Manuales: Modo Lectura Inmersivo y Controles Ergonómicos
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Implementado en `flet_app/ui/views/pdf_viewer.py`.
  * Barra superior ergonómica con selector de manuales, botón TOC, paginación numérica directa, selector de zoom y botón de Modo Zen.
  * Escaneo dinámico automático de manuales disponibles en `data/manuals/`.
  * Botón para importar libros PDF externos vía `ft.FilePicker`.
  * Modo Zen (Lectura Inmersiva): oculta la barra superior y bandeja de dados, dedicando el 100% de la ventana al manual con botón flotante semitransparente para salir.
* **Criterio de Aceptación**: Lectura fluida a pantalla completa y split-screen sin desbordamiento.

---

### Módulo 06: Visualización del Propio Personaje (Retrato, Avatar y Ficha Gráfica)
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Componente `CharacterPortraitCard` en `flet_app/ui/components/portrait_card.py`.
  * Marco artístico dorado con hover interactivo y capa de cámara para selección de imagen (PNG, JPG, WebP).
  * Fallback estético inteligente con icono de clase (mago, bardo, clérigo, paladín, etc.) y siglas del personaje sobre fondo temático.
  * Integrado en la cabecera de `CombatView` y en la tarjeta de identidad de `SheetView`.
* **Criterio de Aceptación**: El personaje cuenta con identidad visual personalizada o fallback heráldico con persistencia local.
