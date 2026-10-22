import React, { useEffect, useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTheme } from "../context/ThemeContext";

import logoEsDark from "../assets/logo/parma-logo-es-dark.svg";
import logoEsLight from "../assets/logo/parma-logo-es-light.svg";
import logoEnDark from "../assets/logo/parma-logo-en-dark.svg";
import logoEnLight from "../assets/logo/parma-logo-en-light.svg";

interface SplashScreenProps {
  onComplete?: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const { language } = useCharacter();
  const { isDark } = useTheme();

  const [phase, setPhase] = useState<"enter" | "hold" | "exit" | "done">("enter");

  const currentLogo = language === "es"
    ? (isDark ? logoEsDark : logoEsLight)
    : (isDark ? logoEnDark : logoEnLight);

  useEffect(() => {
    // Fase 1: Entrada suave hacia adelante (0ms a 700ms)
    const tEnter = setTimeout(() => {
      setPhase("hold");
    }, 700);

    // Fase 2: Pausa elegante (700ms a 1400ms)
    const tHold = setTimeout(() => {
      setPhase("exit");
    }, 1400);

    // Fase 3: Desvanecimiento con ease-out (1400ms a 2000ms)
    const tDone = setTimeout(() => {
      setPhase("done");
      if (onComplete) onComplete();
    }, 2000);

    return () => {
      clearTimeout(tEnter);
      clearTimeout(tHold);
      clearTimeout(tDone);
    };
  }, [onComplete]);

  // Permitir saltar con clic o tecla
  const handleSkip = () => {
    setPhase("exit");
    setTimeout(() => {
      setPhase("done");
      if (onComplete) onComplete();
    }, 300);
  };

  if (phase === "done") return null;

  const isExiting = phase === "exit";
  const isEntering = phase === "enter";

  return (
    <div
      onClick={handleSkip}
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-canvas select-none cursor-pointer transition-opacity duration-600 ease-out ${
        isExiting ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      {/* Contenedor central con animación que viene hacia adelante */}
      <div
        className={`flex flex-col items-center justify-center transform transition-all duration-700 ease-out ${
          isEntering
            ? "scale-90 opacity-0 translate-y-3"
            : isExiting
            ? "scale-105 opacity-0 -translate-y-1"
            : "scale-100 opacity-100 translate-y-0"
        }`}
      >
        {/* Halo y brillo translúcido detrás del logo para realzar contraste */}
        <div className="absolute w-[36rem] sm:w-[46rem] md:w-[56rem] h-[24rem] sm:h-[30rem] md:h-[36rem] max-w-[95vw] -z-10 pointer-events-none flex items-center justify-center">
          {/* Fondo negro sutil difuminado para garantizar legibilidad */}
          <div className="absolute w-3/4 h-3/4 rounded-full bg-black/40 blur-3xl -z-20" />
          {/* Halo blanco suave translúcido con leve luz */}
          <div className="absolute w-2/3 h-2/3 rounded-full bg-white/[0.08] dark:bg-white/[0.09] blur-2xl -z-10 shadow-[0_0_90px_rgba(255,255,255,0.15)] ring-1 ring-white/10" />
          {/* Resplandor dorado místico atenuado */}
          <div className="absolute w-1/2 h-1/2 rounded-full bg-gold/15 blur-3xl -z-10" />
        </div>

        {/* Logotipo vectorial completo de Parma (tamaño ampliado al doble) */}
        <img
          src={currentLogo}
          alt="Parma"
          className="w-[28rem] sm:w-[38rem] md:w-[48rem] lg:w-[54rem] max-w-[92vw] h-auto object-contain drop-shadow-[0_8px_32px_rgba(0,0,0,0.5)] transition-transform duration-500"
        />

        {/* Indicador sutil de inicio */}
        <div className="mt-10 flex items-center gap-2 opacity-70">
          <div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse shadow-[0_0_8px_rgba(201,164,92,0.8)]" />
          <span className="text-xs font-stat tracking-widest uppercase text-muted">
            {language === "es" ? "Iniciando grimorio..." : "Opening Grimoire..."}
          </span>
        </div>
      </div>
    </div>
  );
};
