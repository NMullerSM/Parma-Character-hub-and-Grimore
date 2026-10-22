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
        {/* Halo de resplandor rúnico sutil detrás del logo */}
        <div className="absolute w-72 h-72 rounded-full bg-gold/10 blur-3xl -z-10 pointer-events-none" />

        {/* Logotipo vectorial completo de Parma */}
        <img
          src={currentLogo}
          alt="Parma"
          className="w-72 sm:w-80 md:w-96 h-auto object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.3)]"
        />

        {/* Indicador sutil de inicio */}
        <div className="mt-8 flex items-center gap-1.5 opacity-60">
          <div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
          <span className="text-[11px] font-stat tracking-widest uppercase text-muted">
            {language === "es" ? "Iniciando grimorio..." : "Opening Grimoire..."}
          </span>
        </div>
      </div>
    </div>
  );
};
