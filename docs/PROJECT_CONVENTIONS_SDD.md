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
| **07** | **Calibración de Reglas de Clase & Sentidos Dinámicos** | `✅ COMPLETADO` | Linux / Windows | Aptitud mágica dinámica en SpellsView, corrección de subclase vs subraza en Wizard y sentidos dinámicos. |
| **08** | **Mecánicas de Dados de Golpe, Descansos y Condiciones** | `✅ COMPLETADO` | Linux / Windows | Caras de dados por clase (d6-d12), diálogo de descanso corto interactivo, recuperación en descanso largo y gestor de estados. |
| **09** | **Expansión del Compendio OKF: Armamento, Armaduras y Reglas** | `✅ COMPLETADO` | Linux / Windows | Directorio `equipo_y_armamento/` (armas, armaduras, equipo), reglas de combate y estado, chips con conteo dinámico y 513 entidades indexadas. |
| **10** | **Portabilidad de Personajes: Exportación/Importación JSON & AcroForm PDF** | `✅ COMPLETADO` | Linux / Windows | Exportación e importación individual JSON en gestor de héroes y rellenado editable automático de PDF oficial AcroForm (`export_character_to_pdf`). |
| **11** | **Creador de Personajes D&D Beyond: 3 Modos & 7 Fases** | `✅ COMPLETADO` | Linux / Windows | Hub de selección (Standard, Quick Build 60s, Randomize 4d6), stepper de 7 fases, Point Buy 27 pts, tokens TTUI y side drawer OKF en Markdown. |
| **12** | **TaleSpire Dice Bridge & Session Ledger** | `✅ IMPLEMENTADO` | Windows / Linux | Detección automática de TaleSpire vía IPC Named Pipe, tiradas compuestas, fallback local y registro volátil de sesión. |


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

---

### Módulo 07: Calibración de Reglas de Clase & Sentidos Dinámicos
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * `SpellsView` adaptado con `get_character_spell_stats` para determinar la aptitud mágica real (INT para Magos, SAB para Clérigos/Druidas/Exploradores, CAR para Bardos/Paladines/Brujos/Hechiceros) y actualización reactiva en `update_data`.
  * `CharacterCreatorWizard` corregido para no asignar la subraza al campo `subclass`, manteniendo la subraza en `race` y la subclase limpia en nivel 1.
  * Campo `senses` dinámico agregado a `CharacterSheet`, poblado desde el asistente y mostrado en `SheetView`.
  * Suite de pruebas automatizadas actualizada y en verde (`scratch/test_all_views.py` y `scratch/test_wizard_and_fixes.py`).
* **Criterio de Aceptación**: Cualquier clase mágica o especie muestra sus estadísticas y sentidos correctos y las suites de prueba pasan al 100%.

---

### Módulo 08: Mecánicas de Dados de Golpe, Descansos Oficiales y Condiciones de Combate
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Campos `hit_dice_max`, `hit_dice_current`, `hit_dice_faces` y `conditions` agregados al modelo `CharacterSheet` con deserialización defensiva para bases de datos previas.
  * `perform_short_rest` actualizado para gastar dados reales según la clase (d6, d8, d10, d12) sumando el modificador de Constitución y recargando poderes de descanso corto.
  * Diálogo modal interactivo de Descanso Corto en la barra superior que permite elegir la cantidad exacta de dados a gastar (0 a disponibles).
  * `perform_long_rest` restaurado según reglas oficiales PHB 2024: restablece salud al 100%, todos los espacios y poderes, y recupera la mitad de los dados de golpe máximos gastados (mínimo 1).
  * Gestor interactivo de 9 condiciones oficiales en `CombatView` (Concentración, Envenenado, Asustado, Derribado, Cegado, Ensordecido, Paralizado, Incapacitado, Invisible) con tooltips explicativos y persistencia inmediata.
  * Fila de gasto directo de dado de golpe en `health_card` e indicador en la cabecera vital de `SheetView`.
* **Criterio de Aceptación**: El descanso corto consume y tira los dados correctos según la clase, el descanso largo recupera dados de golpe proporcionales y las condiciones de combate pueden activarse/desactivarse interactivamente.

---

### Módulo 09: Expansión del Compendio OKF: Armamento, Armaduras y Reglas
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Directorio `okf_dnd5e/equipo_y_armamento/` incorporado con catálogo atómico estructurado: `armas_simples.md`, `armas_marciales.md`, `armaduras_y_escudos.md` y `equipo_de_aventuras.md`.
  * Documentos de reglas en `okf_dnd5e/reglas_y_mecanicas/`: `condiciones_de_estado.md` (15 condiciones oficiales de D&D 5e con efectos mecánicos) y `acciones_en_combate.md` (10 acciones estándar de turno).
  * Catálogo e índice maestro `index_metadata.json` ampliado de 507 a 513 entidades atómicas catalogadas con frontmatter YAML.
  * `OkfEngine.count_entities()` implementado para cálculo de totales dinámicos en memoria por taxonomía.
  * Chips de navegación en `OkfCompendiumView` enriquecidos con nueva categoría `🛡️ Equipo & Armamento` y conteos dinámicos en vivo para las 7 categorías sin valores estáticos desfasados.
