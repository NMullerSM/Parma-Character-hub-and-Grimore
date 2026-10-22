# PLAN DE ARQUITECTURA Y TRABAJO: SISTEMA DM ONLINE CON CLOUDFLARE TUNNELS
**Proyecto:** Parma — Visualizador & Editor D&D 5e / 5.5e  
**Autor:** Antigravity AI & Equipo de Desarrollo  
**Fecha:** Octubre 2026  
**Estado:** Propuesta Técnica y Plan de Ejecución  

---

## 1. Visión y Objetivos

El objetivo de esta iniciativa es permitir que un Dungeon Master (DM) y sus jugadores compartan una partida en línea de manera **completamente fluida y sin costo de servidor central (Zero-Server Architecture)**. 

El DM corre Parma en su ordenador de escritorio local. Mediante un subproceso ligero que levanta un **Cloudflare Quick Tunnel** (`cloudflared`), la máquina del DM genera una URL pública segura (HTTPS/WSS). Los jugadores ingresan desde cualquier navegador web (móvil, tablet o PC) sin instalar nada y sin necesidad de abrir puertos (Port Forwarding) ni configurar VPNs.

### Pilares Fundamentales:
1. **Cero Servidor en la Nube:** Todo corre en la máquina del DM (Host local + Base de Datos SQLite local).
2. **Conexión Efímera o Persistente:** Un clic genera el túnel (`https://<hash>.trycloudflare.com`) o un subdominio permanente si el DM tiene token de Cloudflare.
3. **Persistencia & Reanudación de Sesión:** Si el túnel cambia en la próxima sesión, el sistema reconoce a los jugadores y sus personajes mediante un `player_token` criptográfico guardado en su LocalStorage.
4. **Control Táctico en Tiempo Real:** El DM puede auditar fichas completas, aplicar daño y curación remota (con retroalimentación cinemática en la pantalla del jugador), entregar objetos Homebrew y registrar tiradas de dados compartidas.
5. **Cumplimiento de la Ley de Hick:** Interfaz DM organizada en divulgado progresivo: vista resumida de combate rápida para no saturar al DM y visor detallado bajo demanda.

---

## 2. Diagrama de Arquitectura de Comunicación

```
+-------------------------------------------------------------------------+
|                              ORDENADOR DEL DM                           |
|                                                                         |
|   +-------------------+      +--------------------------------------+   |
|   |  Parma Desktop    | <--> | Backend Python (FastAPI / aiohttp)   |   |
|   |  (PyWebView +     | IPC  | - WebSocket Manager (Hub)            |   |
|   |   React Frontend) |      | - SQLite DB (dm_sessions, inventory) |   |
|   +-------------------+      +--------------------------------------+   |
|                                                 ^                       |
|                                                 | localhost:8765        |
|                                                 v                       |
|                              +--------------------------------------+   |
|                              | Subproceso 'cloudflared'             |   |
|                              | (Cloudflare Quick Tunnel / ZeroTrust)|   |
|                              +--------------------------------------+   |
+-------------------------------------------------|-----------------------+
                                                  | Túnel Seguro Saliente
                                                  v
                                      (( Cloudflare Edge Network ))
                                                  |
                         +------------------------+------------------------+
                         | https://<session>.trycloudflare.com             |
                         | wss://<session>.trycloudflare.com/ws            |
                         +------------------------+------------------------+
                                                  |
                +---------------------------------+---------------------------------+
                |                                                                   |
                v                                                                   v
+-------------------------------+                                   +-------------------------------+
|      JUGADOR 1 (Navegador)    |                                   |      JUGADOR 2 (Navegador)    |
| - React Web App (Ficha viva)  |                                   | - React Web App (Ficha viva)  |
| - Vignette Flash (Daño/Cura)  |                                   | - Vignette Flash (Daño/Cura)  |
| - Bandeja de Dados Sincronizada                                  | - Bandeja de Dados Sincronizada|
+-------------------------------+                                   +-------------------------------+
```

---

## 3. Componentes de la Arquitectura

### 3.1. Gestor de Túnel en Backend (`desktop_api/tunnel_manager.py`)
Un servicio en Python administrado por la aplicación de escritorio que:
- Detecta o descarga automáticamente el binario portátil de `cloudflared` (sin requerir instalación global en Windows).
- Lanza el comando:
  ```bash
  cloudflared.exe tunnel --url http://127.0.0.1:8765 --no-autoupdate
  ```
