import React, { useState, useEffect } from "react";
import {
  Shield,
  Wand2,
  Dice5,
  BookOpen,
  Wifi,
  ChevronRight,
  ChevronLeft,
  X,
  Check,
  BellRing,
  Layers,
  Flame,
} from "lucide-react";
import { useTranslation } from "../i18n";

export interface OnboardingModalProps {
  mode: "initial" | "whats_new";
  version: string;
  onClose: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  mode,
  version,
  onClose,
}) => {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState<number>(0);

  const steps = [
    {
      icon: Shield,
      badge: "Offline-First",
      title: t("onboarding.step1Title"),
      desc: t("onboarding.step1Desc"),
      color: "text-accent",
      bg: "bg-accent/15 border-accent/30",
    },
    {
      icon: Wand2,
      badge: "Hero Forge",
      title: t("onboarding.step2Title"),
      desc: t("onboarding.step2Desc"),
      color: "text-amber-500",
      bg: "bg-amber-500/15 border-amber-500/30",
    },
    {
      icon: Dice5,
      badge: "Combat & Stats",
      title: t("onboarding.step3Title"),
      desc: t("onboarding.step3Desc"),
      color: "text-crimson",
      bg: "bg-crimson/15 border-crimson/30",
    },
    {
      icon: BookOpen,
      badge: "OKF Compendium",
      title: t("onboarding.step4Title"),
      desc: t("onboarding.step4Desc"),
      color: "text-emerald-500",
      bg: "bg-emerald-500/15 border-emerald-500/30",
    },
    {
      icon: Wifi,
      badge: "TaleSpire 3D",
      title: t("onboarding.step5Title"),
      desc: t("onboarding.step5Desc"),
      color: "text-purple-400",
      bg: "bg-purple-400/15 border-purple-400/30",
    },
  ];

  // Teclado: Escape cierra, Flechas izquierda/derecha cambian paso
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (mode === "initial") {
        if (e.key === "ArrowRight") {
          setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1));
        } else if (e.key === "ArrowLeft") {
          setCurrentStep((prev) => Math.max(0, prev - 1));
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mode, steps.length, onClose]);

  // =========================================================================
  // MODO: NOVEDADES DE LA VERSIÓN (WHAT'S NEW) TRAS ACTUALIZACIÓN
  // =========================================================================
  if (mode === "whats_new") {
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

          {/* Highlights v1.0.2 */}
          <div className="p-6 space-y-4">
            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
              <div className="p-2 rounded-lg bg-accent/15 border border-accent/30 text-accent shrink-0 mt-0.5">
                <Layers className="w-4 h-4" />
              </div>
              <div className="space-y-0.5 text-xs">
                <div className="font-bold text-main">Nuevo Onboarding Visual por Foco (Spotlight)</div>
                <div className="text-muted leading-relaxed">
                  Telón desenfocado con recorte nítido y halo animado que te guía directamente sobre los botones y secciones reales de la interfaz.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
              <div className="p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-500 shrink-0 mt-0.5">
                <BookOpen className="w-4 h-4" />
              </div>
              <div className="space-y-0.5 text-xs">
                <div className="font-bold text-main">Guías Contextuales Progresivas por Sección</div>
                <div className="text-muted leading-relaxed">
                  Tutoría contextual al ingresar a tu Ficha, Grimorio, Forja o Compendio, con opción para omitir todo o solo la sección actual.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-iron/60 bg-card/50">
              <div className="p-2 rounded-lg bg-crimson/15 border border-crimson/30 text-crimson shrink-0 mt-0.5">
                <Dice5 className="w-4 h-4" />
              </div>
              <div className="space-y-0.5 text-xs">
                <div className="font-bold text-main">Tirada de Prueba Interactiva & Dados 3D</div>
                <div className="text-muted leading-relaxed">
                  Prueba tiradas d20 en vivo directamente desde el tour de bienvenida con física realista y animaciones cinemáticas.
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
  }

  // =========================================================================
  // MODO: TUTORIAL DE BIENVENIDA COMPLETO (PRIMERA VEZ)
  // =========================================================================
  const step = steps[currentStep];
  const StepIcon = step.icon;
  const isLast = currentStep === steps.length - 1;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-pop-in select-none"
    >
      <div
        className="w-full max-w-xl bg-surface border border-iron rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono uppercase tracking-widest text-muted">Parma Desktop</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent/15 border border-accent/30 text-accent font-mono font-bold">
              v{version}
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label={t("onboarding.btnSkip")}
            className="text-xs text-muted hover:text-main px-2 py-1 rounded-lg hover:bg-card/60 transition-colors cursor-pointer"
          >
            {t("onboarding.btnSkip")}
          </button>
        </div>

        {/* Step Card Body */}
        <div className="px-8 py-8 flex flex-col items-center text-center space-y-5">
          <div className={`p-5 rounded-2xl border ${step.bg} shadow-inner transition-transform duration-300 hover:scale-105`}>
            <StepIcon className={`w-12 h-12 ${step.color}`} />
          </div>

          <div className="space-y-2 max-w-md">
            <div className="inline-block px-2.5 py-0.5 rounded-full bg-card border border-iron/80 text-[10px] font-bold uppercase tracking-wider text-muted">
              {step.badge}
            </div>
            <h2 className="text-xl font-bold text-main font-display">
              {step.title}
            </h2>
            <p className="text-xs sm:text-sm text-muted leading-relaxed font-body">
              {step.desc}
            </p>
          </div>
        </div>

        {/* Footer with Step Dots and Navigation Buttons */}
        <div className="px-6 py-4 border-t border-iron/80 bg-card/40 flex items-center justify-between">
          {/* Step Dots */}
          <div className="flex items-center gap-1.5">
            {steps.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setCurrentStep(idx)}
                aria-label={`Paso ${idx + 1}`}
                className={`h-1.5 rounded-full transition-all cursor-pointer ${
                  idx === currentStep ? "w-6 bg-accent" : "w-1.5 bg-iron hover:bg-muted"
                }`}
              />
            ))}
          </div>

          {/* Navigation Actions */}
          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                type="button"
                onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-xl border border-iron bg-surface hover:bg-card text-main active:scale-95 transition-all cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>{t("onboarding.btnPrev")}</span>
              </button>
            )}

            {!isLast ? (
              <button
                type="button"
                onClick={() => setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1))}
                className="flex items-center gap-1 px-4 py-1.5 text-xs font-bold rounded-xl bg-accent text-canvas hover:brightness-110 active:scale-95 transition-all shadow-sm cursor-pointer"
              >
                <span>{t("onboarding.btnNext")}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={onClose}
                className="flex items-center gap-1.5 px-5 py-1.5 text-xs font-bold rounded-xl bg-accent text-canvas hover:brightness-110 active:scale-95 transition-all shadow-md cursor-pointer"
              >
                <span>{t("onboarding.btnStart")}</span>
                <Check className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
