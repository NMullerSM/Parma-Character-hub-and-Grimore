import React from "react";
import { useCharacter } from "../context/CharacterContext";

/**
 * ScreenVignette:
 * Destello cinemático en los bordes internos de la pantalla.
 * - Rojo carmesí al recibir daño / restar puntos de vida.
 * - Verde esmeralda al recibir curación / sumar puntos de vida.
 */
export const ScreenVignette: React.FC = () => {
  const { vignetteFlash } = useCharacter();

  if (!vignetteFlash) return null;

  const isDamage = vignetteFlash === "damage";

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 pointer-events-none z-[9990] transition-opacity duration-300 ${
        isDamage ? "vignette-damage" : "vignette-heal"
      }`}
    >
      {/* Marco de luz interior perimetral sin invadir el centro de la pantalla */}
      <div
        className={`absolute inset-0 border-[2px] transition-colors ${
          isDamage
            ? "border-crimson/50 shadow-[inset_0_0_24px_rgba(230,57,70,0.55)]"
            : "border-emerald-500/50 shadow-[inset_0_0_24px_rgba(16,185,129,0.55)]"
        }`}
      />
    </div>
  );
};
