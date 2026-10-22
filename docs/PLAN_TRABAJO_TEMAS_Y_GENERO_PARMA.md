# Plan de Trabajo: Modo Claro/Oscuro por Tema y Detección de Género en Retratos IA

> **Aplicación:** Parma (Character Hub & Grimoire)  
> **Estado:** Documento de Planificación (Sin Ejecución)  
> **Fecha:** Octubre 2026  
> **Cumplimiento:** Principios de Ley de Hick y Ergonomía Visual D&D 5e/5.5e  

---

## 1. Mapeo Coherente de Modo Claro / Oscuro por Cada Tema

### 1.1. Diagnóstico del Estado Actual
En la arquitectura actual de `frontend/src/context/ThemeContext.tsx`, la función de conmutación de modo (`toggleTheme`) se encuentra desacoplada de la familia del tema seleccionado:

```typescript
// Código actual en ThemeContext.tsx (Líneas 52-55):
const toggleTheme = async () => {
  const nextTheme = isDark ? "light-parchment" : "dark-obsidian";
  await setTheme(nextTheme);
};
```

Esto genera tres problemas inmediatos para el usuario:
1. **Desconexión estética:** Si el usuario selecciona el tema `dark-amethyst` (púrpura arcano) y presiona el interruptor de modo claro, es forzado a `light-parchment` (un pergamino sepia medieval), perdiendo la atmósfera de amatista.
2. **Asimetría de familias de temas:** Actualmente existen 4 temas independientes en `index.css`:
   - `dark-obsidian` (Oscuro: Acero y Piedra volcánica)
   - `light-parchment` (Claro: Manuscrito y Pergamino)
   - `dark-amethyst` (Oscuro: Noche violeta y Amatista) — *Sin contraparte clara*
   - `light-mithril` (Claro: Plata y Azul real) — *Sin contraparte oscura*
3. **Pérdida del tema base al alternar:** Al volver a presionar oscuro desde claro, siempre regresa a `dark-obsidian`, olvidando que el usuario estaba en `dark-amethyst`.

### 1.2. Solución Propuesta (Sin alterar la interfaz existente)

#### A. Organización por Familias de Temas (Theme Families)
Reestructurar la definición de temas en el sistema para que cada concepto visual posea su par armónico de tokens CSS:

| Familia de Tema | Variante Oscura (`dark`) | Variante Clara (`light`) | Identidad Cromática Clave |
| :--- | :--- | :--- | :--- |
| **Obsidian** | `dark-obsidian` *(Existente)* | `light-obsidian` *(Nueva)* | Tonos pizarra fría, acero rúnico y carmesí táctico. |
| **Parchment** | `dark-parchment` *(Nueva)* | `light-parchment` *(Existente)* | Cuero encuadernado cálido, marfil envejecido y cera de lacre. |
| **Amethyst** | `dark-amethyst` *(Existente)* | `light-amethyst` *(Nueva)* | Lavanda pálida, cuarzo violeta y acentos amatista real. |
| **Mithril** | `dark-mithril` *(Nueva)* | `light-mithril` *(Existente)* | Noche de aleación élfica, brillo argénteo y azul cobalto. |

#### B. Nuevas Paletas en `index.css` (Derivadas y Respetuosas con el Contraste)
1. **`light-obsidian` (Acero y Pizarra Clara):**
   - Canvas: `#f0f3f6`, Superficie: `#e4e9ef`, Tarjetas: `#ffffff`, Borde: `#cbd5e1`
   - Acento rúnico: `#1d4ed8` (Azul zafiro rúnico legible en fondo claro)
   - Texto principal: `#0f172a` (Contraste 12:1 WCAG AAA)
2. **`dark-parchment` (Códice de Cuero y Cera):**
   - Canvas: `#1a1612`, Superficie: `#241e18`, Tarjetas: `#2f2720`, Borde: `#4a3e33`
   - Acento: `#c9a45c` (Oro cálido de orfebrería)
   - Texto principal: `#f3ede2`
3. **`light-amethyst` (Cuarzo Místico y Lavanda):**
   - Canvas: `#fbf8ff`, Superficie: `#f3ecfa`, Tarjetas: `#ffffff`, Borde: `#dcc8f0`
   - Acento: `#7c3aed` (Amatista profundo de alta visibilidad)
   - Texto principal: `#231733`