* **Criterio de Aceptación**: Búsqueda instantánea de armas, armaduras, equipo de aventurero y reglas de combate/condiciones integrada y funcional en el visor maestro-detalle OKF.

---

### Módulo 10: Portabilidad de Personajes: Exportación/Importación JSON & AcroForm PDF
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * Implementado en `flet_app/core/pdf_engine.py` (`UniversalAcroFormHandler.export_character_to_pdf`) para rellenado automático de formularios oficiales AcroForm (compatible con anotaciones xref y widgets estándar).
  * Diálogo **🎭 Gestor de Héroes & Personajes** en `flet_app/main.py`:
    * Botón de descarga individual en cada tarjeta para exportar la ficha a `.json`.
    * Botón de exportación oficial en cada tarjeta para generar el PDF editable con las estadísticas, armas, conjuros, puntos de golpe y dados de golpe actuales.
    * Acciones del diálogo con botones para **"📥 Importar JSON"** y **"📄 Importar PDF"** integrados directamente con `ft.FilePicker`.
  * Menú emergente de exportación rápida en la barra superior (`btn_export_menu`) con acceso en un solo clic a exportación JSON y PDF para la ficha activa.
  * Nuevo método `get_character_by_id` en `DatabaseManager` para lectura atómica de cualquier personaje sin alternar forzosamente su estado activo.
* **Criterio de Aceptación**: Cualquier ficha puede exportarse a JSON o a PDF editable oficial y reimportarse de forma transparente en la base de datos local SQLite.

---

### Módulo 11: Creador de Personajes D&D Beyond (3 Modos & 7 Fases)
* **Estado**: `✅ COMPLETADO`
* **Implementación**:
  * **Tokens de Diseño TTUI (D&D Beyond)**: Paleta Obsidian (`#12181c`), superficies de tarjeta (`#232b2f`), bordes de pizarra/hierro (`#323d42`), carmesí oficial D&D (`#c50009`), oro arcano (`#c9a45c`) y texto pergamino (`#ede3d2`) estandarizados en `flet_app/ui/theme.py`.
  * **Prototipado Stitch MCP**: Proyecto `projects/15335208518407567827` ("DnD Beyond Character Builder - Desktop UI") creado con diseño de hub y sistema estético Dark Fantasy.
  * **Motores Desacoplados**:
    * `flet_app/core/point_buy.py`: Calculadora matemática oficial de compra por puntos (27 pts, rango 8-15, tabla de costes no lineal).
    * `flet_app/core/quick_build.py`: Asignación asistida en 60s basada en Priority Arrays sobre el Standard Array para las 12 clases.
    * `flet_app/core/random_generator.py`: Generador procedural con algoritmo 4d6 drop lowest, filtros de clase/especie, escala nivel 1-20 y botón re-roll.
    * `flet_app/core/modifier_pipeline.py`: Pipeline determinista de evaluación de modificadores (Base $\to$ Set $\to$ Bonus $\to$ Proficiency).
  * **Componentes Modulares & UI**:
    * `BuilderHubDialog`: Hub con 3 tarjetas visuales (Standard Build, Quick Build, Randomize).
    * `StandardBuilderDialog`: Constructor en 7 fases (1. Reglas, 2. Especie, 3. Clase, 4. Atributos, 5. Trasfondo, 6. Equipo, 7. Conjuros).
    * `BuilderHeader`: Barra superior flotante reactiva con vitales (Nombre, Clase, Nivel, PG, CA, Avatar).
    * `BuilderStepper`: Stepper horizontal de 7 pasos con badges de alerta para opciones pendientes.
    * `AbilityMatrix`: Matriz de características interactiva soportando Point Buy (botones $+/-$), Standard Array, 4d6 y Manual.
    * `OkfDrawer`: Panel lateral deslizante que renderiza los compendios atómicos Markdown de `okf_dnd5e/` sin cerrar el constructor.
    * `QuickBuildDialog` & `RandomizeDialog`: Modales dedicados para creación en 60s y tiradas procedurales.
* **Criterio de Aceptación**: Los tres modos forjan personajes legales de D&D 5e (PHB 2024), persistiendo en SQLite, actualizando las vistas reactivas y pasando la suite de pruebas unitarias y de integración al 100%.

