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
      {/* Marco de luz interior alrededor de los 4 bordes de la ventana */}
      <div
        className={`absolute inset-0 border-[5px] transition-colors ${
          isDamage
            ? "border-crimson/40 shadow-[inset_0_0_80px_rgba(230,57,70,0.5)]"
            : "border-emerald-500/40 shadow-[inset_0_0_80px_rgba(16,185,129,0.5)]"
        }`}
      />
    </div>
  );
};
