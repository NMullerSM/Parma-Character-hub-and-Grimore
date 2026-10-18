# Decisiones de Arquitectura Backend: Sistema de Datos OKF, Crawler y Puente TaleSpire

**Documento:** `docs/backend/architecture_decisions.md`  
**Estado:** `Aprobado & En Producción`  
**Stack:** Python 3.12+, SQLite 3 (WAL Mode), PyMuPDF 1.25+, Open Knowledge Format (OKF), TaleSpire IPC (LCM Named Pipe & WebSocket)

---

## 1. Arquitectura de Datos Atómica OKF (~1KB por Tarjeta)

### 1.1 El Problema: Bloat de Tokens y Dificultad para Modelos de IA
- Los manuales tradicionales en PDF (como el PHB de 120MB) o los ficheros monolíticos de 50.000 líneas de JSON generan enormes problemas cuando se alimentan a modelos de lenguaje o sistemas de consulta local:
  - Ingestión costosa en tokens (latencia alta y costo prohibitivo).
  - Alucinaciones y pérdida de contexto en árboles de datos profundos.
  - Incapacidad para que un jugador o una IA busque en menos de 5 milisegundos un rasgo específico.

### 1.2 Decisiones Adoptadas
1. **Entidades Atómicas de ~1KB (Open Knowledge Format - OKF)**:
   - Cada conjuro, dote, rasgo de clase, subclase o especie se almacena como un fichero Markdown independiente con **YAML Frontmatter**.
   - Tamaño promedio: 800 bytes a 1.5 KB.
   - Jerarquía clara en directorios temáticos:
     ```
     okf_dnd5e/
     ├── conjuros/
     │   ├── nivel_0_trucos/     # ~1KB c/u
     │   ├── nivel_1/            # ~1KB c/u
     │   └── ...
     ├── clases/
     │   ├── subclases/          # ~1KB c/u
     ├── dotes/                  # ~1KB c/u
     ├── especies_y_linajes/     # ~1KB c/u
     ├── trasfondos/             # ~1KB c/u
     ├── equipo_y_armamento/     # ~1KB c/u
     └── index_metadata.json     # Catálogo maestro de entidades para búsqueda en memoria (<2ms)
     ```
2. **Diseñado para Ingestión por IA (AI-Ready Ingestion)**:
   - El YAML Frontmatter contiene exactamente los metadatos necesarios (id, nombre, nivel, escuela, clases, tiempo, componentes, fuente, tags).
   - El cuerpo de Markdown contiene el texto de la regla limpio de ruido visual.
   - Cualquier modelo de IA (Gemini, Claude, LLM local) puede consumir una o diez entidades específicas sin desbordar la ventana de contexto.

---

## 2. Pipeline de Ingestión y Crawler de Datos SRD (5e-srd-api & AideDD)

### 2.1 Fuentes de Datos
1. **`5e-bits/5e-srd-api` (`packages/5e-database`)**:
   - Monorepo oficial con volcados completos y limpios de las reglas SRD en formato JSON.
   - Contiene tanto las reglas **2014 (Legacy)** como las reglas **2024 (Revised 5.5e)** en `packages/5e-database/src/2024/en` y `src/2014/en`.
   - Incluye tablas maestras: `5e-SRD-Spells.json`, `5e-SRD-Feats.json`, `5e-SRD-Features.json`, `5e-SRD-Classes.json`, `5e-SRD-Species.json`, `5e-SRD-Equipment.json`.
2. **AideDD (`aidedd.org`)**:
   - Referencia bilingüe para mapeo de nombres oficiales en castellano, descripción de componentes y filtros por escuela.

### 2.2 Estrategia de Ingestión Offline-First
- Se provee el módulo `core/srd_importer.py`:
  - Puede ejecutarse localmente con paquetes descargados o consultar las fuentes de forma asíncrona.
  - Normaliza los datos a la taxonomía OKF (traducción de claves a español, cálculo de tags).
  - Escribe atómicamente cada fichero `.md` en la subcarpeta correspondiente sin duplicar información.
  - Reconstruye automáticamente el índice maestro `index_metadata.json`.

