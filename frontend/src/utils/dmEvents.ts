import type { CharacterSheetData, FeatureItemData, WeaponActionData } from "../api/types";

export interface DmEventMessage {
  type: string;
  delta?: unknown;
  item?: any;
  message?: string;
}

/**
 * Normaliza el delta de un evento del DM: valor absoluto, entero, entre 1 y 9999.
 * No numérico (NaN, undefined, "abc") se trata como 1; valores enormes (1e9, Infinity) como 9999.
 */
export const clampDelta = (raw: unknown): number => {
  const n = Math.abs(Number(raw));
  if (Number.isNaN(n)) return 1;
  return Math.min(Math.max(Math.floor(n), 1), 9999);
};

/**
 * Devuelve el parche a aplicar sobre `prev`, o null si el mensaje no modifica la ficha.
 * Función PURA: no muta `prev` ni tiene efectos secundarios (StrictMode la ejecuta dos veces).
 */
export function computeDmEventUpdate(
  prev: CharacterSheetData,
  msg: DmEventMessage
): Partial<CharacterSheetData> | null {
  if (msg.type === "DM_APPLY_DAMAGE") {
    return { hp_current: Math.max(0, (prev.hp_current || 0) - clampDelta(msg.delta)) };
  }
  if (msg.type === "DM_APPLY_HEAL") {
    const maxHp = prev.hp_max || 10;
    return { hp_current: Math.min(maxHp, (prev.hp_current || 0) + clampDelta(msg.delta)) };
  }
  if (msg.type === "DM_GIFT_ITEM" && msg.item) {
    const item = msg.item;
    if (item.category === "weapon") {
      const currentWeapons: WeaponActionData[] = prev.weapon_actions || [];
      const newWeapon: WeaponActionData = {
        name: item.name,
        type: "Arma Marcial / Mágica",
        range_val: "C/C (1.5m)",
        hit_dc: item.bonus_attack ? `+${item.bonus_attack}` : "+0",
        damage_dice: item.damage_dice || "1d8",
        damage_type: item.damage_type || "cortante",
        notes: `${item.rarity || "común"}${item.secondary_dice ? ` + ${item.secondary_dice} ${item.secondary_type || ""}` : ""}: ${item.description || ""}`,
        proficient: true,
      };
      return { weapon_actions: [...currentWeapons, newWeapon] };
    }
    const currentFeatures: FeatureItemData[] = prev.features || [];
    const newFeature: FeatureItemData = {
      name: item.name,
      source: `Homebrew (${item.category || "Objeto"})`,
      description: `${item.rarity || "común"}${item.requires_attunement ? " (Requiere Sintonización)" : ""}: ${item.description || ""}`,
    };
    return { features: [...currentFeatures, newFeature] };
  }
  return null;
}