- Lee la salida estándar de `cloudflared` en streaming y captura mediante Regex la URL generada (`https://[a-zA-Z0-9-]+\.trycloudflare\.com`).
- Permite configurar opcionalmente un **Cloudflare Named Tunnel Token** para quienes tengan dominio propio en Cloudflare y deseen un enlace fijo permanente (ej. `partida.midominio.com`).
- Notifica al frontend el estado del túnel: `INICIANDO`, `CONECTADO`, `URL_LISTA`, `DESCONECTADO`.
- Genera un código QR y un botón "Copiar Enlace de Invitación".

### 3.2. Servidor de Sesión WebSocket & Webhook (`desktop_api/session_server.py`)
Un servidor asíncrono embebido que maneja las salas de juego:
- **Endpoint `/`:** Sirve la versión cliente web de Parma (compilación React optimizada para navegador móvil/desktop).
- **Endpoint `/api/session/info`:** Información pública de la sesión (nombre de la campaña, DM, fecha).
- **Endpoint `/ws`:** Canal WebSocket bidireccional en tiempo real con protocolo de mensajes JSON estructurados.
- **Autenticación Efímera de Jugador:** Cada jugador recibe un `player_token` criptográfico que se almacena en el `localStorage` del navegador. Si el jugador recarga la página o se desconecta temporalmente, se reconecta automáticamente sin duplicar al personaje.

---

## 4. Protocolo de Mensajería en Tiempo Real (JSON RPC)

Todos los mensajes que circulan entre el DM y los jugadores tienen el formato:
```json
{
  "type": "TIPO_DE_EVENTO",
  "sender": "dm" | "player",
  "player_id": "uuid-o-token",
  "payload": { ... },
  "timestamp": 1729550000000
}
```

### Catálogo de Eventos:

| Evento | Emisor | Receptor | Descripción |
| :--- | :--- | :--- | :--- |
| `PLAYER_JOIN` | Jugador | DM | Envía el resumen y datos de la ficha al conectarse a la sesión. |
| `SHEET_SYNC` | Jugador | DM | Notifica cambios de slots de conjuros, rasgos gastados o notas del jugador. |
| `DICE_ROLL_SHARED` | Ambos | Todos | Difunde una tirada de dados para que se renderice en el historial común. |
| `DM_APPLY_DAMAGE` | DM | Jugador | Ordena al personaje restar puntos de vida (activa destello rojo en pantalla). |
| `DM_APPLY_HEAL` | DM | Jugador | Ordena al personaje sumar puntos de vida (activa destello verde en pantalla). |
| `DM_GIFT_ITEM` | DM | Jugador | Inyecta un objeto Homebrew directamente en el inventario del jugador. |
| `PLAYER_STATUS_UPDATE`| Jugador | DM | Notifica estado vital: `ALIVE`, `UNCONSCIOUS`, `DEAD`, o `STABLE`. |
| `SESSION_STATE` | DM | Jugadores | Envía metadatos de la sesión, clima, iniciativa o avisos de mesa. |

---

## 5. Especificación de Features Clave

### 5.1. Panel del DM: Gestión de Mesa & Concordancia de Fichas
- **Grid Táctico de Jugadores (Quick Combat Cards):**
  - Barra de Vida interactiva con números grandes (ej. `34 / 45 HP`).
  - Botones táctiles directos: `[-1]`, `[-5]`, `[+1]`, `[+5]`, `[Personalizado]`.
  - Clase de Armadura (CA), Velocidad y Percepción Pasiva siempre visibles.
  - Indicador de estado vital con insignias visuales claras:
    - Normal (Verde/Azul).
    - Herido (< 50% HP, Amarillo).
    - Crítico (< 25% HP, Naranja).
    - Inconsciente / Tiradas de Muerte (0 HP, Rojo parpadeante).
    - Muerto (Cráneo / Gris).
- **Visor Detallado de Concordancia:**
  - Al hacer clic en la tarjeta del jugador, se despliega una vista modal o lateral con la **hoja completa de personaje** tal como la ve el jugador (atributos, competencias, hechizos, inventario, trasfondo), permitiendo al DM verificar tiradas y concordar estadísticas sin interrumpir la partida.