---

## 3. Motor de Reglas y Sincronización de Personajes (Rules Engine)

### 3.1 Cálculo Dinámico de Rasgos y Sinergias de Clase
- **Inspiración Bárdica**:
  - Fórmula de usos: $\max(1, \text{Modificador de CAR})$.
  - Escala del dado: Nivel 1–4 ($1d6$), Nivel 5–9 ($1d8$), Nivel 10–14 ($1d10$), Nivel 15–20 ($1d12$).
  - Regla de recarga: Descanso Largo por defecto; Descanso Corto a partir de Nivel 5 (*Fuente de Inspiración*).
- **Hojas Psíquicas (Colegio de Susurros)**:
  - Daño psíquico vinculado a la Inspiración Bárdica ($2d6$ a nivel 3, $3d6$ a nivel 5, $5d6$ a nivel 10).
- **Magia Drow (Linaje Élfico)**:
  - Nivel 1: *Luces Danzantes* a voluntad (truco).
  - Nivel 3: *Fuego Feérico* 1 vez por descanso largo.
  - Nivel 5: *Oscuridad* 1 vez por descanso largo.
- **Dote Afortunado**:
  - Puntos de suerte iguales al Bonificador por Competencia.

### 3.2 Sincronización Bidireccional SQLite y PyMuPDF
- Cuando se importa o lee un personaje (ej. `Artanis LVL 4.pdf` o base de datos), el motor de sincronización:
  1. Extrae los valores de los campos AcroForm y XREFs.
  2. Mapea las referencias de conjuros (ej. páginas del PHB o nombres) contra el compendio OKF.
  3. Puebla el listado de conjuros con sus estadísticas completas (tiempo, alcance, componentes, CD de salvación).
  4. Garantiza que las ranuras totales y actuales correspondan a la tabla canónica de lanzadores de D&D 5e.

---

## 4. Integración TaleSpire: Dual-Pipe y Symbiote WebSocket

### 4.1 Arquitectura Tripartita de Comunicación
```
┌─────────────────────────────────┐
│       D&D Sanctum Frontend      │
│      (React + Vite + UI)        │
└───────────────┬─────────────────┘
                │ IPC (PyWebView)
                ▼
┌─────────────────────────────────┐           WebSocket Local            ┌────────────────────────────────┐
│      D&D Sanctum Backend        │ ◄──────────────────────────────────► │       TaleSpire Symbiote       │
│      (Python + SQLite)          │       ws://127.0.0.1:8765            │    (CEF WebView en TaleSpire)  │
└───────────────┬─────────────────┘                                      └───────────────┬────────────────┘
                │                                                                        │
                │ Named Pipe: \\.\pipe\com.bouncyrock.talespire.lcm_pipe                │ window.TS.dice
                ▼                                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         TaleSpire 3D Engine                                             │
│                                (Dados físicos rodando en la mesa)                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Named Pipe Nativo (`lcm_pipe`)**:
   - Envío de comandos de tirada directos al proceso de TaleSpire sin requerir configuración adicional por el jugador.
2. **Symbiote WebSocket (`ws://127.0.0.1:8765`)**:
   - Sincronización bidireccional con el Symbiote oficial instalado en `%LocalAppData%Low\BouncyRock Entertainment\TaleSpire\Symbiotes\`.
   - Recepción en tiempo real de los resultados físicos de los dados vía `TS.dice.onRollResults` y reflejo inmediato en el `SessionRollLedger` de la aplicación.
3. **Formato TaleSpire Chat Roll**:
   - Soporte total para fórmulas como `!1d20+5`, `!Espada:1d8+3`, `!2d20-4+3d12`, `!1d20+2/1d20+2`.
