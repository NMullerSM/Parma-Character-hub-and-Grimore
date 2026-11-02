import React from "react";
import { ArrowUpCircle, X, RefreshCw, CheckCircle2 } from "lucide-react";
import { useTranslation } from "../i18n";
import type { GitHubReleaseInfo, UpdateProgress } from "../api/types";

export interface UpdateNotificationPillProps {
  release: GitHubReleaseInfo;
  onOpenModal: () => void;
  onDismiss: () => void;
  progress?: UpdateProgress;
}

export const UpdateNotificationPill: React.FC<UpdateNotificationPillProps> = ({
  release,
  onOpenModal,
  onDismiss,
  progress,
}) => {
  const { t } = useTranslation();

  const isDownloading = progress?.status === "downloading";
  const isReady = progress?.status === "ready_to_restart";

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-4 left-4 z-40 flex items-center gap-3 px-3.5 py-2.5 rounded-xl border backdrop-blur-md shadow-2xl animate-pop-in transition-all duration-200 select-none ${
        isReady
          ? "border-emerald-500/80 bg-emerald-950/90 shadow-[0_0_20px_rgba(16,185,129,0.3)] animate-pulse"
          : isDownloading
          ? "border-gold/80 bg-card/95"
          : "border-gold/60 bg-card/95 hover:border-gold"
      }`}
    >
      <div className="flex items-center gap-2 text-sm">
        {isReady ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
        ) : isDownloading ? (
          <RefreshCw className="w-4 h-4 text-gold shrink-0 animate-spin" />
        ) : (
          <ArrowUpCircle className="w-4 h-4 text-gold shrink-0" />
        )}

        <span className="font-semibold text-main tracking-tight">
          {isReady
            ? "¡Actualización lista!"
            : isDownloading
            ? `Descargando... ${progress.percent}%`
            : t("updates.newVersionAvailable", "¡Nueva versión!")}
        </span>

        <span
          className={`px-1.5 py-0.5 rounded text-xs font-mono font-bold ${
            isReady
              ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-300"
              : "bg-gold/15 border border-gold/30 text-gold"
          }`}
        >
          {release.tag_name}
        </span>
      </div>

      <div className="flex items-center gap-1.5 pl-2 border-l border-border-iron/80">
        <button
          type="button"
          onClick={onOpenModal}
          className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-all shadow-sm cursor-pointer active:scale-95 ${
            isReady
              ? "bg-emerald-500 hover:bg-emerald-400 text-canvas"
              : "bg-gold hover:bg-gold-hover text-canvas"
          }`}
        >
          {isReady ? "Reiniciar" : isDownloading ? "Ver progreso" : t("updates.updateBtn", "Actualizar")}
        </button>

        {!isDownloading && !isReady && (
          <button
            type="button"
            onClick={onDismiss}
            title={t("updates.dismiss", "Descartar")}
            aria-label={t("updates.dismiss", "Descartar")}
            className="p-1 rounded-lg text-muted hover:text-main hover:bg-surface/80 active:scale-90 transition-all cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