### 5.2. Efecto Cinemático en Pantalla del Jugador (Vignette Flash)
- **Cuando el DM aplica daño (`DM_APPLY_DAMAGE`):**
  - La pantalla del jugador se ilumina en los 4 bordes internos con un halo rojo carmesí pulsante (`.vignette-damage`).
  - Sonido sutil de impacto físico o golpe crítico (configurable).
  - La barra de HP del jugador se descuenta automáticamente con animación de drenaje de vida.
- **Cuando el DM cura (`DM_APPLY_HEAL`):**
  - La pantalla del jugador se ilumina con un halo verde esmeralda místico (`.vignette-heal`).
  - La barra de HP se recupera y muestra el incremento numérico en verde brillante.

### 5.3. Forja Homebrew del DM & Entrega en Vivo al Inventario
- **Creador Homebrew Abierto:**
  - El DM dispone de una pestaña dedicada "Forja Homebrew" dentro de su panel de sesión.
  - Campos configurables:
    - Nombre del objeto (ej. *Espada de las Sombras de Cormyr*).
    - Tipo: Arma, Armadura, Objeto Maravilloso, Anillo, Poción, Vara, Pergamino, Munición.
    - Rareza: Común, Poco común, Raro, Muy raro, Legendario, Artefacto.
    - Requiere sintonización (Attunement): Sí / No.
    - Fórmulas de daño libres: Ej. `1d8` cortante + `1d6` fuego + `+2` mágico.
    - Propiedades mágicas y efectos pasivos (ej. `+1 CA`, ventaja en sigilo).
    - Descripción narrativa y notas secretas para el DM.
- **Despacho Inmediato al Jugador:**
  - Lista desplegable de jugadores conectados: `[ Entregar a: Garret ]`.
  - Al presionar **"Entregar Objeto"**, el backend envía el evento `DM_GIFT_ITEM`.
  - La ficha de Garret recibe el objeto en tiempo real en la pestaña **Inventario / Equipamiento**, mostrando una notificación toast animada: *"Has recibido: Espada de las Sombras de Cormyr"*.

### 5.4. Historial Compartido de Tiradas (Shared Dice Ledger)
- Cualquier tirada realizada por un jugador (ataques, salvaciones, pruebas de habilidad o dados libres) se transmite inmediatamente a la bitácora del DM.
- Si el DM tira dados públicos, los jugadores ven el resultado en su bandeja lateral de dados.
- Si el DM tira en modo "Tirada Oculta" (Secret Roll), solo queda registrado en la bitácora privada del DM.
- Integración completa con TaleSpire: si el DM o jugador tiene TaleSpire conectado, los dados ruedan en la mesa 3D y se reflejan en el túnel.

### 5.5. Bitácora de Sesión & Persistencia Histórica
- Toda sesión creada por el DM queda registrada en SQLite en la tabla `dm_session_history`.
- Registra automáticamente:
  - Fecha, hora de inicio y hora de fin.
  - Lista de jugadores y personajes participantes.
  - Total de daño infligido / curado a cada personaje.
  - Registro de si algún personaje cayó inconsciente o murió.
  - Historial de todas las tiradas efectuadas.
  - Lista de objetos entregados en la sesión.
  - Notas de campaña del DM escritas durante la partida.
- El DM puede exportar la crónica de la sesión como documento Markdown o PDF con un solo clic.

---

## 6. Modelo de Datos Relacional (SQLite)

