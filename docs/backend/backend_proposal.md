# Propuesta de Servicios y Endpoints Backend

**Documento:** `docs/backend/backend_proposal.md`  
**Estado:** `Propuesta Técnica & Especificación de Servicios`  
**Módulos:** `core/srd_importer.py`, `core/okf_engine.py`, `core/rules.py`, `desktop_api/bridge.py`

---

## 1. Resumen de la Propuesta

Para resolver la carencia de conjuros en el grimorio, la desactualización de usos de rasgos y la necesidad de alimentar el árbol de tarjetas OKF atómicas de ~1KB, esta propuesta detalla la arquitectura de tres componentes del backend:

1. **`core/srd_importer.py` (Módulo Ingestor y Generador de Tarjetas OKF)**:
   - Descarga o lee volcados JSON de `5e-bits/5e-srd-api` (`packages/5e-database`) y AideDD.
   - Genera archivos Markdown atómicos (`~1KB`) organizados en carpetas taxonómicas.
   - Actualiza el índice `index_metadata.json` en tiempo real.
2. **Ampliación de `OkfEngine` y `DesktopBridge`**:
   - Nuevos métodos para búsqueda avanzada de conjuros por clase, nivel y escuela.
   - Operaciones CRUD atómicas para añadir o quitar conjuros de la ficha del personaje.
   - Sincronizador de rasgos para calcular automáticamente usos actuales/máximos, caras de dados y recargas de acuerdo al nivel y atributos.
3. **Poblado Canónico de Personajes Existentes (incluyendo Artanis)**:
   - Migración o actualización de la ficha de Artanis en SQLite para que cuente con su grimorio completo de Bardo nivel 4 con linaje Drow y Colegio de Susurros.

---

## 2. Especificación del Ingestor de Tarjetas OKF (`core/srd_importer.py`)

### 2.1 Taxonomía de Salida (Árbol de Directorios)
```
okf_dnd5e/
├── conjuros/
│   ├── nivel_0_trucos/   -> <id>.md (~1KB)
│   ├── nivel_1/          -> <id>.md (~1KB)
│   ├── nivel_2/          -> <id>.md (~1KB)
│   └── ...
├── dotes/                -> <id>.md (~1KB)
├── clases/
│   ├── subclases/        -> <id>.md (~1KB)
├── especies_y_linajes/   -> <id>.md (~1KB)
└── index_metadata.json   -> Índice en memoria para búsqueda <2ms
```

### 2.2 Formato Estándar de Tarjeta (~1KB)
```yaml
---
id: "fuego_feerico"
nombre: "Fuego Feérico"
nombre_ingles: "Faerie Fire"
nivel: 1
escuela: "Evocación"
clases:
  - "Artífice"
  - "Bardo"
  - "Druida"
tiempo_lanzamiento: "1 acción"
alcance: "18 m"
componentes: "V"
duracion: "Concentración, hasta 1 minuto"
concentracion: true
ritual: false
fuente: "PHB 2024"
tags:
  - "evocacion"
  - "nivel_1"
  - "bardo"
  - "concentracion"
---

# Fuego Feérico

Cada objeto en un cubo de 6 m dentro del alcance queda rodeado de una luz tenue azul, verde o violeta.
Cualquier criatura en el área debe superar una salvación de DES o quedará rodeada por la luz.
Cualquier tirada de ataque contra una criatura o un objeto afectado tiene ventaja si el atacante puede verlo.
```

---

## 3. Nuevos Endpoints en el Puente PyWebView (`desktop_api/bridge.py`)

| Método RPC | Parámetros | Retorno | Descripción |
|---|---|---|---|
| `get_available_spells` | `class_name: str, max_level: int, query: str, school: str` | `List[SpellItemData]` | Devuelve todos los conjuros oficiales filtrados para el gestor de grimorio. |
| `add_spell_to_character` | `char_id: int, spell: Dict[str, Any]` | `Dict[str, Any]` | Añade un conjuro a la ficha en SQLite y devuelve la ficha serializada actualizada. |
| `remove_spell_from_character` | `char_id: int, spell_name: str` | `Dict[str, Any]` | Quita un conjuro de la ficha y persiste el cambio inmediatamente. |
| `sync_character_features` | `char_id: int` | `Dict[str, Any]` | Recalcula todos los rasgos de clase, dotes y linaje (Inspiración, Hojas Psíquicas, Magia Drow) con sus usos exactos. |
| `sync_compendium_from_srd` | `edition: str = "2024"` | `Dict[str, Any]` | Dispara el proceso de ingestión y re-indexado de tarjetas OKF de 1KB. |

---

## 4. Pipeline de Sincronización Automática para Artanis

Para corregir la situación detectada por el usuario en su personaje de prueba (Artanis, Drow Bardo nivel 4, Colegio de Susurros), el backend ejecutará:
1. **Inyección de Conjuros de Bardo y Drow**:
   - Trucos: *Luces Danzantes* (Magia Drow), *Burla Dañina*, *Ilusión Menor*, *Mano de Mago*.
   - Nivel 1: *Fuego Feérico* (Magia Drow/Bardo), *Susurros Disonantes*, *Palabra de Curación*, *Ola Atronadora*, *Falsa Vida*.
   - Nivel 2: *Invisibilidad*, *Sugestión*, *Ceguera/Sordera*.
2. **Ajuste de Rasgos y Usos**:
   - *Inspiración Bárdica (d6)*: 5 usos (Carisma 20 = +5), recarga en Descanso Largo.
   - *Hojas Psíquicas*: 5 usos (comparte con Inspiración), inflige +2d6 daño psíquico.
   - *Palabras de Terror*: CD 15 (8 + 2 competencia + 5 Carisma).
   - *Magia Drow*: Fuego Feérico 1/Descanso Largo; Luces Danzantes a voluntad.
   - *Afortunado (Dote)*: 2 puntos de suerte (igual a bonificador de competencia).
