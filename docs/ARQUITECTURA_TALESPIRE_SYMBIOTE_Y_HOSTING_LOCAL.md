# D&D Sanctum — Arquitectura Técnica: TaleSpire Symbiotes, Lectura de Dados 3D y Hosting Multijugador sin Apertura de Puertos

> **Documento:** `docs/ARQUITECTURA_TALESPIRE_SYMBIOTE_Y_HOSTING_LOCAL.md`  
> **Estado:** Especificación Técnica & Arquitectura de Referencia  
> **Áreas Cubiertas:** TaleSpire Symbiote API, Named Pipe vs WebSocket, Ingeniería Inversa REA, Microservicio Local y Hosting P2P sin CGNAT/Puertos.

---

## 1. Integración con TaleSpire: Cómo Leer y Lanzar Dados desde el Juego

### 1.1 El Problema del Named Pipe Actual (`\\.\pipe\com.bouncyrock.talespire.lcm_pipe`)
Actualmente, el ejecutable de D&D Sanctum se comunica con TaleSpire mediante el Named Pipe oficial del sistema operativo Windows:
* **Canal:** `\\.\pipe\com.bouncyrock.talespire.lcm_pipe`
* **Formato:** `talespire://dice/[Etiqueta:]<Cantidad>d<Caras>[+Mod]`
* **Limitación Fundamental:** Este Named Pipe es **estrictamente unidireccional (Write-Only)** desde aplicaciones externas hacia el motor de TaleSpire. TaleSpire acepta la orden, monta los modelos 3D en la bandeja de dados (`UIDiceTray`), pero **nunca devuelve el resultado numérico físico a través de este canal**.

Por esta razón, cuando el usuario tira en modo TaleSpire, la aplicación registra `"🎲 En mesa 3D (TaleSpire)"`, pero no puede saber de forma automática si un d20 cayó en 14, en 20 (crítico) o en 1 (pifia).

---

### 1.2 La Solución Oficial y Nativa: TaleSpire Symbiotes (`window.TS.dice`)

Bouncyrock Entertainment diseñó los **Symbiotes** específicamente para resolver este escenario. Un Symbiote es una aplicación web embebida que corre dentro del propio proceso de TaleSpire a través de **Chromium Embedded Framework (CEF)**.

* **Ruta de instalación en Windows:**
  ```
  %LOCALAPPDATA%Low\BouncyRock Entertainment\TaleSpire\Symbiotes\DnDSanctumCompanion\
  ```
* **Acceso Global al Motor 3D:** El juego inyecta el objeto global `window.TS` en la ventana del Symbiote.

#### Métodos Clave de la API de Dados (`TS.dice`):
1. **`TS.dice.makeRollDescriptors(formula)`**:
   Convierte fórmulas complejas (ej. `"1d20+5"`, `"2d6+1d8+3"`) en descriptores que TaleSpire entiende de forma nativa.
2. **`TS.dice.putDiceInTray(descriptors, forceThrow)`**:
   Coloca físicamente los dados en la bandeja del jugador o DM dentro del mundo 3D y ejecuta el lanzamiento.
3. **`TS.dice.onRollResults(callback)` (¡La clave para leer los dados!)**:
   Evento oficial del juego que se dispara en el Symbiote en el instante exacto en que **los dados físicos dejan de rebotar en la mesa 3D**.
   El payload que recibe el callback contiene la descomposición completa:
   ```javascript
   {
     rollId: "abc-123",
     clientId: "local_player",
     resultsGroups: [
       {
         name: "Salvación de Muerte",
         result: {
           value: 16,
           rolls: [16],
           modifier: 0
         }
       }
     ]
   }
   ```

---

### 1.3 Arquitectura Bidireccional: D&D Sanctum (.exe) ↔ Symbiote (TaleSpire)

Para conectar el ejecutable de escritorio con el Symbiote en tiempo real sin requerir internet:

