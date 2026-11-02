import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import type { SpellItemData } from "../api/types";
import { BookOpen, Sparkles, Trash2 } from "lucide-react";
import { SpellDetailModal } from "../components/SpellDetailModal";
import { SpellBookManagerModal } from "../components/SpellBookManagerModal";
import {
  formatRangeWithTiles,
  formatDurationWithTurns,
} from "../utils/formatters";

export const SpellsView: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    openDiceDrawer,
    showToast,
    addSpell,
    removeSpell,
    language,
  } = useCharacter();

  const {
    t,
    translateSchool,
    translateSpellName,
    translateSpellDescription,
  } = useTranslation();

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
          {t("spells.noCharacter")}
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
      showToast(t("spells.spellNameRequired"), "warn");
      return;
    }
    const updatedSpells = [...spells, { ...newSpell, name: newSpell.name.trim() }];
    updateActiveCharacter({ spells: updatedSpells });
    setNewSpell({
      name: "",
      level: 0,
      school: "Evocación",
      cast_time: language === "en" ? "1 Action" : "1 Acción",
      range_area: language === "en" ? "60 ft" : "18 m",
      components: "V, S",
      duration: language === "en" ? "Instantaneous" : "Instantáneo",
      prepared: true,
      notes: "",
    });
    setIsAddingSpell(false);
    showToast(t("spells.spellAdded"), "success");
  };

  const filteredSpells = spells.filter((s) => {
    if (selectedLevel === "all") return true;
    return s.level === selectedLevel;
  });

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* 1. Header del Grimorio & Estadísticas Mágicas (Hick's Law Layout) */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-border-iron pb-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">
            {t("spells.title")}
          </h1>
          <p className="text-xs text-muted">
            {t("spells.subtitle")}
          </p>
        </div>

        {/* Barra de Estadísticas Mágicas y Acciones */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2 shrink-0">
            <div className="px-3 py-1.5 rounded-lg bg-card border border-border-iron text-center min-w-[70px]">
              <div className="text-[10px] uppercase text-muted font-semibold tracking-wider">{t("spells.spellcastingAbility")}</div>
              <div className="font-stat font-bold text-sm text-gold">
                {spell_stats?.ability || "INT"}
              </div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-card border border-border-iron text-center min-w-[70px]">
              <div className="text-[10px] uppercase text-muted font-semibold tracking-wider">{t("spells.spellSaveDc")}</div>
              <div className="font-stat font-bold text-sm text-main">{spell_stats?.dc ?? 10}</div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-card border border-border-iron text-center min-w-[70px]">
              <div className="text-[10px] uppercase text-muted font-semibold tracking-wider">{t("spells.spellAttackBonus")}</div>
              <div className="font-stat font-bold text-sm text-gold">
                {(spell_stats?.attack_bonus ?? 0) >= 0
                  ? `+${spell_stats?.attack_bonus ?? 0}`
                  : spell_stats?.attack_bonus}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 sm:border-l sm:border-border-iron sm:pl-2.5">
            <button
              id="tour-spell-manager"
              onClick={() => setIsSpellManagerOpen(true)}
              className="px-3 py-2 rounded-lg bg-gold/15 hover:bg-gold hover:text-canvas border border-gold/40 text-gold text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs whitespace-nowrap cursor-pointer"
            >
              <BookOpen className="w-4 h-4 shrink-0" />
              <span>{t("spells.openManager")}</span>
            </button>
            <button
              onClick={() => setIsAddingSpell(!isAddingSpell)}
              className="px-3 py-2 rounded-lg bg-surface hover:bg-card border border-border-iron text-xs font-semibold text-main transition-colors whitespace-nowrap cursor-pointer"
            >
              {isAddingSpell ? t("common.cancel") : t("spells.addCustomSpell")}
            </button>
          </div>
        </div>
      </div>

      {/* Formulario Desplegable para Agregar Conjuro Manual */}
      {isAddingSpell && (
        <section className="bg-card border border-border-iron rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
            {t("spells.addCustomSpell")}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.nameLabel")}</label>
              <input
                type="text"
                value={newSpell.name}
                onChange={(e) => setNewSpell({ ...newSpell, name: e.target.value })}
                placeholder="Bola de Fuego / Fireball"
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.levelLabel")}</label>
              <select
                value={newSpell.level}
                onChange={(e) => setNewSpell({ ...newSpell, level: parseInt(e.target.value, 10) })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              >
                <option value={0}>{t("spells.filterCantrips")}</option>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
                  <option key={lvl} value={lvl}>
                    {t("spells.slotLevel", { lvl })}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.schoolLabel")}</label>
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
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.castTimeLabel")}</label>
              <input
                type="text"
                value={newSpell.cast_time}
                onChange={(e) => setNewSpell({ ...newSpell, cast_time: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.rangeLabel")}</label>
              <input
                type="text"
                value={newSpell.range_area}
                onChange={(e) => setNewSpell({ ...newSpell, range_area: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.durationLabel")}</label>
              <input
                type="text"
                value={newSpell.duration}
                onChange={(e) => setNewSpell({ ...newSpell, duration: e.target.value })}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
              />
            </div>
          </div>
          <div>
            <label className="block text-[11px] uppercase text-muted mb-1">{t("spells.notesLabel")}</label>
            <input
              type="text"
              value={newSpell.notes}
              onChange={(e) => setNewSpell({ ...newSpell, notes: e.target.value })}
              placeholder="Ej: 8d6 fire damage / Daño por fuego"
              className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={() => setIsAddingSpell(false)}
              className="px-3 py-1.5 rounded border border-border-iron text-xs text-muted hover:text-main"
            >
              {t("common.cancel")}
            </button>
            <button
              onClick={handleAddSpell}
              className="px-4 py-1.5 rounded bg-crimson text-white text-xs font-semibold"
            >
              {t("spells.saveSpell")}
            </button>
          </div>
        </section>
      )}

      {/* 2. Rastreador de Ranuras de Conjuro (Spell Slots) */}
      {hasSlots && (
        <section id="tour-spell-slots" className="bg-card border border-border-iron rounded-xl p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
            {t("spells.slotsTitle")}
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
                    {t("spells.slotLevel", { lvl })}
                  </div>
                  <div className="flex items-center justify-center gap-1.5">
                    {Array.from({ length: total }).map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleToggleSlot(lvl, idx)}
                        className={`w-4 h-4 rounded-full border transition-all ${
                          idx < used
                            ? "border-border-iron bg-card/60 opacity-40"
                            : "border-gold bg-gold shadow-[0_0_8px_rgba(201,164,92,0.4)]"
                        }`}
                      />
                    ))}
                  </div>
                  <div className="text-[10px] text-muted font-stat mt-1">
                    {total - used} / {total}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Filtro rápido por nivel */}
      <div id="tour-spell-filters" className="flex items-center gap-1 overflow-x-auto pb-1">
        <button
          onClick={() => setSelectedLevel("all")}
          className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
            selectedLevel === "all"
              ? "bg-gold text-canvas"
              : "bg-card text-muted hover:text-main"
          }`}
        >
          {t("spells.filterAll")} ({spells.length})
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
            {lvl === 0 ? t("spells.filterCantrips") : `${t("combat.levelShort")} ${lvl}`}
          </button>
        ))}
      </div>

      {/* 3. Catálogo de Hechizos */}
      <section className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredSpells.length > 0 ? (
            filteredSpells.map((spell: SpellItemData, idx: number) => {
              const spellDisplayName = (language === "en" && spell.name_en && spell.name_en !== spell.name)
                ? spell.name_en
                : translateSpellName(spell.name);
              return (
                <div
                  key={idx}
                  onClick={() => setActiveSpellForModal(spell)}
                  className="bg-card border border-border-iron rounded-lg p-4 space-y-2 hover:border-gold cursor-pointer transition-all hover:scale-[1.01] hover:shadow-[0_4px_16px_rgba(201,164,92,0.15)] group relative"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-main text-sm group-hover:text-gold transition-colors flex items-center gap-1.5">
                        {spellDisplayName}
                        <Sparkles className="w-3 h-3 text-gold/60 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </h3>
                      <p className="text-xs text-gold">
                        {spell.level === 0 ? t("spells.filterCantrips") : `${t("combat.levelShort")} ${spell.level}`} •{" "}
                        {translateSchool(spell.school)}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => {
                          const updated = spells.map((s, i) =>
                            i === idx ? { ...s, prepared: !s.prepared } : s
                          );
                          updateActiveCharacter({ spells: updated });
                        }}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                          spell.prepared
                            ? "bg-gold text-canvas"
                            : "bg-surface border border-border-iron text-muted"
                        }`}
                      >
                        {spell.prepared ? t("spells.preparedBadge") : t("spells.unpreparedBadge")}
                      </button>
                      <button
                        onClick={() => {
                          removeSpell(spell.name);
                        }}
                        className="p-1 rounded text-muted hover:text-crimson hover:bg-surface transition-colors"
                        title={t("common.delete")}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-1 text-[11px] text-muted pt-1 border-t border-border-iron/40">
                    <div>
                      <span className="font-medium text-main">{t("spells.castTimeLabel")}:</span>{" "}
                      {spell.cast_time || (language === "en" ? "1 Action" : "1 Acción")}
                    </div>
                    <div>
                      <span className="font-medium text-main">{t("spells.rangeLabel")}:</span>{" "}
                      {formatRangeWithTiles(spell.range_area, language)}
                    </div>
                    <div>
                      <span className="font-medium text-main">{t("spells.durationLabel")}:</span>{" "}
                      {formatDurationWithTurns(spell.duration, language)}
                    </div>
                  </div>

                  {translateSpellDescription(spell, language) && (
                    <p className="text-xs text-muted/90 line-clamp-2 leading-relaxed pt-1">
                      {translateSpellDescription(spell, language)}
                    </p>
                  )}
                </div>
              );
            })
          ) : (
            <div className="col-span-2 bg-card border border-border-iron rounded-lg p-6 text-center text-xs text-muted">
              {t("spells.noSpellsFound")}
            </div>
          )}
        </div>
      </section>

      {/* Modales */}
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
              showToast(t("combat.noSpells"), "warn");
              return;
            }
            updateActiveCharacter({
              spell_slots_used: {
                ...spell_slots_used,
                [lvlStr]: used + 1,
              },
            });
            showToast(t("combat.spellSlotUsed", { lvl: slotLevel }), "success");
          } else {
            showToast(activeSpellForModal.name, "success");
          }
          setActiveSpellForModal(null);
        }}
        onRollAttack={() => {
          if (!activeSpellForModal) return;
          openDiceDrawer({
            dice: { "20": 1 },
            modifier: spell_stats?.attack_bonus || 0,
            label: `${t("spells.spellAttackBonus")}: ${activeSpellForModal.name}`,
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
