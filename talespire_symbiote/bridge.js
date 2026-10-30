/**
 * Parma D&D — TaleSpire Symbiote Dice Bridge
 * Comunicación WebSocket bidireccional entre la app Parma y la API de TaleSpire.
 */

const CANDIDATE_PORTS = [8765, 8766, 8767, 8768];
let currentPortIndex = 0;
let ws = null;
let reconnectTimer = null;
let totalRollsCount = 0;

// Elementos de la interfaz UI
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const rollCountEl = document.getElementById("rollCount");
const lastResultEl = document.getElementById("lastResult");
const logContainer = document.getElementById("logContainer");

/**
 * Agrega una entrada formateada al registro visual del Symbiote.
 */
function addLogEntry(message, type = "info") {
  if (!logContainer) return;

  const emptyPlaceholder = logContainer.querySelector(".empty-log");
  if (emptyPlaceholder) {
    emptyPlaceholder.remove();
  }

  const entry = document.createElement("div");
  entry.className = `log-entry ${type}`;

  const timeStr = new Date().toLocaleTimeString();
  entry.innerHTML = `
    <div class="log-time">${timeStr}</div>
    <div class="log-msg">${message}</div>
  `;

  logContainer.insertBefore(entry, logContainer.firstChild);

  // Mantener un máximo de 30 entradas para evitar sobrecarga de memoria
  while (logContainer.children.length > 30) {
    logContainer.removeChild(logContainer.lastChild);
  }
}

/**
 * Actualiza el indicador de conexión en la UI.
 */
function updateConnectionUI(connected, port = null) {
  if (!statusBadge || !statusText) return;

  if (connected) {
    statusBadge.className = "status-badge connected";
    statusText.textContent = `En Línea (:${port})`;
  } else {
    statusBadge.className = "status-badge disconnected";
    statusText.textContent = "Reconectando...";
  }
}

/**
 * Conecta el socket al puerto actual o rota al siguiente si falla.
 */
function initWebSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const port = CANDIDATE_PORTS[currentPortIndex];
  const url = `ws://127.0.0.1:${port}/ws/talespire`;

  try {
    ws = new WebSocket(url);

    ws.onopen = () => {
      console.log(`[Parma Symbiote] Conectado exitosamente con Parma en ${url}`);
      updateConnectionUI(true, port);
      addLogEntry(`Conectado al servidor de Parma en puerto ${port}`, "resolved");

      // Anunciar presencia del Symbiote a Parma
      ws.send(JSON.stringify({
        type: "SYMBIOTE_HELLO",
        version: "1.0.0",
        timestamp: Date.now()
      }));
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (err) {
        console.error("[Parma Symbiote] Error al parsear mensaje recibido:", err);
      }
    };

    ws.onerror = (err) => {
      // Intencionalmente silencioso: rotaremos al siguiente puerto en onclose
    };

    ws.onclose = () => {
      updateConnectionUI(false);
      ws = null;
      // Probar siguiente puerto candidato
      currentPortIndex = (currentPortIndex + 1) % CANDIDATE_PORTS.length;
      scheduleReconnect();
    };
  } catch (e) {
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    initWebSocket();
  }, 2500);
}

/**
 * Procesa mensajes entrantes desde Parma.
 */
async function handleIncomingMessage(msg) {
  if (!msg || !msg.type) return;

  if (msg.type === "DICE_ROLL_DISPATCH") {
    const formula = msg.formula || "1d20";
    const label = msg.label || "Tirada";
    const mode = msg.mode || "normal";
    const actor = msg.actor_name || "Parma";

    addLogEntry(`📥 Orden de Parma: <strong>${formula}</strong> (${label}) [${actor}]`, "dispatched");

    // Despachar a la bandeja de TaleSpire
    await placeDiceInTaleSpireTray(formula, label);
  }
}

/**
 * Envía la fórmula a la bandeja nativa de TaleSpire mediante TS.dice.
 */