```
┌─────────────────────────────────────────┐               WebSocket Local               ┌─────────────────────────────────────────┐
│        D&D Sanctum Desktop (.exe)       │ ◄─────────────────────────────────────────► │           TaleSpire Symbiote            │
│       (PyWebView + Python Core)         │           ws://127.0.0.1:8765               │      (CEF WebView dentro de TaleSpire)  │
└─────────────────────────────────────────┘                                             └─────────────────────────────────────────┘
                    │                                                                                        │
         1. Clic en "Lanzar Salvación"                                                          3. TS.dice.putDiceInTray()
                    │                                                                                        │
                    ▼                                                                                        ▼
         Envía JSON por WebSocket ────────────────────────────────────────────────────────►     Dados ruedan físicamente en mesa 3D
                                                                                                             │
         5. Recibe resultado exacto ◄──────────────────────────────────────────────────────     4. TS.dice.onRollResults() captura
            Calcula Éxito / Fracaso                                                                números reales en reposo (ej: 14)
            Asienta en Ficha y Ledger
```

1. **Servidor WebSocket Local en Python (`core/talespire_symbiote_server.py`)**:
   D&D Sanctum levanta en un hilo secundario un micro-servidor WebSocket ultraligero en `127.0.0.1:8765` (utilizando la biblioteca estándar de Python o `websockets`).
2. **El Symbiote de D&D Sanctum (`data/talespire_symbiote/index.html`)**:
   Al abrirse dentro de TaleSpire, conecta a `ws://127.0.0.1:8765`.
   - Cuando recibe `roll_request` desde D&D Sanctum: ejecuta `TS.dice.putDiceInTray`.
   - Cuando `TS.dice.onRollResults` detecta que los dados se detuvieron: envía el valor real (`{ event: "roll_result", total: 14, dice: [14] }`) de vuelta a D&D Sanctum.
3. **Resultado en D&D Sanctum**:
   D&D Sanctum recibe el número del juego real, determina de inmediato si es Éxito o Fracaso frente a la CD, y lo muestra en pantalla sin requerir interacción manual.

---

### 1.4 ¿Cuándo Usar REA (Reverse Engineer Anything) vs Symbiote Oficial?

