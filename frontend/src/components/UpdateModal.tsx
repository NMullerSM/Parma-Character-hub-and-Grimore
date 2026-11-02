import React, { useState, useEffect, useRef } from "react";
import { ArrowUpCircle, Download, ExternalLink, X, FileText, CheckCircle2, AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { GitHubReleaseInfo, UpdateProgress } from "../api/types";
import { safeStorage } from "../utils/storage";

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
    setActionError(null);
    setIsApplyingRestart(true);
    try {
      const res = await api.applyUpdateAndRestart();
      if (!res.success && res.error) {
        setActionError(res.error);
        setIsApplyingRestart(false);
      }
    } catch (err: any) {
      setActionError(err?.message || "Error al reiniciar");
      setIsApplyingRestart(false);
    }
  };

  const isDownloading = activeProgress.status === "downloading";
  const isReadyToRestart = activeProgress.status === "ready_to_restart";
  const hasError = activeProgress.status === "error" || Boolean(actionError);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs select-none">
      <div className="relative w-full max-w-lg bg-surface border border-gold/40 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-pop-in">
        {/* Cabecera del Modal */}
        <div className="px-6 py-4 border-b border-border-iron flex items-center justify-between bg-card/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gold/15 text-gold border border-gold/30">
              <ArrowUpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display font-bold text-lg text-main">
                {t("updates.modalTitle", "Actualización Disponible")}
              </h2>
              <div className="text-xs text-muted flex items-center gap-2">
                <span>{currentVersion}</span>
                <span>→</span>
                <span className="font-mono font-bold text-gold">{release.tag_name}</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted hover:text-main hover:bg-surface transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Insignia de Cero Pérdida de Datos Garantizada */}
          <div className="p-3.5 rounded-xl bg-card border border-emerald-500/30 text-xs text-muted flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-main text-emerald-300">Cero pérdida de datos garantizada</div>
              <div className="text-[11px] mt-0.5 text-muted leading-relaxed">
                Tus personajes, fichas y bases de datos residen en tu carpeta de usuario y nunca se sobreescriben al actualizar.
              </div>
            </div>
          </div>

          {/* Estado de Descarga en Progreso (Barra de estado animada) */}
          {isDownloading && (
            <div className="p-4 rounded-xl bg-card border border-gold/50 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-main flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 text-gold animate-spin" />
                  <span>{t("updates.downloadingTitle", "Descargando Actualización...")}</span>
                </span>
                <span className="font-mono font-bold text-gold">
                  {activeProgress.percent}%
                </span>
              </div>

              {/* Barra de Progreso */}
              <div className="w-full h-2.5 rounded-full bg-surface overflow-hidden border border-border-iron">
                <div
                  className="h-full bg-gradient-to-r from-gold to-gold-hover transition-all duration-300 ease-out"
                  style={{ width: `${Math.max(5, activeProgress.percent)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-muted">
                <span>{t("updates.downloadingDesc", "Descargando en segundo plano...")}</span>
                {activeProgress.total_mb > 0 && (
                  <span className="font-mono">
                    {activeProgress.downloaded_mb} MB / {activeProgress.total_mb} MB
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Estado Listo para Reiniciar */}
          {isReadyToRestart && (
            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/50 space-y-3">
              <div className="flex items-center gap-2.5 text-emerald-300 text-sm font-bold">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>{t("updates.readyToRestartTitle", "¡Actualización Lista para Instalar!")}</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {t(
                  "updates.readyToRestartDesc",
                  "El instalador se ha descargado correctamente. Guarda tus cambios antes de reiniciar."
                )}
              </p>
              <button
                type="button"
                onClick={handleApplyRestart}
                disabled={isApplyingRestart}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-lg active:scale-98 cursor-pointer disabled:opacity-50"
              >
                {isApplyingRestart ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Iniciando instalador...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{t("updates.btnRestartToUpdate", "Reiniciar para actualizar")}</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Mensaje de Error */}
          {hasError && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-xs text-red-300 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <div className="leading-relaxed">
                {actionError || activeProgress.error || "Ocurrió un error durante la actualización."}
              </div>
            </div>
          )}

          {/* Notas de la Versión (Changelog) */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-main flex items-center gap-1.5 uppercase tracking-wider text-muted">
              <FileText className="w-3.5 h-3.5 text-gold" />
              <span>{t("updates.releaseNotes", "Notas del Parche")}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-card/60 border border-border-iron text-xs text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap font-sans leading-relaxed select-text">
              {release.body || "Mejoras de rendimiento, correcciones visuales y optimizaciones generales."}
            </div>
          </div>
        </div>

        {/* Pie del Modal con Acciones */}
        <div className="px-6 py-3 border-t border-border-iron bg-card/40 flex flex-wrap items-center justify-between gap-2">
          {onIgnoreVersion && (
            <button
              type="button"
              onClick={() => onIgnoreVersion(release.tag_name)}
              className="text-[11px] text-muted hover:text-main underline cursor-pointer"
            >
              {t("updates.ignoreVersion", "No volver a avisar de esta versión")}
            </button>
          )}

          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-xl border border-border-iron hover:bg-surface text-xs font-medium text-muted hover:text-main transition-colors cursor-pointer"
            >
              {isDownloading ? "Descargar en segundo plano" : t("common.close", "Cerrar")}
            </button>

            {!isDownloading && !isReadyToRestart && (
              <button
                type="button"
                onClick={handleStartDownload}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-bold text-xs transition-all shadow-sm active:scale-95 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{t("updates.updateBtn", "Actualizar al tiro")}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