async function placeDiceInTaleSpireTray(formula, label = "") {
  try {
    if (typeof TS !== "undefined" && TS.dice) {
      // 1. Validar si la fórmula es aceptada por TaleSpire
      let valid = true;
      if (typeof TS.dice.isValidRollString === "function") {
        valid = TS.dice.isValidRollString(formula);
      }

      if (!valid) {
        console.warn(`[Parma Symbiote] Fórmula no estándar para TaleSpire: ${formula}. Adaptando...`);
      }

      // 2. Crear los descriptores oficiales de tirada
      let descriptors = null;
      if (typeof TS.dice.makeRollDescriptors === "function") {
        descriptors = TS.dice.makeRollDescriptors(formula);
      } else {
        descriptors = [{ name: label || "Tirada Parma", roll: formula }];
      }

      // 3. Colocar en la bandeja 3D de TaleSpire (sin mover el cursor del SO)
      if (typeof TS.dice.putDiceInTray === "function") {
        await TS.dice.putDiceInTray(descriptors);
        addLogEntry(`🎲 Dados en bandeja 3D: <strong>${formula}</strong>. (Presiona Espacio o Clic)`, "resolved");
        return true;
      }
    } else {
      console.warn("[Parma Symbiote] API TS.dice no disponible (¿ejecutando fuera de TaleSpire?)");
      addLogEntry(`⚠️ API de TaleSpire no disponible en este entorno (${formula})`, "dispatched");
    }
  } catch (error) {
    console.error("[Parma Symbiote] Error al colocar dados en bandeja:", error);
    addLogEntry(`❌ Error en bandeja TaleSpire: ${error.message || error}`, "dispatched");
  }
  return false;
}

/**
 * Subscripción oficial de TaleSpire: captura física de resultados.
 * Declarada en manifest.json: "subscriptions": { "dice": { "onRollResults": "handleRollResults" } }
 */
window.handleRollResults = function (rollResults) {
  try {
    console.log("[Parma Symbiote] onRollResults recibido de TaleSpire:", rollResults);

    let totalCalculated = 0;
    const parsedGroups = [];

    if (rollResults && Array.isArray(rollResults.resultsGroups)) {
      for (const group of rollResults.resultsGroups) {
        let groupTotal = 0;
        try {
          if (typeof TS !== "undefined" && TS.dice && typeof TS.dice.evaluateDiceResultsGroup === "function") {
            groupTotal = TS.dice.evaluateDiceResultsGroup(group);
          } else {
            groupTotal = fallbackEvaluateGroup(group);
          }
        } catch (evalErr) {
          console.warn("[Parma Symbiote] Error en evaluateDiceResultsGroup:", evalErr);
          groupTotal = fallbackEvaluateGroup(group);
        }

        totalCalculated += groupTotal;
        parsedGroups.push({
          name: group.name || "Resultado",
          total: groupTotal,
          groupData: group
        });
      }
    }

    // Actualizar métricas visuales en el HUD
    totalRollsCount++;
    if (rollCountEl) rollCountEl.textContent = String(totalRollsCount);
    if (lastResultEl) lastResultEl.textContent = String(totalCalculated);

    addLogEntry(`🎯 Resultado Físico 3D: <strong>${totalCalculated}</strong>`, "resolved");

    // Construir payload enriquecido para Parma
    const resolvedPayload = {
      type: "DICE_ROLL_RESOLVED",
      rollId: rollResults ? rollResults.rollId : null,
      clientId: rollResults ? rollResults.clientId : null,
      total: totalCalculated,
      groups: parsedGroups,
      raw: rollResults,
      timestamp: Date.now()
    };

    // Reenviar a Parma vía WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(resolvedPayload));
    }
  } catch (err) {
    console.error("[Parma Symbiote] Error al procesar handleRollResults:", err);
  }
};

/**
 * Evaluación de respaldo en caso de que evaluateDiceResultsGroup no esté disponible.
 */
function fallbackEvaluateGroup(group) {
  if (!group) return 0;
  if (typeof group.value === "number") return group.value;
  if (typeof group.total === "number") return group.total;
  return 0;
}

/**
 * Botón de prueba rápida desde la UI del Symbiote.
 */
function testTrayRoll(formula) {
  addLogEntry(`🧪 Prueba manual solicitada: <strong>${formula}</strong>`, "dispatched");
  placeDiceInTaleSpireTray(formula, "Prueba Manual");
}

// Iniciar búsqueda y conexión al cargar
document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
});