4. **`dark-mithril` (Bastión de Plata y Noche):**
   - Canvas: `#0f131a`, Superficie: `#161c26`, Tarjetas: `#1e2634`, Borde: `#2c384c`
   - Acento: `#38bdf8` (Plata luminosa / Mithril forjado)
   - Texto principal: `#f1f5f9`

#### C. Lógica Inteligente en `ThemeContext.tsx`
El conmutador `toggleTheme()` consultará el mapa de pares en lugar de usar valores fijos:

```typescript
const THEME_PAIRS: Record<string, string> = {
  "dark-obsidian": "light-obsidian",
  "light-obsidian": "dark-obsidian",
  "dark-amethyst": "light-amethyst",
  "light-amethyst": "dark-amethyst",
  "dark-parchment": "light-parchment",
  "light-parchment": "dark-parchment",
  "dark-mithril": "light-mithril",
  "light-mithril": "dark-mithril",
};

const toggleTheme = async () => {
  const targetTheme = THEME_PAIRS[theme] || (isDark ? "light-parchment" : "dark-obsidian");
  await setTheme(targetTheme);
};
```

#### D. Ajustes en el Selector de Ajustes (`SettingsView.tsx`)
- En lugar de listar una lista plana de 8 botones mezclados, agruparlos visualmente por **Familia** (Obsidian, Pergamino, Amatista, Mithril), mostrando el botón de alternancia Claro/Oscuro de manera contextual sin sobrecargar opciones inmediatas (Ley de Hick).

---

## 2. Generación de Imagen de Personaje: Detección y Especificación de Género

### 2.1. Diagnóstico del Estado Actual
En `frontend/src/components/AiPortraitModal.tsx`, la función `buildInternalPrompt()` construye el prompt hacia los motores de IA (Pollinations.ai, FLUX, Stable Diffusion, etc.) de la siguiente forma:

```typescript
// Código actual en AiPortraitModal.tsx (Líneas 64-69):
const name = char.name || "Adventurer";
const race = char.race || "Human";
const charClass = char.char_class || "Warrior";
const identity = `${name}, ${race} ${charClass}`;
const rawAppearance = (char.appearance || "").trim();
const appearanceText = rawAppearance ? `Physical appearance, face and equipment: ${rawAppearance}.` : "";
```

**Causas del sesgo hacia retratos femeninos:**
1. **Ausencia de descriptor de género explícito:** En inglés, `Human Warrior`, `Elf Wizard` o `Tiefling Rogue` son palabras sin género gramatical. Los modelos de difusión basados en CLIP (como Stable Diffusion / Pollinations) tienen priors de entrenamiento donde la categoría "fantasy portrait" con caras detalladas está fuertemente ponderada hacia ilustraciones femeninas.
2. **Descripción en español no traducida:** Si el usuario escribe en apariencia *"Es un clérigo enano anciano con barba gris y armadura de placas"*, las palabras *"clérigo enano"* no son reconocidas como masculinas por el tokenizador en inglés de la IA, por lo que ignora el género gramatical y aplica su sesgo por defecto.

### 2.2. Solución Propuesta (En 3 Niveles Progresivos)

#### Nivel 1: Detección Automática por Contexto Lingüístico (NLP Heurístico Ligero)
Crear una función pura de análisis léxico sobre los campos del personaje (`name`, `appearance`, `background`, `notes`, `char_class`, `gender` si existiera):

