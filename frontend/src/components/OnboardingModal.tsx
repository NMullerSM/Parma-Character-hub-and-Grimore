import React, { useEffect } from "react";
import { BellRing, Layers, Flame, X } from "lucide-react";
import { useTranslation } from "../i18n";

export interface OnboardingModalProps {
  version: string;
  onClose: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  version,
  onClose,
}) => {
  const { t, language } = useTranslation();
  const isEn = language === "en";

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Única vista de este modal: novedades de la versión (What's New) tras actualizar.
  // El tutorial de bienvenida paso a paso vive en SpotlightTour.tsx.
  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-pop-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-surface border border-iron rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="relative px-6 pt-6 pb-4 border-b border-iron/60 bg-card/60">
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.close")}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-muted hover:text-main hover:bg-surface/80 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-accent/15 border border-accent/30 text-accent">
              <BellRing className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-main">
                {t("onboarding.whatsNewTitle")} <span className="text-accent font-mono">v{version}</span>
              </h2>
              <p className="text-xs text-muted">{t("onboarding.whatsNewSubtitle")}</p>
            </div>
          </div>
        </div>

        {/* Highlights */}
        <div className="p-6 space-y-4">
          <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
            <div className="p-2 rounded-lg bg-accent/15 border border-accent/30 text-accent shrink-0 mt-0.5">
              <BellRing className="w-4 h-4" />
            </div>
            <div className="space-y-0.5 text-xs">
              <div className="font-bold text-main">
                {isEn ? "GitHub Update Notifications" : "Notificador de Actualizaciones en GitHub"}
              </div>
              <div className="text-muted leading-relaxed">
                {isEn
                  ? "Unobtrusive notifications in the lower corner when a new release is available, with direct download for Windows and Linux."
                  : "Aviso discreto en la esquina inferior izquierda cuando se publique una nueva versión, con descarga directa para Windows y Linux."}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
            <div className="p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-500 shrink-0 mt-0.5">
              <Layers className="w-4 h-4" />
            </div>
            <div className="space-y-0.5 text-xs">
              <div className="font-bold text-main">
                {isEn ? "Smart Version Onboarding" : "Onboarding Inteligente por Versión"}
              </div>
              <div className="text-muted leading-relaxed">
                {isEn
                  ? "Interactive guided tour for new players and curated highlights overview after each update."
                  : "Tutorial guiado interactivo para jugadores nuevos y resumen selectivo de novedades tras cada actualización."}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
            <div className="p-2 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-500 shrink-0 mt-0.5">
              <Flame className="w-4 h-4" />
            </div>
            <div className="space-y-0.5 text-xs">
              <div className="font-bold text-main">
                {isEn ? "Cross-Platform Stability" : "Estabilidad Multiplataforma"}
              </div>
              <div className="text-muted leading-relaxed">
                {isEn
                  ? "Official Windows installer (.exe), Debian native packages (.deb), and portable builds with guaranteed SQLite persistence."
                  : "Soporte Inno Setup oficial para Windows (.exe), paquetes nativos Debian (.deb) y portables con persistencia SQLite asegurada."}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-iron/60 bg-card/40 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-xs font-bold rounded-xl bg-accent text-canvas hover:brightness-110 active:scale-95 transition-all shadow-md cursor-pointer"
          >
            {t("onboarding.btnUnderstand")}
          </button>
        </div>
      </div>
    </div>
  );
};
