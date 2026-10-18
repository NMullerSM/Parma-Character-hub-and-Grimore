# Informe de Auditoría y Remediación Técnica — `pywebview-migration`

> **Estado:** 100% Implementado y Verificado  
> **Fecha:** Octubre 2026  
> **Proyecto:** Visualizador & Editor D&D 5e / 5.5e (D&D Sanctum Desktop)  
> **Arquitectura:** PyWebView + React 19 + TypeScript + Tailwind CSS v4 + SQLite + OkfEngine

---

## 1. Diagnóstico Ejecutivo y Resumen de la Remediación

La decisión arquitectónica de migrar la interfaz de **Flet (Flutter)** a **PyWebView + React + TypeScript** es la dirección correcta para el proyecto. Sin embargo, durante el primer borrador de la migración se generó una **ruptura severa en el contrato de datos** entre el backend Python (`core/models.py`) y el frontend (`frontend/src/api/types.ts`), ocultada durante el desarrollo debido a los datos estáticos de prueba (*mock*) de `client.ts`. Además, varios motores del núcleo (`core/quick_build.py`, `core/random_generator.py`, `core/point_buy.py`, `core/okf_engine.py`) permanecían huérfanos sin comunicarse con la interfaz.

En esta intervención se corrigieron **todos los puntos críticos de falla**, se unificó bidireccionalmente el contrato de serialización, se implementó auto-guardado en SQLite con *debounce*, se conectó la Forja con los 3 modos de creación oficiales y se restablecieron todas las funciones siguiendo estrictamente la **Ley de Hick** (sin saturación de iconos, divulgación progresiva y salidas claras con tecla Escape).

---

## 2. Puntos Críticos de Falla Corregidos

### 2.1. Contrato de Datos Unificado (`core/models.py` ⇄ `desktop_api/bridge.py` ⇄ `frontend/src/api/`)
Se implementó un adaptador bidireccional en `DesktopBridge._serialize_character()` y se enriqueció `CharacterSheet.from_dict()`:

| Concepto | Problema Anterior | Solución Implementada |
| :--- | :--- | :--- |
| **Atributos (`abilities`)** | Python guardaba `Dict[str, int]` mientras React esperaba `Record<string, AbilityScoreData>` (`base, bonus, proficient, save_bonus`). En la UI aparecía `undefined` y al guardar desde React causaba `TypeError: unsupported operand type(s) for -: 'dict' and 'int'`. | `_serialize_character()` enriquece los 6 atributos calculando modificadores y salvaciones oficiales. `from_dict()` acepta tanto enteros directos como diccionarios estructurados. |
| **Habilidades (`skills`)** | Python guardaba `Dict[str, str]` (`"proficient"`), pero React esperaba `{proficient, bonus, expertise}`. Los bonos en la hoja aparecían como `+undefined`. | El bridge calcula dinámicamente las 18 habilidades oficiales de 5e con `core.rules.get_skill_modifier()`, respetando competencias y pericias. |
| **Acciones de Arma (`weapon_actions`)** | Disparidad de nombres (`attack_bonus` vs `hit_dc`, `damage` vs `damage_dice`). Las armas de SQLite no se mostraban y las creadas en React se perdían. | Homogeneización bidireccional de armas en `from_dict()` y `_serialize_character()`. Se añadieron tiradas independientes para impacto (`1d20`) y dados de daño. |
| **Ranuras de Conjuro (`spell_slots`)** | Disparidad entre `SpellSlotTier(level, total, current)` y `spell_slots_total`/`spell_slots_used`. No se renderizaban ni persistían. | Normalización bidireccional completa. Soporte para gastar/recuperar ranuras interactivamente con persistencia automática en base de datos. |
| **Estadísticas de Combate** | `ac` vs `armor_class`, `initiative` vs `initiative_bonus`, `death_save_successes` vs `death_saves_success`. | Soporte para ambos nombres en el serializador y deserializador. |
| **Velocidad y Dados de Golpe** | `speed` se mostraba como `"9 m pies"` y los dados de golpe como números planos. | `_parse_speed_feet()` convierte automáticamente distancias métricas o imperiales a pies enteros (`30`, `25`, `35`). Los dados de golpe se formatean como `XdY` (`4d10`). |

---

### 2.2. Bugs Críticos en el Backend Python
1. **Crash en Exportación de PDF:**
   - *Error:* `bridge.py` intentaba instanciar `UniversalAcroFormHandler(template_pdf)` y llamar al método inexistente `fill_from_character()`.
   - *Solución:* Conectado al método de clase real `UniversalAcroFormHandler.export_character_to_pdf(char, template_pdf_path, output_path)`.
2. **Rutas Base fuera del Repositorio:**
   - *Error:* `core/okf_engine.py` y `core/pdf_engine.py` conservaban tres llamadas anidadas a `os.path.dirname(...)` de cuando residían en `flet_app/core/`, apuntando al directorio padre del repositorio (`.../Repos`).
   - *Solución:* Ajustado el cálculo relativo a 2 niveles para ubicar con precisión `okf_dnd5e/` y las plantillas PDF en la raíz del proyecto.
