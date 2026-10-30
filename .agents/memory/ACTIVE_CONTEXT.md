# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-30 00:20 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `22539469780447be0f2d5f500a39d8020f5327fe`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas (Commits Pushed a `develop`)

1. **TaleSpire Symbiote Headless (`talespire_symbiote/`)**
   - Creado Symbiote oficial nativo con `manifest.json`, `index.html` y `bridge.js`.
   - **Fin del macro de arrastre con cursor de ratón:** Los dados se envían de forma nativa e invisible a la bandeja 3D oficial con `talespire.dice.putDiceInTray()`.
   - Conexión por WebSocket bidireccional (`ws://localhost:8765/ws/talespire`) con reconexión automática en background.
   - Captura de eventos físicos de caída de dados (`onRollResults`) y retransmisión a Parma para registrar el resultado en el historial (`SessionRollLedger`).

2. **Auto-Instalador y Servidor Local (`core/talespire_bridge.py` & `desktop_api/session_server.py`)**
   - Detección automática de instalación de TaleSpire tanto en Windows como en Linux (Steam Proton / Wine / Flatpak).
   - Función `install_or_update_symbiote()` que copia automáticamente la carpeta del Symbiote al directorio oficial de TaleSpire (`.../LocalLow/BouncyRock Entertainment/TaleSpire/Symbiotes/ParmaDiceBridge`).
   - Endpoint WebSocket `/ws/talespire` en `session_server.py` para sincronización en tiempo real.

3. **UX Minimalista por Colores en Header (`frontend/src/components/Header.tsx` & `SettingsView.tsx`)**
   - Botón *"TaleSpire"* simplificado con indicador circular LED:
     - ⚪ **Gris:** Desconectado (TaleSpire cerrado o no instalado).
     - 🟡 **Ámbar:** Juego abierto en memoria, esperando conexión del Symbiote.
     - 🟢 **Verde Esmeralda:** Conectado y sincronizado; tiradas y lecturas 3D en vivo.
   - Panel en Configuración con leyenda explicativa de colores y botones de auto-instalación manual y apertura de carpetas.

4. **Barra de Vida Táctica "Ghost HP Bar" (`frontend/src/components/AnimatedHealthBar.tsx`)**
   - **Al recibir daño (-HP):** La barra principal desciende instantáneamente; la barra espectral gris de fondo espera 350ms y luego se drena suavemente con transición de 500ms (`ease-out`).
   - **Al recibir curación (+HP):** La barra asciende fluidamente con un resplandor verde esmeralda (`#10b981`).
   - Soporte para puntos de golpe temporales (dorado).
   - Integrada en `SheetView.tsx` y `CombatView.tsx`.

---

## 🎯 Tareas Pendientes Prioritarias para Desktop (Windows 11)

- [ ] **GitHub Desktop en Windows 11:**
  - Cambiar a la rama `develop` y ejecutar `Pull origin` para recibir los 5 commits.
- [ ] **Verificación de TaleSpire Symbiote en Windows:**
  - Abrir Parma en Windows y comprobar que detecta la carpeta `.../AppData/LocalLow/BouncyRock Entertainment/TaleSpire/Symbiotes`.
  - Abrir TaleSpire y verificar que el Symbiote *"Parma Dice Bridge"* aparezca en el menú de Symbiotes y cambie el LED a verde esmeralda.
- [ ] **Fase 7 - Guardrails Canónicos de Conjuros:**
  - Implementar la validación canónica estricta en el modal de grimorio (`SpellBookManagerModal.tsx`) para impedir que un personaje elija conjuros ajenos a su clase/arquetipo, salvo excepciones de dotes (*Fey Touched*, *Shadow Touched*, *Magic Initiate*) o autorización del DM.
- [ ] **Pruebas de Empaquetado:**
  - Comenzar a formular el empaquetado del ejecutable de Windows en la rama correspondiente.
