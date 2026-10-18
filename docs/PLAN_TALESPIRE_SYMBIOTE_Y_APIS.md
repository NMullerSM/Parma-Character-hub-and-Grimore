# Plan de Arquitectura: Integración TaleSpire Symbiotes y Crawler de APIs Online D&D 5e

Este documento detalla la investigación técnica, especificaciones oficiales y hoja de ruta para la sincronización con **TaleSpire Symbiotes** y el consumo **offline-first** de APIs de D&D 5e (**dnd5eapi.co**, **AideDD**, **Nivel 20** y **5e-database**).

---

## 1. Integración con TaleSpire Symbiotes (Bouncyrock)

### 1.1 ¿Qué es un Symbiote en TaleSpire?
A diferencia de los parches tradicionales de ensamblado (BepInEx / MonoMod), los **Symbiotes** son extensiones oficiales ejecutadas en vistas web embebidas (**Chromium Embedded Framework**) dentro o junto al cliente de TaleSpire.
- **Ruta de instalación en Windows**:
  ```
  %APPDATA%\..\LocalLow\BouncyRock Entertainment\TaleSpire\Symbiotes\<NombreDelSymbiote>\
  ```
- **Capacidades**:
  - Inyección del objeto global `window.TS` en el DOM de la vista web.
  - Subscripción a eventos del tablero de juego (`onRollResults`, selección de criaturas, cambio de tableros).
  - Envío de tiradas de dados físicas al motor 3D con indicador de autenticidad en la UI del juego.

### 1.2 La API de Dados de TaleSpire (`TS.dice`)

| Método / Evento | Descripción | Ejemplo de Uso |
|---|---|---|
| `TS.dice.makeRollDescriptors(formula)` | Convierte un string de fórmula de dados en un array de descriptores que la bandeja de TaleSpire comprende. | `const desc = await TS.dice.makeRollDescriptors("1d20+5");` |
| `TS.dice.putDiceInTray(descriptors, forceThrow)` | Envía los dados especificados a la bandeja de dados física en el mundo 3D. Marca el origen con el indicador oficial de Symbiote. | `await TS.dice.putDiceInTray(desc, true);` |
| `TS.dice.onRollResults(callback)` | Dispara un callback cuando una tirada de dados concluye en la mesa de TaleSpire (tanto del DM como de los jugadores). | `TS.dice.onRollResults((res) => { ... });` |

### 1.3 Arquitectura Bidireccional: D&D Sanctum ↔ Symbiote

```
┌─────────────────────────────────┐           WebSocket Local            ┌────────────────────────────────┐
│           D&D Sanctum           │ ◄──────────────────────────────────► │       TaleSpire Symbiote       │
│  (PyWebView + Python Desktop)   │       ws://127.0.0.1:8765            │    (CEF WebView en TaleSpire)  │
└─────────────────────────────────┘                                      └────────────────────────────────┘
                 │                                                                        │
        Lanzar ataque/conjuro                                                  window.TS.dice.putDiceInTray
                 ▼                                                                        ▼
        Envía payload WebSocket ───────────────────────────────────────►  Dados ruedan en mesa 3D TaleSpire
                                                                                          │
        Recibe resultado y anima ◄──────────────────────────────────────  window.TS.dice.onRollResults
```

1. **D&D Sanctum actúa como Host Local**:
   - Inicia un microservidor WebSocket local asíncrono en `127.0.0.1:8765` en un hilo secundario de Python (`core/talespire_bridge.py`).
2. **El Symbiote (`data/talespire_symbiote`)**:
   - Se copia a la carpeta de Symbiotes de TaleSpire.
   - Conecta a `ws://127.0.0.1:8765`.
   - Cuando el usuario pulsa un arma o conjuro en D&D Sanctum, el comando viaja por WebSocket y el Symbiote llama a `TS.dice.putDiceInTray`.
   - Cuando los dados terminan de rebotar en TaleSpire, `TS.dice.onRollResults` envía los números reales hacia D&D Sanctum, activando la animación poliédrica local y guardando la tirada en el `SessionRollLedger`.

---

## 2. Consumo de Recursos y APIs de D&D 5e (Offline-First)

### 2.1 Fuentes de Datos Identificadas

