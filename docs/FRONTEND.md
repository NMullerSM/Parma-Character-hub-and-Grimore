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
│   ├── ErrorBoundary.tsx      # Resguardo global contra caídas de renderizado en React
│   ├── FeatureDetailModal.tsx # Inspección detallada de rasgos de clase y dotes
│   ├── MarkdownViewer.tsx     # Renderizado enriquecido de texto de reglas
│   ├── SpellBookManagerModal  # Gestor de conjuros preparados vs conocidos
│   ├── SpellDetailModal.tsx   # Tarjeta de conjuro con comandos de tirada para TaleSpire
│   ├── SpotlightTour.tsx      # Sistema de onboarding guiado táctico con foco visual (Ley de Hick)
│   ├── UpdateModal.tsx        # Modal de actualización in-app con telemetría en tiempo real
│   └── UpdateNotificationPill # Píldora no intrusiva de actualización en la cabecera
├── context/
│   └── CharacterContext.tsx   # Estado global reactivo y bus de eventos
├── i18n/                      # Motor de internacionalización y traducción D&D
│   ├── dndTranslations.ts     # Diccionario canónico de términos D&D (ES / EN)
│   └── en.ts / es.ts          # Diccionarios de interfaz de usuario
│   └── index.ts               # Hook useTranslation() con saneamiento de claves dinámicas
├── utils/
│   └── storage.ts             # Abstracción safeStorage con fallback en memoria resiliente a WebKitGTK
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

### 4. Soporte Estricto para `verbatimModuleSyntax` en `ErrorBoundary.tsx` (Error TS1484)
* **Problema:** Al activar el compilador de TypeScript con `"verbatimModuleSyntax": true`, importar tipos junto a valores en una misma instrucción (`import React, { Component, ErrorInfo, ReactNode } from "react"`) provocaba el error TS1484: *"'ErrorInfo' is a type and must be imported using a type-only import"*.
* **Solución:** Separación explícita de importaciones de tipo:
  ```typescript
  import React, { Component } from "react";
  import type { ErrorInfo, ReactNode } from "react";
  ```

### 5. Sincronización de Contrato de Propiedades en `SettingsView.tsx` (Error TS2322)
* **Problema:** En `App.tsx`, el modal de ajustes recibía el prop `onResetSectionTours={() => ...}`, pero la interfaz `SettingsViewProps` en `SettingsView.tsx` no declaraba dicho callback, causando rechazo de compilación TS2322 en los pipelines de GitHub Actions.
* **Solución:** Declaración explícita del manejador opcional en `SettingsView.tsx`:
  ```typescript
  interface SettingsViewProps {
    onClose: () => void;
    onReplayTour?: () => void;
    onResetSectionTours?: () => void;
  }
  ```

### 6. Resiliencia contra `Can't find variable: localStorage` en WebKitGTK (`safeStorage`)
* **Problema:** En entornos WebKitGTK (Linux) bajo PyWebView, al servir la aplicación mediante un servidor local en localhost, el objeto global `window.localStorage` puede estar bloqueado o no instanciado en el ciclo temprano de arranque, provocando un `ReferenceError` letal que dejaba la pantalla en negro al evaluar `localStorage.getItem(...)`.
* **Solución Defensiva en 4 Capas:**
  1. **Polyfill Síncrono Pre-Bootstrap:** Inyección en `frontend/index.html` de un script inline previo al bundle de Vite que inicializa un `MemoryStorage` si `window.localStorage` no está accesible o lanza excepción.
  2. **Módulo Centralizado `frontend/src/utils/storage.ts`:** Expone la API `safeStorage` con implementaciones seguras envueltas en `try / catch` (`getItem`, `setItem`, `removeItem`, `clear`) y persistencia dual en memoria (`fallbackMap`).
  3. **Reemplazo Universal:** Erradicación de todas las llamadas directas a `localStorage` en `App.tsx`, `CharacterContext.tsx`, `UpdateModal.tsx` y `ErrorBoundary.tsx`.
  4. **Activación Nativa en GTK:** Introspección nativa en `desktop_app.py` invocando `set_enable_html5_local_storage(True)`.

### 7. Layout Anti-Colisión y Ley de Hick en `SpotlightTour.tsx`
* **Problema:** Los coach marks del onboarding sufrían colisiones visuales:
  * El botón *"Saltar todo"* flotaba en la esquina superior derecha tapando los botones de dados, TaleSpire y ajustes.
  * Si el elemento a resaltar estaba pegado a la cabecera superior (`y < 140`), la tarjeta de explicación se posicionaba hacia arriba, saliendo fuera del viewport.
  * Nombres largos de claves o traducciones desbordaban la tarjeta y empujaban el botón de avanzar fuera de la vista.
  * Claves inexistentes como `onboarding.global.step_batch` se imprimían crudas en pantalla.
* **Solución:**
  * **Saneamiento i18n:** `translate(path, defaultText)` devuelve `""` en lugar de la clave cruda cuando no existe coincidencia, permitiendo que `t("key") || "Texto"` evalúe correctamente sus fallbacks limpios.
  * **Despeje de Cabecera:** Botón *"Saltar todo"* reubicado a la esquina inferior derecha (`fixed bottom-4 right-4 z-40`).
  * **Auto-Posicionamiento Inteligente:** Detección de elementos con `y < 140` forzando `placement: "bottom"`.
  * **Contención Flexible:** Contenedor de botones con `flex-wrap gap-2 items-center justify-between` y `whitespace-nowrap flex-shrink-0 ml-auto` para garantizar que *Anterior*, *Siguiente* y *Saltar sección* permanezcan legibles y contenidos sin desborde.
  * **Resiliencia Gráfica:** Eliminación de `backdrop-blur-xs` en el elemento SVG `<rect>` para prevenir cuelgues del compositor EGL en WebKitGTK.

### 8. Flujo Reactivo de Actualización In-App (`UpdateModal.tsx` & `UpdateNotificationPill.tsx`)
* **Problema:** Los usuarios eran redirigidos a la web de GitHub para descargar instaladores manualmente, lo cual interrumpía la partida y aumentaba el riesgo de pérdidas de datos accidentales.
* **Solución:**
  * Flujo completo integrado en la interfaz de usuario:
    * Modal `UpdateModal.tsx` con detalles de la versión y changelog formateado.
    * Botón de descarga en segundo plano que permite cerrar el modal y seguir jugando mientras los trozos se descargan vía RPC.
    * Sondeo adaptativo cada 450ms únicamente mientras el estado sea `"downloading"`.
    * Píldora no intrusiva `UpdateNotificationPill.tsx` en el header mostrando el porcentaje descargado.
    * Al finalizar, la píldora se ilumina en color verde esmeralda y el modal ofrece el botón animado *"Reiniciar para actualizar"*, ejecutando la instalación silenciosa sin intervención manual.
