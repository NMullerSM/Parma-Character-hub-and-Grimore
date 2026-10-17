import React from "react";
import { useCharacter } from "../context/CharacterContext";

export const CombatView: React.FC = () => {
  const { activeCharacter, updateActiveCharacter, performRestAction, openDiceDrawer } = useCharacter();

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">Selecciona un personaje para el modo combate táctico.</p>
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
    death_save_successes,
    death_save_failures,
    inspiration,
    weapon_actions,
  } = activeCharacter;

  const handleHpDelta = (delta: number) => {
    const next = Math.max(0, Math.min(hp_max + 100, hp_current + delta));
    updateActiveCharacter({ hp_current: next });
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

  const isDying = hp_current === 0;

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-6 max-w-5xl mx-auto">
      {/* 1. Header Táctico */}
      <div className="flex items-center justify-between border-b border-border-iron pb-3">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">{name} — Modo Combate</h1>
          <p className="text-xs text-muted">Nivel {level} {char_class} • CA {ac} • Velocidad {speed} pies</p>
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
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted mb-2">
            <span>Puntos de Golpe en Combate</span>
            <span>Máximo: {hp_max} PG</span>
          </div>

          <div className="flex items-center justify-center my-4 gap-4">
            <span
              className={`font-stat font-bold text-6xl md:text-7xl ${
                isDying ? "text-crimson animate-pulse" : hp_current <= hp_max / 2 ? "text-amber-400" : "text-main"
              }`}
            >
              {hp_current}
            </span>
            {hp_temp > 0 && (
              <span className="font-stat font-bold text-xl text-gold border border-gold/40 px-2 py-1 rounded">
                +{hp_temp} Temp
              </span>
            )}
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

        {/* Salvaciones de Muerte y Descansos */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* Salvaciones de Muerte */}
          <div className="bg-card border border-border-iron rounded-xl p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Salvaciones de Muerte</h3>
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
              onClick={() => openDiceDrawer({ dice: { "20": 1 }, modifier: 0, label: "Tirada de Salvación contra Muerte" })}
              className="w-full mt-3 py-1.5 rounded border border-border-iron hover:border-gold text-xs text-main bg-surface transition-colors font-medium"
            >
              Tirar Salvación de Muerte (1d20)
            </button>
          </div>

          {/* Descansos */}
          <div className="bg-card border border-border-iron rounded-xl p-4 space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-1">Descansos Tácticos</h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => performRestAction("short", 1)}
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

      {/* 3. Acciones de Ataque Rápido */}
      <section className="space-y-3">
        <h2 className="font-display font-semibold text-lg text-gold">Acciones Rápidas en Turno</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {weapon_actions?.map((w, idx) => (
            <div
              key={idx}
              onClick={() =>
                openDiceDrawer({
                  dice: { "20": 1 },
                  modifier: parseInt(w.hit_dc.replace("+", ""), 10) || 0,
                  label: `Ataque: ${w.name}`,
                })
              }
              className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.01]"
            >
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-semibold text-sm text-main">{w.name}</h4>
                <span className="font-stat font-bold text-xs text-gold">{w.hit_dc} impacto</span>
              </div>
              <p className="font-stat text-xs text-muted">{w.damage_dice} {w.damage_type}</p>
            </div>
          ))}

          {/* Acción Rápida de Iniciativa */}
          <div
            onClick={() => openDiceDrawer({ dice: { "20": 1 }, modifier: initiative, label: "Tirada de Iniciativa" })}
            className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.01] flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-sm text-main">Tirar Iniciativa</h4>
              <span className="font-stat font-bold text-xs text-gold">
                {initiative >= 0 ? `+${initiative}` : initiative}
              </span>
            </div>
            <p className="text-xs text-muted mt-1">Lanza 1d20 + Bono de Destreza al inicio del combate.</p>
          </div>
        </div>
      </section>
    </div>
  );
};
