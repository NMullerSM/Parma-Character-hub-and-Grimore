import React, { useEffect } from "react";
import type { FeatureItemData } from "../api/types";
import { MarkdownViewer } from "./MarkdownViewer";
import { X, Dices, Copy, Check } from "lucide-react";

interface FeatureDetailModalProps {
  feature: FeatureItemData | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleUse?: (slotIndex: number) => void;
  onSpendUse?: () => void;
  onRecoverUse?: () => void;
  onRollDice?: (formula: string, label: string) => void;
}

export const FeatureDetailModal: React.FC<FeatureDetailModalProps> = ({
  feature,
  isOpen,
  onClose,
  onToggleUse,
  onSpendUse,
  onRecoverUse,
  onRollDice,
}) => {
  const [copiedTs, setCopiedTs] = React.useState(false);

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

  if (!isOpen || !feature) return null;

  const maxUses = feature.uses_max || 0;
  const currentUses = feature.uses_current ?? maxUses;
  const spentUses = maxUses - currentUses;

  // Extracción de dados en el título o descripción (ej: d6, 2d6, 3d6)
  const fullText = `${feature.name} ${feature.description}`;
  const diceMatch = fullText.match(/(\d*)d(4|6|8|10|12|20|100)/i);
  const diceFormula = diceMatch ? (diceMatch[1] ? `${diceMatch[1]}d${diceMatch[2]}` : `1d${diceMatch[2]}`) : null;
  const tsCommand = diceFormula ? `!${feature.name.split("(")[0].trim()}:${diceFormula}` : null;

  const handleCopyTs = () => {
    if (!tsCommand) return;
    navigator.clipboard.writeText(tsCommand);
    setCopiedTs(true);
    setTimeout(() => setCopiedTs(false), 2000);
  };

  const handleRoll = () => {
    if (diceFormula && onRollDice) {
      onRollDice(diceFormula, feature.name);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg bg-card border border-border-iron rounded-xl shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="flex items-start justify-between gap-3 border-b border-border-iron pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-surface border border-border-iron text-gold">
                {feature.source || "Rasgo Oficial"}
              </span>
              {feature.recharge && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border-iron text-muted">
                  Recarga: {feature.recharge === "SR" || feature.recharge === "Corto" ? "Descanso Corto" : feature.recharge === "Largo" ? "Descanso Largo" : feature.recharge}
                </span>
              )}
            </div>
            <h2 className="font-display font-bold text-xl text-gold">{feature.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contador de Usos */}
        {maxUses > 0 && (
          <div className="bg-surface/80 border border-border-iron rounded-lg p-3 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold text-main">Usos Disponibles</div>
              <div className="text-[11px] text-muted">
                {currentUses} de {maxUses} restantes
              </div>
            </div>

            <div className="flex items-center gap-1.5 flex-wrap">
              {Array.from({ length: maxUses }).map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => onToggleUse && onToggleUse(idx)}
                  title={`Ranura ${idx + 1}`}
                  className={`w-5 h-5 rounded-full border transition-all ${
                    idx < spentUses
                      ? "border-border-iron bg-card opacity-30 scale-90"
                      : "border-gold bg-gold shadow-[0_0_8px_rgba(201,164,92,0.4)]"
                  }`}
                />
              ))}
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={onSpendUse}
                disabled={currentUses <= 0}
                className="px-2.5 py-1 rounded bg-crimson/20 border border-crimson text-crimson hover:bg-crimson hover:text-white disabled:opacity-40 text-xs font-medium transition-colors"
              >
                Gastar
              </button>
              <button
                onClick={onRecoverUse}
                disabled={currentUses >= maxUses}
                className="px-2.5 py-1 rounded bg-surface border border-border-iron hover:border-gold text-main text-xs font-medium transition-colors"
              >
                Recuperar
              </button>
            </div>
          </div>
        )}

        {/* Cuerpo / Descripción */}
        <div className="text-sm text-main leading-relaxed max-h-64 overflow-y-auto pr-1">
          <MarkdownViewer content={feature.description} />
        </div>

        {/* Acciones de Tirada de Dados y TaleSpire */}
        {diceFormula && (
          <div className="pt-2 border-t border-border-iron/60 flex flex-col sm:flex-row items-center justify-between gap-2.5">
            <button
              onClick={handleRoll}
              className="w-full sm:w-auto px-4 py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-all active:scale-95"
            >
              <Dices className="w-4 h-4" />
              <span>Tirar {diceFormula} ({feature.name.split("(")[0].trim()})</span>
            </button>

            {tsCommand && (
              <button
                onClick={handleCopyTs}
                className="w-full sm:w-auto px-3 py-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main text-xs font-mono flex items-center justify-center gap-1.5 transition-colors"
                title="Copiar comando de chat de TaleSpire"
              >
                {copiedTs ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{tsCommand}</span>
              </button>
            )}
          </div>
        )}

        {/* Pie de modal */}
        <div className="pt-3 border-t border-border-iron flex justify-end">
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
