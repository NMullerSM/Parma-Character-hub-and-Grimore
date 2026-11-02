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
                rx={10}
                ry={10}
                fill="black"
              />
            )}
          </mask>
        </defs>

        {/* Rectángulo de oscurecimiento global conectado a la máscara (sin backdrop-blur-xs para no quebrar WebKitGTK en Linux) */}
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(5, 7, 10, 0.78)"
          mask="url(#spotlight-tour-mask)"
        />
      </svg>

      {/* 2. Anillo de Resplandor Dorado alrededor del elemento objetivo */}
      {targetRect && (
        <div
          className="fixed pointer-events-none z-40 rounded-xl transition-all duration-300 ease-out border-2 border-gold shadow-[0_0_25px_rgba(234,179,8,0.45)] ring-4 ring-gold/20 animate-pulse"
          style={{
            top: `${targetRect.y}px`,
            left: `${targetRect.x}px`,
            width: `${targetRect.w}px`,
            height: `${targetRect.h}px`,
          }}
        />
      )}

      {/* 3. Tarjeta de Coach Mark Flotante (Anti-Colisión & Responsiva) */}
      <div
        ref={popoverRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-step-title"
        className="fixed z-50 transition-all duration-300 ease-out w-[min(380px,calc(100vw-32px))] max-h-[calc(100vh-32px)] overflow-y-auto"
        style={{
          top: `${popoverPos.top}px`,
          left: `${popoverPos.left}px`,
        }}
      >
        <div className="bg-card border border-gold/60 rounded-2xl p-5 shadow-[0_20px_50px_rgba(0,0,0,0.85)] backdrop-blur-md relative overflow-hidden flex flex-col justify-between">
          {/* Acento decorativo sutil */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-gold to-transparent opacity-80" />

          {/* Cabecera de la tarjeta: Badge + Paso + Botón Cerrar */}
          <div className="flex items-start justify-between gap-2 mb-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded text-[11px] font-bold tracking-wider uppercase bg-gold/15 text-gold border border-gold/30">
                {step.badge || (isContextual ? t("onboarding.sectionGuide") : t("onboarding.stepLabel"))}
              </span>
              <span className="text-xs text-muted font-medium">
                {currentStepIndex + 1} / {steps.length}
              </span>
            </div>

            <button
              type="button"
              onClick={onClose}
              title={`${t("common.close")} (Esc)`}
              aria-label={t("common.close")}
              className="p-1 rounded-lg text-muted hover:text-main hover:bg-surface/80 active:scale-95 transition-all cursor-pointer -mr-1 -mt-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Título y Descripción concisa (Ley de Hick: máximo 2-3 oraciones clave) */}
          <div className="mb-4">
            <h3 id="tour-step-title" className="text-base font-bold text-main tracking-tight font-serif mb-1.5">
              {step.title}
            </h3>
            <p className="text-xs text-muted leading-relaxed select-text">
              {step.description}
            </p>
          </div>

          {/* Botón de acción interactiva opcional (ej: tirar dado de prueba) */}
          {step.actionButton && (
            <div className="mb-4">
              <button
                type="button"
                onClick={step.actionButton.onClick}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-gold/15 border border-gold/40 text-gold hover:bg-gold/25 active:scale-98 transition-all cursor-pointer shadow-xs"
              >
                {step.actionButton.icon}
                <span>{step.actionButton.label}</span>
              </button>
            </div>
          )}

          {/* Barra de progreso visual inferior (Puntos indicadores) */}
          <div className="flex items-center justify-between pt-3 border-t border-border-iron/80">
            {/* Puntos de navegación */}
            <div className="flex items-center gap-1.5">
              {steps.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onStepChange(idx)}
                  className={`h-1.5 rounded-full transition-all cursor-pointer ${
                    idx === currentStepIndex
                      ? "w-6 bg-gold"
                      : idx < currentStepIndex
                      ? "w-2 bg-gold/40 hover:bg-gold/60"
                      : "w-2 bg-border-iron hover:bg-muted"
                  }`}
                  title={`${t("onboarding.stepLabel")} ${idx + 1}`}
                  aria-label={`${t("onboarding.stepLabel")} ${idx + 1}`}
                />
              ))}
            </div>

            {/* Contenedor responsivo anti-colisión para botones de control */}
            <div className="flex flex-wrap gap-2 items-center justify-end ml-auto">
              {/* Botón Saltar Sección */}
              {onSkipSection && !isLast && (
                <button
                  type="button"
                  onClick={onSkipSection}
                  className="px-2 py-1.5 text-xs font-medium text-muted hover:text-main rounded-lg hover:bg-surface active:scale-95 transition-all cursor-pointer whitespace-nowrap"
                >
                  {t("onboarding.btnSkipSection")}
                </button>
              )}

              {/* Botón Anterior */}
              {!isFirst && (
                <button
                  type="button"
                  onClick={() => onStepChange(currentStepIndex - 1)}
                  className="p-1.5 rounded-lg border border-border-iron hover:border-gold/50 bg-surface/80 hover:bg-surface text-muted hover:text-main active:scale-95 transition-all cursor-pointer flex-shrink-0"
                  title={t("onboarding.btnPrev")}
                  aria-label={t("onboarding.btnPrev")}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              )}

              {/* Botón Siguiente o Iniciar Aventura */}
              <button
                type="button"
                onClick={() => {
                  if (isLast) {
                    onClose();
                  } else {
                    onStepChange(currentStepIndex + 1);
                  }
                }}
                className={`flex items-center gap-1 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95 cursor-pointer whitespace-nowrap flex-shrink-0 ml-auto ${
                  isLast
                    ? "bg-gradient-to-r from-gold to-gold-hover text-canvas shadow-gold/20"
                    : "bg-gold hover:bg-gold-hover text-canvas"
                }`}
              >
                <span>{isLast ? t("onboarding.btnStart") : t("onboarding.btnNext")}</span>
                {isLast ? <Check className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Botón Global "Saltar Todo el Onboarding" reubicado a la esquina inferior derecha
          para no colisionar jamás con los botones de Dados, TaleSpire y Ajustes de la cabecera */}
      {!isContextual && (
        <div className="fixed bottom-4 right-4 z-40 animate-fade-in pointer-events-auto">
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-surface/90 hover:bg-surface border border-border-iron/80 hover:border-gold/50 text-muted hover:text-main shadow-lg backdrop-blur-md active:scale-95 transition-all cursor-pointer"
          >
            <FastForward className="w-3.5 h-3.5 text-gold/80" />
            <span>{t("onboarding.btnSkipAll")}</span>
          </button>
        </div>
      )}
    </div>
  );
};
