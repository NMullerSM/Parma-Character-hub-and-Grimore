# Atribución Legal y Licenciamiento de Datos del Compendio

Este documento certifica el origen, la procedencia legal y el licenciamiento de todos los datos utilizados en el compendio de **Parma Character Hub & Grimoire** (monstruos, conjuros, equipo y armamento).

---

## 1. Declaración de Gobernanza y Fuentes Autorizadas

En estricto cumplimiento con la gobernanza OKF y las políticas de propiedad intelectual de este proyecto:

1. **SRD 5.2 (2024) y SRD 5.1 (2014) de Wizards of the Coast**:
   - Todo el contenido de monstruos, conjuros, armas, armaduras y equipo se deriva exclusivamente del *Systems Reference Document 5.2* (D&D 2024) y del *Systems Reference Document 5.1* (D&D 2014) publicados por Wizards of the Coast LLC.
   - Dicho contenido está liberado y disponible bajo la **Licencia Creative Commons Atribución 4.0 Internacional (CC-BY-4.0)**.
   - Texto de la licencia: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)

2. **Foundry Virtual Tabletop (`foundryvtt/dnd5e`)**:
   - Los paquetes de datos fuente procesados provienen de los paquetes abiertos oficiales del sistema `dnd5e` de Foundry VTT (`packs/_source/`):
     - `monsters` / `actors24`
     - `spells` / `spells24`
     - `items` / `equipment24`
   - El código de procesamiento y herramientas de Foundry VTT está bajo la **Licencia MIT**.
   - Los datos contenidos en dichos paquetes son redistribuidos bajo los términos de la licencia **CC-BY-4.0** de Wizards of the Coast.
   - Repositorio oficial: [https://github.com/foundryvtt/dnd5e](https://github.com/foundryvtt/dnd5e)

3. **Exclusión Estricta de Fuentes Propietarias / No Licenciadas**:
   - Queda explícita y permanentemente prohibida la ingestión de datos no autorizados, datos de extracción web propietaria o repositorios no libres tales como `5etools-src` o libros con derechos reservados fuera de las SRD 5.1 y 5.2.
   - Todos los datos presentes en `data/dnd_database.db` provienen exclusivamente de las fuentes CC-BY-4.0 verificadas.

---

## 2. Aviso de Atribución Canónico (SRD CC-BY-4.0)

> This work includes material taken from the System Reference Document 5.1 (“SRD 5.1”) and System Reference Document 5.2 (“SRD 5.2”) by Wizards of the Coast LLC and available at [https://dnd.wizards.com/resources/systems-reference-document](https://dnd.wizards.com/resources/systems-reference-document). The SRD 5.1 and SRD 5.2 are licensed under the Creative Commons Attribution 4.0 International License available at [https://creativecommons.org/licenses/by/4.0/legalcode](https://creativecommons.org/licenses/by/4.0/legalcode).

---

## 3. Mecanismo de Ingestión y Reproducibilidad

La base de datos del compendio se genera de manera reproducible y automatizada mediante:

```bash
python scripts/ingest_compendium_55e.py --foundry-packs /ruta/a/foundryvtt/dnd5e/packs/_source
```

El importador implementado en `core/compendium_importer.py`:
- Parsea los archivos YAML fuente de Foundry VTT de forma tipada y defensiva.
- Genera automáticamente los registros bilingües en español (`language="es"`) e inglés (`language="en"`).
- Normaliza los identificadores, alineamientos, escuelas de magia, tipos de daño y propiedades de dominio de armas (*Weapon Mastery* 2024).
- Almacena los registros indexados en las tablas SQLite `compendium_monsters`, `compendium_spells` y `compendium_items`.
