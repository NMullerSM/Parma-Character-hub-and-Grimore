import React, { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { AppSettings } from "../api/types";
import { X, Upload, Palette, Sun, Moon, FolderOpen, RefreshCw, CheckCircle2, BookOpen } from "lucide-react";

export const SettingsView: React.FC<{
  onClose: () => void;
  onReplayTour?: () => void;
  onResetSectionTours?: () => void;
}> = ({
  onClose,
  onReplayTour,
  onResetSectionTours,
}) => {
  const {
    isDark,
    activeFamily,
    themeFamilies,
    setActiveFamily,
    toggleTheme,
  } = useTheme();
  const {
    setUserRole,
    talespireStatus,
    connectTaleSpire,
    refreshTaleSpire,
    showToast,
    characters,
    reloadCharacters,
    selectCharacter,
    language,
    setLanguage,
  } = useCharacter();

  const { t, translateClass } = useTranslation();

  const [settings, setSettings] = useState<AppSettings>({
    theme: "dark-obsidian",
    talespire_mode: "dm",
    talespire_enabled: true,
    talespire_auto_throw: true,
    okf_path: "okf_dnd5e",
    custom_themes_dir: "themes",
  });

  const [autoThrow, setAutoThrow] = useState<boolean>(true);
  const [showIpcDetails, setShowIpcDetails] = useState<boolean>(false);
  const [showCalibration, setShowCalibration] = useState<boolean>(false);
  const [showGuideModal, setShowGuideModal] = useState<boolean>(false);

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getSettings();
        setSettings(s);
        if (typeof s.talespire_auto_throw === "boolean") {
          setAutoThrow(s.talespire_auto_throw);
        }
      } catch (e) {
        console.error("Error loading settings:", e);
      }
    }
    load();
  }, []);

  // Ley de Hick: Salida rápida con tecla Escape (cierra primero modal de guía si está abierto)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (showGuideModal) {
          setShowGuideModal(false);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, showGuideModal]);

  const handleModeChange = async (mode: "dm" | "player") => {
    setSettings((prev) => ({ ...prev, talespire_mode: mode }));
    await setUserRole(mode);
  };

  const handleThrowModeChange = async (auto: boolean) => {
    setAutoThrow(auto);
    setSettings((prev) => ({ ...prev, talespire_auto_throw: auto }));
    await api.setSetting("talespire_auto_throw", auto ? "true" : "false");
    showToast(
      auto
        ? (t("settings.throwModeAuto") || "Lanzamiento automático activado")
        : (t("settings.throwModeManual") || "Bandeja manual activada"),
      "info"
    );
  };

  const handleLanguageChange = async (lang: "es" | "en") => {
    await setLanguage(lang);
    await api.setSetting("language", lang);
  };

  const handleTestGesture = async () => {
    showToast(t("settings.testingGesture"), "info");
    const success = await api.triggerTaleSpireGesture();
    if (success) {
      showToast(t("settings.gestureSuccess"), "success");
    } else {
      showToast(t("settings.gestureFailed"), "warn");
    }
  };

  const handleReinstallSymbiote = async () => {
    try {
      showToast("Comprobando e instalando Symbiote en TaleSpire...", "info");
      const res = await api.reinstallTaleSpireSymbiote();
      await refreshTaleSpire();
      if (res.success) {
        showToast(res.message || "Symbiote cargado correctamente en TaleSpire", "success");
      } else {
        showToast(res.error || res.message || "TaleSpire no detectado en el equipo", "warn");
      }
    } catch (e) {
      showToast("Error al sincronizar Symbiote", "warn");
    }
  };

  const handleOpenSymbiotesFolder = async () => {
    try {
      const res = await api.openTaleSpireSymbiotesFolder();
      if (!res.success) {
        showToast(res.error || "No se pudo abrir la carpeta", "warn");
      }
    } catch (e) {
      showToast("Error al abrir carpeta de Symbiotes", "warn");
    }
  };

  const handleDeleteCharacter = async (id: number, charName: string) => {
    if (window.confirm(t("settings.confirmDeleteChar", { name: charName }))) {
      await api.deleteCharacter(id);
      await reloadCharacters();
      showToast(t("settings.charDeleted", { name: charName }), "info");
    }
  };

  const handleImportPdf = async () => {
    try {
      const res = await api.importCharacterPdf();
      if (res.success && res.character) {
        await reloadCharacters();
        showToast(t("settings.importedPdf", { name: res.character.name }), "success");
      } else if (res.error && res.error !== "Importación cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast(t("settings.importPdfError"), "warn");
    }
  };

  const handleImportJson = async () => {
    try {
      const res = await api.importCharacterJson();
      if (res.success && res.character) {
        await reloadCharacters();
        showToast(t("settings.importedJson", { name: res.character.name }), "success");
      } else if (res.error && res.error !== "Importación cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast(t("settings.importJsonError"), "warn");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-xs" onClick={onClose} />

      {/* Modal Centrado */}
      <div className="relative w-full max-w-2xl bg-surface border border-border-iron rounded-2xl shadow-2xl flex flex-col max-h-[85vh] z-10 select-none overflow-hidden">
        {/* Header del Modal */}
        <div className="px-6 py-4 border-b border-border-iron flex items-center justify-between">
          <div>
            <h2 className="font-display font-bold text-xl text-gold">{t("settings.title")}</h2>
            <p className="text-xs text-muted">{t("settings.subtitle")}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted hover:text-main hover:bg-card transition-colors cursor-pointer"
            title={`${t("common.close")} (Esc)`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido con Scroll */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* 1. Selector de Tema Visual (Combobox unificado con toggle compacto Sol/Luna) */}
          <section className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
              <Palette className="w-3.5 h-3.5 text-gold" />
              <span>{t("settings.visualTheme")}</span>
            </h3>

            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <select
                  value={activeFamily}
                  onChange={(e) => setActiveFamily(e.target.value)}
                  className="w-full bg-card text-main border border-border-iron rounded-xl px-4 py-2.5 text-sm font-semibold focus:border-gold outline-none transition-colors appearance-none cursor-pointer pr-10 shadow-xs"
                >
                  {themeFamilies.map((fam) => (
                    <option key={fam.id} value={fam.id} className="bg-surface text-main py-1.5">
                      {fam.name} {fam.id === "obsidian" || fam.id === "parchment" || fam.id === "amethyst" || fam.id === "mithril" ? "" : "⭐ [Homebrew]"}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted text-xs">
                  ▼
                </div>
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                className="p-2.5 rounded-xl border border-border-iron bg-card/60 hover:bg-card hover:border-gold/60 text-main transition-colors shadow-xs flex items-center justify-center shrink-0 cursor-pointer"
                title={isDark ? "Cambiar a variante Clara" : "Cambiar a variante Oscura"}
              >
                {isDark ? (
                  <Sun className="w-4 h-4 text-amber-300" />
                ) : (
                  <Moon className="w-4 h-4 text-sky-400" />
                )}
              </button>
            </div>
          </section>

          {/* 2. Selector de Idioma de la Interfaz & Compendio (Segmented Switch) */}
          <section className="space-y-2 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.languageSectionTitle")}
            </h3>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleLanguageChange("es")}
                className={`flex-1 py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                  language === "es"
                    ? "bg-card border-gold text-gold shadow-xs ring-1 ring-gold/40"
                    : "bg-surface/60 border-border-iron text-muted hover:text-main hover:bg-card"
                }`}
              >
                <span>🇪🇸</span>
                <span>Español (ES)</span>
                {language === "es" && <span className="w-1.5 h-1.5 rounded-full bg-gold shrink-0" />}
              </button>
              <button
                type="button"
                onClick={() => handleLanguageChange("en")}
                className={`flex-1 py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                  language === "en"
                    ? "bg-card border-gold text-gold shadow-xs ring-1 ring-gold/40"
                    : "bg-surface/60 border-border-iron text-muted hover:text-main hover:bg-card"
                }`}
              >
                <span>🇬🇧</span>
                <span>English (EN)</span>
                {language === "en" && <span className="w-1.5 h-1.5 rounded-full bg-gold shrink-0" />}
              </button>
            </div>
          </section>

          {/* 3. Integración con TaleSpire */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.talespireTitle")}
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              {/* Estado y Conexión */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-main">{t("settings.ipcStatus")}</div>
                  <div className="text-xs text-muted mt-0.5 flex items-center gap-2">
                    <span>{t("settings.ipcStateLabel")}</span>
                    <span className="font-semibold text-gold capitalize">{talespireStatus.state_label.replace("_", " ")}</span>
                    {talespireStatus.symbiote_connected && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/40">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Symbiote Live
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={connectTaleSpire}
                  className="px-3 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main transition-colors cursor-pointer"
                >
                  {t("settings.connectRefresh")}
                </button>
              </div>

              {/* Conmutador de Modo de Lanzamiento (Automático vs Manual) */}
              <div className="pt-2 border-t border-border-iron/40 space-y-2">
                <label className="text-xs font-semibold text-main block">
                  {t("settings.talespireThrowMode") || "Modo de Lanzamiento en TaleSpire"}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleThrowModeChange(true)}
                    className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                      autoThrow
                        ? "border-gold bg-surface ring-1 ring-gold/40 shadow-xs"
                        : "border-border-iron bg-card/40 hover:bg-card text-muted hover:text-main"
                    }`}
                  >
                    <div className="text-xs font-semibold flex items-center gap-1.5">
                      <span>⚡</span>
                      <span className={autoThrow ? "text-gold" : "text-main"}>
                        {t("settings.throwModeAuto") || "Automático (Micro-gesto 3D)"}
                      </span>
                    </div>
                    <div className="text-[11px] text-muted mt-1 leading-snug">
                      {t("settings.throwModeAutoDesc") || "Coloca los dados en la bandeja y ejecuta el lanzamiento físico automático hacia la mesa."}
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleThrowModeChange(false)}
                    className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                      !autoThrow
                        ? "border-gold bg-surface ring-1 ring-gold/40 shadow-xs"
                        : "border-border-iron bg-card/40 hover:bg-card text-muted hover:text-main"
                    }`}
                  >
                    <div className="text-xs font-semibold flex items-center gap-1.5">
                      <span>✋</span>
                      <span className={!autoThrow ? "text-gold" : "text-main"}>
                        {t("settings.throwModeManual") || "Bandeja Manual (Oficial)"}
                      </span>
                    </div>
                    <div className="text-[11px] text-muted mt-1 leading-snug">
                      {t("settings.throwModeManualDesc") || "Coloca en bandeja; tú decides cuándo lanzar haciendo clic o arrastrando con el ratón."}
                    </div>
                  </button>
                </div>
              </div>

              {/* Detalles Técnicos & Estados LED (Acordeón desplegable) */}
              <div className="pt-2 border-t border-border-iron/40">
                <button
                  type="button"
                  onClick={() => setShowIpcDetails(!showIpcDetails)}
                  className="w-full flex items-center justify-between py-1 text-xs text-muted hover:text-gold transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-1.5 font-medium">
                    <span>{showIpcDetails ? "▼" : "▶"}</span>
                    <span>{t("settings.ipcDetailsToggle") || "Detalles Técnicos & Estados LED"}</span>
                  </span>
                  <span className="text-[10px] uppercase font-mono text-muted">{showIpcDetails ? "Ocultar" : "Mostrar"}</span>
                </button>

                {showIpcDetails && (
                  <div className="mt-3 space-y-3 pt-2 border-t border-border-iron/30">
                    {/* Leyenda Visual de Estados LED */}
                    <div className="grid grid-cols-1 gap-1.5 text-[11px] text-muted">
                      <div className="flex items-start gap-2 bg-surface/40 p-2 rounded-lg border border-border-iron/50">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)] shrink-0 mt-0.5" />
                        <span>{t("settings.talespireLegendGreen")}</span>
                      </div>
                      <div className="flex items-start gap-2 bg-surface/40 p-2 rounded-lg border border-border-iron/50">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse shrink-0 mt-0.5" />
                        <span>{t("settings.talespireLegendAmber")}</span>
                      </div>
                      <div className="flex items-start gap-2 bg-surface/40 p-2 rounded-lg border border-border-iron/50">
                        <span className="w-2.5 h-2.5 rounded-full bg-slate-500 shrink-0 mt-0.5" />
                        <span>{t("settings.talespireLegendGray")}</span>
                      </div>
                    </div>

                    {/* Explicación del Symbiote */}
                    <div className="p-3 rounded-lg bg-surface/60 border border-border-iron text-xs text-muted flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-gold/10 text-gold shrink-0">🎲</div>
                      <div>{t("settings.talespireSymbioteHint")}</div>
                    </div>

                    {/* Detección y Sincronización del Symbiote */}
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-semibold text-main flex items-center gap-1.5">
                        <CheckCircle2 className={`w-3.5 h-3.5 ${talespireStatus.symbiote_folder_installed ? "text-emerald-400" : "text-muted"}`} />
                        <span>{t("settings.talespireAutoInstallTitle")}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={handleReinstallSymbiote}
                          className="px-2 py-1 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-[11px] font-medium text-main flex items-center gap-1 transition-colors cursor-pointer"
                          title="Sincronizar y forzar actualización del Symbiote en TaleSpire"
                        >
                          <RefreshCw className="w-3 h-3 text-gold" />
                          <span>{t("settings.talespireBtnReinstall")}</span>
                        </button>
                        {talespireStatus.symbiote_install_path && (
                          <button
                            type="button"
                            onClick={handleOpenSymbiotesFolder}
                            className="px-2 py-1 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-[11px] font-medium text-main flex items-center gap-1 transition-colors cursor-pointer"
                            title="Abrir la carpeta oficial de Symbiotes en el explorador de archivos"
                          >
                            <FolderOpen className="w-3 h-3 text-sky-400" />
                            <span>{t("settings.talespireBtnOpenFolder")}</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {talespireStatus.symbiote_folder_installed ? (
                      <div className="bg-surface/40 p-2.5 rounded-lg border border-border-iron/60 text-[11px] space-y-1">
                        <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          <span>{t("settings.talespireAutoInstalled")}</span>
                        </div>
                        <div className="text-muted font-stat text-[10px] break-all bg-card/60 p-1.5 rounded border border-border-iron/40 select-all">
                          {talespireStatus.symbiote_install_path}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-surface/30 p-2.5 rounded-lg border border-border-iron/40 text-[11px] text-muted">
                        {t("settings.talespireNotDetectedHint")}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Opciones Avanzadas de Calibración de Cursor (Acordeón desplegable) */}
              <div className="pt-2 border-t border-border-iron/40">
                <button
                  type="button"
                  onClick={() => setShowCalibration(!showCalibration)}
                  className="w-full flex items-center justify-between py-1 text-xs text-muted hover:text-gold transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-1.5 font-medium">
                    <span>{showCalibration ? "▼" : "▶"}</span>
                    <span>⚙️ {t("settings.calibrationAdvanced") || "Calibración de Altura (Modo DM / Jugador)"}</span>
                  </span>
                  <span className="text-[10px] uppercase font-mono text-muted">{showCalibration ? "Ocultar" : "Mostrar"}</span>
                </button>

                {showCalibration && (
                  <div className="mt-3 space-y-2 pt-2 border-t border-border-iron/30">
                    <label className="block text-xs text-muted font-medium">
                      {t("settings.calibrationLabel")}
                    </label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleModeChange("dm")}
                        className={`flex-1 py-1.5 rounded-lg border text-xs font-semibold transition-colors cursor-pointer ${
                          settings.talespire_mode === "dm"
                            ? "bg-gold text-canvas border-gold"
                            : "border-border-iron bg-surface text-muted hover:text-main"
                        }`}
                      >
                        {t("settings.dmMode")}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleModeChange("player")}
                        className={`flex-1 py-1.5 rounded-lg border text-xs font-semibold transition-colors cursor-pointer ${
                          settings.talespire_mode === "player"
                            ? "bg-gold text-canvas border-gold"
                            : "border-border-iron bg-surface text-muted hover:text-main"
                        }`}
                      >
                        {t("settings.playerMode")}
                      </button>
                    </div>
                    <div className="flex justify-end pt-1">
                      <button
                        type="button"
                        onClick={handleTestGesture}
                        className="text-xs text-gold hover:underline font-medium cursor-pointer"
                      >
                        {t("settings.testGesture")}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* 4. Guías & Aprendizaje (Modal y Reinicio de Tours) */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5 text-gold" />
              <span>{t("settings.guideSectionTitle") || "Guías & Aprendizaje"}</span>
            </h3>
            <div className="p-4 rounded-xl border border-border-iron bg-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="text-xs text-muted max-w-sm">
                Consulta la guía completa de funcionalidades de Parma o reinicia los tutoriales guiados en cualquier momento.
              </div>
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setShowGuideModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <BookOpen className="w-3.5 h-3.5 text-gold" />
                  <span>{t("settings.openGuideModal") || "Ver Guía de Parma"}</span>
                </button>
                {onReplayTour && (
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onReplayTour();
                    }}
                    className="px-3 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-muted hover:text-main flex items-center gap-1.5 transition-colors cursor-pointer"
                    title="Repetir el tour guiado por la aplicación"
                  >
                    <RefreshCw className="w-3.5 h-3.5 text-gold" />
                    <span>{t("onboarding.replayTour") || "Tour de Bienvenida"}</span>
                  </button>
                )}
                {onResetSectionTours && (
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm(t("settings.resetToursConfirm") || "¿Deseas restablecer los tutoriales y guías interactivas para volver a verlos?")) {
                        onResetSectionTours();
                        showToast(t("onboarding.sectionToursResetSuccess") || "Tutoriales reiniciados", "success");
                      }
                    }}
                    className="px-2.5 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-muted hover:text-main flex items-center gap-1 transition-colors cursor-pointer"
                    title="Reiniciar los tutoriales de secciones individuales"
                  >
                    <RefreshCw className="w-3 h-3 text-muted" />
                    <span>{t("onboarding.resetSectionTours") || "Reiniciar guías"}</span>
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* 5. Fuentes de Datos OKF (Reubicado limpiamente al final) */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.okfTitle")}
            </h3>

            <div className="p-3.5 rounded-xl border border-border-iron bg-card/60 flex items-center justify-between text-xs">
              <span className="text-muted">{t("settings.okfPath")}</span>
              <span className="font-stat text-main bg-surface px-2.5 py-1 rounded-lg border border-border-iron text-[11px] truncate max-w-[280px]">
                {settings.okf_path}
              </span>
            </div>
          </section>

          {/* 6. Gestión e Importación de Personajes (Reubicado limpiamente al final) */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                {t("settings.charactersTitle")}
              </h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleImportPdf}
                  className="px-2.5 py-1 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{t("settings.importPdf")}</span>
                </button>
                <button
                  type="button"
                  onClick={handleImportJson}
                  className="px-2.5 py-1 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{t("settings.importJson")}</span>
                </button>
              </div>
            </div>

            <div className="bg-card border border-border-iron rounded-xl divide-y divide-border-iron/60 overflow-hidden">
              {characters.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted">
                  No hay personajes guardados en la base de datos local.
                </div>
              ) : (
                characters.map((c) => (
                  <div key={c.id} className="p-3 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-main">{c.name}</span>
                      <span className="text-muted ml-2">
                        {t("header.levelShort")} {c.level} {translateClass(c.char_class)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          selectCharacter(c.id);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded-lg bg-surface border border-border-iron hover:border-gold text-muted hover:text-main cursor-pointer"
                      >
                        {t("settings.load")}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteCharacter(c.id, c.name)}
                        className="px-2 py-1 rounded-lg text-crimson hover:bg-crimson/10 border border-transparent hover:border-crimson/40 cursor-pointer"
                      >
                        {t("settings.delete")}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        {/* Footer del Modal */}
        <div className="px-6 py-3 border-t border-border-iron flex justify-end bg-card/40">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-1.5 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs transition-colors shadow-sm cursor-pointer"
          >
            {t("settings.acceptClose")}
          </button>
        </div>
      </div>

      {/* Modal Implícito de Guía de Parma */}
      {showGuideModal && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-xs" onClick={() => setShowGuideModal(false)} />
          <div className="relative w-full max-w-xl bg-surface border border-border-iron rounded-2xl shadow-2xl flex flex-col max-h-[80vh] z-10 overflow-hidden select-none">
            {/* Cabecera de la Guía */}
            <div className="px-6 py-4 border-b border-border-iron flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="p-2 rounded-lg bg-gold/10 text-gold text-base">📖</span>
                <div>
                  <h3 className="font-display font-bold text-lg text-gold">{t("settings.guideModalTitle") || "Guía Rápida de Parma D&D"}</h3>
                  <p className="text-xs text-muted">Tu asistente de escritorio para D&D 2024 y 5e</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowGuideModal(false)}
                className="p-1.5 rounded-lg text-muted hover:text-main hover:bg-card transition-colors cursor-pointer"
                title="Cerrar Guía (Esc)"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido Desplazable de la Guía */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              <div className="p-3.5 rounded-xl bg-card border border-border-iron/80 space-y-1.5">
                <div className="font-semibold text-main text-sm flex items-center gap-2">
                  <span>🛡️</span>
                  <span>Hoja de Personaje & Atributos</span>
                </div>
                <p className="text-muted leading-relaxed">
                  Calcula automáticamente modificadores de características, bonificador de competencia, tiradas de salvación y ataques. Las 18 habilidades oficiales y armamento se sincronizan con las reglas de D&D.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-card border border-border-iron/80 space-y-1.5">
                <div className="font-semibold text-main text-sm flex items-center gap-2">
                  <span>⚡</span>
                  <span>Reglas Dinámicas 2024 / 5e Clásica</span>
                </div>
                <p className="text-muted leading-relaxed">
                  Conmuta en cualquier momento desde la barra superior entre las reglas 2024 (5.5e) y 5e clásicas. Las descripciones de dotes, trasfondos y conjuros se adaptan en tiempo real según la edición seleccionada.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-card border border-border-iron/80 space-y-1.5">
                <div className="font-semibold text-main text-sm flex items-center gap-2">
                  <span>🔮</span>
                  <span>Grimorio Arcano & Ranuras de Conjuro</span>
                </div>
                <p className="text-muted leading-relaxed">
                  Gestiona tus espacios mágicos con gemas interactivas que se restablecen con descanso largo. Filtra conjuros por nivel o escuela y añade hechizos caseros o del compendio oficial OKF.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-card border border-border-iron/80 space-y-1.5">
                <div className="font-semibold text-main text-sm flex items-center gap-2">
                  <span>🎲</span>
                  <span>Bandeja de Dados & TaleSpire 3D</span>
                </div>
                <p className="text-muted leading-relaxed">
                  Lanza dados tácticos con ventaja, desventaja y cálculo de éxito contra CD. Si tienes TaleSpire abierto, Parma envía las tiradas a tu mesa 3D mediante el Symbiote oficial con resolución física real.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-card border border-border-iron/80 space-y-1.5">
                <div className="font-semibold text-main text-sm flex items-center gap-2">
                  <span>⌨️</span>
                  <span>Atajos de Teclado Tácticos</span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                  <div className="flex items-center gap-2 bg-surface/50 p-2 rounded-lg border border-border-iron/50">
                    <kbd className="px-2 py-0.5 rounded bg-card border border-border-iron font-mono text-gold font-bold">Espacio</kbd>
                    <span className="text-muted">Bandeja de dados</span>
                  </div>
                  <div className="flex items-center gap-2 bg-surface/50 p-2 rounded-lg border border-border-iron/50">
                    <kbd className="px-2 py-0.5 rounded bg-card border border-border-iron font-mono text-gold font-bold">Esc</kbd>
                    <span className="text-muted">Cerrar modales</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer de la Guía */}
            <div className="px-6 py-3 border-t border-border-iron flex justify-end bg-card/40">
              <button
                type="button"
                onClick={() => setShowGuideModal(false)}
                className="px-5 py-1.5 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs transition-colors shadow-sm cursor-pointer"
              >
                {t("settings.closeGuideModal") || "Entendido, Cerrar Guía"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
