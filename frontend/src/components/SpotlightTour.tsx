import React, { useState, useEffect, useRef, useCallback } from "react";
import { ChevronRight, ChevronLeft, X, FastForward, Check } from "lucide-react";
import { useTranslation } from "../i18n";

export interface TourStep {
  targetId: string;
  title: string;
  description: string;
  badge?: string;
  placement?: "bottom" | "top" | "left" | "right" | "auto";
  actionButton?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
}

export interface SpotlightTourProps {
  isOpen: boolean;
  steps: TourStep[];
  currentStepIndex: number;
  onStepChange: (index: number) => void;
  onClose: () => void; // Finalizar o saltar todo
  onSkipSection?: () => void; // Saltar solo este tour
  isContextual?: boolean;
}

interface TargetRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export const SpotlightTour: React.FC<SpotlightTourProps> = ({
  isOpen,
  steps,
  currentStepIndex,
  onStepChange,
  onClose,
  onSkipSection,
  isContextual = false,
}) => {
  const { t } = useTranslation();
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number; placement: string }>({
    top: 0,
    left: 0,
    placement: "bottom",
  });
  const popoverRef = useRef<HTMLDivElement>(null);

  const step = steps[currentStepIndex];

  // Actualizar coordenadas del elemento destacado con padding
  const updateTargetRect = useCallback(() => {
    if (!step || !isOpen) {
      setTargetRect(null);
      return;
    }

    const el = document.getElementById(step.targetId);
    if (!el) {
      setTargetRect(null);
      return;
    }

    // Scroll suave para asegurar que el elemento esté visible
    el.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });

    const rect = el.getBoundingClientRect();
    const padding = 8;
    const x = Math.max(0, rect.left - padding);
    const y = Math.max(0, rect.top - padding);
    const w = rect.width + padding * 2;
    const h = rect.height + padding * 2;

    setTargetRect({ x, y, w, h });
  }, [step, isOpen]);

  // Posicionar la tarjeta de información inteligentemente según la Ley de Hick
  useEffect(() => {
    updateTargetRect();

    const handleResize = () => {
      updateTargetRect();
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("scroll", handleResize, true);

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("scroll", handleResize, true);
    };
  }, [updateTargetRect]);

  // Recalcular posición del Popover cada vez que cambia el targetRect o el paso
  useEffect(() => {
    const popoverEl = popoverRef.current;
    const pWidth = popoverEl ? Math.min(popoverEl.offsetWidth, window.innerWidth - 32) : 380;
    const pHeight = popoverEl ? popoverEl.offsetHeight : 220;
    const margin = 14;

    if (!targetRect) {
      // Si el elemento no existe o aún no está en DOM, centrar en pantalla
      setPopoverPos({
        top: Math.max(20, (window.innerHeight - pHeight) / 2),
        left: Math.max(16, (window.innerWidth - pWidth) / 2),
        placement: "center",
      });
      return;
    }

    const { x, y, w, h } = targetRect;
    let placement = step?.placement || "auto";

    // Si el elemento está en la barra superior o cabecera (y < 140), SIEMPRE colocar abajo
    // para nunca ocultar el objetivo ni solaparse con la barra de navegación o dados
    if (y < 140) {
      placement = "bottom";
    } else if (placement === "auto") {
      const spaceBelow = window.innerHeight - (y + h);
      const spaceAbove = y;
      if (spaceBelow >= pHeight + margin + 10) {
        placement = "bottom";
      } else if (spaceAbove >= pHeight + margin + 10) {
        placement = "top";
      } else {
        placement = "bottom";
      }
    }

    let left = Math.max(16, Math.min(window.innerWidth - pWidth - 16, x + w / 2 - pWidth / 2));
    let top = 0;

    if (placement === "bottom") {
      top = y + h + margin;
      // Clamping para no salir de pantalla
      if (top + pHeight > window.innerHeight - 16) {
        if (y > pHeight + margin + 20) {
          top = Math.max(16, y - pHeight - margin);
          placement = "top";
        } else {
          top = Math.max(16, window.innerHeight - pHeight - 16);
        }
      }
    } else if (placement === "top") {
      top = Math.max(16, y - pHeight - margin);
    } else {
      top = y + h + margin;
    }

    setPopoverPos({ top, left, placement });
  }, [targetRect, step, currentStepIndex]);

  // Atajos de Teclado (Escape para salir, flechas para avanzar/retroceder)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowRight") {
        if (currentStepIndex < steps.length - 1) {
          onStepChange(currentStepIndex + 1);
        } else {
          onClose();
        }
      } else if (e.key === "ArrowLeft") {
        if (currentStepIndex > 0) {
          onStepChange(currentStepIndex - 1);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, currentStepIndex, steps.length, onStepChange, onClose]);

  if (!isOpen || !step) return null;

  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === steps.length - 1;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden pointer-events-auto select-none">
      {/* 1. Telón de fondo con desenfoque cinematográfico y máscara SVG de foco */}
      <svg
        className="fixed inset-0 w-full h-full pointer-events-none z-40 transition-opacity duration-300"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <mask id="spotlight-tour-mask">
            {/* Fondo blanco: Todo queda oscurecido */}
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {/* Hueco negro: La sección destacada se transparenta nítidamente */}
            {targetRect && (
              <rect
                x={targetRect.x}
                y={targetRect.y}
                width={targetRect.w}
                height={targetRect.h}
                rx="14"
                ry="14"
                fill="black"
                className="transition-all duration-400 ease-out"
              />
            )}
          </mask>
        </defs>
        {/* Capa oscura semitransparente con máscara y blur nativo */}
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(5, 7, 10, 0.78)"
          mask="url(#spotlight-tour-mask)"
          className="pointer-events-auto backdrop-blur-xs"
        />
      </svg>

      {/* 2. Halo y Borde Animado Dorado alrededor del elemento destacado */}
      {targetRect && (
        <div
          style={{
            position: "fixed",
            left: targetRect.x,
            top: targetRect.y,
            width: targetRect.w,
            height: targetRect.h,
          }}
          className="z-40 pointer-events-none rounded-xl border-2 border-gold shadow-[0_0_24px_rgba(201,164,92,0.6)] ring-4 ring-gold/20 animate-pulse transition-all duration-400 ease-out"
        />
      )}

      {/* 3. Botón Flotante Inferior: Saltar Todo el Onboarding (Ubicado en bottom-4 para evitar colisiones con botones de cabecera) */}
      <div className="fixed bottom-4 right-4 z-40 flex items-center gap-2">
        <button
          onClick={onClose}
          title="Omitir el tutorial completo (Escape)"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface/90 hover:bg-card border border-border-iron text-muted hover:text-main text-xs font-semibold backdrop-blur-md shadow-lg transition-colors cursor-pointer group"
        >
          <FastForward className="w-3.5 h-3.5 text-gold group-hover:translate-x-0.5 transition-transform" />
          <span>{t("onboarding.btnSkipAll", "Saltar todo el tutorial")}</span>
        </button>
        <span className="hidden sm:inline-block px-2 py-1 rounded bg-black/40 border border-white/10 text-[10px] text-muted font-mono">
          Esc
        </span>
      </div>

      {/* 4. Tarjeta Flotante de Explicación Táctica (Coach Mark Popover) */}
      <div
        ref={popoverRef}
        style={{
          position: "fixed",
          top: popoverPos.top,
          left: popoverPos.left,
        }}
        className="z-50 w-[min(380px,calc(100vw-32px))] max-h-[calc(100vh-32px)] overflow-y-auto box-border bg-surface/95 backdrop-blur-md border border-gold/50 rounded-2xl p-4 sm:p-5 shadow-[0_20px_50px_rgba(0,0,0,0.6)] flex flex-col gap-3 transition-all duration-300 ease-out animate-pop-in"
      >
        {/* Cabecera de la Tarjeta */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-stat tracking-wider bg-gold/15 text-gold border border-gold/30 uppercase truncate">
              {step.badge || `${t("onboarding.stepLabel", "Paso")} ${currentStepIndex + 1}/${steps.length}`}
            </span>
            {isContextual && (
              <span className="text-[10px] text-muted uppercase tracking-wider font-semibold truncate">
                {t("onboarding.sectionGuide", "Guía de Sección")}
              </span>
            )}
          </div>
          <button
            onClick={onSkipSection || onClose}
            className="p-1 rounded text-muted hover:text-main hover:bg-card transition-colors cursor-pointer flex-shrink-0"
            title="Cerrar este paso"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Título y Descripción Conforme a la Ley de Hick */}
        <div>
          <h3 className="font-display font-bold text-lg text-gold leading-snug break-words">
            {step.title}
          </h3>
          <p className="text-xs text-muted leading-relaxed mt-1 break-words">
            {step.description}
          </p>
        </div>

        {/* Botón de Acción Especial / Demostración en Vivo */}
        {step.actionButton && (
          <div className="pt-1">
            <button
              onClick={step.actionButton.onClick}
              className="w-full py-2 px-3 rounded-lg bg-crimson hover:bg-crimson-hover text-white text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm active:scale-98 cursor-pointer"
            >
              {step.actionButton.icon}
              <span>{step.actionButton.label}</span>
            </button>
          </div>
        )}

        {/* Indicadores de Progreso por Puntos */}
        <div className="flex items-center justify-center gap-1.5 py-1">
          {steps.map((_, idx) => (
            <button
              key={idx}
              onClick={() => onStepChange(idx)}
              className={`h-1.5 rounded-full transition-all cursor-pointer ${
                idx === currentStepIndex
                  ? "w-6 bg-gold"
                  : "w-2 bg-border-iron hover:bg-muted"
              }`}
              title={`Ir al paso ${idx + 1}`}
            />
          ))}
        </div>

        {/* Pie de Controles: Navegación Táctica con Prevención de Desbordamiento y Flex-Wrap */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-border-iron/80">
          <div className="flex items-center gap-2 min-w-0">
            {onSkipSection ? (
              <button
                onClick={onSkipSection}
                className="text-xs text-muted hover:text-main underline decoration-dotted transition-colors cursor-pointer truncate"
              >
                {t("onboarding.btnSkipSection", "Saltar sección")}
              </button>
            ) : (
              <span className="text-[11px] text-muted whitespace-nowrap">
                {currentStepIndex + 1} de {steps.length}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 ml-auto">
            {!isFirst && (
              <button
                onClick={() => onStepChange(currentStepIndex - 1)}
                className="px-3 py-1.5 rounded-lg bg-card hover:bg-surface border border-border-iron text-xs font-semibold text-main transition-colors flex items-center gap-1 cursor-pointer whitespace-nowrap"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>{t("onboarding.btnPrev", "Anterior")}</span>
              </button>
            )}

            <button
              onClick={() => {
                if (isLast) {
                  onClose();
                } else {
                  onStepChange(currentStepIndex + 1);
                }
              }}
              className="px-4 py-1.5 rounded-lg bg-gold hover:bg-gold-hover text-canvas text-xs font-bold transition-all shadow-sm flex items-center gap-1 cursor-pointer active:scale-95 whitespace-nowrap"
            >
              {isLast ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>{t("onboarding.btnStart", "¡Comenzar!")}</span>
                </>
              ) : (
                <>
                  <span>{t("onboarding.btnNext", "Siguiente")}</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
