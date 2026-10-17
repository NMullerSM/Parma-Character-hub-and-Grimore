import React, { useEffect, useState } from "react";
import { useCharacter } from "../context/CharacterContext";

export const DiceRollAnimation: React.FC = () => {
  const { isRollingAnimation, currentRollingData } = useCharacter();
  const [animState, setAnimState] = useState<"launch" | "settle">("launch");

  useEffect(() => {
    if (isRollingAnimation) {
      setAnimState("launch");
      const timer = setTimeout(() => {
        setAnimState("settle");
      }, 700);
      return () => clearTimeout(timer);
    }
  }, [isRollingAnimation]);

  if (!isRollingAnimation || !currentRollingData) return null;

  const { dice_rolls, total, label, modifier } = currentRollingData;

  // Renderizador de forma geométrica del dado según lados
  const renderDieShape = (sides: number, roll: number, index: number) => {
    // Desfase aleatorio para dispersión realista
    const rot = ((index * 47) % 70) - 35;
    const offsetX = ((index * 60) % 180) - 90;

    let shapeClasses = "rounded-lg border-2";
    let badgeLabel = `d${sides}`;

    if (sides === 20) {
      shapeClasses = "rounded-xl border-2 border-gold shadow-[0_0_20px_rgba(121,192,255,0.4)]";
    } else if (sides === 6) {
      shapeClasses = "rounded-md border-2 border-border-iron";
    } else if (sides === 100) {
      shapeClasses = "rounded-full border-2 border-crimson";
    }

    const isNat20 = sides === 20 && roll === 20;
    const isNat1 = sides === 20 && roll === 1;

    return (
      <div
        key={index}
        className={`relative flex flex-col items-center justify-center w-16 h-16 md:w-20 md:h-20 bg-card/95 transition-all duration-700 ${shapeClasses} ${
          isNat20
            ? "border-emerald-400 bg-emerald-950/60 shadow-[0_0_25px_rgba(16,185,129,0.7)]"
            : isNat1
            ? "border-crimson bg-crimson/20 shadow-[0_0_25px_rgba(230,57,70,0.7)]"
            : ""
        }`}
        style={{
          transform:
            animState === "launch"
              ? `translateY(160px) scale(0.6) rotate(${rot * 3}deg)`
              : `translateY(0px) translateX(${offsetX}px) scale(1) rotate(${rot}deg)`,
        }}
      >
        <span className="absolute top-1 text-[9px] uppercase font-stat font-bold text-muted/70 tracking-widest">
          {badgeLabel}
        </span>
        <span
          className={`font-stat font-bold text-2xl md:text-3xl mt-2 ${
            isNat20 ? "text-emerald-300" : isNat1 ? "text-crimson" : "text-main"
          }`}
        >
          {roll}
        </span>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center">
      {/* Fondo con viñeta suave */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity duration-300" />

      {/* Contenedor Central de Impacto */}
      <div className="relative z-10 flex flex-col items-center gap-6 px-6 py-8">
        {/* Motivo de la tirada */}
        <div className="px-4 py-1.5 rounded-full bg-surface/90 border border-border-iron shadow-lg text-xs font-semibold text-gold tracking-wide">
          {label}
        </div>

        {/* Grupo de Dados Esparcidos */}
        <div className="flex flex-wrap items-center justify-center gap-4 max-w-xl min-h-[100px]">
          {dice_rolls.map((r, i) => renderDieShape(r.sides, r.roll, i))}
        </div>

        {/* Total Final Iluminado */}
        <div
          className={`flex items-center gap-3 px-6 py-2 rounded-2xl bg-surface/95 border-2 border-gold shadow-[0_0_30px_rgba(121,192,255,0.35)] transition-all duration-500 ${
            animState === "settle" ? "scale-100 opacity-100" : "scale-75 opacity-0"
          }`}
        >
          <span className="text-xs font-semibold uppercase text-muted tracking-wider">Total:</span>
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
