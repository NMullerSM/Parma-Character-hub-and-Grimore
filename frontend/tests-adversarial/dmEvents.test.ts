/**
 * Tests adversariales de los eventos del DM sobre la ficha (hallazgo A4, grupo 5).
 *
 * Invariantes protegidos:
 *  - I5-a: un evento del DM se aplica sobre el estado MÁS RECIENTE (no sobre un snapshot).
 *  - I5-b: dos eventos seguidos se acumulan (30 -> 25 -> 20), ninguno pisa al otro.
 *  - I5-c: HP nunca queda < 0 ni > hp_max por un evento del DM (delta negativo, NaN, enorme).
 *  - Pureza: computeDmEventUpdate no muta el estado previo (StrictMode lo ejecuta dos veces).
 *
 * Módulo bajo test puro (sin React). Se ejecuta con `node --test` (type stripping de Node 22).
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { clampDelta, computeDmEventUpdate } from "../src/utils/dmEvents.ts";
import type { DmEventMessage } from "../src/utils/dmEvents.ts";
import type { CharacterSheetData } from "../src/api/types.ts";

/** Ficha mínima: solo los campos que lee el helper. */
function sheet(over: Record<string, unknown> = {}): CharacterSheetData {
  return {
    name: "Thorin",
    hp_current: 30,
    hp_max: 30,
    weapon_actions: [],
    features: [],
    ...over,
  } as unknown as CharacterSheetData;
}

/** Simula el actualizador funcional de updateActiveCharacter: aplica el parche sobre el estado previo. */
function applyDm(prev: CharacterSheetData, msg: DmEventMessage): CharacterSheetData {
  return { ...prev, ...(computeDmEventUpdate(prev, msg) ?? {}) };
}

describe("A4 / I5-a: estado más reciente, no snapshot", () => {
  // Categoría: concurrencia / orden
  it("el daño se aplica sobre el prev nuevo (25), no sobre el snapshot (30)", () => {
    const snapshotAtSocketOpen = sheet({ hp_current: 30 });
    const currentState = { ...snapshotAtSocketOpen, hp_current: 25 }; // el jugador editó a 25
    const next = applyDm(currentState, { type: "DM_APPLY_DAMAGE", delta: 5 });
    assert.equal(next.hp_current, 20);
    assert.notEqual(next.hp_current, 25);
  });
});

describe("A4 / I5-b: eventos encadenados se acumulan", () => {
  // Categoría: concurrencia
  it("dos daños seguidos: 30 -> 25 -> 20", () => {
    const s1 = applyDm(sheet({ hp_current: 30 }), { type: "DM_APPLY_DAMAGE", delta: 5 });
    assert.equal(s1.hp_current, 25);
    const s2 = applyDm(s1, { type: "DM_APPLY_DAMAGE", delta: 5 });
    assert.equal(s2.hp_current, 20);
  });
});

describe("A4 / I5-c: delta negativo nunca sube el HP", () => {
  // Categoría: input malformado
  it("delta -5 en daño se trata como 5 y HP no sube", () => {
    const prev = sheet({ hp_current: 30 });
    const next = applyDm(prev, { type: "DM_APPLY_DAMAGE", delta: -5 });
    assert.equal(next.hp_current, 25);
    assert.ok(next.hp_current! <= prev.hp_current!);
  });
});

describe("A4 / I5-c: delta no numérico se trata como 1", () => {
  // Categoría: input malformado
  for (const delta of ["abc", NaN, undefined, null, "", {}]) {
    it(`delta ${JSON.stringify(String(delta))} -> 1`, () => {
      assert.equal(clampDelta(delta), 1);
      const next = applyDm(sheet({ hp_current: 30 }), { type: "DM_APPLY_DAMAGE", delta });
      assert.equal(next.hp_current, 29);
    });
  }
});

