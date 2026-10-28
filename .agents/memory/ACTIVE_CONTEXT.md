# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-28
- **Dispositivo**: Pop!_OS Linux
- **Estado de Conexiones**: Probadas y validadas exitosamente (Cloudflare Tunnels, WebSocket DM/Player session y sincronización en tiempo real).

---

## 🛠️ Decisiones Técnicas y Cambios Recientes

### 1. Reparación de Generación de Retratos IA (Pollinations.ai)
- **Problema detectado**: Pollinations generaba siempre figuras femeninas independientemente de si el personaje era masculino o se indicaba explícitamente en el texto.
- **Causas identificadas**:
  1. Truncamiento severo a `prompt[:350]` en `desktop_api/bridge.py`, cercenando la descripción de apariencia física y sexo del personaje.
  2. Parámetro `enhance=true` por defecto en Pollinations: su LLM intermedio reescribía los prompts de fantasía forzando clichés de "hermosas doncellas élficas".
  3. Ausencia del modelo FLUX (`model=flux`) en la llamada GET.
  4. Falta de tokens explícitos de género en inglés (`solo 1man, adult male, masculine facial features`) y clases/razas en español sin mapeo.
- **Solución implementada**:
  - `desktop_api/bridge.py`: Límite de caracteres ampliado a 1800, URL de Pollinations configurada con `model=flux` y `enhance=false` explícito.
  - `frontend/src/components/AiPortraitModal.tsx`:
    - Incorporado selector interactivo de Género/Sexo (Masculino ♂, Femenino ♀, Andrógino ⚥, Criatura 🐉) con auto-detección según el trasfondo y apariencia del personaje.
    - Mapeo y traducción de razas y clases de D&D 5e al inglés.
    - Inyección prioritaria de tokens de género al inicio de la descripción para anclar la atención de FLUX.
    - Botón de recarga de plantilla (`RotateCcw`).
  - `frontend/src/i18n/`: Soporte bilingüe completo (ES/EN) para las nuevas opciones.

---

## 📋 Tareas Pendientes / Siguiente Equipo
1. Lanzar `./iniciar.sh` (detectará los cambios en `frontend/src` y compilará Vite automáticamente).
2. Validar la generación de retratos masculinos con varios estilos (Pixel Art, Fantasía Digital, Óleo, etc.).
3. Verificar persistencia del retrato generado en la ficha del héroe en SQLite.
