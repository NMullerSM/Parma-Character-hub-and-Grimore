import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import type { SpellItemData } from "../api/types";
import { X, BookOpen, Sparkles } from "lucide-react";
import { SpellDetailModal } from "../components/SpellDetailModal";
import { SpellBookManagerModal } from "../components/SpellBookManagerModal";

export const SpellsView: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    openDiceDrawer,
    showToast,
    addSpell,
    removeSpell,
  } = useCharacter();
  const [selectedLevel, setSelectedLevel] = useState<number | "all">("all");
  const [isAddingSpell, setIsAddingSpell] = useState<boolean>(false);
  const [isSpellManagerOpen, setIsSpellManagerOpen] = useState<boolean>(false);
  const [activeSpellForModal, setActiveSpellForModal] = useState<SpellItemData | null>(null);
  const [newSpell, setNewSpell] = useState<SpellItemData>({
    name: "",
    level: 0,
    school: "Evocación",
    cast_time: "1 Acción",
    range_area: "60 pies",
    components: "V, S",
    duration: "Instantáneo",
    prepared: true,
    notes: "",
  });

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">
          Selecciona un personaje para consultar su grimorio.
        </p>
      </div>
    );
  }

  const {
    spells = [],
    spell_slots_total = {},
    spell_slots_used = {},
    spell_stats,
    char_class,
    level,
  } = activeCharacter;

  const hasSlots = Object.keys(spell_slots_total).length > 0;
  const isCaster = spell_stats?.is_caster || hasSlots || spells.length > 0;

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

  const handleAddSpell = () => {
    if (!newSpell.name.trim()) {
      showToast("Ingresa el nombre del conjuro", "warn");
      return;
    }
    const updatedSpells = [...spells, { ...newSpell, name: newSpell.name.trim() }];
    updateActiveCharacter({ spells: updatedSpells });
    setNewSpell({
      name: "",
      level: 0,
      school: "Evocación",
      cast_time: "1 Acción",
      range_area: "60 pies",
      components: "V, S",
      duration: "Instantáneo",
      prepared: true,
      notes: "",
    });
    setIsAddingSpell(false);
    showToast("Conjuro añadido al grimorio", "success");
  };


  const filteredSpells = spells.filter((s) => {
    if (selectedLevel === "all") return true;
    return s.level === selectedLevel;
  });

  // Ley de Hick: Si la clase es puramente marcial y no posee conjuros, mostrar vista sintetizada limpia
  if (!isCaster && !isAddingSpell) {
    return (
      <div className="h-full flex items-center justify-center p-8 max-w-xl mx-auto text-center">
        <div className="bg-card border border-border-iron rounded-xl p-6 space-y-3">
          <h2 className="font-display font-bold text-xl text-gold">
            Clase Marcial ({char_class})
          </h2>
          <p className="text-xs text-muted leading-relaxed">
            Este personaje no utiliza lanzamiento de conjuros por clase actualmente. Si obtuvo un
            conjuro innato por Especie o Dote (como Iniciado en la Magia), puedes buscarlo en el
            compendio o registrarlo manualmente.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <button
              onClick={() => setIsSpellManagerOpen(true)}
              className="px-4 py-2 rounded bg-gold text-canvas hover:bg-gold-hover text-xs font-bold transition-colors inline-flex items-center gap-1.5"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Explorar Compendio OKF
            </button>
            <button
              onClick={() => setIsAddingSpell(true)}
              className="px-4 py-2 rounded bg-surface hover:bg-gold hover:text-canvas border border-gold text-gold text-xs font-semibold transition-colors"
            >
              + Manual
            </button>
          </div>
        </div>
      </div>
    );
  }

  const spellAttackBonus = spell_stats?.attack_bonus ?? 0;
  const spellSaveDc = spell_stats?.dc ?? 10;
  const spellAbility = spell_stats?.ability || "INT";

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* 1. Header del Grimorio & Estadísticas Mágicas */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-iron pb-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">
            Grimorio & Ranuras de Conjuro
          </h1>
          <p className="text-xs text-muted">
            Gestiona tus hechizos preparados, consulta el compendio 5e SRD y usa ranuras mágicas.
          </p>
        </div>

        {/* Estadísticas de Lanzamiento de Conjuros (Aptitud, CD, Ataque Mágico) */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="px-3 py-1.5 rounded bg-card border border-border-iron text-center">
            <div className="text-[10px] uppercase text-muted font-semibold">Aptitud Mágica</div>
            <div className="font-stat font-bold text-sm text-gold">{spellAbility}</div>
          </div>
          <div className="px-3 py-1.5 rounded bg-card border border-border-iron text-center">
            <div className="text-[10px] uppercase text-muted font-semibold">CD Salvación</div>
            <div className="font-stat font-bold text-sm text-main">{spellSaveDc}</div>
          </div>
          <button
            onClick={() =>
              openDiceDrawer({
                dice: { "20": 1 },
                modifier: spellAttackBonus,
                label: "Ataque de Conjuro",
              })
            }
            className="px-3 py-1.5 rounded bg-card hover:border-gold border border-border-iron text-center transition-colors"
            title="Clic para tirar Ataque de Conjuro (1d20)"
          >
            <div className="text-[10px] uppercase text-muted font-semibold">Ataque Mágico</div>
            <div className="font-stat font-bold text-sm text-gold">
              {spellAttackBonus >= 0 ? `+${spellAttackBonus}` : spellAttackBonus}
            </div>
          </button>
          
          <button
            onClick={() => setIsSpellManagerOpen(true)}
            className="px-3 py-2 rounded bg-gold hover:bg-gold-hover text-canvas text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-[0_0_8px_rgba(201,164,92,0.3)]"
            title="Buscar y añadir conjuros oficiales del Compendio SRD"
          >
            <BookOpen className="w-3.5 h-3.5" />
            + Compendio OKF
          </button>
          <button
            onClick={() => setIsAddingSpell(true)}
            className="px-3 py-2 rounded bg-surface border border-border-iron hover:border-gold text-muted hover:text-main text-xs font-medium transition-colors"
          >
            + Manual
          </button>
        </div>
      </div>

      {/* Modal / Formulario de Nuevo Conjuro con Salida Clara */}
      {isAddingSpell && (
        <section className="bg-card border border-gold rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-iron pb-2">
            <h3 className="font-display font-bold text-base text-gold">Añadir Conjuro al Grimorio</h3>
            <button
              onClick={() => setIsAddingSpell(false)}
              className="p-1 text-muted hover:text-main"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-[11px] uppercase text-muted mb-1">Nombre</label>
              <input
                type="text"
                value={newSpell.name}
                onChange={(e) => setNewSpell({ ...newSpell, name: e.target.value })}
                placeholder="Ej: Bola de Fuego"
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">Nivel (0=Truco)</label>
              <input
                type="number"
                min={0}
                max={9}
                value={newSpell.level}
                onChange={(e) =>
                  setNewSpell({
                    ...newSpell,
                    level: Math.max(0, Math.min(9, parseInt(e.target.value, 10) || 0)),
                  })
                }
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs font-stat focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">Escuela</label>
              <input
                type="text"
                value={newSpell.school}
                onChange={(e) => setNewSpell({ ...newSpell, school: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">Tiempo</label>
              <input
                type="text"
                value={newSpell.cast_time}
                onChange={(e) => setNewSpell({ ...newSpell, cast_time: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">Alcance</label>
              <input
                type="text"
                value={newSpell.range_area}
                onChange={(e) => setNewSpell({ ...newSpell, range_area: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">Duración</label>
              <input
                type="text"
                value={newSpell.duration}
                onChange={(e) => setNewSpell({ ...newSpell, duration: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
          </div>
          <div>
            <label className="block text-[11px] uppercase text-muted mb-1">Efecto / Notas</label>
            <input
              type="text"
              value={newSpell.notes}
              onChange={(e) => setNewSpell({ ...newSpell, notes: e.target.value })}
              placeholder="Ej: 8d6 daño por fuego en radio de 20 pies (Salv. DES mitad)."
              className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={() => setIsAddingSpell(false)}
              className="px-3 py-1.5 rounded border border-border-iron text-xs text-muted hover:text-main"
            >
              Cancelar
            </button>
            <button
              onClick={handleAddSpell}
              className="px-4 py-1.5 rounded bg-crimson text-white text-xs font-semibold"
            >
              Guardar Conjuro
            </button>
          </div>
        </section>
      )}

      {/* 2. Rastreador de Ranuras de Conjuro (Spell Slots) */}
      {hasSlots && (
        <section className="bg-card border border-border-iron rounded-xl p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
            Ranuras de Conjuro Disponibles
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {Object.entries(spell_slots_total).map(([lvl, total]) => {
              const used = spell_slots_used[lvl] || 0;
              return (
                <div
                  key={lvl}
                  className="bg-surface border border-border-iron/80 rounded-lg p-2.5 text-center"
                >
                  <div className="text-[11px] font-semibold text-muted uppercase tracking-wider mb-1.5">
                    Nivel {lvl}
                  </div>
                  <div className="flex items-center justify-center gap-1.5">
                    {Array.from({ length: total }).map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleToggleSlot(lvl, idx)}
                        title={
                          idx < used
                            ? "Ranura Gastada (Clic para recuperar)"
                            : "Ranura Disponible (Clic para gastar)"
                        }
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

      {/* Filtro rápido por nivel */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        <button
          onClick={() => setSelectedLevel("all")}
          className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
            selectedLevel === "all"
              ? "bg-gold text-canvas"
              : "bg-card text-muted hover:text-main"
          }`}
        >
          Todos ({spells.length})
        </button>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
          <button
            key={lvl}
            onClick={() => setSelectedLevel(lvl)}
            className={`px-2 py-1 rounded text-xs font-stat transition-colors ${
              selectedLevel === lvl
                ? "bg-gold text-canvas font-bold"
                : "bg-card text-muted hover:text-main"
            }`}
          >
            {lvl === 0 ? "Trucos" : `Nvl ${lvl}`}
          </button>
        ))}
      </div>

      {/* 3. Catálogo de Hechizos Preparados */}
      <section className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredSpells.length > 0 ? (
            filteredSpells.map((spell: SpellItemData, idx: number) => (
              <div
                key={idx}
                onClick={() => setActiveSpellForModal(spell)}
                className="bg-card border border-border-iron rounded-lg p-4 space-y-2 hover:border-gold cursor-pointer transition-all hover:scale-[1.01] hover:shadow-[0_4px_16px_rgba(201,164,92,0.15)] group relative"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-main text-sm group-hover:text-gold transition-colors flex items-center gap-1.5">
                      {spell.name}
                      <Sparkles className="w-3 h-3 text-gold/60 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </h3>
                    <p className="text-xs text-gold">
                      {spell.level === 0 ? "Truco" : `Nivel ${spell.level}`} • Escuela de{" "}
                      {spell.school}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setActiveSpellForModal(spell)}
                      className="px-2.5 py-1 rounded bg-surface hover:bg-gold hover:text-canvas border border-border-iron text-xs font-semibold text-muted transition-colors"
                      title="Abrir ficha detallada (Pop-forward)"
                    >
                      Ver / Lanzar
                    </button>
                    <button
                      onClick={() => removeSpell(spell.name)}
                      className="p-1 text-muted hover:text-crimson transition-colors"
                      title="Eliminar conjuro del grimorio"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
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
                  <p className="text-xs text-muted/90 pt-1 leading-relaxed bg-surface/40 p-2 rounded border border-border-iron/30 line-clamp-2">
                    {spell.notes}
                  </p>
                )}
              </div>
            ))
          ) : (
            <div className="col-span-2 bg-card border border-border-iron rounded-xl p-8 text-center text-muted text-sm space-y-3">
              <p>No hay conjuros que coincidan con el nivel seleccionado.</p>
              <button
                onClick={() => setIsSpellManagerOpen(true)}
                className="px-4 py-2 rounded bg-gold text-canvas hover:bg-gold-hover text-xs font-bold inline-flex items-center gap-1.5"
              >
                <BookOpen className="w-3.5 h-3.5" />
                Abrir Compendio Mágico SRD
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Modales Pop-Forward & Compendio */}
      <SpellDetailModal
        spell={activeSpellForModal}
        isOpen={!!activeSpellForModal}
        onClose={() => setActiveSpellForModal(null)}
        spellStats={spell_stats}
        spellSlotsTotal={spell_slots_total}
        spellSlotsUsed={spell_slots_used}
        onCastSpell={(slotLevel: number) => {
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
        characterClass={char_class}
        characterLevel={level}
        currentSpells={spells}
        onAddSpell={addSpell}
        onRemoveSpell={removeSpell}
      />
    </div>
  );
};
