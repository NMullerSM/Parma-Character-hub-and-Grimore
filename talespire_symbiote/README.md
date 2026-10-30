# Parma D&D — TaleSpire Symbiote Dice Bridge

Este symbiote permite la comunicación nativa y bidireccional entre la aplicación de escritorio **Parma D&D** y el tablero 3D de **TaleSpire**.

---

## 🎲 ¿Cómo funciona?

1. **Sin macros de ratón invasivas:** Ya no se utiliza simulación del cursor del sistema operativo. Las tiradas se colocan limpiamente dentro de la bandeja nativa de TaleSpire mediante la API oficial `TS.dice.putDiceInTray`.
2. **Físicas Reales 3D:** El jugador o DM tira los dados presionando la **Barra Espaciadora** en TaleSpire (o haciendo clic en la bandeja).
3. **Captura Bidireccional en Vivo:** A través de la suscripción `onRollResults`, el Symbiote lee los números exactos obtenidos en la mesa física de TaleSpire y los envía de inmediato a Parma vía WebSockets locales (`ws://127.0.0.1:8765/ws/talespire`).
4. **Ejecución en Segundo Plano:** Gracias a la directiva `"capabilities": ["runInBackground"]`, el puente sigue activo aunque minimices la barra lateral del Symbiote.

---

## 🛠️ Instalación en TaleSpire

1. Inicia **TaleSpire**.
2. Ve a los **Ajustes** del juego $\rightarrow$ pestaña **Symbiotes** $\rightarrow$ haz clic en **Abrir Directorio de Symbiotes** (*Open Symbiotes Directory*):
   - En Windows suele ser: `%APPDATA%\..\LocalLow\Bouncyrock Entertainment\TaleSpire\Symbiotes`
3. Copia esta carpeta completa (`talespire_symbiote`) dentro del directorio de Symbiotes y renómbrala a `ParmaDiceBridge` si lo deseas.
4. En el menú lateral derecho de TaleSpire, abre la lista de Symbiotes y haz clic en **Parma Dice Bridge** para activarlo.
5. Verás el indicador en verde `En Línea` y Parma cambiará su indicador a verde esmeralda.

---

## 📋 Estructura de Archivos

- `manifest.json`: Definición del Symbiote, capacidades de segundo plano y suscripción al evento `dice.onRollResults`.
- `index.html`: Panel visual HUD con estado en tiempo real, contador de tiradas y pruebas manuales.
- `bridge.js`: Cliente WebSocket con autoreconexión y enlace con la API `TS.dice`.