describe("A4 / I5-c: delta enorme se acota", () => {
  // Categoría: límite
  it("curación con delta 1e9 deja HP == hp_max", () => {
    const next = applyDm(sheet({ hp_current: 5, hp_max: 20 }), { type: "DM_APPLY_HEAL", delta: 1e9 });
    assert.equal(next.hp_current, 20);
  });

  it("daño con delta 1e9 deja HP en 0 (nunca negativo)", () => {
    const next = applyDm(sheet({ hp_current: 30 }), { type: "DM_APPLY_DAMAGE", delta: 1e9 });
    assert.equal(next.hp_current, 0);
  });

  it("delta Infinity se acota a 9999 y no rompe el HP", () => {
    assert.equal(clampDelta(Infinity), 9999);
    const next = applyDm(sheet({ hp_current: 30 }), { type: "DM_APPLY_DAMAGE", delta: Infinity });
    assert.equal(next.hp_current, 0);
  });
});

describe("A4 / compat: curación sin hp_max usa 10 como antes", () => {
  // Categoría: compatibilidad
  it("hp_max ausente -> tope 10", () => {
    const prev = sheet({ hp_current: 5, hp_max: undefined });
    const next = applyDm(prev, { type: "DM_APPLY_HEAL", delta: 1e9 });
    assert.equal(next.hp_current, 10);
  });
});

describe("A4 / pérdida de datos: regalo de arma no pisa armas previas", () => {
  // Categoría: pérdida de datos
  it("regalar un arma tras haber otra conserva ambas", () => {
    const prev = sheet({
      weapon_actions: [
        { name: "Daga", type: "Arma", range_val: "C/C", hit_dc: "+4", damage_dice: "1d4", damage_type: "perforante", notes: "", proficient: true },
      ],
    });
    const next = applyDm(prev, {
      type: "DM_GIFT_ITEM",
      item: { category: "weapon", name: "Espada Lunar", bonus_attack: 2, damage_dice: "1d8", damage_type: "radiante", rarity: "rara", description: "brilla" },
    });
    const names = (next.weapon_actions || []).map((w) => w.name);
    assert.deepEqual(names, ["Daga", "Espada Lunar"]);
    assert.equal(next.weapon_actions![1].hit_dc, "+2");
    assert.equal(next.weapon_actions![1].notes, "rara: brilla");
  });
});

describe("A4 / regresión: regalo no-arma va a features con el formato actual", () => {
  // Categoría: regresión
  it("un objeto no-arma se agrega a features", () => {
    const next = applyDm(sheet(), {
      type: "DM_GIFT_ITEM",
      item: { category: "wondrous", name: "Amuleto", rarity: "poco común", requires_attunement: true, description: "protege" },
    });
    assert.equal(next.features!.length, 1);
    assert.deepEqual(next.features![0], {
      name: "Amuleto",
      source: "Homebrew (wondrous)",
      description: "poco común (Requiere Sintonización): protege",
    });
  });
});

describe("A4 / input malformado: tipos desconocidos o sin item devuelven null", () => {
  // Categoría: input malformado
  it("tipo desconocido -> null", () => {
    assert.equal(computeDmEventUpdate(sheet(), { type: "DM_FOO", delta: 3 }), null);
  });

  it("DM_GIFT_ITEM sin item -> null", () => {
    assert.equal(computeDmEventUpdate(sheet(), { type: "DM_GIFT_ITEM" }), null);
  });
});

describe("A4 / StrictMode: la función es pura y no muta prev", () => {
  // Categoría: efectos secundarios
  it("prev queda intacto tras aplicar daño, curación y regalo", () => {
    const prev = sheet({
      hp_current: 30,
      weapon_actions: [{ name: "Daga", type: "Arma", range_val: "C/C", hit_dc: "+4", damage_dice: "1d4", damage_type: "perforante", notes: "", proficient: true }],
      features: [{ name: "Rasgo", source: "Clase", description: "x" }],
    });
    const before = structuredClone(prev);
    computeDmEventUpdate(prev, { type: "DM_APPLY_DAMAGE", delta: 5 });
    computeDmEventUpdate(prev, { type: "DM_APPLY_HEAL", delta: 5 });
    computeDmEventUpdate(prev, { type: "DM_GIFT_ITEM", item: { category: "weapon", name: "Hacha" } });
    computeDmEventUpdate(prev, { type: "DM_GIFT_ITEM", item: { category: "wondrous", name: "Anillo" } });
    assert.deepEqual(prev, before);
  });
});
