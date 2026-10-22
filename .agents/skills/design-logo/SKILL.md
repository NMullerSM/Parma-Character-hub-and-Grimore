# Design Logo

Generate a commercial-grade SVG logo for a project by reading its codebase and iterating with the user.

## When to use

When the user says "design logo", "整 logo", "make a logo", "brand design", or wants a visual identity for a project/org.

## Workflow

### Phase 1: Understand the Brand

1. Read the project's codebase to understand identity:
   ```bash
   # If it's a GitHub org
   ~/.local/bin/gh api orgs/{org} --jq '{name, description}'
   ~/.local/bin/gh repo list {org} --json name,description --limit 20

   # If it's a single repo
   cat README.md | head -50
   cat package.json | grep -E '"name"|"description"|"keywords"'
   ```

2. Ask the user 3 questions (keep it fast, don't overthink):
   - **Who is your target user?** (developers only? general public? both?)
   - **What feeling?** (sharp/bold? soft/friendly? minimal/clean? premium/luxury?)
   - **Any color preference?** (warm? cool? specific color? no preference?)

### Phase 2: Generate Concepts

3. Generate **6-8 SVG logo concepts** with different approaches:
   - Vary: icon style, color palette, typography weight, corner radius
   - Always include: at least 1 geometric, 1 abstract, 1 text-heavy
   - Each concept should have a different personality

4. **Package ALL concepts into a single HTML preview file:**
   ```
   /tmp/{project}-logo-preview.html
   ```

   HTML requirements:
   - Grid layout (2 columns)
   - Each concept shows BOTH light and dark background preview side by side
   - Concept name + 1-line description
   - User opens `file:///tmp/{project}-logo-preview.html` to compare all at once

### Phase 3: Iterate

5. User picks a direction → generate **4 variations** of that direction:
   - Vary: stroke weight, dot size, color saturation, corner sharpness, tagline
   - Show icon-only variants at different sizes (64px, 32px, 16px)
   - Still package in single HTML preview (replace same file)

6. Repeat until user says "this one" or "OK"

### Phase 4: Final Package

7. **DO NOT run text_to_path** on the final SVG. Keep original `<text>` elements — they render perfectly in browsers (GitHub, npm, websites). text_to_path degrades quality (wrong kerning, loses gradient fills on tspan, font mismatch). Only use text_to_path if user specifically needs print/offline use.

8. Generate the complete logo package in a **single final HTML preview** (`/tmp/{project}-logo-final.html`):

   **Must include ALL of these:**
   - Full logo (icon + wordmark) — light & dark
   - Full logo PNG (800w, 400w)
   - Full logo monochrome (black, white)
   - Icon only — multiple sizes (1024, 512, 256, 48, 32, 16)
   - OG image (1200x630)
   - Brand color swatches with hex codes

9. If LogoLoom MCP is available, use `export_brand_kit` tool to generate all files automatically. If not, manually write SVG files.

## SVG Design Rules

### DO:
- Use `<svg>`, `<path>`, `<circle>`, `<rect>`, `<text>`, `<linearGradient>`
- Use `system-ui, -apple-system, sans-serif` for sans-serif text
- Use `'Courier New', monospace` for monospace text
- Use Tailwind CSS color palette (consistent, well-tested)
- Use `viewBox` for scalability
- Keep SVG code clean and human-readable
- Use `stroke-linecap="round"` for friendly feel
- Use `stroke-linejoin="miter"` for sharp feel

### DON'T:
- Don't use external fonts (won't render without internet)
- Don't use `<image>` tags (defeats the purpose of SVG)
- Don't make overly complex paths (keep it simple, logos should work at 16px)
- Don't use more than 3 colors in the gradient
- Don't add drop shadows or complex filters for the primary version (OK for "glow" variant)

### Size & Scaling:
- Full logo viewBox: `0 0 400 120`
- Icon only viewBox: `0 0 100 100`
- Wordmark only viewBox: `0 0 280 70`
- Test readability at: 64px, 32px, 16px (icon must be recognizable at all sizes)

