import React, { useEffect, useRef } from "react";
import { useCharacter } from "../context/CharacterContext";

/**
 * OnlinePlayerSync:
 * Escucha eventos en tiempo real cuando el jugador o el DM están conectados a través del túnel o WebSocket.
 * - Recibe órdenes de Daño del DM -> activa el halo rojo cinemático (.vignette-damage) y descuenta HP.
 * - Recibe órdenes de Curación del DM -> activa el halo verde cinemático (.vignette-heal) y suma HP.
 * - Recibe objetos Homebrew del DM -> los inyecta en el inventario del personaje activo.
 * - Sincroniza tiradas compartidas.
 */
export const OnlinePlayerSync: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    triggerVignetteFlash,
    showToast,
  } = useCharacter();

  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Solo conectar WebSocket si estamos en un navegador web o túnel (no empaquetado local puro de pywebview)
    if (typeof window === "undefined") return;

    // Obtener token persistente de jugador o generar uno
    let playerToken = localStorage.getItem("parma_player_token");
    if (!playerToken) {
      playerToken = `p_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem("parma_player_token", playerToken);
    }

    // Determinar URL de WebSocket
    const isHttps = window.location.protocol === "https:";
    const wsProto = isHttps ? "wss:" : "ws:";
    const host = window.location.host;

    // Si estamos en localhost dev puro sin backend WebSocket, omitir error ruidoso
    const wsUrl = `${wsProto}//${host}/ws?token=${playerToken}&role=player`;

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        // Enviar ficha inicial al DM
        if (activeCharacter) {
          ws.send(
            JSON.stringify({
              type: "SHEET_SYNC",
              character: activeCharacter,
            })
          );
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "DM_APPLY_DAMAGE") {
            const delta = Number(data.delta) || 1;
            triggerVignetteFlash("damage");
            if (activeCharacter) {
              const nextHp = Math.max(0, (activeCharacter.hp_current || 0) - delta);
              updateActiveCharacter({ hp_current: nextHp });
            }
            showToast(data.message || `Has recibido ${delta} puntos de daño del DM`, "warn");
          } else if (data.type === "DM_APPLY_HEAL") {
            const delta = Number(data.delta) || 1;
            triggerVignetteFlash("heal");
            if (activeCharacter) {
              const maxHp = activeCharacter.hp_max || 10;
              const nextHp = Math.min(maxHp, (activeCharacter.hp_current || 0) + delta);
              updateActiveCharacter({ hp_current: nextHp });
            }
            showToast(data.message || `Has sido curado por ${delta} puntos de golpe`, "success");
          } else if (data.type === "DM_GIFT_ITEM") {
            const item = data.item;
            if (item && activeCharacter) {
              if (item.category === "weapon") {
                const currentWeapons = activeCharacter.weapon_actions || [];
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
              } else {
                const currentFeatures = activeCharacter.features || [];
                const newFeature = {
                  name: item.name,
                  source: `Homebrew (${item.category || "Objeto"})`,
                  description: `${item.rarity || "común"}${item.requires_attunement ? " (Requiere Sintonización)" : ""}: ${item.description || ""}`,
                };
                updateActiveCharacter({ features: [...currentFeatures, newFeature] });
              }
            }
            showToast(data.message || `¡Has recibido un objeto mágico del DM!`, "success");
          }
        } catch (e) {
          console.error("Error al procesar mensaje de WebSocket:", e);
        }
      };

      ws.onerror = () => {
        // Silencioso en modo local sin servidor
      };
    } catch (e) {
      // Ignorar si no hay servidor websocket
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [activeCharacter?.id]);

  return null;
};
