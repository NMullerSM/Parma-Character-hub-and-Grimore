import React, { useState, useEffect, useRef } from "react";

interface AnimatedHealthBarProps {
  currentHp: number;
  maxHp: number;
  tempHp?: number;
  heightClass?: string;
  showText?: boolean;
  className?: string;
}

/**
 * AnimatedHealthBar:
 * Barra de vida táctica con patrón "Ghost Bar" (Barra Espectral):
 * - Al recibir Daño (-HP): La barra activa cae rápido, dejando una barra gris/ámbar
 *   atrás que retiene el valor anterior durante 350ms y luego se drena progresivamente.
 * - Al recibir Curación (+HP): La barra sube suavemente con un resplandor verde esmeralda brillante.
 * - Soporta Puntos de Golpe Temporales (+Temp HP) en color dorado.
 */
export const AnimatedHealthBar: React.FC<AnimatedHealthBarProps> = ({
  currentHp,
  maxHp,
  tempHp = 0,
  heightClass = "h-2.5",
  showText = false,
  className = "",
}) => {
  const safeMax = Math.max(1, maxHp);
  const currentPct = Math.min(100, Math.max(0, (currentHp / safeMax) * 100));
  const tempPct = Math.min(100, Math.max(0, (tempHp / safeMax) * 100));

  const [ghostPct, setGhostPct] = useState(currentPct);
  const [isHealing, setIsHealing] = useState(false);
  const prevHpRef = useRef(currentHp);
  const ghostTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const healTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const prevHp = prevHpRef.current;

    if (currentHp < prevHp) {
      // DAÑO: La barra activa desciende de inmediato; la barra gris espera 350ms y se drena
      setIsHealing(false);
      const prevPct = Math.min(100, Math.max(0, (prevHp / safeMax) * 100));
      setGhostPct(prevPct);
      if (ghostTimeoutRef.current) clearTimeout(ghostTimeoutRef.current);
      ghostTimeoutRef.current = setTimeout(() => {
        setGhostPct(currentPct);
      }, 350);
    } else if (currentHp > prevHp) {
      // CURACIÓN: La barra ghost se ajusta al instante y la barra principal asciende con resplandor verde
      setGhostPct(currentPct);
      setIsHealing(true);
      if (healTimeoutRef.current) clearTimeout(healTimeoutRef.current);
      healTimeoutRef.current = setTimeout(() => {
        setIsHealing(false);
      }, 850);
    } else {
      // Si cambia maxHp o inicialización directa
      setGhostPct(currentPct);
    }

    prevHpRef.current = currentHp;
  }, [currentHp, currentPct, safeMax]);

  useEffect(() => {
    return () => {
      if (ghostTimeoutRef.current) clearTimeout(ghostTimeoutRef.current);
      if (healTimeoutRef.current) clearTimeout(healTimeoutRef.current);
    };
  }, []);

  const isDying = currentHp <= 0;
  const isBloodied = currentHp > 0 && currentHp <= safeMax / 2;

  return (
    <div className={`relative w-full ${className}`}>
      {/* Contenedor de la Pista de Salud */}
      <div
        className={`relative w-full ${heightClass} bg-surface/90 border border-border-iron/80 rounded-full overflow-hidden shadow-inner select-none`}
      >
        {/* 1. Barra Gris Espectral (Ghost Bar de Daño) */}
        <div
          className="absolute left-0 top-0 h-full bg-slate-400/80 dark:bg-slate-500/80 rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${ghostPct}%`,
          }}
        />

        {/* 2. Barra Activa de Salud Actual (Con efecto Verde de Curación o Rojo de Daño suavizados) */}
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-200 ease-out ${
            isHealing
              ? "bg-emerald-600/90 shadow-sm"
              : isDying
              ? "bg-rose-900/60"
              : isBloodied
              ? "bg-amber-600/90 shadow-sm"
              : "bg-rose-600/90 shadow-sm"
          }`}
          style={{ width: `${currentPct}%` }}
        />

        {/* 3. Segmento de Puntos de Golpe Temporales / Escudo (Plateado / Slate) */}
        {tempPct > 0 && (
          <div
            className="absolute top-0 h-full bg-slate-300 dark:bg-slate-300/90 border-l border-surface/80 rounded-r-full shadow-xs transition-all duration-300"
            style={{
              left: `${currentPct}%`,
              width: `${Math.min(100 - currentPct, tempPct)}%`,
            }}
            title={`+${tempHp} Puntos de Golpe Temporales`}
          />
        )}
      </div>

      {/* Texto Opcional de Vitales */}
      {showText && (
        <div className="flex items-center justify-between text-[11px] font-stat font-semibold text-muted mt-1 px-0.5">
          <span className="flex items-center gap-1">
            <span className={isDying ? "text-rose-500 font-bold animate-pulse" : isBloodied ? "text-amber-400" : "text-main"}>
              {currentHp}
            </span>
            <span className="text-muted/70">/ {maxHp} HP</span>
          </span>
          {tempHp > 0 && (
            <span className="text-slate-200 font-bold bg-slate-400/20 px-1.5 py-0.2 rounded border border-slate-400/40 text-[10px]">
              +{tempHp} Temp
            </span>
          )}
        </div>
      )}
    </div>
  );
};
