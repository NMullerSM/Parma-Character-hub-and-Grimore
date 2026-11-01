import React, { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { AppSettings } from "../api/types";
import { X, Upload, Palette, Sun, Moon, FolderOpen, RefreshCw, CheckCircle2, BookOpen } from "lucide-react";

export const SettingsView: React.FC<{ onClose: () => void; onReplayTour?: () => void }> = ({
  onClose,
  onReplayTour,
}) => {
  const {
    theme,
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
    okf_path: "okf_dnd5e",
    custom_themes_dir: "themes",
  });

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getSettings();
        setSettings(s);
      } catch (e) {
        console.error("Error loading settings:", e);
      }
    }
    load();
  }, []);

  // Ley de Hick: Salida rápida con tecla Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleModeChange = async (mode: "dm" | "player") => {
    setSettings((prev) => ({ ...prev, talespire_mode: mode }));
    await setUserRole(mode);
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
            className="p-1 rounded text-muted hover:text-main hover:bg-card transition-colors"
            title={`${t("common.close")} (Esc)`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido con Scroll */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* 1. Selector de Tema Visual (Combobox unificado con soporte Homebrew y alternancia Claro/Oscuro) */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
                <Palette className="w-3.5 h-3.5 text-gold" />
                <span>{t("settings.visualTheme")}</span>
              </h3>
              <button
                onClick={toggleTheme}
                className="flex items-center gap-1.5 px-3 py-1 text-xs rounded-lg border border-border-iron bg-card/60 hover:bg-card hover:border-gold/60 text-main transition-colors shadow-xs"
                title="Alternar entre variante Clara y Oscura de la familia seleccionada"
              >
                {isDark ? (
                  <>
                    <Sun className="w-3.5 h-3.5 text-amber-300" />
                    <span>Variante: <strong>Oscuro</strong></span>
                  </>
                ) : (
                  <>
                    <Moon className="w-3.5 h-3.5 text-sky-400" />
                    <span>Variante: <strong>Claro</strong></span>
                  </>
                )}
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-muted block">
                Familia visual o tema personalizado (incluye temas creados en la carpeta <code className="text-gold font-mono">themes/</code>):
              </label>
              <div className="relative">
                <select
                  value={activeFamily}
                  onChange={(e) => setActiveFamily(e.target.value)}
                  className="w-full bg-card text-main border border-border-iron rounded-xl px-4 py-3 text-sm font-semibold focus:border-gold outline-none transition-colors appearance-none cursor-pointer pr-10 shadow-xs"
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
            </div>

            <div className="p-3 rounded-xl bg-card/40 border border-border-iron text-xs text-muted flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div>
                Tema activo: <span className="font-semibold text-main">{theme}</span>
              </div>
              <div className="text-[11px] text-muted">
                💡 Alterna claro/oscuro fácilmente con el botón de sol/luna ☀️/🌙 en la barra superior.
              </div>
            </div>
          </section>

          {/* Selector de Idioma de la Interfaz & Compendio (ES / EN) */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.languageSectionTitle")}
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setLanguage("es")}
                className={`p-3 rounded-lg border text-left transition-all ${
                  language === "es"
                    ? "border-gold bg-card ring-1 ring-gold shadow-sm"
                    : "border-border-iron bg-card/40 hover:bg-card hover:border-gold/50"
                }`}
              >
                <div className="font-semibold text-sm text-main flex items-center justify-between">
                  <span>{t("settings.langEsTitle")}</span>
                  {language === "es" && (
                    <span className="text-[10px] text-gold font-bold">
                      {t("settings.langActiveBadge")}
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted mt-0.5">{t("settings.langEsDesc")}</div>
              </button>
              <button
                onClick={() => setLanguage("en")}
                className={`p-3 rounded-lg border text-left transition-all ${
                  language === "en"
                    ? "border-gold bg-card ring-1 ring-gold shadow-sm"
                    : "border-border-iron bg-card/40 hover:bg-card hover:border-gold/50"
                }`}
              >
                <div className="font-semibold text-sm text-main flex items-center justify-between">
                  <span>{t("settings.langEnTitle")}</span>
                  {language === "en" && (
                    <span className="text-[10px] text-gold font-bold">
                      {t("settings.langActiveBadge")}
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted mt-0.5">{t("settings.langEnDesc")}</div>
              </button>
            </div>
          </section>

          {/* 2. Integración con TaleSpire */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.talespireTitle")}
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
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
                  onClick={connectTaleSpire}
                  className="px-3 py-1.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main transition-colors"
                >
                  {t("settings.connectRefresh")}
                </button>
              </div>

              {/* Leyenda Visual de Estados LED */}
              <div className="pt-2 border-t border-border-iron/40 space-y-2">
                <div className="text-xs font-semibold text-main">{t("settings.talespireLegendTitle")}</div>
                <div className="grid grid-cols-1 gap-1.5 text-[11px] text-muted">
                  <div className="flex items-start gap-2 bg-surface/40 p-2 rounded border border-border-iron/50">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)] shrink-0 mt-0.5" />
                    <span>{t("settings.talespireLegendGreen")}</span>
                  </div>
                  <div className="flex items-start gap-2 bg-surface/40 p-2 rounded border border-border-iron/50">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse shrink-0 mt-0.5" />
                    <span>{t("settings.talespireLegendAmber")}</span>
                  </div>
                  <div className="flex items-start gap-2 bg-surface/40 p-2 rounded border border-border-iron/50">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-500 shrink-0 mt-0.5" />
                    <span>{t("settings.talespireLegendGray")}</span>
                  </div>
                </div>
              </div>

              {/* Explicación de Funcionamiento del Symbiote */}
              <div className="p-3 rounded-lg bg-surface/60 border border-border-iron text-xs text-muted flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-gold/10 text-gold shrink-0">🎲</div>
                <div>{t("settings.talespireSymbioteHint")}</div>
              </div>

              {/* Carga y Detección Automática del Symbiote */}
              <div className="pt-2 border-t border-border-iron/40 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-main flex items-center gap-1.5">
                    <CheckCircle2 className={`w-3.5 h-3.5 ${talespireStatus.symbiote_folder_installed ? "text-emerald-400" : "text-muted"}`} />
                    <span>{t("settings.talespireAutoInstallTitle")}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={handleReinstallSymbiote}
                      className="px-2 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-[11px] font-medium text-main flex items-center gap-1 transition-colors"
                      title="Sincronizar y forzar actualización del Symbiote en TaleSpire"
                    >
                      <RefreshCw className="w-3 h-3 text-gold" />
                      <span>{t("settings.talespireBtnReinstall")}</span>
                    </button>
                    {talespireStatus.symbiote_install_path && (
                      <button
                        onClick={handleOpenSymbiotesFolder}
                        className="px-2 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-[11px] font-medium text-main flex items-center gap-1 transition-colors"
                        title="Abrir la carpeta oficial de Symbiotes en el explorador de archivos"
                      >
                        <FolderOpen className="w-3 h-3 text-sky-400" />
                        <span>{t("settings.talespireBtnOpenFolder")}</span>
                      </button>
                    )}
                  </div>
                </div>

                {talespireStatus.symbiote_folder_installed ? (
                  <div className="bg-surface/40 p-2.5 rounded border border-border-iron/60 text-[11px] space-y-1">
                    <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>{t("settings.talespireAutoInstalled")}</span>
                    </div>
                    <div className="text-muted font-stat text-[10px] break-all bg-card/60 p-1.5 rounded border border-border-iron/40 select-all">
                      {talespireStatus.symbiote_install_path}
                    </div>
                  </div>
                ) : (
                  <div className="bg-surface/30 p-2.5 rounded border border-border-iron/40 text-[11px] text-muted">
                    {t("settings.talespireNotDetectedHint")}
                  </div>
                )}
              </div>

              {/* Modo de Altura del Cursor */}
              <div className="pt-2 border-t border-border-iron/40">
                <label className="block text-xs text-muted mb-1.5 font-medium">
                  {t("settings.calibrationLabel")}
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleModeChange("dm")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "dm"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    {t("settings.dmMode")}
                  </button>
                  <button
                    onClick={() => handleModeChange("player")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "player"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    {t("settings.playerMode")}
                  </button>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleTestGesture}
                  className="text-xs text-gold hover:underline font-medium"
                >
                  {t("settings.testGesture")}
                </button>
              </div>
            </div>
          </section>

          {/* 3. Fuentes de Datos OKF */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("settings.okfTitle")}
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">{t("settings.okfPath")}</span>
                <span className="font-stat text-main bg-surface px-2 py-0.5 rounded border border-border-iron">
                  {settings.okf_path}
                </span>
              </div>
            </div>
          </section>

          {/* Guía y Tutorial Interactivo */}
          {onReplayTour && (
            <section className="space-y-3 pt-3 border-t border-border-iron">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-gold" />
                <span>{t("onboarding.replayTour")}</span>
              </h3>
              <div className="p-4 rounded-xl border border-border-iron bg-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="text-xs text-muted max-w-sm">
                  {t("onboarding.subtitleWelcome")}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onReplayTour();
                  }}
                  className="px-3 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
                >
                  <BookOpen className="w-3.5 h-3.5 text-gold" />
                  <span>{t("onboarding.replayTour")}</span>
                </button>
              </div>
            </section>
          )}

          {/* 4. Gestión e Importación de Personajes */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                {t("settings.charactersTitle")}
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleImportPdf}
                  className="px-2.5 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{t("settings.importPdf")}</span>
                </button>
                <button
                  onClick={handleImportJson}
                  className="px-2.5 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{t("settings.importJson")}</span>
                </button>
              </div>
            </div>

            <div className="bg-card border border-border-iron rounded-xl divide-y divide-border-iron/60 overflow-hidden">
              {characters.map((c) => (
                <div key={c.id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-main">{c.name}</span>
                    <span className="text-muted ml-2">
                      {t("header.levelShort")} {c.level} {translateClass(c.char_class)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        selectCharacter(c.id);
                        onClose();
                      }}
                      className="px-2.5 py-1 rounded bg-surface border border-border-iron hover:border-gold text-muted hover:text-main"
                    >
                      {t("settings.load")}
                    </button>
                    <button
                      onClick={() => handleDeleteCharacter(c.id, c.name)}
                      className="px-2 py-1 rounded text-crimson hover:bg-crimson/10 border border-transparent hover:border-crimson/40"
                    >
                      {t("settings.delete")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Footer del Modal */}
        <div className="px-6 py-3 border-t border-border-iron flex justify-end bg-card/40">
          <button
            onClick={onClose}
            className="px-5 py-1.5 rounded bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs transition-colors shadow-sm"
          >
            {t("settings.acceptClose")}
          </button>
        </div>
      </div>
    </div>
  );
};