### Text & Tagline Alignment (IMPORTANT — learned from mcpware logo):

**Centering tagline under wordmark:**
1. Calculate wordmark width using opentype.js:
   ```javascript
   import opentype from 'opentype.js';
   const font = await opentype.load('./src/fonts/Inter-Bold.ttf');
   let totalWidth = 0;
   for (let i = 0; i < text.length; i++) {
     const glyph = font.charToGlyph(text[i]);
     totalWidth += (glyph.advanceWidth / font.unitsPerEm) * fontSize;
     if (i < text.length - 1) totalWidth += letterSpacing;
   }
   const centerX = totalWidth / 2;
   ```
2. Set tagline: `<text x="{centerX}" text-anchor="middle" ...>`
3. Different fonts have different widths — always calculate, never guess

**Common mistake:** Using a fixed x value (e.g. x="125") without measuring — will look off-center on different systems.

### Color Variants:
- Light mode: darker primary colors, light background
- Dark mode: slightly lighter/more saturated colors, dark background
- Monochrome: pure black or pure white, no gradients
- Always provide hex codes for every color used

### Dark Mode Icon Background:
- Don't use a different background color that creates a visible box
- Either match the dark background exactly, or use transparent background
- Test: place dark icon SVG on a dark page — should blend seamlessly

## Lessons Learned (from mcpware logo design)

1. **text_to_path degrades quality** — opentype.js converts text to paths but loses: gradient fills on `<tspan>`, correct letter-spacing, font-weight nuance. For web use (99% of cases), keep `<text>` tags. Only convert for print.

2. **Tagline must be mathematically centered** — use opentype.js to calculate exact wordmark width, then set tagline `x` to half that width with `text-anchor="middle"`. Never eyeball it.

3. **Always preview light AND dark side by side** — dark mode often needs different saturation, and icon background boxes can look wrong.

4. **Icon extraction must include `<defs>`** — if the icon uses gradients, the extracted icon SVG must copy the `<defs>` block too, otherwise gradients disappear.

5. **Full logo PNGs are essential** — users need PNG for README headers, presentations, social media. Export both icon-only PNGs (square) and full-logo PNGs (wide).

6. **Start with 6-8 concepts, narrow to 4 variations, then polish 1** — don't skip straight to final. The iteration loop is where the real design happens.

## BRAND.md Template

```markdown
# {Project} Brand Guidelines

## Logo Files

### Full Logo (icon + wordmark)
| File | Usage |
|------|-------|
| `logo-full-light.svg` | Primary — light backgrounds |
| `logo-full-dark.svg` | Dark backgrounds |
| `logo-full-800w.png` | README header, presentations |
| `logo-full-400w.png` | Smaller placements |
| `logo-full-mono-black.svg` | Single-color printing |
| `logo-full-mono-white.svg` | Single-color on dark |

### Icon Only
| File | Usage |
|------|-------|
| `icon-light.svg` / `icon-dark.svg` | App icon, avatar |
| `icon-mono-black.svg` / `icon-mono-white.svg` | Single-color |
| `icon-256.png` / `icon-512.png` / `icon-1024.png` | Raster |
| `favicon.ico` / `favicon-16.png` / `favicon-48.png` | Favicon |
| `og-image.png` | Social share (1200×630) |

## Colors
| Name | Hex | Usage |
|------|-----|-------|
| Primary | #xxx | Gradient start, CTA buttons |
| Secondary | #xxx | Gradient end, accents |
| Text (light) | #xxx | Body text on light bg |
| Text (dark) | #xxx | Body text on dark bg |
| Background (light) | #xxx | Light mode bg |
| Background (dark) | #xxx | Dark mode bg |

## Typography
- Headings: system-ui, -apple-system, sans-serif, weight 800
- Body: system-ui, -apple-system, sans-serif, weight 400

## Usage Rules
- Minimum icon size: 16×16px
- Always maintain aspect ratio
- Do not stretch, rotate, or add effects
- Use monochrome version for single-color printing
- Minimum clear space: 25% of icon width on all sides
```
