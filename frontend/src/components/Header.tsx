import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTheme } from "../context/ThemeContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import {
  Dice5,
  Settings as SettingsIcon,
  Sun,
  Moon,
  Crown,
  Globe,
  X,
  Clipboard,
} from "lucide-react";
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
    displayedCharacters,
    selectCharacter,
    talespireStatus,
    connectTaleSpire,
    openDiceDrawer,
    dndEdition,
    setDndEdition,
    language,
    userRole,
    setUserRole,
    activeSessionId,
    setActiveSessionId,
    sessionScopeActive,
    showToast,
  } = useCharacter();
  const { isDark, toggleTheme } = useTheme();
  const { t, translateClass } = useTranslation();

  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [sessionInput, setSessionInput] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);

  const currentLogo = language === "es"
    ? (isDark ? logoEsDark : logoEsLight)
    : (isDark ? logoEnDark : logoEnLight);

  // Pestañas centrales tácticas sin sobrecarga cognitiva (Ley de Hick)
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

  const handlePasteClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setSessionInput(text.trim());
        showToast("Enlace pegado desde el portapapeles", "info");
      }
    } catch (e) {
      showToast("No se pudo leer el portapapeles automáticamente", "warn");
    }
  };

  const handleConnectToSession = async () => {
    if (!sessionInput.trim()) {
      showToast("Por favor pega el enlace o ingresa el ID de la sesión", "warn");
      return;
    }
    setIsConnecting(true);
    try {
      let resolvedId = sessionInput.trim();
      // Si el usuario pegó una URL completa, extraer el ID si viene como parámetro o usar el host
      if (resolvedId.includes("http://") || resolvedId.includes("https://")) {
        try {
          const parsed = new URL(resolvedId);
          const sessParam = parsed.searchParams.get("session") || parsed.searchParams.get("session_id");
          if (sessParam) {
            resolvedId = sessParam;
          } else {
            // Intentar consultar sesión al endpoint del túnel
            const res = await fetch(`${parsed.origin}/api/session/info`);
            if (res.ok) {
              const data = await res.json();
              if (data.session_id) resolvedId = data.session_id;
            }
          }
        } catch (_) {}
      }

      setActiveSessionId(resolvedId);

      // Si el usuario tiene un personaje activo, asociarlo a esta sesión
      if (activeCharacter?.id) {
        try {
          await api.saveCharacter({ ...activeCharacter, session_id: resolvedId });
        } catch (_) {}
      }

      showToast(`¡Conectado exitosamente a la sesión "${resolvedId}"!`, "success");
      setIsJoinModalOpen(false);
      setSessionInput("");
    } catch (e) {
      showToast("Error al conectarse a la sesión", "warn");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnectSession = () => {
    setActiveSessionId(null);
    showToast("Te has desconectado de la sesión online.", "info");
    setIsJoinModalOpen(false);
  };

  return (
    <>
      <header className="h-16 border-b border-border-iron bg-surface px-2 sm:px-4 md:px-6 flex items-center justify-between shrink-0 select-none shadow-xs gap-2">
        {/* Título de Marca, Selector de Versión y Selector de Personaje Activo */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <div
            id="tour-logo"
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
          <div id="tour-edition" className="flex items-center bg-card border border-border-iron rounded-md p-0.5 text-[11px] font-stat font-semibold">
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

          {/* Selector de personaje activo (respeta el ámbito de sesión cuando está activo) */}
          {characters.length > 0 && (
            <div id="tour-character-select" className="flex items-center gap-1.5 pl-2 sm:pl-3 border-l border-border-iron">
              {sessionScopeActive && activeSessionId && (
                <span title="Filtrando por sesión activa" className="text-amber-400 text-xs">
                  🎯
                </span>
              )}
              <select
                value={activeCharacter?.id || ""}
                onChange={(e) => selectCharacter(Number(e.target.value))}
                className="bg-card text-main border border-border-iron rounded px-2 py-1 text-xs focus:border-gold outline-none transition-colors max-w-[110px] sm:max-w-[160px] md:max-w-[210px] truncate"
                title={sessionScopeActive ? "Personajes en esta sesión" : t("header.selectActiveCharacter")}
              >
                {displayedCharacters.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} — {t("header.levelShort")} {c.level} {translateClass(c.char_class)}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Navegación Táctica Central (Limpia, sin pestaña DM que congestione) */}
        <nav id="tour-nav-tabs" className="flex items-center gap-1 bg-card/70 border border-border-iron/80 rounded-lg p-1 overflow-x-auto mx-1 sm:mx-3 lg:mx-4 shrink min-w-0">
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

        {/* Acciones de Utilidad Derecha */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {/* Selector Rápido de Rol: DM vs Jugador */}
          <div id="tour-role-toggle" className="flex items-center bg-card border border-border-iron rounded-md p-0.5 text-[11px] font-stat font-semibold">
            <button
              onClick={() => setUserRole("dm")}
              title="Modo Dungeon Master"
              className={`px-1.5 sm:px-2 py-0.5 rounded transition-all ${
                userRole === "dm"
                  ? "bg-gold text-canvas font-bold"
                  : "text-muted hover:text-main"
              }`}
            >
              DM
            </button>
            <button
              onClick={() => setUserRole("player")}
              title="Modo Jugador"
              className={`px-1.5 sm:px-2 py-0.5 rounded transition-all ${
                userRole === "player"
                  ? "bg-gold text-canvas font-bold"
                  : "text-muted hover:text-main"
              }`}
            >
              PJ
            </button>
          </div>

          {/* Botón Distintivo según Rol */}
          {userRole === "dm" ? (
            <button
              onClick={() => setActiveTab("dm")}
              title="Host DM Online (Consola & Cloudflare Tunnel)"
              className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg border text-xs font-bold transition-all shadow-xs ${
                activeTab === "dm"
                  ? "bg-gold text-canvas border-gold shadow-[0_0_12px_rgba(201,164,92,0.4)]"
                  : "bg-card border-border-iron text-gold hover:border-gold/60 hover:bg-surface"
              }`}
            >
              <Crown className="w-3.5 h-3.5 text-gold shrink-0" />
              <span className="hidden md:inline">Host DM</span>
              {activeSessionId && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5" />
              )}
            </button>
          ) : (
            <button
              onClick={() => setIsJoinModalOpen(true)}
              title="Unirse a una partida online de DM pegando el enlace o código"
              className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg border text-xs font-bold transition-all shadow-xs ${
                activeSessionId
                  ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-300"
                  : "bg-card border-border-iron text-main hover:border-gold/60"
              }`}
            >
              <Globe className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="hidden md:inline">
                {activeSessionId ? "En Sesión" : "Unirse a Sesión"}
              </span>
              {activeSessionId && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5" />
              )}
            </button>
          )}

          {/* Estado TaleSpire con LED Tricolor Minimalista */}
          <button
            id="tour-talespire"
            onClick={connectTaleSpire}
            title={
              talespireStatus.symbiote_connected
                ? t("header.talespireSymbioteLive")
                : talespireStatus.is_connected
                ? t("header.talespireConnected")
                : talespireStatus.is_running
                ? t("header.talespireWaitingSymbiote")
                : talespireStatus.is_installed
                ? t("header.talespireInstalled")
                : t("header.talespireNotFound")
            }
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded border border-border-iron hover:border-gold/60 bg-card transition-colors select-none"
          >
            <span
              className={`w-2 h-2 rounded-full transition-all ${
                talespireStatus.symbiote_connected || talespireStatus.is_connected
                  ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]"
                  : talespireStatus.is_running
                  ? "bg-amber-400 animate-pulse"
                  : "bg-slate-500"
              }`}
            />
            <span className="text-muted font-stat text-[11px] font-semibold tracking-wide">TaleSpire</span>
          </button>

          {/* Botón Lanzador de Dados */}
          <button
            id="tour-dice"
            onClick={() => openDiceDrawer()}
            title={t("header.diceButtonTooltip")}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-crimson hover:bg-crimson-hover text-white rounded text-xs font-bold transition-all shadow-sm active:scale-95 cursor-pointer"
          >
            <Dice5 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t("header.diceButton")}</span>
          </button>

          {/* Alternar Tema Claro/Oscuro */}
          <button
            id="tour-theme-toggle"
            onClick={toggleTheme}
            title={isDark ? t("header.themeLightTooltip") : t("header.themeDarkTooltip")}
            className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors cursor-pointer"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-200" /> : <Moon className="w-4 h-4 text-slate-700" />}
          </button>

          {/* Ajustes */}
          <button
            id="tour-settings"
            onClick={openSettings}
            title={t("header.settingsTooltip")}
            className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors cursor-pointer"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Modal para que los Jugadores se conecten a la Sesión del DM */}
      {isJoinModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs select-none">
          <div className="relative bg-surface border border-border-iron rounded-2xl p-6 max-w-md w-full flex flex-col space-y-4 shadow-2xl">
            <button
              onClick={() => setIsJoinModalOpen(false)}
              className="absolute top-4 right-4 p-1 text-muted hover:text-main rounded hover:bg-card transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400">
                <Globe className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-gold">Unirse a Sesión Online</h3>
                <p className="text-xs text-muted">
                  Conéctate con tu personaje a la mesa de juego del Dungeon Master.
                </p>
              </div>
            </div>

            {activeSessionId ? (
              <div className="p-4 rounded-xl bg-card border border-border-iron space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted">Sesión actual:</span>
                  <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    {activeSessionId}
                  </span>
                </div>
                <p className="text-xs text-muted">
                  Tu personaje <strong className="text-main">{activeCharacter?.name || "activo"}</strong> está vinculado a esta sesión. Las notas y tiradas se sincronizan automáticamente.
                </p>
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleDisconnectSession}
                    className="flex-1 py-2 px-3 rounded-lg border border-crimson/50 bg-crimson/10 text-crimson hover:bg-crimson hover:text-white text-xs font-semibold transition-colors"
                  >
                    Desconectar de la Sesión
                  </button>
                  <button
                    onClick={() => setIsJoinModalOpen(false)}
                    className="flex-1 py-2 px-3 rounded-lg bg-gold hover:bg-gold-hover text-canvas text-xs font-bold transition-colors"
                  >
                    Entendido
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-main block">
                    Enlace de Cloudflare o ID de la Sesión:
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={sessionInput}
                      onChange={(e) => setSessionInput(e.target.value)}
                      placeholder="https://ejemplo.trycloudflare.com o sess_xyz"
                      className="flex-1 bg-card text-main border border-border-iron rounded-xl px-3 py-2 text-xs focus:border-gold outline-none font-mono"
                    />
                    <button
                      onClick={handlePasteClipboard}
                      className="px-3 py-2 rounded-xl bg-card border border-border-iron hover:border-gold/60 text-muted hover:text-gold text-xs flex items-center gap-1.5 transition-colors"
                      title="Pegar del portapapeles"
                    >
                      <Clipboard className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Pegar</span>
                    </button>
                  </div>
                </div>

                {activeCharacter && (
                  <div className="p-3 rounded-xl bg-card/60 border border-border-iron flex items-center justify-between text-xs">
                    <span className="text-muted">Personaje que se unirá:</span>
                    <span className="font-semibold text-main">
                      {activeCharacter.name} (Nvl {activeCharacter.level} {translateClass(activeCharacter.char_class)})
                    </span>
                  </div>
                )}

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setIsJoinModalOpen(false)}
                    className="px-4 py-2 rounded-xl border border-border-iron text-muted hover:text-main text-xs transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleConnectToSession}
                    disabled={isConnecting}
                    className="px-4 py-2 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-bold text-xs shadow-md transition-all flex items-center gap-1.5 active:scale-95"
                  >
                    {isConnecting ? "Conectando..." : "Conectarse a la Mesa"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};