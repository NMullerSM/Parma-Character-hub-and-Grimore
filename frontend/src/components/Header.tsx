import React from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTheme } from "../context/ThemeContext";
import { useTranslation } from "../i18n";
import { Dice5, Settings as SettingsIcon, Sun, Moon } from "lucide-react";
import logoEsDark from "../assets/logo/parma-logo-es-dark.svg";
import logoEsLight from "../assets/logo/parma-logo-es-light.svg";
import logoEnDark from "../assets/logo/parma-logo-en-dark.svg";
import logoEnLight from "../assets/logo/parma-logo-en-light.svg";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  openSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, openSettings }) => {
  const {
    activeCharacter,
    characters,
    selectCharacter,
    talespireStatus,
    connectTaleSpire,
    openDiceDrawer,
    dndEdition,
    setDndEdition,
    language,
  } = useCharacter();
  const { isDark, toggleTheme } = useTheme();
  const { t, translateClass } = useTranslation();

  const currentLogo = language === "es"
    ? (isDark ? logoEsDark : logoEsLight)
    : (isDark ? logoEnDark : logoEnLight);

  const tabs = [
    { id: "sheet", label: t("header.tabSheet") },
    { id: "combat", label: t("header.tabCombat") },
    { id: "spells", label: t("header.tabSpells") },
    { id: "journal", label: t("header.tabJournal") },
    { id: "network", label: t("header.tabNetwork") },
    { id: "pdf", label: t("header.tabPdf") },
    { id: "compendium", label: t("header.tabCompendium") },
    { id: "forge", label: t("header.tabForge") },
  ];

  return (
    <header className="h-16 border-b border-border-iron bg-surface px-2 sm:px-4 md:px-6 flex items-center justify-between shrink-0 select-none shadow-xs gap-2">
      {/* Título de Marca, Selector de Versión y Selector de Personaje Activo */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <div
          className="flex items-center cursor-pointer py-1"
          onClick={() => setActiveTab("sheet")}
          title="Parma — Character Hub & Grimoire"
        >
          <img
            src={currentLogo}
            alt="Parma — Character Hub & Grimoire"
            className="h-10 sm:h-11 w-auto object-contain"
          />
        </div>

        {/* Selector de Versión D&D (5.5e 2024 vs 5e 2014) */}
        <div className="flex items-center bg-card border border-border-iron rounded-md p-0.5 text-[11px] font-stat font-semibold">
          <button
            onClick={() => setDndEdition("5.5e")}
            title={t("header.edition55Tooltip")}
            className={`px-1.5 sm:px-2 py-0.5 rounded transition-all ${
              dndEdition === "5.5e"
                ? "bg-gold text-canvas font-bold"
                : "text-muted hover:text-main"
            }`}
          >
            5.5e
          </button>
          <button
            onClick={() => setDndEdition("5e")}
            title={t("header.edition5eTooltip")}
            className={`px-1.5 sm:px-2 py-0.5 rounded transition-all ${
              dndEdition === "5e"
                ? "bg-gold text-canvas font-bold"
                : "text-muted hover:text-main"
            }`}
          >
            5e
          </button>
        </div>

        {/* Selector de personaje activo (siempre visible con truncamiento responsivo) */}
        {characters.length > 0 && (
          <div className="flex items-center gap-1.5 pl-2 sm:pl-3 border-l border-border-iron">
            <select
              value={activeCharacter?.id || ""}
              onChange={(e) => selectCharacter(Number(e.target.value))}
              className="bg-card text-main border border-border-iron rounded px-2 py-1 text-xs focus:border-gold outline-none transition-colors max-w-[110px] sm:max-w-[160px] md:max-w-[210px] truncate"
              title={t("header.selectActiveCharacter")}
            >
              {characters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {t("header.levelShort")} {c.level} {translateClass(c.char_class)}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Navegación Táctica Principal con márgenes claros para evitar solapamientos */}
      <nav className="flex items-center gap-1 bg-card/70 border border-border-iron/80 rounded-lg p-1 overflow-x-auto mx-1 sm:mx-3 lg:mx-4 shrink min-w-0">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-2.5 sm:px-3 py-1 sm:py-1.5 rounded text-xs font-medium tracking-wide transition-all whitespace-nowrap ${
                isActive
                  ? "bg-gold text-canvas font-bold shadow-xs"
                  : "text-muted hover:text-main hover:bg-surface/60"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Acciones de Utilidad Derecha con shrink-0 */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        {/* Estado TaleSpire */}
        <button
          onClick={connectTaleSpire}
          title={
            talespireStatus.is_connected
              ? t("header.talespireConnected")
              : talespireStatus.is_running
              ? t("header.talespireRunning")
              : talespireStatus.is_installed
              ? t("header.talespireInstalled")
              : t("header.talespireNotFound")
          }
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded border border-border-iron hover:border-gold/60 bg-card transition-colors"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              talespireStatus.is_connected
                ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]"
                : talespireStatus.is_running
                ? "bg-amber-400 animate-pulse"
                : "bg-slate-500"
            }`}
          />
          <span className="hidden xl:inline text-muted font-stat text-[11px]">TaleSpire</span>
        </button>

        {/* Botón Lanzador de Dados */}
        <button
          onClick={() => openDiceDrawer()}
          title={t("header.diceButtonTooltip")}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-crimson hover:bg-crimson-hover text-white rounded text-xs font-bold transition-all shadow-sm active:scale-95"
        >
          <Dice5 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">{t("header.diceButton")}</span>
        </button>

        {/* Alternar Tema Claro/Oscuro */}
        <button
          onClick={toggleTheme}
          title={isDark ? t("header.themeLightTooltip") : t("header.themeDarkTooltip")}
          className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-200" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>

        {/* Ajustes */}
        <button
          onClick={openSettings}
          title={t("header.settingsTooltip")}
          className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
