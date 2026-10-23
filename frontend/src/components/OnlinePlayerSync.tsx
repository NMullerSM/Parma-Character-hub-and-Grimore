import React, { useEffect, useRef } from "react";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";

/**
 * OnlinePlayerSync:
 * Administra el ciclo de vida de la conexión en tiempo real del Jugador con el DM:
 * - Registra la ficha inicial y cambios mediante HTTP POST /api/player/join y WebSocket SHEET_SYNC.
 * - Recibe órdenes de Daño del DM -> activa el halo rojo cinemático y descuenta HP.
 * - Recibe órdenes de Curación del DM -> activa el halo verde cinemático y suma HP.
 * - Recibe objetos Homebrew del DM -> los inyecta en el inventario/armas del personaje activo.
 * - Retransmite tiradas de dados locales hacia la mesa y recibe tiradas remotas (DICE_ROLL_SHARED).
 * - Detecta desconexión del DM (SESSION_CLOSED) y limpia el estado sin dejar "fantasmas" en sesión.
 */
export const OnlinePlayerSync: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    triggerVignetteFlash,
    showToast,
    activeSessionId,
    setActiveSessionId,
  } = useCharacter();

  const socketRef = useRef<WebSocket | null>(null);
  const characterRef = useRef(activeCharacter);
  characterRef.current = activeCharacter;

  // 1. Efecto de conexión WebSocket con el servidor del DM
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Obtener token persistente de jugador o generar uno nuevo
    let playerToken = localStorage.getItem("parma_player_token");
    if (!playerToken) {
      playerToken = `p_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem("parma_player_token", playerToken);
    }

    // Resolver URL del servidor (usar origen actual o el host configurado al unirse)
    const storedUrl = localStorage.getItem("parma_session_url");
    let targetOrigin = window.location.origin;
    if (storedUrl && (storedUrl.startsWith("http://") || storedUrl.startsWith("https://"))) {
      try {
        targetOrigin = new URL(storedUrl).origin;
      } catch (_) {}
    }

    const isHttps = targetOrigin.startsWith("https:");
    const wsProto = isHttps ? "wss:" : "ws:";
    const host = targetOrigin.replace(/^https?:\/\//, "");

    const wsUrl = `${wsProto}//${host}/ws?token=${playerToken}&role=player`;

    let ws: WebSocket;
    let isCleanClose = false;

    try {
      ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = async () => {
        // Enviar handshake de enrolamiento HTTP para persistir en SQLite
        const currentChar = characterRef.current;
        if (currentChar) {
          try {
            await api.joinPlayerSession(targetOrigin, currentChar);
          } catch (_) {}

          // Enviar ficha por WebSocket
          try {
            ws.send(
              JSON.stringify({
                type: "SHEET_SYNC",
                character: currentChar,
              })
            );
          } catch (_) {}
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "CONNECTION_ESTABLISHED") {
            if (data.session_id) {
              setActiveSessionId(data.session_id);
            }
          } else if (data.type === "SESSION_CLOSED") {
            isCleanClose = true;
            setActiveSessionId(null);
            localStorage.removeItem("parma_session_url");
            localStorage.removeItem("parma_active_session_id");
            showToast(data.message || "El DM ha finalizado la sesión online.", "info");
          } else if (data.type === "DM_APPLY_DAMAGE") {
            const delta = Number(data.delta) || 1;
            triggerVignetteFlash("damage");
            const char = characterRef.current;
            if (char) {
              const nextHp = Math.max(0, (char.hp_current || 0) - delta);
              updateActiveCharacter({ hp_current: nextHp });
            }
            showToast(data.message || `Has recibido ${delta} puntos de daño del DM`, "warn");
          } else if (data.type === "DM_APPLY_HEAL") {
            const delta = Number(data.delta) || 1;
            triggerVignetteFlash("heal");
            const char = characterRef.current;
            if (char) {
              const maxHp = char.hp_max || 10;
              const nextHp = Math.min(maxHp, (char.hp_current || 0) + delta);
              updateActiveCharacter({ hp_current: nextHp });
            }
            showToast(data.message || `Has sido curado por ${delta} puntos de golpe`, "success");
          } else if (data.type === "DM_GIFT_ITEM") {
            const item = data.item;
            const char = characterRef.current;
            if (item && char) {
              if (item.category === "weapon") {
                const currentWeapons = char.weapon_actions || [];
                const newWeapon = {
                  name: item.name,
                  type: "Arma Marcial / Mágica",
                  range_val: "C/C (1.5m)",
                  hit_dc: item.bonus_attack ? `+${item.bonus_attack}` : "+0",
                  damage_dice: item.damage_dice || "1d8",
                  damage_type: item.damage_type || "cortante",
                  notes: `${item.rarity || "común"}${item.secondary_dice ? ` + ${item.secondary_dice} ${item.secondary_type || ""}` : ""}: ${item.description || ""}`,
                  proficient: true,
                };
                updateActiveCharacter({ weapon_actions: [...currentWeapons, newWeapon] });
              } else if (item.category === "scroll") {
                const currentFeatures = char.features || [];
                const scrollDesc = [
                  item.description ? item.description : "",
                  item.scroll_content ? `\n\n📜 Contenido del documento:\n${item.scroll_content}` : "",
                ].filter(Boolean).join("");
                const newScrollFeature = {
                  name: item.name,
                  source: "📜 Pergamino / Documento",
                  description: scrollDesc || "Documento entregado por el DM.",
                };
                updateActiveCharacter({ features: [...currentFeatures, newScrollFeature] });
              } else {
                const currentFeatures = char.features || [];
                const newFeature = {
                  name: item.name,
                  source: `Homebrew (${item.category || "Objeto"})`,
                  description: `${item.rarity || "común"}${item.requires_attunement ? " (Requiere Sintonización)" : ""}: ${item.description || ""}`,
                };
                updateActiveCharacter({ features: [...currentFeatures, newFeature] });
              }
            }
            showToast(data.message || `¡Has recibido un objeto del DM!`, "success");
          } else if (data.type === "DICE_ROLL_SHARED") {
            // Tirada compartida en la mesa
            if (data.player_token !== playerToken) {
              window.dispatchEvent(new CustomEvent("parma_remote_dice_roll", { detail: data }));
            }
          }
        } catch (e) {
          console.error("[OnlinePlayerSync] Error al procesar mensaje de WebSocket:", e);
        }
      };

      ws.onclose = (ev) => {
        if (!isCleanClose && ev.code === 1000) {
          setActiveSessionId(null);
          showToast("Sesión online finalizada.", "info");
        }
      };

      ws.onerror = () => {
        // Silencioso si no hay servidor activo
      };
    } catch (e) {
      // Ignorar si el host no es un servidor válido
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [activeSessionId, setActiveSessionId, showToast, triggerVignetteFlash, updateActiveCharacter]);

  // 2. Escuchar cambios en la ficha activa y sincronizar con el DM
  useEffect(() => {
    if (!activeCharacter || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    try {
      socketRef.current.send(
        JSON.stringify({
          type: "SHEET_SYNC",
          character: activeCharacter,
        })
      );
    } catch (_) {}
  }, [
    activeCharacter?.hp_current,
    activeCharacter?.hp_max,
    activeCharacter?.ac,
    activeCharacter?.level,
    activeCharacter?.name,
  ]);

  // 3. Escuchar evento de tirada de dados local y despacharla al WebSocket
  useEffect(() => {
    const handleSendRoll = (event: Event) => {
      const customEvent = event as CustomEvent;
      const data = customEvent.detail;
      if (!data || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        return;
      }
      try {
        socketRef.current.send(
          JSON.stringify({
            type: "DICE_ROLL",
            character_name: data.character_name || "Aventurero",
            roll: data.roll,
          })
        );
      } catch (e) {
        console.error("[OnlinePlayerSync] Error enviando tirada a WebSocket:", e);
      }
    };

    window.addEventListener("parma_send_dice_roll", handleSendRoll);
    return () => {
      window.removeEventListener("parma_send_dice_roll", handleSendRoll);
    };
  }, []);

  return null;
};