```sql
-- Sesiones creadas por el DM
CREATE TABLE IF NOT EXISTS dm_sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    campaign_name TEXT DEFAULT 'Campaña Principal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    tunnel_url TEXT,
    notes TEXT DEFAULT ''
);

-- Jugadores registrados que han participado en sesiones
CREATE TABLE IF NOT EXISTS dm_session_players (
    session_id TEXT NOT NULL,
    player_token TEXT NOT NULL,
    character_id INTEGER,
    character_name TEXT NOT NULL,
    character_class TEXT,
    character_level INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    max_hp INTEGER,
    end_hp INTEGER,
    status TEXT DEFAULT 'ALIVE', -- ALIVE, UNCONSCIOUS, DEAD
    PRIMARY KEY (session_id, player_token),
    FOREIGN KEY (session_id) REFERENCES dm_sessions(id) ON DELETE CASCADE
);

-- Bitácora de eventos y tiradas de la sesión
CREATE TABLE IF NOT EXISTS dm_session_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL, -- DAMAGE, HEAL, ROLL, ITEM_GIFT, DEATH, NOTE
    actor_name TEXT NOT NULL,
    target_name TEXT,
    details_json TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES dm_sessions(id) ON DELETE CASCADE
);

-- Biblioteca de Objetos Homebrew creados por el DM
CREATE TABLE IF NOT EXISTS dm_homebrew_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- weapon, armor, wondrous, potion, ring, scroll
    rarity TEXT DEFAULT 'common',
    requires_attunement INTEGER DEFAULT 0,
    damage_dice TEXT,       -- ej: '1d8'
    damage_type TEXT,       -- ej: 'slashing'
    secondary_dice TEXT,    -- ej: '1d6'
    secondary_type TEXT,    -- ej: 'fire'
    bonus_attack INTEGER DEFAULT 0,
    bonus_damage INTEGER DEFAULT 0,
    ac_bonus INTEGER DEFAULT 0,
    properties_json TEXT DEFAULT '[]',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Fases de Ejecución del Proyecto

### Fase 1: Infraestructura de Túneles & Servidor Local WebSocket
- [ ] Incorporar gestor de binario portátil de `cloudflared` en `desktop_api/tunnel_manager.py`.
- [ ] Implementar servidor local HTTP/WebSocket en `desktop_api/session_server.py` escuchando en puerto dinámico libre.
- [ ] Añadir métodos al puente nativo de PyWebView (`start_dm_tunnel()`, `stop_dm_tunnel()`, `get_tunnel_status()`).
- [ ] Crear compilación web del cliente para ser servida a través del túnel.

### Fase 2: Panel del DM (Party Live Tracker) & Control de Vida
- [ ] Crear la vista `DMConsoleView.tsx` accesible desde la barra superior de navegación cuando el modo DM esté activo.
- [ ] Visualizador de enlace activo: botón "Copiar Enlace", código QR flotante y visor de jugadores conectados.
- [ ] Grid de tarjetas tácticas de jugadores con actualización instantánea de HP, CA, y percepción.
- [ ] Controles rápidos de aplicar Daño / Curación que envían el mensaje WebSocket a la ficha del jugador.

### Fase 3: Efectos Visuales Cinemáticos en Ficha Jugador
- [ ] Integrar el componente `ScreenVignette.tsx` con el listener de eventos del WebSocket cliente.
- [ ] Animación de pulso carmesí al recibir daño y pulso esmeralda al recibir curación.
- [ ] Feedback hápico / sonoro opcional respetando el estándar antifatiga.

### Fase 4: Forja Homebrew & Despacho de Ítems
- [ ] Crear modal / vista `HomebrewForgeModal.tsx` con selectores libres de dados, atributos y rareza.
- [ ] Guardar ítems en la tabla SQLite `dm_homebrew_items`.
- [ ] Botón de despacho directo "Entregar a Jugador" mediante WebSocket con inserción en el inventario activo.

### Fase 5: Bitácora de Sesión, Registro Histórico & Reanudación
- [ ] Implementar guardado continuo de eventos en `dm_session_logs`.
- [ ] Reconocimiento de jugadores previos al reconectar en una nueva sesión o túnel nuevo.
- [ ] Vista de resumen de fin de sesión con métricas: tiradas más altas, daño total recibido, bajas en combate y notas del DM.
- [ ] Exportación de la sesión a Markdown / PDF para crónicas de campaña.

---

## 8. Consideraciones de Seguridad y Rendimiento

1. **Sin Exposición de Red Local:** Cloudflare Tunnels solo abre un canal saliente HTTPS hacia la red perimetral de Cloudflare; no abre puertos entrantes en el router del usuario ni expone su dirección IP pública.
2. **Encriptación de Extremo a Extremo:** Toda la comunicación entre los jugadores y la máquina del DM viaja protegida por certificados TLS/SSL válidos de Cloudflare.
3. **Optimización de Ancho de Banda:** Los mensajes de sincronización de fichas y tiradas son payloads JSON compactos (< 2 KB), lo que garantiza una latencia menor a 60ms incluso con conexiones residenciales estándar.
4. **Respeto a la Ley de Hick:** Las interfaces se mantienen limpias, divididas en paneles colapsables, evitando botones innecesarios durante el combate en vivo.