1. **`dnd5eapi.co` (REST / GraphQL)**:
   - Contiene la totalidad del SRD 5.1 en JSON estructurado (clases, conjuros, equipo, condiciones, dotes).
   - Acceso gratuito, público y sin autenticación obligatoria.
   - Endpoint clave: `https://www.dnd5eapi.co/api/spells/`
2. **AideDD (`aidedd.org/dnd-filters/sorts.php`)**:
   - Referencia exhaustiva con filtros por clase, escuela, componentes verbales/somáticos y descripciones de conjuros.
   - Especialmente útil para validaciones cruzadas de textos y tarjetas de conjuro.
3. **Nivel 20 (`nivel20.com`)**:
   - La plataforma digital en español de referencia para D&D 5e.
   - Nombres oficiales en castellano, alineados con las traducciones de Edge / Wizards of the Coast.
4. **5e-database (GitHub - `5e-bits/5e-database`)**:
   - Repositorio estático open source con volcados JSON completos de monstruos, conjuros y objetos mágicos del SRD.

### 2.2 Estrategia de Arquitectura: "Offline-First Local Cache"

> [!IMPORTANT]
> **Principio de Resiliencia**: El programa nunca depende de la conexión a internet para funcionar. Toda la lógica del visualizador, forja y combate corre 100% offline contra la base de datos local SQLite y los archivos OKF.

```
                  ┌──────────────────────────────────────────────┐
                  │          Comprobación de Conectividad        │
                  └──────────────────────┬───────────────────────┘
                                         │
                    ¿Hay internet? ──────┴────── ¿Offline?
                          │                         │
                          ▼                         ▼
            ┌───────────────────────────┐   ┌───────────────────────────┐
            │   Sincronizador Asíncrono │   │    Carga Inmediata Local  │
            │   - Consulta dnd5eapi.co  │   │    - SQLite dnd_sanctum.db│
            │   - Traduce y complementa │   │    - OKF local            │
            │   - Upsert en SQLite      │   │    - Cero latencia        │
            └───────────────────────────┘   └───────────────────────────┘
```

### 2.3 Modelo de Datos para Tarjetas de Conjuros y Rasgos en SQLite

Se enriquecerá la tabla `compendium_entries` en SQLite con los siguientes campos estandarizados:

```sql
CREATE TABLE IF NOT EXISTS compendium_spells (
    id TEXT PRIMARY KEY,
    name_es TEXT NOT NULL,
    name_en TEXT NOT NULL,
    level INTEGER NOT NULL,          -- 0 para trucos, 1-9 para conjuros
    school TEXT NOT NULL,            -- Evocación, Abjuración, Nigromancia, etc.
    cast_time TEXT NOT NULL,         -- 1 acción, 1 acción adicional, reacción
    range_area TEXT NOT NULL,        -- 18 m, Toque, Personal
    components TEXT NOT NULL,        -- V, S, M (descripción de componentes)
    duration TEXT NOT NULL,          -- Instantáneo, 1 minuto (Concentración)
    description TEXT NOT NULL,       -- Texto completo de la regla
    classes TEXT NOT NULL,           -- JSON array: ["Mago", "Hechicero", "Brujo"]
    source TEXT DEFAULT 'SRD 5.1',
    edition TEXT DEFAULT '5.5e',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Hoja de Ruta de Implementación

1. **Fase 1 (Completada)**:
   - Overhaul del Creador de Personajes con los 3 Modos (Paso a Paso, Rápido 60s, Aleatorio 4d6).
   - Componentes interactivos `<SpellCard>` y `<FeatureCard>`.
   - Modos conectados a `core/quick_build.py`, `core/random_generator.py` y `core/point_buy.py`.
2. **Fase 2 (Symbiote Starter)**:
   - Paquete de Symbiote funcional en `data/talespire_symbiote/` con `manifest.json` e `index.html`.
   - Conexión por WebSocket para recepción de `TS.dice.onRollResults` y emisión de `TS.dice.putDiceInTray`.
3. **Fase 3 (Crawler & Sincronización Online)**:
   - Módulo en Python (`core/compendium_crawler.py`) para descargar bajo demanda los conjuros de `dnd5eapi.co` y normalizarlos con terminología castellana.
   - Botón en Configuración: *"Sincronizar Compendio Online (dnd5eapi.co)"*.
