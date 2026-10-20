import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import type { SpellItemData, FeatureItemData } from "../api/types";
import { FeatureDetailModal } from "../components/FeatureDetailModal";
import { SpellDetailModal } from "../components/SpellDetailModal";
import { SpellBookManagerModal } from "../components/SpellBookManagerModal";
import { BookOpen } from "lucide-react";

const DND_CONDITIONS = [
  "Apresado",
  "Asustado",
  "Aturdido",
  "Cegado",
  "Concentración",
  "Derribado",
  "Envenenado",
  "Hechizado",
  "Incapacitado",
  "Invisible",
  "Paralizado",
  "Restringido",
];

export const CombatView: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    performRestAction,
    openDiceDrawer,
    showToast,
    addSpell,
    removeSpell,
  } = useCharacter();
  const [shortRestDiceToSpend, setShortRestDiceToSpend] = useState<number>(1);
  const [selectedSpellLevel, setSelectedSpellLevel] = useState<number | "all">("all");
  const [selectedActionFilter, setSelectedActionFilter] = useState<"all" | "action" | "bonus" | "reaction">("all");
  const [isSpellManagerOpen, setIsSpellManagerOpen] = useState<boolean>(false);
  const [activeSpellForModal, setActiveSpellForModal] = useState<SpellItemData | null>(null);
  const [activeFeatureForModal, setActiveFeatureForModal] = useState<FeatureItemData | null>(null);

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">
          Selecciona un personaje para el modo combate táctico.
        </p>
      </div>
    );
  }

  const {
    name,
    char_class,
    level,
    hp_current,
    hp_max,
    hp_temp,
    ac,
    speed,
    initiative,
    hit_dice_total,
    hit_dice_current,
    hit_dice_max,
    hit_dice_faces,
    death_save_successes,
    death_save_failures,
    inspiration,
    conditions = [],
    weapon_actions,
    features = [],
    spells = [],
    spell_slots_total = {},
    spell_slots_used = {},
    spell_stats,
  } = activeCharacter;

  const currentHdCount =
    parseInt(String(hit_dice_current || "1").split("d")[0], 10) || 0;
  const maxHdCount = hit_dice_max || level || 1;
  const hdFaces = hit_dice_faces || 8;

  const handleHpDelta = (delta: number) => {
    if (delta < 0 && hp_temp > 0) {
      const dmg = Math.abs(delta);
      if (hp_temp >= dmg) {
        updateActiveCharacter({ hp_temp: hp_temp - dmg });
        return;
      } else {
        const leftover = dmg - hp_temp;
        const nextHp = Math.max(0, hp_current - leftover);
        updateActiveCharacter({ hp_temp: 0, hp_current: nextHp });
        return;
      }
    }
    const next = Math.max(0, Math.min(hp_max + 100, hp_current + delta));
    updateActiveCharacter({ hp_current: next });
  };

  const handleTempHpDelta = (delta: number) => {
    const nextTemp = Math.max(0, (hp_temp || 0) + delta);
    updateActiveCharacter({ hp_temp: nextTemp });
  };

  const handleDeathSave = (type: "success" | "failure", index: number) => {
    if (type === "success") {
      const next = death_save_successes === index + 1 ? index : index + 1;
      updateActiveCharacter({ death_save_successes: next });
    } else {
      const next = death_save_failures === index + 1 ? index : index + 1;
      updateActiveCharacter({ death_save_failures: next });
    }
  };

  const toggleCondition = (cond: string) => {
    const exists = conditions.includes(cond);
    const next = exists ? conditions.filter((c) => c !== cond) : [...conditions, cond];
    updateActiveCharacter({ conditions: next });
  };

  const isDying = hp_current === 0;

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-6 max-w-5xl mx-auto">
      {/* 1. Header Táctico */}
      <div className="flex items-center justify-between border-b border-border-iron pb-3">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">{name} — Modo Combate</h1>
          <p className="text-xs text-muted">
            Nivel {level} {char_class} • CA {ac} • Velocidad {speed} pies
          </p>
        </div>

        {/* Inspiración Heroica */}
        <button
          onClick={() => updateActiveCharacter({ inspiration: !inspiration })}
          className={`px-3 py-1.5 rounded border text-xs font-semibold transition-all ${
            inspiration
              ? "bg-gold text-canvas border-gold shadow-[0_0_12px_rgba(201,164,92,0.4)]"
              : "bg-card text-muted border-border-iron hover:border-gold/50"
          }`}
        >
          {inspiration ? "★ Inspiración Activa" : "☆ Sin Inspiración"}
        </button>
      </div>

      {/* 2. Centro de Salud y Daño Dinámico */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-5 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted">
            <span>Puntos de Golpe en Combate</span>
            <span>Máximo: {hp_max} PG</span>
          </div>

          <div className="flex items-center justify-center my-2 gap-4">
            <span
              className={`font-stat font-bold text-6xl md:text-7xl ${
                isDying
                  ? "text-crimson animate-pulse"
                  : hp_current <= hp_max / 2
                  ? "text-amber-400"
                  : "text-main"
              }`}
            >
              {hp_current}
            </span>
            <div className="flex flex-col items-start gap-1">
              <span className="font-stat font-bold text-sm text-gold border border-gold/40 px-2 py-0.5 rounded bg-surface">
                +{hp_temp || 0} PG Temp
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleTempHpDelta(5)}
                  className="px-1.5 py-0.5 rounded border border-border-iron hover:border-gold text-[10px] font-stat text-muted hover:text-gold bg-surface"
                >
                  +5 Temp
                </button>
                {hp_temp > 0 && (
                  <button
                    onClick={() => updateActiveCharacter({ hp_temp: 0 })}
                    className="px-1.5 py-0.5 rounded border border-border-iron hover:border-crimson text-[10px] font-stat text-muted hover:text-crimson bg-surface"
                  >
                    Limpiar
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Botones de Control de Daño y Curación Rápida */}
          <div className="grid grid-cols-4 gap-2">
            <button
              onClick={() => handleHpDelta(-5)}
              className="py-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-crimson text-crimson font-stat font-bold text-sm transition-colors"
            >
              -5 Daño
            </button>
            <button
              onClick={() => handleHpDelta(-1)}
              className="py-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-crimson text-crimson font-stat font-bold text-sm transition-colors"
            >
              -1 Daño
            </button>
            <button
              onClick={() => handleHpDelta(1)}
              className="py-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-emerald-500 text-emerald-400 font-stat font-bold text-sm transition-colors"
            >
              +1 Cura
            </button>
            <button
              onClick={() => handleHpDelta(5)}
              className="py-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-emerald-500 text-emerald-400 font-stat font-bold text-sm transition-colors"
            >
              +5 Cura
            </button>
          </div>
        </div>

        {/* Salvaciones de Muerte, Dados de Golpe y Descansos */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* Salvaciones de Muerte */}
          <div className="bg-card border border-border-iron rounded-xl p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
              Salvaciones de Muerte
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">Éxitos:</span>
                <div className="flex gap-2">
                  {[0, 1, 2].map((i) => (
                    <button
                      key={i}
                      onClick={() => handleDeathSave("success", i)}
                      className={`w-5 h-5 rounded-full border transition-all ${
                        i < death_save_successes
                          ? "bg-emerald-500 border-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                          : "border-border-iron bg-surface"
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">Fallos:</span>
                <div className="flex gap-2">
                  {[0, 1, 2].map((i) => (
                    <button
                      key={i}
                      onClick={() => handleDeathSave("failure", i)}
                      className={`w-5 h-5 rounded-full border transition-all ${
                        i < death_save_failures
                          ? "bg-crimson border-crimson-hover shadow-[0_0_8px_rgba(197,0,9,0.5)]"
                          : "border-border-iron bg-surface"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={() =>
                openDiceDrawer({
                  dice: { "20": 1 },
                  modifier: 0,
                  label: "Tirada de Salvación contra Muerte",
                  dc: 10,
                  is_death_save: true,
                  is_saving_throw: true,
                })
              }
              className="w-full mt-3 py-1.5 rounded border border-border-iron hover:border-gold text-xs text-main bg-surface transition-colors font-medium flex items-center justify-center gap-1"
            >
              <span>Tirar Salvación de Muerte (CD 10)</span>
            </button>
          </div>

          {/* Dados de Golpe y Descansos */}
          <div className="bg-card border border-border-iron rounded-xl p-4 space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                Dados de Golpe & Descansos
              </h3>
              <span className="font-stat font-bold text-xs text-gold">
                {hit_dice_current || `${currentHdCount}d${hdFaces}`} /{" "}
                {hit_dice_total || `${maxHdCount}d${hdFaces}`}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs bg-surface px-2.5 py-1.5 rounded border border-border-iron">
              <span className="text-muted">Gastar en Desc. Corto:</span>
              <div className="flex items-center gap-1.5 font-stat">
                <button
                  onClick={() => setShortRestDiceToSpend((v) => Math.max(0, v - 1))}
                  className="w-5 h-5 rounded border border-border-iron hover:border-gold text-center"
                >
                  -
                </button>
                <span className="w-6 text-center font-bold text-main">
                  {Math.min(shortRestDiceToSpend, currentHdCount)}
                </span>
                <button
                  onClick={() => setShortRestDiceToSpend((v) => Math.min(currentHdCount, v + 1))}
                  className="w-5 h-5 rounded border border-border-iron hover:border-gold text-center"
                >
                  +
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() =>
                  performRestAction("short", Math.min(shortRestDiceToSpend, currentHdCount))
                }
                className="py-2 rounded border border-border-iron hover:border-gold bg-surface text-xs font-semibold text-main transition-colors"
              >
                Descanso Corto
              </button>
              <button
                onClick={() => performRestAction("long")}
                className="py-2 rounded bg-gold hover:bg-gold-hover text-canvas text-xs font-semibold transition-colors shadow-sm"
              >
                Descanso Largo
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Estados y Condiciones Tácticas */}
      <section className="bg-card border border-border-iron rounded-xl p-4 space-y-2.5">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">
            Estados y Condiciones Activas
          </h2>
          {conditions.length > 0 && (
            <button
              onClick={() => updateActiveCharacter({ conditions: [] })}
              className="text-xs text-crimson hover:underline"
            >
              Limpiar estados ({conditions.length})
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {DND_CONDITIONS.map((cond) => {
            const isActive = conditions.includes(cond);
            return (
              <button
                key={cond}
                onClick={() => toggleCondition(cond)}
                className={`px-2.5 py-1 rounded border text-xs transition-all ${
                  isActive
                    ? cond === "Concentración"
                      ? "border-gold bg-gold/20 text-gold font-semibold"
                      : "border-crimson bg-crimson/20 text-crimson font-semibold"
                    : "border-border-iron bg-surface text-muted hover:text-main"
                }`}
              >
                {cond}
              </button>
            );
          })}
        </div>
      </section>

      {/* 4. Acciones de Ataque Rápido */}
      <section className="space-y-3">
        <h2 className="font-display font-semibold text-lg text-gold">Acciones Rápidas en Turno</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {weapon_actions?.map((w, idx) => (
            <div
              key={idx}
              onClick={() =>
                openDiceDrawer({
                  dice: { "20": 1 },
                  modifier: parseInt(String(w.hit_dc).replace("+", ""), 10) || 0,
                  label: `Ataque: ${w.name}`,
                })
              }
              className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.01]"
            >
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-semibold text-sm text-main">{w.name}</h4>
                <span className="font-stat font-bold text-xs text-gold">{w.hit_dc} impacto</span>
              </div>
              <p className="font-stat text-xs text-muted">
                {w.damage_dice} {w.damage_type}
              </p>
            </div>
          ))}

          {/* Acción Rápida de Iniciativa */}
          <div
            onClick={() =>
              openDiceDrawer({
                dice: { "20": 1 },
                modifier: initiative,
                label: "Tirada de Iniciativa",
              })
            }
            className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.01] flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-sm text-main">Tirar Iniciativa</h4>
              <span className="font-stat font-bold text-xs text-gold">
                {initiative >= 0 ? `+${initiative}` : initiative}
              </span>
            </div>
            <p className="text-xs text-muted mt-1">
              Lanza 1d20 + Bono de Destreza al inicio del combate.
            </p>
          </div>
        </div>
      </section>

      {/* 4.5 Rasgos Especiales y Recursos de Clase */}
      {features && features.length > 0 && (
        <section className="bg-card border border-border-iron rounded-xl p-4 md:p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-border-iron/80 pb-2.5">
            <div>
              <h2 className="font-display font-semibold text-lg text-gold flex items-center gap-2">
                <span>Rasgos & Habilidades Tácticas</span>
                <span className="font-stat text-xs px-2 py-0.5 rounded bg-surface border border-border-iron text-muted">
                  {features.length} disponibles
                </span>
              </h2>
              <p className="text-xs text-muted">
                Haz clic en cualquier tarjeta para proyectarla hacia adelante con tiradas y control de usos.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {features.map((f, idx) => {
              const maxUses = f.uses_max || 0;
              const cur = f.uses_current ?? maxUses;
              const hasUses = maxUses > 0;
              return (
                <div
                  key={idx}
                  onClick={() => setActiveFeatureForModal(f)}
                  className="bg-surface border border-border-iron hover:border-gold/70 rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.01] flex flex-col justify-between space-y-2 group"
                >
                  <div>
                    <div className="flex items-start justify-between gap-1 mb-1">
                      <h4 className="font-semibold text-xs text-main group-hover:text-gold transition-colors truncate">
                        {f.name}
                      </h4>
                      <span className="text-[10px] text-gold font-stat shrink-0">{f.source}</span>
                    </div>
                    <p className="text-xs text-muted line-clamp-2 leading-relaxed">
                      {f.description}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-1.5 border-t border-border-iron/40 text-[10px]">
                    <span className="text-muted">
                      {f.recharge ? `Recarga: ${f.recharge}` : "Pasivo"}
                    </span>
                    {hasUses && (
                      <span className="font-stat font-bold text-gold px-1.5 py-0.5 rounded bg-card border border-border-iron">
                        {cur}/{maxUses} usos
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 5. Panel de Hechizos & Magia en Combate */}
      <section className="bg-card border border-border-iron rounded-xl p-4 md:p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-iron/80 pb-3">
          <div>
            <h2 className="font-display font-semibold text-lg text-gold flex items-center gap-2">
              <span>Hechizos & Grimorio de Combate</span>
              {spells.length > 0 && (
                <span className="font-stat text-xs px-2 py-0.5 rounded bg-surface border border-border-iron text-muted">
                  {spells.length} conjuros
                </span>
              )}
            </h2>
            <p className="text-xs text-muted">
              Lanzamiento táctico con gestión inmediata de ranuras mágicas.
            </p>
          </div>

          {/* Estadísticas de conjuros compactas y botón de gestión */}
          <div className="flex flex-wrap items-center gap-2">
            {spell_stats && (
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2 py-1 rounded bg-surface border border-border-iron font-semibold text-muted">
                  Aptitud: <strong className="text-gold">{spell_stats.ability || "INT"}</strong>
                </span>
                <span className="px-2 py-1 rounded bg-surface border border-border-iron font-semibold text-muted">
                  CD: <strong className="text-main">{spell_stats.dc || 10}</strong>
                </span>
                <button
                  onClick={() =>
                    openDiceDrawer({
                      dice: { "20": 1 },
                      modifier: spell_stats.attack_bonus || 0,
                      label: "Ataque Mágico",
                    })
                  }
                  className="px-2.5 py-1 rounded bg-surface hover:bg-gold hover:text-canvas border border-border-iron hover:border-gold font-semibold text-gold transition-colors"
                  title="Tirar Ataque de Conjuro (1d20 + Bono)"
                >
                  Atq: {spell_stats.attack_bonus >= 0 ? `+${spell_stats.attack_bonus}` : spell_stats.attack_bonus}
                </button>
              </div>
            )}
            <button
              onClick={() => setIsSpellManagerOpen(true)}
              className="px-3 py-1 rounded bg-gold/15 hover:bg-gold hover:text-canvas border border-gold/40 text-gold font-semibold text-xs flex items-center gap-1.5 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Gestionar Grimorio</span>
            </button>
          </div>
        </div>

        {/* Ranuras de Conjuro en Combate */}
        {Object.keys(spell_slots_total).length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Ranuras de Conjuro en Combate
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
              {Object.entries(spell_slots_total).map(([lvl, total]) => {
                const used = spell_slots_used[lvl] || 0;
                return (
                  <div
                    key={lvl}
                    className="bg-surface border border-border-iron/80 rounded-lg p-2 text-center"
                  >
                    <div className="text-[10px] font-semibold text-muted uppercase tracking-wider mb-1">
                      Nivel {lvl}
                    </div>
                    <div className="flex items-center justify-center gap-1.5">
                      {Array.from({ length: total }).map((_, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            const nextUsed = idx < used ? idx : idx + 1;
                            updateActiveCharacter({
                              spell_slots_used: {
                                ...spell_slots_used,
                                [lvl]: nextUsed,
                              },
                            });
                          }}
                          title={
                            idx < used
                              ? "Ranura Gastada (Clic para recuperar)"
                              : "Ranura Disponible (Clic para gastar)"
                          }
                          className={`w-3.5 h-3.5 rounded-full border transition-all ${
                            idx < used
                              ? "border-border-iron bg-card/60 opacity-30"
                              : "border-gold bg-gold shadow-[0_0_6px_rgba(201,164,92,0.4)]"
                          }`}
                        />
                      ))}
                    </div>
                    <div className="text-[10px] text-muted font-stat mt-1">
                      {total - used}/{total}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Filtros de Conjuro */}
        {spells.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border-iron/40">
            {/* Filtro por Nivel */}
            <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
              <button
                onClick={() => setSelectedSpellLevel("all")}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                  selectedSpellLevel === "all"
                    ? "bg-gold text-canvas"
                    : "bg-surface border border-border-iron text-muted hover:text-main"
                }`}
              >
                Todos
              </button>
              {Array.from(new Set(spells.map((s) => s.level)))
                .sort((a, b) => a - b)
                .map((lvl) => (
                  <button
                    key={lvl}
                    onClick={() => setSelectedSpellLevel(lvl)}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                      selectedSpellLevel === lvl
                        ? "bg-gold text-canvas"
                        : "bg-surface border border-border-iron text-muted hover:text-main"
                    }`}
                  >
                    {lvl === 0 ? "Trucos" : `Niv ${lvl}`}
                  </button>
                ))}
            </div>

            {/* Filtro por Acción */}
            <div className="flex items-center gap-1">
              {(
                [
                  { id: "all", label: "Cualquiera" },
                  { id: "action", label: "Acción" },
                  { id: "bonus", label: "Bonus" },
                  { id: "reaction", label: "Reacción" },
                ] as const
              ).map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedActionFilter(f.id)}
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                    selectedActionFilter === f.id
                      ? "bg-gold/20 text-gold border border-gold"
                      : "bg-surface border border-border-iron text-muted hover:text-main"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Listado de Tarjetas de Conjuros */}
        {spells.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {spells
              .filter((s) => {
                if (selectedSpellLevel !== "all" && s.level !== selectedSpellLevel) return false;
                if (selectedActionFilter !== "all") {
                  const ct = (s.cast_time || "").toLowerCase();
                  if (selectedActionFilter === "action" && !ct.includes("acción") && !ct.includes("action")) return false;
                  if (selectedActionFilter === "bonus" && !ct.includes("adicional") && !ct.includes("bonus")) return false;
                  if (selectedActionFilter === "reaction" && !ct.includes("reacción") && !ct.includes("reaction")) return false;
                }
                return true;
              })
              .map((spell: SpellItemData, sIdx: number) => {
                const isConcentration = (spell.duration || "").toLowerCase().includes("concentra");
                return (
                  <div
                    key={sIdx}
                    onClick={() => setActiveSpellForModal(spell)}
                    className="bg-surface border border-border-iron hover:border-gold rounded-lg p-3 flex flex-col justify-between space-y-2 cursor-pointer transition-all hover:scale-[1.01] group"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-1 mb-1">
                        <h4 className="font-semibold text-sm text-main group-hover:text-gold transition-colors truncate" title={spell.name}>
                          {spell.name}
                        </h4>
                        <span className="font-stat text-[10px] px-1.5 py-0.5 rounded bg-card border border-border-iron text-gold shrink-0">
                          {spell.level === 0 ? "Truco" : `Nivel ${spell.level}`}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-muted mb-1.5">
                        <span className="px-1.5 py-0.5 rounded bg-card/80 border border-border-iron">
                          {spell.cast_time}
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-card/80 border border-border-iron">
                          {spell.range_area}
                        </span>
                        {isConcentration && (
                          <span className="px-1.5 py-0.5 rounded bg-gold/15 text-gold border border-gold/40 font-semibold">
                            Concentración
                          </span>
                        )}
                      </div>

                      {spell.notes && (
                        <p className="text-xs text-muted/90 line-clamp-2 leading-tight">
                          {spell.notes}
                        </p>
                      )}
                    </div>

                    <div className="pt-2 border-t border-border-iron/40 flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
                      <span className="text-[10px] text-muted italic truncate max-w-[100px]">
                        {spell.school}
                      </span>
                      <button
                        onClick={() => setActiveSpellForModal(spell)}
                        className="px-3 py-1 rounded bg-crimson hover:bg-crimson-hover text-white text-xs font-semibold transition-colors shadow-xs"
                      >
                        {spell.level > 0 ? "Lanzar / Ver" : "Ver Truco"}
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        ) : (
          <div className="text-center py-8 text-muted text-xs bg-surface/50 rounded-lg border border-dashed border-border-iron p-6 space-y-3">
            <p className="text-sm font-semibold text-main">No hay conjuros registrados en el grimorio de este personaje.</p>
            <p className="text-xs text-muted max-w-md mx-auto">
              Puedes seleccionar y añadir conjuros oficiales de {char_class} o cualquier otra clase directamente desde la base de datos OKF.
            </p>
            <button
              onClick={() => setIsSpellManagerOpen(true)}
              className="px-4 py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs inline-flex items-center gap-2 shadow-sm transition-all active:scale-95"
            >
              <BookOpen className="w-4 h-4" />
              <span>Explorar y Añadir Conjuros desde el Compendio Oficial</span>
            </button>
          </div>
        )}
      </section>

      {/* Modales Interactivos Pop-Forward */}
      <FeatureDetailModal
        feature={activeFeatureForModal}
        isOpen={!!activeFeatureForModal}
        onClose={() => setActiveFeatureForModal(null)}
        onSpendUse={() => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            const next = [...(features || [])];
            const target = { ...next[idx] };
            const maxU = target.uses_max || 0;
            const curU = target.uses_current ?? maxU;
            if (curU > 0) {
              target.uses_current = curU - 1;
              next[idx] = target;
              updateActiveCharacter({ features: next });
              setActiveFeatureForModal(target);
              showToast(`1 uso de ${target.name} consumido`, "info");
            }
          }
        }}
        onRecoverUse={() => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            const next = [...(features || [])];
            const target = { ...next[idx] };
            const maxU = target.uses_max || 0;
            const curU = target.uses_current ?? 0;
            if (curU < maxU) {
              target.uses_current = curU + 1;
              next[idx] = target;
              updateActiveCharacter({ features: next });
              setActiveFeatureForModal(target);
              showToast(`1 uso de ${target.name} recuperado`, "info");
            }
          }
        }}
        onToggleUse={(slotIdx) => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            const next = [...(features || [])];
            const target = { ...next[idx] };
            const maxU = target.uses_max || 0;
            const curU = target.uses_current ?? maxU;
            const spentU = maxU - curU;
            const nextSpent = slotIdx < spentU ? slotIdx : slotIdx + 1;
            target.uses_current = Math.max(0, maxU - nextSpent);
            next[idx] = target;
            updateActiveCharacter({ features: next });
            setActiveFeatureForModal(target);
          }
        }}
        onRollDice={(formula, label) => {
          const match = formula.match(/(\d*)d(\d+)/i);
          if (match) {
            const cnt = parseInt(match[1] || "1", 10);
            const s = match[2];
            openDiceDrawer({ dice: { [s]: cnt }, label });
          }
        }}
      />

      <SpellDetailModal
        spell={activeSpellForModal}
        isOpen={!!activeSpellForModal}
        onClose={() => setActiveSpellForModal(null)}
        spellStats={spell_stats}
        spellSlotsTotal={spell_slots_total}
        spellSlotsUsed={spell_slots_used}
        onCastSpell={(slotLevel) => {
          if (!activeSpellForModal) return;
          if (slotLevel > 0) {
            const lvlStr = String(slotLevel);
            const total = spell_slots_total[lvlStr] || 0;
            const used = spell_slots_used[lvlStr] || 0;
            if (used >= total) {
              showToast(`No te quedan ranuras de nivel ${slotLevel}`, "warn");
              return;
            }
            updateActiveCharacter({
              spell_slots_used: {
                ...spell_slots_used,
                [lvlStr]: used + 1,
              },
            });
            showToast(`Lanzado: ${activeSpellForModal.name} (Ranura Nvl ${slotLevel})`, "success");
          } else {
            showToast(`Lanzado truco: ${activeSpellForModal.name}`, "success");
          }
          setActiveSpellForModal(null);
        }}
        onRollAttack={() => {
          if (!activeSpellForModal) return;
          openDiceDrawer({
            dice: { "20": 1 },
            modifier: spell_stats?.attack_bonus || 0,
            label: `Ataque Mágico: ${activeSpellForModal.name}`,
            dc: spell_stats?.dc,
          });
        }}
        onRollDamage={(formula, label) => {
          const match = formula.match(/(\d*)d(\d+)(?:\s*([+-]\s*\d+))?/i);
          if (match) {
            const cnt = parseInt(match[1] || "1", 10);
            const s = match[2];
            const mod = match[3] ? parseInt(match[3].replace(/\s+/g, ""), 10) : 0;
            openDiceDrawer({ dice: { [s]: cnt }, modifier: mod, label });
          }
        }}
      />

      <SpellBookManagerModal
        isOpen={isSpellManagerOpen}
        onClose={() => setIsSpellManagerOpen(false)}
        characterClass={char_class || "Bardo"}
        characterLevel={level || 1}
        currentSpells={spells || []}
        onAddSpell={addSpell}
        onRemoveSpell={removeSpell}
      />
    </div>
  );
};