3. **Colisiones de Clave Primaria en SQLite (`core/db.py`):**
   - *Error:* `save_character()` buscaba personajes por `WHERE name = ?` en vez de su `char.id`, causando duplicación al renombrar o sobreescritura accidental. Asimismo, la tabla `network_nodes` usaba `id TEXT PRIMARY KEY` global, arrojando `sqlite3.IntegrityError` cuando dos personajes tenían un `node_1`.
   - *Solución:* Se prioriza la búsqueda por `char.id` y la tabla relacional se actualizó a `PRIMARY KEY (id, character_id)` con `INSERT OR REPLACE`.
4. **Condición de Carrera con `pywebviewready`:**
   - *Error:* En frío, `window.pywebview.api` se inyectaba milisegundos después del montaje inicial de React, provocando que `isNative()` diera falso y se cargaran datos simulados.
   - *Solución:* `CharacterContext.tsx` y `ThemeContext.tsx` escuchan el evento nativo `window.addEventListener("pywebviewready", ...)` para sincronizar inmediatamente los datos reales de SQLite.
5. **Autosave con Debounce para Combate y Grimorio:**
   - *Solución:* Modificaciones de PG, PG temporales, salvaciones de muerte, condiciones, ranuras de conjuro y usos de rasgos activan un temporizador de 350 ms que sincroniza automáticamente el estado con `api.saveCharacter()`, evitando la pérdida de datos tras descansos cortos o largos.

---

## 3. Integración de Motores y Nuevas Funcionalidades

### 3.1. Forja de Personajes (`CharacterWizard.tsx`)
Conectada directamente con `OkfEngine`, `QuickBuildEngine`, `RandomCharacterGenerator` y `PointBuyCalculator`:
- **3 Modos de Creación Oficiales:**
  1. *Paso a Paso (Estándar):* Progresión secuencial (Concepto → Especie → Clase → Atributos) respetando la Ley de Hick. Subrazas reveladas únicamente si la especie posee linajes; selección de habilidades limitada al cupo de clase; arquetipos desbloqueados dinámicamente según nivel y edición (`5.5e` Nivel 3 unificado; `5e` Nivel 1/2/3).
  2. *Creación Rápida (60s):* Genera instantáneamente estadísticas, competencias, equipo inicial y trasfondo optimizado por arquetipo.
  3. *Aleatorio (4d6 Drop Lowest):* Tiradas matemáticas auténticas 4d6 descartando el menor valor, con desglose de dados auditables.
- **Validación Estricta de Point Buy:**
  - Presupuesto oficial de 27 puntos (rango 8 a 15).
  - Los botones `+` se deshabilitan en tiempo real si el costo excede el presupuesto restante (`can_increment: false`).
  - Botón de un solo clic para aplicar la Matriz Estándar (`15, 14, 13, 12, 10, 8`).

### 3.2. Motor de Dados y Puente TaleSpire 3D (`DiceDrawer.tsx`)
- **Modos de Tirada:** Selector explícito de **Normal**, **Ventaja** y **Desventaja** para dados de 20 caras (`d20`).
- **Respeto a la Física 3D de TaleSpire:** Cuando la tirada se despacha a TaleSpire (`send_to_talespire: true`), no se inventan números aleatorios en 2D que contradigan la física del juego. Se notifica mediante toast y se registra en el historial como `"🎲 En mesa 3D (TaleSpire)"`.
- **Atajos Globales:** Tecla `Espacio` para desplegar/ocultar la bandeja de dados (inhibida dentro de campos de texto) y tecla `Escape` para cerrar.

### 3.3. Hoja de Personaje y Modo Combate (`SheetView.tsx` & `CombatView.tsx`)
- **Retrato de Personaje:** Visualización de avatar con carga mediante selector nativo de archivos (`uploadCharacterPortrait`).
- **Sentidos e Idiomas:** Integrados en la cabecera del personaje a partir de los datos raciales de OKF.
- **Gestión de Recursos:** Casillas interactivas de uso y recarga para rasgos de clase y especie (`uses_current` / `uses_max`).
- **Combate Táctico:**
  - Control de Puntos de Golpe Temporales con absorción prioritaria de daño.
  - Selector de Dados de Golpe (`XdY`) a gastar en Descanso Corto.
  - Barra interactiva de Condiciones/Estados oficiales (Concentración, Envenenado, Cegado, Derribado, etc.).
- **Exportación / Importación:** Botones para Exportar a PDF oficial AcroForm, Exportar a JSON, Importar desde PDF e Importar desde JSON.

### 3.4. Grimorio de Conjuros (`SpellsView.tsx`)
- Cabecera con cálculo automático de **Aptitud Mágica**, **CD de Salvación de Conjuros** y botón interactivo para tirar el **Ataque Mágico** con modificadores reales.
- Formulario modal con salida limpia para registrar nuevos conjuros o dotes innatas.
- Síntesis automática para clases puramente marciales sin conjuros (Ley de Hick).

