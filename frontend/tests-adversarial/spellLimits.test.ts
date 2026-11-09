// Tests adversariales del grimorio (hallazgo A3, grupo 4).
// Invariantes: I4-a (toggle modifica exactamente un conjuro), I4-b (tope no saltable
// desde la vista), I4-c (límites ausentes o malformados nunca bloquean), I4-d (compat:
// no lanzadores pueden agregar; datos excedidos pueden desmarcar).
import { describe, test } from "node:test";
import assert from "node:assert/strict";
import {
  filterSpellsWithIndex,
  effectiveCap,
  canAddSpell,
  canTogglePrepared,
  togglePreparedAt,
} from "../src/utils/spellLimits.ts";

const mk = (name: string, level: number, prepared = false) => ({
  name,
  level,
  school: "Evocación",
  cast_time: "1 Acción",
  range_area: "18 m",
  components: "V, S",
  duration: "Instantáneo",
  prepared,
  notes: "",
});

describe("A3 / I4-a: indice original con filtro activo (categoria: bug de indice)", () => {
  test("togglear la 2.a entrada filtrada cambia solo su indice original", () => {
    const spells = [mk("A", 1), mk("B", 2), mk("C", 1)];
    const entries = filterSpellsWithIndex(spells, 1);
    assert.equal(entries.length, 2);
    assert.equal(entries[1].originalIndex, 2);
    const out = togglePreparedAt(spells, entries[1].originalIndex);
    assert.equal(out[2].prepared, true);
    assert.equal(out[0].prepared, false);
    assert.equal(out[1].prepared, false);
    assert.equal(out[1].name, "B");
  });

  test("nombres duplicados: solo cambia el indice tocado (categoria: limite)", () => {
    const spells = [mk("X", 1), mk("X", 1)];
    const out = togglePreparedAt(spells, 1);
    assert.equal(out[0].prepared, false);
    assert.equal(out[1].prepared, true);
  });

  test("indice fuera de rango no modifica nada", () => {
    const spells = [mk("A", 1)];
    const out = togglePreparedAt(spells, 5);
    assert.deepEqual(out, spells);
  });

  test("filtro 'all' conserva todos los indices originales", () => {
    const spells = [mk("A", 1), mk("B", 2)];
    const entries = filterSpellsWithIndex(spells, "all");
    assert.deepEqual(entries.map((e) => e.originalIndex), [0, 1]);
  });

  test("filtro de trucos (nivel 0) conserva el indice original (categoria: limite)", () => {
    const spells = [mk("L1", 1), mk("T", 0)];
    const entries = filterSpellsWithIndex(spells, 0);
    assert.equal(entries.length, 1);
    assert.equal(entries[0].originalIndex, 1);
  });
});

describe("A3 / I4-c: limites ausentes o malformados nunca bloquean (categoria: input malformado)", () => {
  test("limites undefined: sin tope para agregar ni para preparar", () => {
    const spells = [mk("A", 1, true), mk("B", 1, true), mk("C", 1, true), mk("D", 1, false), mk("T", 0)];
    assert.equal(canAddSpell(spells, undefined, 1), true);
    assert.equal(canAddSpell(spells, undefined, 0), true);
    assert.equal(canTogglePrepared(spells, undefined, 3), true);
  });

  test("maximos NaN, negativo o string no bloquean ni lanzan excepcion", () => {
    const spells = [mk("A", 1, true), mk("B", 1, true)];
    const nan = { cantrips_max: NaN, cantrips_current: 0, spells_prepared_max: NaN, spells_prepared_current: 2, is_caster: true };
    const neg = { cantrips_max: -1, cantrips_current: 0, spells_prepared_max: -1, spells_prepared_current: 2, is_caster: true };
    const str = { cantrips_max: "3", cantrips_current: 0, spells_prepared_max: "2", spells_prepared_current: 2, is_caster: true };
    for (const limits of [nan, neg, str]) {
      assert.equal(effectiveCap(limits, "cantrips"), null);
      assert.equal(effectiveCap(limits, "prepared"), null);
      assert.equal(canAddSpell(spells, limits, 1), true);
      assert.equal(canTogglePrepared(spells, limits, 0), true);
    }
  });
});

