# 🎨 Parma — Arquitectura del Frontend

Este documento detalla la arquitectura de frontend de **Parma (Character Hub & Grimoire)**, su diseño de componentes, gestión de estado reactivo, enlaces RPC y las soluciones técnicas implementadas para garantizar estabilidad y rendimiento.

---

## 1. Stack Tecnológico

* **Framework UI:** React 18.x
* **Herramienta de Construcción:** Vite 8.x con `@vitejs/plugin-react`
* **Estilos y Diseño:** Tailwind CSS v4 con plugin nativo `@tailwindcss/vite` (motor Oxide en Rust)
* **Tipado Estricto:** TypeScript 6.x
* **Iconografía:** Lucide React (vectorial de alto rendimiento)
* **Visualizador Markdown:** MarkdownViewer optimizado con soporte de badges y tablas

---

## 2. Arquitectura de Vistas y Componentes

El frontend está estructurado en vistas modulares desacopladas dentro de `frontend/src/views/`:

```
frontend/src/
├── api/
│   ├── client.ts              # Conector RPC a window.pywebview.api + mocks para desarrollo
│   └── types.ts               # Contratos e interfaces TypeScript
├── components/
│   ├── AnimatedHealthBar.tsx  # Barra de vida animada con gradientes reactivos
│   ├── DiceDrawer.tsx         # Bandeja lateral interactiva para lanzamiento de dados
│   ├── DicePhysicsModal.tsx   # Animación visual de impacto de dados
│   ├── FeatureDetailModal.tsx # Inspección detallada de rasgos de clase y dotes
│   ├── MarkdownViewer.tsx     # Renderizado enriquecido de texto de reglas
│   ├── SpellBookManagerModal  # Gestor de conjuros preparados vs conocidos
│   └── SpellDetailModal.tsx   # Tarjeta de conjuro con comandos de tirada para TaleSpire
├── context/
│   └── CharacterContext.tsx   # Estado global reactivo y bus de eventos
├── i18n/                      # Motor de internacionalización y traducción D&D
│   ├── dndTranslations.ts     # Diccionario canónico de términos D&D (ES / EN)
│   ├── en.ts / es.ts          # Diccionarios de interfaz de usuario
│   └── index.ts               # Hook useTranslation()
└── views/
    ├── CharacterWizard.tsx    # Asistente de creación de personaje 100% legal
    ├── CombatView.tsx         # Consola de combate activa, armas, salud y magia
    ├── CompendiumView.tsx     # Explorador del compendio OKF de 570+ tarjetas
    ├── DmConsoleView.tsx      # Panel de control de sesión en vivo para el DM
    ├── JournalView.tsx        # Diario de campaña, crónicas y registro de botín
    ├── NetworkView.tsx        # Grafo visual interactivo de relaciones y PNJs
    ├── PdfReaderView.tsx      # Visor integrado de manuales PDF y fichas
    ├── SettingsView.tsx       # Ajustes de temas visuales, idioma y TaleSpire
    ├── SheetView.tsx          # Ficha clásica de personaje con habilidades y salvaciones
    └── SpellsView.tsx         # Grimorio mágico completo y control de ranuras
```

---

## 3. Estado Global: `CharacterContext`

Toda la aplicación se apoya en un contexto centralizado (`CharacterContext.tsx`):
* **Ficha Activa:** `activeCharacter` (`CharacterSheetData`), sincronizado en tiempo real con SQLite.
* **TaleSpire Status:** `talespireStatus` (instalación, proceso activo, conexión WebSocket y Symbiote).
* **Feedback Visual de Combate:**
  * `vignetteFlash`: Efecto cinemático en los bordes de la pantalla al recibir daño (resplandor carmesí) o curación (esmeralda).
* **Bandeja de Dados y Animaciones:**
  * `openDiceDrawer(req)`: Modal interactivo con ventajas/desventajas, modificadores y botón directo de envío a TaleSpire.
  * `rollHistory`: Registro histórico de tiradas con reconocimiento de 20 natural (Crítico) y 1 natural (Pifia).
* **Internacionalización Dinámica:** Cambio fluido entre Español e Inglés sin recargar la aplicación.

---

## 4. Capa de Comunicación RPC (`client.ts`)

La interfaz de usuario interactúa con el backend de Python a través de `frontend/src/api/client.ts`.

### Modo Híbrido Nativo / Web Mock
* **Modo Nativo (Escritorio):** Si `window.pywebview` está presente, delega las llamadas a las funciones de Python de forma asíncrona:
  ```typescript
  async getClassSpells(className: string, maxLevel: number = 1, lang: string = "es"): Promise<SpellItemData[]> {
    if (this.isNative()) return await window.pywebview!.api.get_class_spells(className, maxLevel, lang);
    return mockActiveCharacter.spells.filter((s) => s.level <= maxLevel);
  }
  ```
* **Modo Web Mock (Desarrollo Rápido):** Al ejecutar `npm run dev` en un navegador web convencional, el cliente simula todas las respuestas mediante mocks en memoria, permitiendo diseñar y probar componentes sin compilar Python.

---

## 5. Problemas Técnicos Resueltos y Lecciones Aprendidas

### 1. Sincronización Estricta del Contrato `SpellStatsData`
* **Problema:** En el frontend, `SpellStatsData` tenía sus atributos marcados como opcionales (`ability?: string`, `dc?: number`, `attack_bonus?: number`). En TypeScript 6 con modo estricto, esto provocaba errores `TS2345` ("Argument of type 'string | undefined' is not assignable to parameter of type 'string'") al invocar `translateAbility(spellStats.ability)` y `TS18048` al evaluar `spell_stats.attack_bonus >= 0`.
* **Solución:**
  En `frontend/src/api/types.ts`, se formalizaron como obligatorios los tres campos fundamentales que Python siempre envía, preservando los alias opcionales por compatibilidad con futuras versiones del SRD:
  ```typescript
  export interface SpellStatsData {
    ability: string;
    dc: number;
    attack_bonus: number;
    save_dc?: number;
    is_caster?: boolean;
    casting_ability?: string;
    spell_save_dc?: number;
    spell_attack_bonus?: number;
    ability_mod?: number;
  }
  ```

### 2. Prevención de Componentes Descontrolados en `JournalView`
* **Problema:** Los campos opcionales de una crónica (`id?: number`, `loot?: string`, `xp_gained?: number`) pasaban `undefined` a estados de React que esperaban `string` o `number`, provocando advertencias de "uncontrolled component" y rechazos de tipado.
* **Solución:** Implementación de operadores de coalescencia nula seguros:
  ```typescript
  setSelectedId(sess.id ?? null);
  setLoot(sess.loot ?? "");
  setXpGained(sess.xp_gained ?? 0);
  ```

### 3. Resolución de Módulos en `tsconfig.node.json` (Error TS5110)
* **Problema:** El archivo de compilación de herramientas `tsconfig.node.json` contenía `"module": "nodenext"` sin resolución emparejada, rompiendo la compilación con Vite 8.
* **Solución:** Se alineó con el estándar moderno de Vite:
  ```json
  "module": "ESNext",
  "moduleResolution": "Bundler"
  ```