### 3.5. Compendio OKF y Diario de Campaña (`CompendiumView.tsx` & `JournalView.tsx`)
- Incorporación del componente [`MarkdownViewer.tsx`](file:///c:/Users/natha/Documents/Repos/Vizualizador%20Dnd/frontend/src/components/MarkdownViewer.tsx) para renderizar encabezados, negritas, cursivas, listas, citas y tablas Markdown nativas del compendio OKF y notas de crónica.

### 3.6. Visor de PDFs y Ajustes (`PdfViewerView.tsx` & `SettingsView.tsx`)
- Corrección del zoom en el visor PDF (permitiendo ampliaciones de hasta el 250% con scroll interactivo en vez de compresión fija `max-w-full`).
- Botón nativo para abrir y examinar cualquier manual o ficha PDF externa del sistema.
- Corrección de las alturas relativas de TaleSpire (`30.0%` Modo DM y `24.0%` Modo Jugador).
- Salida limpia con tecla `Escape` en todos los modales de la aplicación.

---

## 4. Verificación de Compilación y Pruebas

1. **Compilación Frontend (Vite + TypeScript):**
   ```bash
   npm run build
   # ✓ 1938 modules transformed.
   # dist/assets/index-CADMTtXn.js   373.17 kB
   # ✓ built in 723ms con 0 errores y 0 advertencias de tipos.
   ```
2. **Suite de Verificación End-to-End en Backend:**
   - Verificación de consulta y búsqueda en `OkfEngine`.
   - Generación de personajes con `build_character_from_wizard` (validando cálculo de CA, salvaciones, ranuras y CD mágica).
   - Previsualizaciones de `QuickBuildEngine` y `RandomCharacterGenerator` (4d6 drop lowest).
   - Validación de reglas en `PointBuyCalculator`.
   - Tiradas de dados con ventaja y desventaja en `core.rules.roll_dice_pool`.
   - Exportación de ficha PDF AcroForm editable y reimportación completa con `UniversalAcroFormHandler`.
   - **Resultado:** `ALL_CHECKS_PASSED_SUCCESSFULLY`.

---

## 5. Segunda Iteración de Mejoras y Depuración de Residuos

### 5.1. Depuración del Repositorio
- **Eliminación de `scratch/`:** Se purgaron 15 scripts antiguos de prueba y exploración (`extract_all_phb2024.py`, `populate_okf_subclasses.py`, scripts PowerShell y tests huérfanos con dependencias de Flet), dejando la raíz del proyecto limpia y profesional.

### 5.2. Correcciones en el Visor de PDFs (`PdfViewerView.tsx` & `core/pdf_engine.py`)
- **Erradicación de Marcos de Escaneo:** Detección y recorte quirúrgico de los marcos de imprenta (rojos en Xanathar `RGB(236, 27, 36)` y negros en Tasha `RGB(0, 0, 0)`), con ajuste subpíxel de dimensiones y enlaces internos.
- **Botón Selector:** Control `[Sin Marcos / Con Marcos]` en la barra de herramientas del visor.
- **Hipervínculos Limpios:** Reemplazo de los recuadros dorados fijos por overlays sutiles que solo se iluminan al pasar el cursor (`hover:bg-gold/20`).

### 5.3. Veredicto de Tiradas de Salvación y Muerte (`DiceDrawer.tsx` & `bridge.py`)
- **Cálculo de CD Objetivo:** Evaluación automática de éxito o fracaso frente a dificultad fijada (con presets `[CD10] [CD12] [CD15] [CD18]`).
- **Salvaciones de Muerte (CD 10):** Detección de Crítico (+2 éxitos / reanima), Éxito (+1), Fracaso (+1) y Pifia (+2 fallos) con botón de un clic `[✓ Asentar en Salvaciones de Muerte]` para sincronizar con la ficha activa.

### 5.4. Panel de Hechizos en Combate (`CombatView.tsx`)
- **Gestión Táctica de Ranuras:** Visualización y consumo/restauración de ranuras de conjuro (Niveles 1 a 9) directamente en la interfaz de combate.
- **Filtros por Nivel y Economía de Acción:** Filtros rápidos por tiempo de lanzamiento (`1 Acción`, `Acción Adicional`, `Reacción`).
- **Lanzamiento con un Clic:** Despacho de tiradas de ataque mágico o daño hacia el `DiceDrawer` con deducción automática de ranura.

### 5.5. Hoja de Ruta para Próximas Iteraciones
1. **Symbiote WebSocket Bridge:** Implementar microservidor local `ws://127.0.0.1:8765` para recibir lecturas 3D en vivo de `TS.dice.onRollResults` desde TaleSpire (`docs/ARQUITECTURA_TALESPIRE_SYMBIOTE_Y_HOSTING_LOCAL.md`).
2. **Hosting Multijugador sin Puertos:** Microservicio local en Python con Código QR para conexión de hojas de personaje en la misma red local WiFi/LAN.
3. **Consumo de APIs de D&D 5e:** Integración diferida de catálogo de conjuros externos (AideDD / dnd5eapi) a la base de datos local SQLite.
