import type { SpellItemData, CharacterSheetData } from "../api/types";

export type SpellLimits = NonNullable<CharacterSheetData["spell_limits"]>;
export type SpellLimitKind = "cantrips" | "prepared";

export interface SpellEntry {
  spell: SpellItemData;
  originalIndex: number;
}

export function filterSpellsWithIndex(spells: SpellItemData[], level: number | "all"): SpellEntry[] {
  return spells
    .map((spell, originalIndex) => ({ spell, originalIndex }))
    .filter(({ spell }) => level === "all" || Number(spell.level) === level);
}

/** Tope efectivo, o null si no corresponde bloquear (ver "Decisión de dominio"). */
export function effectiveCap(limits: SpellLimits | null | undefined, kind: SpellLimitKind): number | null {
  if (!limits) return null;
  const raw = kind === "cantrips" ? limits.cantrips_max : limits.spells_prepared_max;
  if (typeof raw !== "number" || !Number.isFinite(raw) || raw < 0) return null;
  if (raw > 0) return Math.floor(raw);
  return limits.is_caster === true && kind === "prepared" ? 0 : null;
}

const isCantrip = (s: SpellItemData) => Number(s.level) === 0;

/** Conteo "conocidos" (misma semántica que backend add_spell y el modal). */
export function countKnown(spells: SpellItemData[], kind: SpellLimitKind): number {
  return spells.filter((s) => (kind === "cantrips" ? isCantrip(s) : !isCantrip(s))).length;
}

export function canAddSpell(spells: SpellItemData[], limits: SpellLimits | null | undefined, level: number): boolean {
  const kind: SpellLimitKind = Number(level) === 0 ? "cantrips" : "prepared";
  const cap = effectiveCap(limits, kind);
  return cap === null || countKnown(spells, kind) < cap;
}

/** Desmarcar siempre se permite; marcar respeta el tope sobre los marcados como preparados. */
export function canTogglePrepared(spells: SpellItemData[], limits: SpellLimits | null | undefined, index: number): boolean {
  const target = spells[index];
  if (!target) return false;
  if (target.prepared || isCantrip(target)) return true;
  const cap = effectiveCap(limits, "prepared");
  if (cap === null) return true;
  const preparedNow = spells.filter((s) => !isCantrip(s) && s.prepared === true).length;
  return preparedNow < cap;
}

export function togglePreparedAt(spells: SpellItemData[], index: number): SpellItemData[] {
  return spells.map((s, i) => (i === index ? { ...s, prepared: !s.prepared } : s));
}
