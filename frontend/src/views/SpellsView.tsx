import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import type { SpellItemData } from "../api/types";

export const SpellsView: React.FC = () => {
  const { activeCharacter, updateActiveCharacter, openDiceDrawer } = useCharacter();
  const [selectedLevel, setSelectedLevel] = useState<number | "all">("all");

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">Selecciona un personaje para consultar su grimorio.</p>
      </div>
    );
  }

  const { spells, spell_slots_total, spell_slots_used } = activeCharacter;

  const handleToggleSlot = (lvl: string, index: number) => {
    const used = spell_slots_used[lvl] || 0;
    const nextUsed = index < used ? index : index + 1;
    updateActiveCharacter({
      spell_slots_used: {
        ...spell_slots_used,
        [lvl]: nextUsed,
      },
    });
  };

  const filteredSpells = (spells || []).filter((s) => {
    if (selectedLevel === "all") return true;
    return s.level === selectedLevel;
  });

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* 1. Header del Grimorio & Ranuras */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-iron pb-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">Grimorio & Ranuras de Conjuro</h1>
          <p className="text-xs text-muted">Gestiona tus hechizos preparados y el consumo de ranuras mágicas.</p>
        </div>

        {/* Filtro rápido por nivel */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setSelectedLevel("all")}
            className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
              selectedLevel === "all" ? "bg-gold text-canvas" : "bg-card text-muted hover:text-main"
            }`}
          >
            Todos
          </button>
          {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedLevel(lvl)}
              className={`px-2 py-1 rounded text-xs font-stat transition-colors ${
                selectedLevel === lvl ? "bg-gold text-canvas font-bold" : "bg-card text-muted hover:text-main"
              }`}
            >
              {lvl === 0 ? "Trucos" : `Nvl ${lvl}`}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Rastreador de Ranuras de Conjuro (Spell Slots) */}
      {spell_slots_total && Object.keys(spell_slots_total).length > 0 && (
        <section className="bg-card border border-border-iron rounded-xl p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Ranuras de Conjuro Disponibles</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {Object.entries(spell_slots_total).map(([lvl, total]) => {
              const used = spell_slots_used[lvl] || 0;
              return (
                <div key={lvl} className="bg-surface border border-border-iron/80 rounded-lg p-2.5 text-center">
                  <div className="text-[11px] font-semibold text-muted uppercase tracking-wider mb-1.5">
                    Nivel {lvl}
                  </div>
                  <div className="flex items-center justify-center gap-1.5">
                    {Array.from({ length: total }).map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleToggleSlot(lvl, idx)}
                        title={idx < used ? "Ranura Gastada (Clic para recuperar)" : "Ranura Disponible (Clic para gastar)"}
                        className={`w-4 h-4 rounded-full border transition-all ${
                          idx < used
                            ? "border-border-iron bg-card/60 opacity-40"
                            : "border-gold bg-gold shadow-[0_0_8px_rgba(201,164,92,0.4)]"
                        }`}
                      />
                    ))}
                  </div>
                  <div className="text-[10px] text-muted font-stat mt-1">
                    {total - used} de {total}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 3. Catálogo de Hechizos Preparados */}
      <section className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredSpells.length > 0 ? (
            filteredSpells.map((spell: SpellItemData, idx: number) => (
              <div
                key={idx}
                className="bg-card border border-border-iron rounded-lg p-4 space-y-2 hover:border-gold/60 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-main text-sm">{spell.name}</h3>
                    <p className="text-xs text-gold">
                      {spell.level === 0 ? "Truco" : `Nivel ${spell.level}`} • Escuela de {spell.school}
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      openDiceDrawer({
                        dice: { "20": 1 },
                        modifier: 0,
                        label: `Lanzar: ${spell.name}`,
                      })
                    }
                    className="px-2.5 py-1 rounded bg-surface hover:bg-gold hover:text-canvas border border-border-iron text-xs font-semibold text-muted transition-colors"
                  >
                    Lanzar
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-muted pt-1 border-t border-border-iron/40 font-stat">
                  <div>
                    <span className="font-medium text-main">Tiempo:</span> {spell.cast_time}
                  </div>
                  <div>
                    <span className="font-medium text-main">Alcance:</span> {spell.range_area}
                  </div>
                  <div>
                    <span className="font-medium text-main">Componentes:</span> {spell.components}
                  </div>
                  <div>
                    <span className="font-medium text-main">Duración:</span> {spell.duration}
                  </div>
                </div>

                {spell.notes && (
                  <p className="text-xs text-muted/90 pt-1 leading-relaxed bg-surface/40 p-2 rounded border border-border-iron/30">
                    {spell.notes}
                  </p>
                )}
              </div>
            ))
          ) : (
            <div className="col-span-2 bg-card border border-border-iron rounded-xl p-8 text-center text-muted text-sm">
              No hay conjuros que coincidan con el nivel seleccionado.
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
