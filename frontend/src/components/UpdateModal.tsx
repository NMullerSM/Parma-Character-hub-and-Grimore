import React, { useState, useEffect, useRef } from "react";
import { ArrowUpCircle, Download, ExternalLink, X, FileText, CheckCircle2, AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { GitHubReleaseInfo, UpdateProgress } from "../api/types";

export interface UpdateModalProps {
  release: GitHubReleaseInfo;
  currentVersion: string;
  onClose: () => void;
  onIgnoreVersion?: (version: string) => void;
  progress?: UpdateProgress;
  onStartDownload?: () => void;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({
  release,
  currentVersion,
  onClose,
  onIgnoreVersion,
  progress: externalProgress,
  onStartDownload,
}) => {
  const { t } = useTranslation();
  const [internalProgress, setInternalProgress] = useState<UpdateProgress>({
    status: "idle",
    percent: 0,
    downloaded_mb: 0,
    total_mb: 0,
  });
  const [isApplyingRestart, setIsApplyingRestart] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const pollTimerRef = useRef<any>(null);

  const activeProgress = externalProgress || internalProgress;

  const isWindows = typeof navigator !== "undefined" && /win/i.test(navigator.userAgent);
  const isLinux = typeof navigator !== "undefined" && /linux/i.test(navigator.userAgent);

  const exeAsset = release.assets?.find((a) => a.name.toLowerCase().endsWith(".exe"));
  const zipAsset = release.assets?.find((a) => a.name.toLowerCase().includes("windows") && a.name.toLowerCase().endsWith(".zip"));
  const debAsset = release.assets?.find((a) => a.name.toLowerCase().endsWith(".deb"));
  const tarAsset = release.assets?.find((a) => a.name.toLowerCase().includes("linux") && (a.name.toLowerCase().endsWith(".tar.gz") || a.name.toLowerCase().endsWith(".tgz")));

  // Elegir el asset primario para la plataforma activa
  const primaryAsset = isWindows ? (exeAsset || zipAsset) : (debAsset || tarAsset || exeAsset);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  // Sondeo periódico del progreso si estamos en estado de descarga
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const prog = await api.getUpdateProgress();
        setInternalProgress(prog);
      } catch (err) {
        console.warn("Error al consultar progreso de actualización:", err);
      }
    };

    checkStatus();

    if (activeProgress.status === "downloading") {
      pollTimerRef.current = setInterval(checkStatus, 400);
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [activeProgress.status]);

  const handleStartDownload = async () => {
    setActionError(null);
    if (!primaryAsset) {
      // Si no hay asset binario directo, abrir enlace de GitHub
      window.open(release.html_url, "_blank");
      return;
    }

    if (onStartDownload) {
      onStartDownload();
    }

    try {
      setInternalProgress((prev) => ({ ...prev, status: "downloading", percent: 0 }));
      const res = await api.startAutoUpdate(primaryAsset.browser_download_url, release.tag_name);
      if (!res.success && res.error) {
        setActionError(res.error);
        setInternalProgress((prev) => ({ ...prev, status: "error", error: res.error }));
      }
    } catch (err: any) {
      setActionError(err?.message || "Error al iniciar la descarga");
      setInternalProgress((prev) => ({ ...prev, status: "error", error: String(err) }));
    }
  };

  const handleApplyRestart = async () => {
    setIsApplyingRestart(true);
    setActionError(null);
    try {
      const res = await api.applyUpdateAndRestart();
      if (!res.success && res.error) {
        setActionError(res.error);
        setIsApplyingRestart(false);
      }
    } catch (err: any) {
      setActionError(err?.message || "Error al reiniciar para actualizar");
      setIsApplyingRestart(false);
    }
  };

  const handleIgnore = () => {
    if (onIgnoreVersion) {
      onIgnoreVersion(release.tag_name);
    } else {
      try {
        localStorage.setItem("parma_ignored_update_version", release.tag_name);
      } catch (e) {
        console.warn(e);
      }
      onClose();
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-pop-in select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-surface border border-gold/40 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-iron bg-card/70">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gold/15 border border-gold/30 text-gold">
              <ArrowUpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-display font-bold text-main flex items-center gap-2">
                <span>{t("updates.modalTitle", "Actualización Disponible")}</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-gold text-canvas font-mono font-bold">
                  {release.tag_name}
                </span>
              </h2>
              <p className="text-xs text-muted">
                {t("common.version", "Versión actual")}: <span className="font-mono text-main">{currentVersion}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("updates.close", "Cerrar")}
            className="p-1.5 rounded-lg text-muted hover:text-main hover:bg-surface/80 active:scale-95 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Cuerpo del Modal */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {/* 1. Panel de Estado del Auto-Updater */}
          {activeProgress.status === "downloading" && (
            <div className="p-4 rounded-xl border border-gold/40 bg-gold/10 space-y-3 animate-fade-in">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-gold flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-gold" />
                  <span>{t("updates.downloadingTitle", "Descargando Actualización...")}</span>
                </span>
                <span className="font-mono font-bold text-main">
                  {activeProgress.percent}%
                </span>
              </div>

              {/* Barra de Progreso Fluida */}
              <div className="w-full h-2.5 rounded-full bg-black/40 overflow-hidden p-0.5 border border-gold/30">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-gold/80 to-gold transition-all duration-300 shadow-[0_0_12px_rgba(201,164,92,0.8)]"
                  style={{ width: `${Math.max(4, activeProgress.percent)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-muted">
                <span>{t("updates.downloadingDesc", "Descargando en segundo plano. Puedes continuar jugando con tu personaje.")}</span>
                {activeProgress.downloaded_mb > 0 && (
                  <span className="font-mono whitespace-nowrap ml-2">
                    {activeProgress.downloaded_mb} MB {activeProgress.total_mb > 0 ? `/ ${activeProgress.total_mb} MB` : ""}
                  </span>
                )}
              </div>
            </div>
          )}

          {activeProgress.status === "ready_to_restart" && (
            <div className="p-4 rounded-xl border border-emerald-500/50 bg-emerald-500/10 space-y-3 animate-fade-in">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-emerald-300">
                    {t("updates.readyToRestartTitle", "¡Actualización Lista para Instalar!")}
                  </h4>
                  <p className="text-xs text-muted leading-relaxed">
                    {t("updates.readyToRestartDesc", "El instalador se ha descargado correctamente. Guarda tus cambios antes de reiniciar.")}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-[11px] text-emerald-400/90 pt-1 border-t border-emerald-500/20">
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                <span>Cero pérdida de datos: tus personajes, base de datos SQLite y notas están respaldados en tu carpeta de usuario.</span>
              </div>
            </div>
          )}

          {actionError && (
            <div className="p-3 rounded-xl border border-crimson/50 bg-crimson/15 text-xs text-red-200 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{actionError}</span>
            </div>
          )}

          {/* 2. Notas del Parche / Changelog */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-gold" />
              <span>{t("updates.releaseNotes", "Notas del Parche")}</span>
            </h3>
            <div className="p-4 rounded-xl border border-border-iron bg-canvas/60 text-sm text-main whitespace-pre-wrap font-body max-h-52 overflow-y-auto leading-relaxed select-text">
              {release.body?.trim() ? release.body : "Actualización de estabilidad, correcciones tácticas y mejoras de rendimiento."}
            </div>
          </div>

          {/* 3. Garantía de Seguridad de Datos */}
          <div className="p-3 rounded-xl border border-border-iron/80 bg-card/40 flex items-center gap-2.5 text-xs text-muted">
            <ShieldCheck className="w-4 h-4 text-gold shrink-0" />
            <span>Actualización no destructiva: La base de datos SQLite y las fichas de héroe en almacenamiento local permanecen intactas.</span>
          </div>
        </div>

        {/* Pie de Acciones del Modal */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-t border-border-iron bg-card/50">
          <div className="flex items-center gap-3">
            <a
              href={release.html_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-xs text-muted hover:text-gold transition-colors"
            >
              <span>{t("updates.viewOnGitHub", "Ver en GitHub Releases")}</span>
              <ExternalLink className="w-3 h-3" />
            </a>

            <button
              type="button"
              onClick={handleIgnore}
              className="text-xs text-muted hover:text-main underline decoration-dotted transition-colors cursor-pointer"
            >
              {t("updates.ignoreVersion", "No avisar de esta versión")}
            </button>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-surface border border-border-iron hover:bg-card text-main active:scale-95 transition-all cursor-pointer"
            >
              {activeProgress.status === "downloading"
                ? "Continuar en segundo plano"
                : t("updates.close", "Cerrar")}
            </button>

            {activeProgress.status === "ready_to_restart" ? (
              <button
                type="button"
                onClick={handleApplyRestart}
                disabled={isApplyingRestart}
                className="px-5 py-2 text-xs font-bold rounded-xl bg-emerald-500 hover:bg-emerald-400 text-canvas active:scale-95 transition-all shadow-md flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isApplyingRestart ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Reiniciando aplicación...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{t("updates.btnRestartToUpdate", "Reiniciar para actualizar")}</span>
                  </>
                )}
              </button>
            ) : activeProgress.status === "downloading" ? (
              <button
                type="button"
                disabled
                className="px-5 py-2 text-xs font-bold rounded-xl bg-gold/50 text-canvas flex items-center gap-2 cursor-not-allowed"
              >
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Descargando ({activeProgress.percent}%)...</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStartDownload}
                className="px-5 py-2 text-xs font-bold rounded-xl bg-gold hover:bg-gold-hover text-canvas active:scale-95 transition-all shadow-md flex items-center gap-2 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{t("updates.updateBtn", "Actualizar")}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
