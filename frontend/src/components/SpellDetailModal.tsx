import React, { useState, useEffect } from "react";
import type { SpellItemData, SpellStatsData } from "../api/types";
import { MarkdownViewer } from "./MarkdownViewer";
import { X, Sparkles, Dices, Copy, Check } from "lucide-react";

interface SpellDetailModalProps {
  spell: SpellItemData | null;
  isOpen: boolean;
  onClose: () => void;
  spellStats?: SpellStatsData;
  spellSlotsTotal?: Record<string, number>;
  spellSlotsUsed?: Record<string, number>;
  onCastSpell?: (slotLevel: number) => void;
  onRollAttack?: () => void;
  onRollDamage?: (formula: string, label: string) => void;
}

export const SpellDetailModal: React.FC<SpellDetailModalProps> = ({
  spell,
  isOpen,
  onClose,
  spellStats,
  spellSlotsTotal = {},
  spellSlotsUsed = {},
  onCastSpell,
  onRollAttack,
  onRollDamage,
}) => {
  const [selectedSlotLevel, setSelectedSlotLevel] = useState<number>(1);
  const [copiedTs, setCopiedTs] = useState(false);

  useEffect(() => {
    if (spell) {
      setSelectedSlotLevel(Math.max(1, spell.level));
    }
  }, [spell]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !spell) return null;

  const isCantrip = spell.level === 0;
  const isConcentration =
    spell.concentration || (spell.duration || "").toLowerCase().includes("concentra");
  const isRitual =
    spell.ritual || (spell.notes || "").toLowerCase().includes("ritual");

  // Detección de daño
  const fullText = `${spell.name} ${spell.notes || ""} ${spell.description || ""}`;
  const dmgMatch = fullText.match(/(\d+)d(\d+)(?:\s*([+-]\s*\d+))?/i);
  const dmgFormula = dmgMatch
    ? `${dmgMatch[1]}d${dmgMatch[2]}${dmgMatch[3] ? `+${dmgMatch[3].replace(/\s+/g, "")}` : ""}`
    : null;

  const atkBonus = spellStats?.attack_bonus ?? 0;
  const atkBonusStr = atkBonus >= 0 ? `+${atkBonus}` : `${atkBonus}`;
  const tsCommand = isCantrip
    ? `!${spell.name}:1d20${atkBonusStr}`
    : dmgFormula
    ? `!${spell.name}:${dmgFormula}`
    : `!${spell.name}:1d20${atkBonusStr}`;

  const handleCopyTs = () => {
    navigator.clipboard.writeText(tsCommand);
    setCopiedTs(true);
    setTimeout(() => setCopiedTs(false), 2000);
  };

  const handleCast = () => {
    if (onCastSpell) {
      onCastSpell(isCantrip ? 0 : selectedSlotLevel);
    }
  };

  // Ranuras disponibles para escalado (nivel del conjuro hasta 9)
  const availableTiers = Object.keys(spellSlotsTotal)
    .map((k) => parseInt(k, 10))
    .filter((lvl) => lvl >= spell.level)
    .sort((a, b) => a - b);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-xl bg-card border border-border-iron rounded-xl shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="flex items-start justify-between gap-3 border-b border-border-iron pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-surface border border-border-iron text-gold">
                {isCantrip ? "Truco" : `Nivel ${spell.level}`}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border-iron text-muted">
                {spell.school}
              </span>
              {isConcentration && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-gold/15 text-gold border border-gold/40 font-semibold">
                  Concentración
                </span>
              )}
              {isRitual && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border-iron text-cyan-400">
                  Ritual
                </span>
              )}
            </div>
            <h2 className="font-display font-bold text-xl text-gold">{spell.name}</h2>
            {spell.name_en && spell.name_en !== spell.name && (
              <p className="text-xs text-muted italic">{spell.name_en}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Fila de Propiedades Canónicas */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-surface/70 p-3 rounded-lg border border-border-iron">
          <div>
            <span className="text-muted block text-[10px] uppercase">Tiempo:</span>
            <span className="font-medium text-main">{spell.cast_time || spell.casting_time || "1 acción"}</span>
          </div>
          <div>
            <span className="text-muted block text-[10px] uppercase">Alcance / Área:</span>
            <span className="font-medium text-main">{spell.range_area || spell.range || "18 m"}</span>
          </div>
          <div>
            <span className="text-muted block text-[10px] uppercase">Componentes:</span>
            <span className="font-medium text-main truncate block" title={spell.components}>
              {spell.components || "V, S"}
            </span>
          </div>
          <div>
            <span className="text-muted block text-[10px] uppercase">Duración:</span>
            <span className="font-medium text-main">{spell.duration || "Instantáneo"}</span>
          </div>
        </div>

        {/* CD de Salvación y Ataque Mágico */}
        {spellStats && (
          <div className="flex items-center justify-between text-xs px-3 py-1.5 rounded bg-surface/40 border border-border-iron/60 text-muted">
            <span>
              Aptitud Mágica: <strong className="text-main">{spellStats.ability}</strong>
            </span>
            <span>
              CD de Salvación: <strong className="text-gold">{spellStats.dc}</strong>
            </span>
            <span>
              Bono de Ataque: <strong className="text-gold">{atkBonusStr}</strong>
            </span>
          </div>
        )}

        {/* Descripción del Conjuro */}
        <div className="text-sm text-main leading-relaxed max-h-56 overflow-y-auto pr-1">
          <MarkdownViewer content={spell.description || spell.notes || "Sin descripción disponible."} />
          {spell.higher_levels && (
            <div className="mt-3 p-2.5 rounded bg-surface border border-border-iron text-xs">
              <span className="font-bold text-gold block mb-1">En Niveles Superiores:</span>
              <p className="text-muted">{spell.higher_levels}</p>
            </div>
          )}
        </div>

        {/* Selector de Escalado y Acciones de Combate */}
        <div className="pt-3 border-t border-border-iron space-y-3">
          {!isCantrip && availableTiers.length > 0 && (
            <div className="flex items-center justify-between gap-3 bg-surface p-2.5 rounded-lg border border-border-iron">
              <div className="text-xs">
                <span className="font-semibold text-main block">Nivel de Lanzamiento:</span>
                <span className="text-[10px] text-muted">Escala el efecto con ranuras mayores</span>
              </div>
              <div className="flex items-center gap-1.5">
                {availableTiers.map((lvl) => {
                  const total = spellSlotsTotal[String(lvl)] || 0;
                  const used = spellSlotsUsed[String(lvl)] || 0;
                  const remaining = Math.max(0, total - used);
                  return (
                    <button
                      key={lvl}
                      onClick={() => setSelectedSlotLevel(lvl)}
                      disabled={remaining <= 0}
                      className={`px-2.5 py-1 rounded text-xs font-stat transition-all ${
                        selectedSlotLevel === lvl
                          ? "bg-gold text-canvas font-bold shadow-sm"
                          : remaining > 0
                          ? "bg-card border border-border-iron text-main hover:border-gold"
                          : "bg-surface opacity-30 cursor-not-allowed text-muted"
                      }`}
                    >
                      Niv {lvl} ({remaining})
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Botones de Combate Táctico */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <button
                onClick={handleCast}
                className="px-4 py-2 rounded-lg bg-crimson hover:bg-crimson-hover text-white font-bold text-xs flex items-center gap-1.5 shadow-md transition-all active:scale-95"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isCantrip ? "Lanzar Truco" : `Lanzar (Ranura Niv ${selectedSlotLevel})`}</span>
              </button>

              {onRollAttack && (
                <button
                  onClick={onRollAttack}
                  className="px-3 py-2 rounded-lg bg-surface border border-border-iron hover:border-gold text-main font-semibold text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Dices className="w-3.5 h-3.5 text-gold" />
                  <span>Ataque ({atkBonusStr})</span>
                </button>
              )}

              {dmgFormula && onRollDamage && (
                <button
                  onClick={() => onRollDamage(dmgFormula, `Daño: ${spell.name}`)}
                  className="px-3 py-2 rounded-lg bg-surface border border-border-iron hover:border-gold text-main font-semibold text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Dices className="w-3.5 h-3.5 text-crimson" />
                  <span>Daño ({dmgFormula})</span>
                </button>
              )}
            </div>

            {/* Comando TaleSpire */}
            <button
              onClick={handleCopyTs}
              className="px-2.5 py-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main text-xs font-mono flex items-center gap-1 transition-colors"
              title="Copiar comando para chat de TaleSpire"
            >
              {copiedTs ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{tsCommand}</span>
            </button>
          </div>
        </div>

        {/* Pie */}
        <div className="pt-2 border-t border-border-iron flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-border-iron hover:border-gold text-xs text-muted hover:text-main transition-colors font-medium"
          >
            Cerrar (Esc)
          </button>
        </div>
      </div>
    </div>
  );
};