describe("A3 / I4-b: tope de preparados y trucos (categoria: limite)", () => {
  test("maximo 3 con 3 conocidos de nivel>0: no se agrega otro preparado; el truco sigue permitido", () => {
    const spells = [mk("A", 1, true), mk("B", 2, true), mk("C", 1, true)];
    const limits = { cantrips_max: 2, cantrips_current: 0, spells_prepared_max: 3, spells_prepared_current: 3, is_caster: true };
    assert.equal(canAddSpell(spells, limits, 1), false);
    assert.equal(canAddSpell(spells, limits, 0), true);
  });

  test("lanzador con preparados=0 (no modelado): tope duro para preparados", () => {
    const spells: ReturnType<typeof mk>[] = [];
    const limits = { cantrips_max: 2, cantrips_current: 0, spells_prepared_max: 0, spells_prepared_current: 0, is_caster: true };
    assert.equal(canAddSpell(spells, limits, 1), false);
  });

  test("decision de dominio: trucos=0 en lanzador (Paladin) no bloquea trucos", () => {
    const spells: ReturnType<typeof mk>[] = [];
    const limits = { cantrips_max: 0, cantrips_current: 0, spells_prepared_max: 2, spells_prepared_current: 0, is_caster: true };
    assert.equal(canAddSpell(spells, limits, 0), true);
  });

  test("marcar preparado en el limite se rechaza; desmarcar siempre se permite", () => {
    const spells = [mk("A", 1, true), mk("B", 1, true), mk("C", 1, true), mk("D", 1, false)];
    const limits = { cantrips_max: 2, cantrips_current: 0, spells_prepared_max: 3, spells_prepared_current: 3, is_caster: true };
    assert.equal(canTogglePrepared(spells, limits, 3), false);
    assert.equal(canTogglePrepared(spells, limits, 0), true);
  });

  test("truco no cuenta para el tope de preparados", () => {
    const spells = [mk("T", 0, false), mk("A", 1, true)];
    const limits = { cantrips_max: 2, cantrips_current: 1, spells_prepared_max: 2, spells_prepared_current: 1, is_caster: true };
    assert.equal(canTogglePrepared(spells, limits, 0), true);
  });

  test("tope de trucos se respeta al agregar (categoria: limite)", () => {
    const spells = [mk("T1", 0), mk("T2", 0)];
    const limits = { cantrips_max: 2, cantrips_current: 2, spells_prepared_max: 4, spells_prepared_current: 0, is_caster: true };
    assert.equal(canAddSpell(spells, limits, 0), false);
    assert.equal(canAddSpell(spells, limits, "0" as unknown as number), false);
  });
});

describe("A3 / I4-d: compatibilidad (categoria: compatibilidad hacia atras)", () => {
  test("no lanzador (Guerrero, is_caster false, maximo 0) puede agregar conjuros", () => {
    const spells: ReturnType<typeof mk>[] = [];
    const limits = { cantrips_max: 0, cantrips_current: 0, spells_prepared_max: 0, spells_prepared_current: 0, is_caster: false };
    assert.equal(canAddSpell(spells, limits, 1), true);
  });

  test("payload viejo sin is_caster con maximo 0: sin tope", () => {
    const spells: ReturnType<typeof mk>[] = [];
    const limits = { cantrips_max: 0, cantrips_current: 0, spells_prepared_max: 0, spells_prepared_current: 0 };
    assert.equal(canAddSpell(spells, limits, 1), true);
  });

  test("personaje que ya excede el tope (datos viejos): puede desmarcar, no marcar mas", () => {
    const spells = [mk("A", 1, true), mk("B", 1, true), mk("C", 1, true), mk("D", 1, true), mk("E", 1, true), mk("F", 1, false)];
    const limits = { cantrips_max: 2, cantrips_current: 0, spells_prepared_max: 3, spells_prepared_current: 5, is_caster: true };
    assert.equal(canTogglePrepared(spells, limits, 0), true);
    assert.equal(canTogglePrepared(spells, limits, 5), false);
  });
});
