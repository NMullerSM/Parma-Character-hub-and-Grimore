import React from "react";
import { useCharacter } from "../context/CharacterContext";

export const ToastContainer: React.FC = () => {
  const { toasts } = useCharacter();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto px-4 py-2.5 rounded shadow-lg border text-xs font-medium backdrop-blur-sm transition-all duration-200 animate-in fade-in slide-in-from-bottom-2 ${
            t.type === "success"
              ? "bg-card/95 border-emerald-500/50 text-emerald-300"
              : t.type === "warn"
              ? "bg-card/95 border-amber-500/50 text-amber-300"
              : "bg-card/95 border-border-gold/50 text-main"
          }`}
        >
          {t.text}
        </div>
      ))}
    </div>
  );
};
