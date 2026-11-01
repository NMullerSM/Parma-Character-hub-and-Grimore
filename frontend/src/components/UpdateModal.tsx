import React from "react";
import { ArrowUpCircle, Download, ExternalLink, X, FileText } from "lucide-react";
import { useTranslation } from "../i18n";
import type { GitHubReleaseInfo } from "../api/types";

export interface UpdateModalProps {
  release: GitHubReleaseInfo;
  currentVersion: string;
  onClose: () => void;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({
  release,
  currentVersion,
  onClose,
}) => {
  const { t } = useTranslation();

  const isWindows = typeof navigator !== "undefined" && /win/i.test(navigator.userAgent);
  const isLinux = typeof navigator !== "undefined" && /linux/i.test(navigator.userAgent);

  const exeAsset = release.assets?.find((a) => a.name.toLowerCase().endsWith(".exe"));
  const zipAsset = release.assets?.find((a) => a.name.toLowerCase().includes("windows") && a.name.toLowerCase().endsWith(".zip"));
  const debAsset = release.assets?.find((a) => a.name.toLowerCase().endsWith(".deb"));
  const tarAsset = release.assets?.find((a) => a.name.toLowerCase().includes("linux") && (a.name.toLowerCase().endsWith(".tar.gz") || a.name.toLowerCase().endsWith(".tgz")));

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-pop-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-surface border border-iron rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-iron/80 bg-card/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-accent/15 border border-accent/30 text-accent">
              <ArrowUpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-main flex items-center gap-2">
                <span>{t("updates.modalTitle")}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-accent text-canvas font-mono font-bold">
                  {release.tag_name}
                </span>
              </h2>
              <p className="text-xs text-muted">
                {t("common.version") || "Versión actual"}: <span className="font-mono text-main">{currentVersion}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("updates.close")}
            className="p-1.5 rounded-lg text-muted hover:text-main hover:bg-surface/80 active:scale-95 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body: Changelog / Release Notes */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" />
              <span>{t("updates.releaseNotes")}</span>
            </h3>
            <div className="p-4 rounded-xl border border-iron/60 bg-canvas/60 text-sm text-main whitespace-pre-wrap font-body max-h-60 overflow-y-auto leading-relaxed select-text">
              {release.body?.trim() ? release.body : "Actualización de estabilidad, correcciones y mejoras."}
            </div>
          </div>

          {/* Download Options */}
          <div className="space-y-2.5 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
              {t("common.download") || "Descargas disponibles"}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Primary OS Download (Windows or Linux) */}
              {isWindows && exeAsset && (
                <a
                  href={exeAsset.browser_download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-3 rounded-xl border border-accent bg-accent/15 hover:bg-accent/25 text-main transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <Download className="w-4 h-4 text-accent shrink-0 group-hover:translate-y-0.5 transition-transform" />
                    <div>
                      <div className="text-xs font-bold text-accent">Windows Setup (.exe)</div>
                      <div className="text-[11px] text-muted">{formatFileSize(exeAsset.size)}</div>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-accent text-canvas font-semibold">Recomendado</span>
                </a>
              )}

              {isWindows && zipAsset && (
                <a
                  href={zipAsset.browser_download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-3 rounded-xl border border-iron bg-card/60 hover:bg-card text-main transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <Download className="w-4 h-4 text-muted shrink-0 group-hover:translate-y-0.5 transition-transform" />
                    <div>
                      <div className="text-xs font-semibold">Windows Portable (.zip)</div>
                      <div className="text-[11px] text-muted">{formatFileSize(zipAsset.size)}</div>
                    </div>
                  </div>
                </a>
              )}

              {isLinux && debAsset && (
                <a
                  href={debAsset.browser_download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-3 rounded-xl border border-accent bg-accent/15 hover:bg-accent/25 text-main transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <Download className="w-4 h-4 text-accent shrink-0 group-hover:translate-y-0.5 transition-transform" />
                    <div>
                      <div className="text-xs font-bold text-accent">Paquete Debian / Ubuntu (.deb)</div>
                      <div className="text-[11px] text-muted">{formatFileSize(debAsset.size)}</div>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-accent text-canvas font-semibold">Recomendado</span>
                </a>
              )}

              {isLinux && tarAsset && (
                <a
                  href={tarAsset.browser_download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-3 rounded-xl border border-iron bg-card/60 hover:bg-card text-main transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <Download className="w-4 h-4 text-muted shrink-0 group-hover:translate-y-0.5 transition-transform" />
                    <div>
                      <div className="text-xs font-semibold">Linux Portable (.tar.gz)</div>
                      <div className="text-[11px] text-muted">{formatFileSize(tarAsset.size)}</div>
                    </div>
                  </div>
                </a>
              )}

              {/* Fallback if OS not strictly matched or all platforms shown */}
              {(!isWindows && !isLinux) && (
                <>
                  {exeAsset && (
                    <a
                      href={exeAsset.browser_download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-3 rounded-xl border border-iron bg-card/60 hover:bg-card text-main transition-all"
                    >
                      <span className="text-xs font-semibold">Instalador Windows (.exe)</span>
                      <span className="text-[11px] text-muted">{formatFileSize(exeAsset.size)}</span>
                    </a>
                  )}
                  {debAsset && (
                    <a
                      href={debAsset.browser_download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-3 rounded-xl border border-iron bg-card/60 hover:bg-card text-main transition-all"
                    >
                      <span className="text-xs font-semibold">Paquete Linux (.deb)</span>
                      <span className="text-[11px] text-muted">{formatFileSize(debAsset.size)}</span>
                    </a>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-iron/80 bg-card/40">
          <a
            href={release.html_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted hover:text-accent transition-colors"
          >
            <span>{t("updates.viewOnGitHub")}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-surface border border-iron hover:bg-card text-main active:scale-95 transition-all cursor-pointer"
          >
            {t("updates.close")}
          </button>
        </div>
      </div>
    </div>
  );
};