* **Uso de REA (Ingeniería Inversa sobre Ensamblados C# / Unity):**
  - Esencial para analizar la física interna (`Bouncyrock.TaleSpire.Runtime.dll`), desensamblar `DiceRollManager`, calcular las coordenadas de pantalla para el arrastre del ratón (`execute_throw_gesture`), o crear mods de BepInEx (`AutoThrowPatch.cs`).
* **Uso del Symbiote Oficial:**
  - Para la **comunicación y lectura de dados**, la API oficial de Symbiotes es superior a cualquier hook de memoria o ingeniería inversa: no se rompe con las actualizaciones de TaleSpire en Steam, no requiere inyectar DLLs y cuenta con validación criptográfica del juego contra trampas.

---

## 2. Arquitectura de Hosting Multijugador sin Abrir Puertos

### 2.1 El Desafío: Redes Domésticas y CGNAT
Cuando un Master o jugador quiere hospedar una partida para que sus compañeros se conecten a sus hojas de personaje:
* La inmensa mayoría de routers domésticos bloquean conexiones entrantes (firewall).
* Muchos proveedores de internet utilizan **CGNAT** (Carrier-Grade NAT), lo que imposibilita abrir puertos incluso configurando el router (`Port Forwarding`).
* Obligar a los jugadores a abrir puertos o configurar firewalls arruina la experiencia de usuario.

---

### 2.2 Estrategias de Conexión Diseñadas para el `.exe` (100% Autónomas)

```
                       ┌───────────────────────────────────────────────┐
                       │     ¿Dónde están jugando tus compañeros?     │
                       └───────────────────────┬───────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
             [Misma Red Local / WiFi]                      [A través de Internet]
                        │                                             │
                        ▼                                             ▼
             ┌─────────────────────┐                       ┌─────────────────────┐
             │  Servidor LAN HTTP  │                       │  Túnel / WebRTC /   │
             │  - Microservicio en │                       │  TaleSpire Relay    │
             │    el .exe (Python) │                       │  - Cero puertos     │
             │  - Código QR en     │                       │  - Enlace HTTPS     │
             │    pantalla / IP    │                       │    compartible      │
             └─────────────────────┘                       └─────────────────────┘
```

---

### Opción A: Servidor Local LAN con Código QR (Mesa Presencial / Misma WiFi)
* **Cómo funciona:**
  - El propio ejecutable de Python levanta un servidor HTTP local en el puerto `8000` (`http://192.168.1.X:8000`).
  - La aplicación genera un **Código QR** en pantalla.
  - Los jugadores sentados en la mesa escanean el QR con su teléfono móvil o tablet y abren su hoja de personaje interactiva en el navegador del teléfono, sincronizada en vivo con la pantalla del DM.
* **Ventajas:** Cero configuración de red, latencia de 1 milisegundo, no requiere internet.

---

### Opción B: Túnel Efímero Cero-Configuración (Cloudflare Quick Tunnel)
* **Cómo funciona:**
  - El ejecutable `.exe` puede incluir el binario embebido de Cloudflare Tunnel (`cloudflared`) o realizar un enlace outbound por WebSocket seguro (puerto 443 saliente).
  - Al pulsar **`[Iniciar Sesión como Host]`**, el `.exe` inicia el túnel y obtiene una URL segura pública temporal:
    `https://dragon-sanctum-8492.trycloudflare.com`
  - El DM comparte ese link por WhatsApp o Discord. Sus jugadores abren el link y ya están conectados al servidor del DM.
* **Ventajas:**
  - **No requiere abrir puertos en el router** ni lidiar con CGNAT.
  - Conexión cifrada de extremo a extremo con SSL/HTTPS oficial.
  - Los puertos salientes (443) nunca están bloqueados por los operadores.

---

### Opción C: La Partida de TaleSpire como Relay de Sincronización
* **Cómo funciona:**
  - Si el grupo ya está jugando en TaleSpire, todos los jugadores están conectados al mismo servidor de Bouncyrock.
  - El Symbiote de cada jugador puede leer el ID de la criatura seleccionada en el tablero (`TS.creatures.getSelectedCreatures()`) y vincular el token 3D con la ficha de D&D Sanctum.
  - Los datos de combate, iniciativa y dados se transmiten a través de los eventos de la propia mesa de TaleSpire.

---

### Opción D: WebRTC P2P (Peer-to-Peer directo Navegador ↔ Navegador)
* **Cómo funciona:**
  - Conexión directa P2P entre navegadores utilizando servidores públicos STUN de Google (`stun:stun.l.google.com:19302`).
  - El DM comparte un código de sala de 6 letras (ej. `"DRAGON"`).
  - La sincronización viaja por `RTCDataChannel` sin servidores intermedios de pago.

---

## 3. Hoja de Ruta de Implementación Sugerida

1. **Fase Inmediata (Completada en esta sesión):**
   - Corrección del marco de escaneo en manuales PDF (eliminación de recuadros negros/rojos en Tasha y Xanathar con auto-recorte configurable).
   - Detección automática de Éxito / Fracaso en Tiradas de Salvación y Salvaciones de Muerte (CD 10, críticos y botón para asentar en ficha).
   - Panel táctico de Hechizos y Ranuras Mágicas en la vista de Combate.
2. **Fase Symbiote V1:**
   - Servidor WebSocket local `ws://127.0.0.1:8765` en `core/talespire_symbiote_server.py`.
   - Instalador con 1 clic para copiar la carpeta `data/talespire_symbiote` a la ruta `%LOCALAPPDATA%Low\...\Symbiotes`.
   - Recepción en vivo de los dados reales desde `TS.dice.onRollResults`.
3. **Fase Multiplayer Host V1:**
   - Microservicio HTTP local embebido en `desktop_app.py` con pantalla de Código QR para dispositivos en la misma red local.
