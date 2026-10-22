import React, { useEffect, useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";

interface DieSvgProps {
  sides: number;
  roll: number;
  isNat20: boolean;
  isNat1: boolean;
}

const PolyhedralDieSvg: React.FC<DieSvgProps> = ({ sides, roll, isNat20, isNat1 }) => {
  // Colores reactivos según resultado crítico / pifia / normal
  const strokeColor = isNat20 ? "#34d399" : isNat1 ? "#e63946" : sides === 20 ? "#79c0ff" : "currentColor";
  const fillColor = isNat20 ? "rgba(6, 78, 59, 0.75)" : isNat1 ? "rgba(127, 29, 29, 0.7)" : "var(--bg-card, #1c242c)";
  const textColor = isNat20 ? "#a7f3d0" : isNat1 ? "#fca5a5" : "var(--text-main, #f0f4f8)";

  switch (sides) {
    case 4:
      // d4: Tetraedro triangular
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-md">
          <polygon points="50,10 90,85 10,85" fill={fillColor} stroke={strokeColor} strokeWidth="3" strokeLinejoin="round" />
          <line x1="50" y1="10" x2="50" y2="85" stroke={strokeColor} strokeWidth="1.5" strokeDasharray="2,2" opacity="0.6" />
          <text x="50" y="65" textAnchor="middle" fill={textColor} fontSize="28" fontWeight="bold" fontFamily="Space Grotesk, sans-serif">
            {roll}
          </text>
        </svg>
      );

    case 6:
      // d6: Cubo redondeado facetado
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-md">
          <rect x="15" y="15" width="70" height="70" rx="14" fill={fillColor} stroke={strokeColor} strokeWidth="3" />
          <circle cx="28" cy="28" r="3" fill={strokeColor} opacity="0.4" />
          <circle cx="72" cy="72" r="3" fill={strokeColor} opacity="0.4" />
          <text x="50" y="60" textAnchor="middle" fill={textColor} fontSize="32" fontWeight="bold" fontFamily="Space Grotesk, sans-serif">
            {roll}
          </text>
        </svg>
      );

    case 8:
      // d8: Octaedro en rombo diamante
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-md">
          <polygon points="50,8 88,50 50,92 12,50" fill={fillColor} stroke={strokeColor} strokeWidth="3" strokeLinejoin="round" />
          <line x1="12" y1="50" x2="88" y2="50" stroke={strokeColor} strokeWidth="1.5" opacity="0.5" />
          <text x="50" y="58" textAnchor="middle" fill={textColor} fontSize="26" fontWeight="bold" fontFamily="Space Grotesk, sans-serif">
            {roll}
          </text>
        </svg>
      );

    case 10:
    case 100:
      // d10 / d100: Cometa facetada
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-md">
          <polygon points="50,6 88,38 72,88 28,88 12,38" fill={fillColor} stroke={strokeColor} strokeWidth="3" strokeLinejoin="round" />
          <line x1="50" y1="6" x2="50" y2="88" stroke={strokeColor} strokeWidth="1.5" opacity="0.4" />
          <line x1="12" y1="38" x2="50" y2="52" stroke={strokeColor} strokeWidth="1.2" opacity="0.5" />
          <line x1="88" y1="38" x2="50" y2="52" stroke={strokeColor} strokeWidth="1.2" opacity="0.5" />
          <text x="50" y="66" textAnchor="middle" fill={textColor} fontSize="24" fontWeight="bold" fontFamily="Space Grotesk, sans-serif">
            {sides === 100 && roll === 0 ? "00" : roll}
          </text>
        </svg>
      );

    case 12:
      // d12: Dodecaedro pentagonal
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-md">
          <polygon points="50,8 88,24 96,66 64,94 36,94 4,66 12,24" fill={fillColor} stroke={strokeColor} strokeWidth="2.5" strokeLinejoin="round" />
          <polygon points="50,26 76,46 66,74 34,74 24,46" fill="none" stroke={strokeColor} strokeWidth="1.2" opacity="0.45" />
          <text x="50" y="60" textAnchor="middle" fill={textColor} fontSize="25" fontWeight="bold" fontFamily="Space Grotesk, sans-serif">
            {roll}
          </text>
        </svg>
      );

    case 20:
    default:
      // d20: Icosaedro triangular con facetas completas
      return (
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-lg">
          {/* Contorno exterior */}
          <polygon points="50,6 90,30 90,75 50,96 10,75 10,30" fill={fillColor} stroke={strokeColor} strokeWidth="3" strokeLinejoin="round" />
          {/* Faceta central */}
          <polygon points="50,22 80,68 20,68" fill="rgba(121, 192, 255, 0.08)" stroke={strokeColor} strokeWidth="1.6" />
          {/* Aristas hacia vértices exteriores */}
          <line x1="50" y1="6" x2="50" y2="22" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />
          <line x1="90" y1="30" x2="50" y2="22" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />
          <line x1="10" y1="30" x2="50" y2="22" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />
          <line x1="90" y1="75" x2="80" y2="68" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />
          <line x1="10" y1="75" x2="20" y2="68" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />
          <line x1="50" y1="96" x2="50" y2="68" stroke={strokeColor} strokeWidth="1.4" opacity="0.6" />

          {/* Número destacado */}
          <text
            x="50"
            y="57"
            textAnchor="middle"
            fill={textColor}
            fontSize="26"
            fontWeight="bold"
            fontFamily="Space Grotesk, sans-serif"
          >
            {roll}
          </text>
        </svg>
      );
  }
};

