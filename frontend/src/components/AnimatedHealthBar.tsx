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

        {/* 2. Barra Activa de Salud Actual (Con efecto Verde de Curación o Rojo de Daño) */}
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-200 ease-out ${
            isHealing
              ? "bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.85)] brightness-110"
              : isDying
              ? "bg-crimson/50"
              : isBloodied
              ? "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"
              : "bg-crimson shadow-[0_0_6px_rgba(239,68,68,0.4)]"
          }`}
          style={{ width: `${currentPct}%` }}
        />

        {/* 3. Segmento de Puntos de Golpe Temporales (Dorado) */}
        {tempPct > 0 && (
          <div
            className="absolute top-0 h-full bg-gold/90 border-l border-surface/80 rounded-r-full shadow-xs transition-all duration-300"
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
            <span className={isDying ? "text-crimson font-bold animate-pulse" : isBloodied ? "text-amber-400" : "text-main"}>
              {currentHp}
            </span>
            <span className="text-muted/70">/ {maxHp} HP</span>
          </span>
          {tempHp > 0 && (
            <span className="text-gold font-bold bg-gold/10 px-1.5 py-0.2 rounded border border-gold/30 text-[10px]">
              +{tempHp} Temp
            </span>
          )}
        </div>
      )}
    </div>
  );
};
