# Decisiones de Arquitectura Frontend: Visualizador & Editor D&D 5e

**Documento:** `docs/frontend/frontend_decisions.md`  
**Estado:** `Aprobado & En Producción`  
**Stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4, Lucide Icons (restringido), PyWebView IPC / Chromium Embedded Framework (CEF)

---

## 1. Ergonomía Visual y Cumplimiento Estricto de la Ley de Hick

### 1.1 El Problema Previo
En herramientas digitales tradicionales de D&D (como D&D Beyond o Roll20), las pantallas de combate y de consulta presentan decenas de números, botones e iconos diminutos simultáneamente. Esto provoca:
- **Sobrecarga Cognitiva (Hick's Law: $T = b \cdot \log_2(n + 1)$)**: El jugador o DM tarda valiosos segundos en decidir qué botón pulsar durante su turno.
- **Proliferación Innecesaria de Iconos**: Etiquetas con iconos redundantes (`❤️ Vida:`, `🛡️ CA:`, `⚡ Inic:`, `📜 Rasgo:`) que saturan la vista sin aportar valor informativo.
- **Falta de Divulgación Progresiva**: Mostrar todos los textos completos de 30 conjuros a la vez produce desbordamiento y fatiga visual.

### 1.2 Decisiones de Diseño Adoptadas
1. **Divulgación Progresiva (Progressive Disclosure)**:
   - Las tarjetas de combate y grimorio muestran únicamente el nombre, nivel, tiempo de acción, alcance y etiqueta de concentración.
   - Al pulsar cualquier tarjeta (arma, conjuro o rasgo especial), esta **emerge hacia adelante en un diálogo modal ("Pop-Forward Card")** con el texto completo, fórmulas de dados interactivas y botones de acción unificados.
2. **Restricción Estricta de Iconografía (Anti-Icon Proliferation)**:
   - Prohibido el uso de iconos decorativos en cada texto o título.
   - Se prioriza contraste tipográfico limpio: fuente Display clásica para títulos, pesos `semibold`/`bold` para valores clave, y paleta semántica (`text-gold`, `text-crimson`, `text-muted`).
   - Iconos reservados exclusivamente para acciones universales: Cerrar (`✕`), Buscar (`Search`), Añadir (`+`), y Tirar Dados (`Casino/Dice`).
3. **Mecanismos de Escape Claros (Clear Escape Hatches)**:
   - Todo diálogo modal o vista flotante cuenta obligatoriamente con triple salida:
     - Botón visible `[✕]` en la esquina superior derecha.
     - Botón explícito `Cerrar` o `Cancelar` en la barra inferior.
     - Cierre automático al presionar la tecla `Escape` o al hacer clic sobre el fondo difuminado (backdrop).

---

## 2. Gestión Unificada de Grimorio y Modo Combate Táctico

### 2.1 El Problema: "Grimorio Vacío sin Salida Directa"
Anteriormente, si un personaje no tenía conjuros precargados en su ficha, la vista de Combate mostraba únicamente:
> *"No hay conjuros registrados en el grimorio de este personaje."*

El jugador no tenía forma inmediata de saber cómo registrarlos ni de consultar la base de datos de conjuros sin abandonar la partida.

### 2.2 Decisiones Adoptadas
1. **Gestor de Grimorio Integrado (`SpellBookManagerModal`)**:
   - Accesible tanto desde la vista de Grimorio (`SpellsView`) como directamente desde la vista de Combate (`CombatView`).
   - Si el grimorio está vacío, la pantalla muestra un botón de llamada a la acción primario:
     `[+ Añadir Conjuros desde el Compendio Oficial (378 disponibles)]`
   - Permite búsqueda en tiempo real, filtros por clase (Bardo, Mago, Clérigo, etc.), nivel de conjuro (0 a 9) y escuela de magia.
   - Inserción y eliminación atómica con un solo clic, sincronizada con la base de datos local SQLite y el estado de React.
2. **Tarjeta Interactiva de Conjuro ("Pop-Forward")**:
   - Al pulsar un conjuro en combate, se abre el modal con:
     - Datos canónicos completos: componentes (V, S, M), duración, alcance, concentración y ritual.
     - Selector dinámico de ranura para **lanzamiento en niveles superiores (Upcasting)**.
     - Botones directos de tirada: `[Tirar Ataque Mágico]` y `[Tirar Daño]` con cálculo automático de dados.
     - Gasto automático de la ranura de conjuro correspondiente al nivel elegido.

---

## 3. Tarjetas Interactivas de Rasgos y Recursos de Clase

### 3.1 El Problema: Habilidades Pasivas Desconectadas del Motor de Dados
Rasgos emblemáticos como **Inspiración Bárdica**, **Hojas Psíquicas**, **Magia Drow** o la dote **Afortunado** estaban limitados a textos estáticos sin interacción directa ni cálculo dinámico de usos según el nivel y características del personaje.

### 3.2 Decisiones Adoptadas
1. **Motor Reactivo de Usos de Clase y Linaje**:
   - **Inspiración Bárdica**: Usos máximos vinculados dinámicamente al modificador de Carisma ($\ge 1$). Tamaño del dado escalado según nivel del bardo (Nvl 1-4: d6; Nvl 5-9: d8; Nvl 10-14: d10; Nvl 15-20: d12). Recarga en descanso largo (o descanso corto/largo a partir de nivel 5 gracias a *Fuente de Inspiración*).
   - **Hojas Psíquicas (Psychic Blades - Colegio de Susurros)**: Gasta un uso de Inspiración Bárdica y añade daño psíquico ($2d6$ a nvl 3, $3d6$ a nvl 5, $5d6$ a nvl 10).
   - **Magia Drow**: Progresión por nivel (Nvl 1: *Luces Danzantes*; Nvl 3: *Fuego Feérico* 1/descanso largo; Nvl 5: *Oscuridad* 1/descanso largo).
   - **Dotes (ej. Afortunado)**: Usos vinculados al Bonificador por Competencia.
2. **Modal Interactivo de Rasgo (`FeatureDetailModal`)**:
   - Al hacer clic en cualquier tarjeta de rasgo o habilidad especial, la tarjeta se proyecta hacia adelante.
   - Muestra el texto oficial de la regla, el tipo de recarga (Descanso Corto / Largo / Especial), y botones para **Gastar Uso**, **Recuperar Uso** y **Tirar Dado Asociado** (ej. tirar el d6 de Inspiración o los 2d6 de Hojas Psíquicas directamente en mesa o TaleSpire).

---

## 4. Adaptabilidad para TaleSpire Symbiote y Entorno de Escritorio

### 4.1 Entorno Híbrido: PyWebView + Chromium Embedded Framework (CEF)
La aplicación frontend está diseñada para operar idénticamente bajo tres contextos:
1. **Aplicación de Escritorio Nativa**: Ejecutada mediante `pywebview` en Windows con aceleración Edge/WebView2.
2. **TaleSpire Symbiote Embebido**: Ejecutado directamente dentro del panel lateral de TaleSpire en CEF. Se comunica con el juego mediante `window.TS` y el protocolo WebSocket `ws://127.0.0.1:8765`.
3. **Navegador Web Standalone / Tableta / Móvil**: Con adaptadores mock automáticos para pruebas de desarrollo (`npm run dev`) sin necesidad de levantar el ejecutable de Python.

### 4.2 Soporte de Sintaxis TaleSpire Chat Roll
En las tiradas de dados, el frontend genera y expone la sintaxis canónica de TaleSpire (`!1d20+5`, `!Rapier:1d20+4`, `!2d20-4+3d12`), permitiendo al usuario tanto enviar los dados a rodar en el motor 3D de TaleSpire como copiar el comando con un clic para pegarlo en el chat del juego.