export const DiceRollAnimation: React.FC = () => {
  const { isRollingAnimation, currentRollingData } = useCharacter();
  const { t } = useTranslation();
  const [animState, setAnimState] = useState<"launch" | "settle">("launch");

  useEffect(() => {
    if (isRollingAnimation) {
      setAnimState("launch");
      const timer = setTimeout(() => {
        setAnimState("settle");
      }, 550);
      return () => clearTimeout(timer);
    }
  }, [isRollingAnimation]);

  if (!isRollingAnimation || !currentRollingData) return null;

  const { dice_rolls, total, label, modifier } = currentRollingData;
  const displayLabel = label === "Tirada Rápida" || label === "Quick Roll" ? t("dice.quickRoll") : label;

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4">
      {/* Fondo con viñeta cinematográfica */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300" />

      {/* Contenedor Central de Lanzamiento */}
      <div className="relative z-10 flex flex-col items-center gap-5 max-w-2xl w-full">
        {/* Motivo de la tirada */}
        <div className="px-5 py-1.5 rounded-full bg-surface/95 border border-border-iron shadow-xl text-xs font-semibold text-gold tracking-wider uppercase animate-in fade-in duration-300">
          {displayLabel}
        </div>

        {/* Mesa de Dados: Dispersión limpia sin colisiones ni superposiciones */}
        <div className="flex flex-wrap items-center justify-center gap-4 md:gap-5 min-h-[90px] w-full px-4">
          {dice_rolls.map((r, i) => {
            const rot = ((i * 37 + 13) % 40) - 20; // Ángulo aleatorio suave (-20deg a +20deg)
            const isNat20 = r.sides === 20 && r.roll === 20;
            const isNat1 = r.sides === 20 && r.roll === 1;

            return (
              <div
                key={i}
                className="relative flex flex-col items-center justify-center w-14 h-14 md:w-16 md:h-16 transition-all duration-600 ease-out select-none"
                style={{
                  transform:
                    animState === "launch"
                      ? `translateY(220px) scale(0.35) rotate(${rot * 4}deg)`
                      : `translateY(0px) scale(1) rotate(${rot}deg)`,
                  filter: isNat20
                    ? "drop-shadow(0 0 16px rgba(16, 185, 129, 0.9))"
                    : isNat1
                    ? "drop-shadow(0 0 16px rgba(230, 57, 70, 0.9))"
                    : r.sides === 20
                    ? "drop-shadow(0 0 10px rgba(121, 192, 255, 0.45))"
                    : "drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5))",
                }}
              >
                <PolyhedralDieSvg sides={r.sides} roll={r.roll} isNat20={isNat20} isNat1={isNat1} />

                {/* Etiqueta del dado */}
                <span className="absolute -bottom-2 text-[9px] font-stat font-bold uppercase text-muted tracking-wider bg-card/90 px-1 rounded border border-border-iron/60">
                  d{r.sides}
                </span>
              </div>
            );
          })}
        </div>

        {/* Total Final Iluminado */}
        <div
          className={`flex items-center gap-3 px-6 py-2.5 rounded-2xl bg-surface/95 border-2 border-gold shadow-[0_0_35px_rgba(121,192,255,0.4)] transition-all duration-500 ${
            animState === "settle" ? "scale-100 opacity-100 translate-y-0" : "scale-80 opacity-0 translate-y-4"
          }`}
        >
          <span className="text-xs font-semibold uppercase text-muted tracking-wider">{t("dice.total")}</span>
          <span className="font-stat font-bold text-4xl md:text-5xl text-gold">{total}</span>
          {modifier !== 0 && (
            <span className="text-xs font-stat text-muted">
              ({modifier > 0 ? `+${modifier}` : modifier} mod)
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