```typescript
type InferredGender = "male" | "female" | "neutral" | "unspecified";

function detectGenderFromContext(char: CharacterSheetData): InferredGender {
  const corpus = `${char.name} ${char.appearance} ${char.notes} ${char.background}`.toLowerCase();

  // Marcadores masculinos en español e inglés
  const maleMarkers = [
    /\b(él|el|hombre|varón|chico|muchacho|anciano|viejo|caballero|señor|rey|príncipe|padre|hermano|hijo)\b/,
    /\b(guerrero|mago|bárbaro|pícaro|bardo|clérigo|druida|paladín|monje|brujo|explorador)\b/,
    /\b(enano|humano|elfo|mediano|tiflin|dracónido|gnomo|orco|semiorco)\b/,
    /\b(he|him|his|man|male|boy|elder|gentleman|sir|king|prince|father|brother|son)\b/,
    /\b(barbudo|forzudo|robusto|alto|musculoso|anciano|armado)\b/
  ];

  // Marcadores femeninos en español e inglés
  const femaleMarkers = [
    /\b(ella|la|mujer|dama|chica|muchacha|anciana|vieja|reina|princesa|madre|hermana|hija)\b/,
    /\b(guerrera|maga|bárbara|pícara|barda|clériga|druida|paladina|monja|bruja|exploradora)\b/,
    /\b(enana|humana|elfa|mediana|tiflina|gnoma|orca|semiorca)\b/,
    /\b(she|her|hers|woman|female|girl|lady|queen|princess|mother|sister|daughter)\b/,
    /\b(barbuda|forzuda|robusta|alta|musculosa|anciana|armada)\b/
  ];

  let maleScore = maleMarkers.reduce((acc, regex) => acc + (corpus.match(regex)?.length || 0), 0);
  let femaleScore = femaleMarkers.reduce((acc, regex) => acc + (corpus.match(regex)?.length || 0), 0);

  if (maleScore > femaleScore) return "male";
  if (femaleScore > maleScore) return "female";
  return "unspecified";
}
```

#### Nivel 2: Selector Conciso de Género en el Modal (Ergonomía Ley de Hick)
En la parte superior del modal `AiPortraitModal.tsx`, encima o al lado del estilo artístico, añadir un selector discreto de 3 opciones (segmented control sin iconos invasivos):

```tsx
<div className="flex items-center justify-between text-xs mb-3 bg-card/60 p-1.5 rounded-lg border border-border-iron">
  <span className="text-muted font-medium pl-1">Género del Retrato:</span>
  <div className="flex gap-1">
    {(["auto", "male", "female", "neutral"] as const).map((g) => (
      <button
        key={g}
        onClick={() => setSelectedGender(g)}
        className={`px-2.5 py-1 rounded text-xs transition-colors ${
          selectedGender === g
            ? "bg-gold text-canvas font-bold"
            : "text-muted hover:text-main"
        }`}
      >
        {g === "auto" && `Auto (${detectedGender === "male" ? "Hombre" : detectedGender === "female" ? "Mujer" : "Neutro"})`}
        {g === "male" && "Hombre"}
        {g === "female" && "Mujer"}
        {g === "neutral" && "Andrógino / Fantasía"}
      </button>
    ))}
  </div>
</div>
```

#### Nivel 3: Inyección Determinística en el Prompt de IA
En `buildInternalPrompt`, inyectar términos inequívocos en inglés según el género resuelto:

```typescript
let genderDescriptor = "";
const effectiveGender = selectedGender === "auto" ? detectedGender : selectedGender;

if (effectiveGender === "male") {
  genderDescriptor = "male portrait, handsome manly features, masculine hero";
} else if (effectiveGender === "female") {
  genderDescriptor = "female portrait, heroine, feminine features";
} else if (effectiveGender === "neutral") {
  genderDescriptor = "androgynous mystical character";
}

// Prompt inyectado:
// "Masterpiece digital fantasy illustration...: John, male portrait, masculine hero, Human Warrior..."
```

---

## 3. Plan de Verificación y Criterios de Aceptación

### Verificación de Temas (Claro / Oscuro)
1. Al seleccionar cualquier tema (Obsidian, Parchment, Amethyst, Mithril), el botón de conmutar sol/luna alterna exclusivamente entre su versión clara y oscura de la misma familia.
2. La paleta preserva los acentos visuales característicos (carmesí, amatista, sepia, zafiro) en ambos modos.
3. Se verifica contraste texto/fondo en las 8 vistas principales (Ficha, Combate, Grimorio, Diario, Red, PDFs, Compendio, Forja).

### Verificación de Retratos IA
1. Un personaje con descripción masculina (*"Guerrero noble llamado Thorin, fornido con barba"* y modo `Auto`) genera un prompt explícito con `male portrait, masculine hero`.
2. Un personaje con descripción femenina genera `female portrait, heroine`.
3. El usuario puede forzar manualmente `Hombre` o `Mujer` con un solo clic si el texto no contiene suficientes pistas gramaticales.

---
*Este plan queda registrado y listo para su fase de aprobación e implementación controlada.*
