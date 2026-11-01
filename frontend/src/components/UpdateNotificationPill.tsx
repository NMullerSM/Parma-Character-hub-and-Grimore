import React from "react";
import { ArrowUpCircle, X } from "lucide-react";
import { useTranslation } from "../i18n";
import type { GitHubReleaseInfo } from "../api/types";

export interface UpdateNotificationPillProps {
  release: GitHubReleaseInfo;
  onOpenModal: () => void;
  onDismiss: () => void;
}

export const UpdateNotificationPill: React.FC<UpdateNotificationPillProps> = ({
  release,
  onOpenModal,
  onDismiss,
}) => {
  const { t } = useTranslation();

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-4 left-4 z-40 flex items-center gap-3 px-3.5 py-2.5 rounded-xl border border-accent/60 bg-card/95 backdrop-blur-md shadow-2xl animate-pop-in transition-all duration-200 hover:border-accent"
    >
      <div className="flex items-center gap-2 text-sm">
        <ArrowUpCircle className="w-4 h-4 text-accent shrink-0" />
        <span className="font-semibold text-main tracking-tight">
          {t("updates.newVersionAvailable")}
        </span>
        <span className="px-1.5 py-0.5 rounded bg-accent/15 border border-accent/30 text-xs font-mono font-bold text-accent">
          {release.tag_name}
        </span>
      </div>

      <div className="flex items-center gap-1.5 pl-2 border-l border-iron/60">
        <button
          type="button"
          onClick={onOpenModal}
          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-accent text-canvas hover:brightness-110 active:scale-95 transition-all shadow-sm cursor-pointer"
        >
          {t("updates.updateBtn")}
        </button>

        <button
          type="button"
          onClick={onDismiss}
          title={t("updates.dismiss")}
          aria-label={t("updates.dismiss")}
          className="p-1 rounded-lg text-muted hover:text-main hover:bg-surface/80 active:scale-90 transition-all cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
