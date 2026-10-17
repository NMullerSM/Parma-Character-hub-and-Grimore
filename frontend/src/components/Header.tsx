import React from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTheme } from "../context/ThemeContext";
import { Dice5, Settings as SettingsIcon, Sun, Moon } from "lucide-react";

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
  } = useCharacter();
  const { isDark, toggleTheme } = useTheme();

  const tabs = [
    { id: "sheet", label: "Ficha" },
    { id: "combat", label: "Combate" },
    { id: "spells", label: "Grimorio" },
    { id: "journal", label: "Diario" },
    { id: "network", label: "Red" },
    { id: "pdf", label: "PDFs" },
    { id: "compendium", label: "Compendio" },
    { id: "forge", label: "Forja" },
  ];

  return (
    <header className="h-16 border-b border-border-iron bg-surface px-4 md:px-6 flex items-center justify-between shrink-0 select-none shadow-xs">
      {/* Título de Marca y Selector de Versión D&D */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => setActiveTab("sheet")}
        >
          <span className="font-display font-bold text-xl md:text-2xl text-gold tracking-wide">
            D&D Sanctum
          </span>
        </div>

        {/* Selector de Versión D&D (5.5e 2024 vs 5e 2014) */}
        <div className="flex items-center bg-card border border-border-iron rounded-md p-0.5 text-[11px] font-stat font-semibold">
          <button
            onClick={() => setDndEdition("5.5e")}
            title="D&D 5.5e (Reglas 2024 / 2025)"
            className={`px-2 py-0.5 rounded transition-all ${
              dndEdition === "5.5e"
                ? "bg-gold text-canvas font-bold"
                : "text-muted hover:text-main"
            }`}
          >
            5.5e
          </button>
          <button
            onClick={() => setDndEdition("5e")}
            title="D&D 5e (Reglas 2014 clásicas)"
            className={`px-2 py-0.5 rounded transition-all ${
              dndEdition === "5e"
                ? "bg-gold text-canvas font-bold"
                : "text-muted hover:text-main"
            }`}
          >
            5e
          </button>
        </div>

        {/* Selector de personaje activo */}
        {characters.length > 0 && (
          <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-border-iron">
            <select
              value={activeCharacter?.id || ""}
              onChange={(e) => selectCharacter(Number(e.target.value))}
              className="bg-card text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none transition-colors"
            >
              {characters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — Nvl {c.level} {c.char_class}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Navegación Táctica Principal */}
      <nav className="flex items-center gap-1 bg-card/70 border border-border-iron/80 rounded-lg p-1 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded text-xs font-medium tracking-wide transition-all whitespace-nowrap ${
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
      <div className="flex items-center gap-2">
        {/* Estado TaleSpire */}
        <button
          onClick={connectTaleSpire}
          title={
            talespireStatus.is_connected
              ? "TaleSpire Conectado (Clic para refrescar)"
              : talespireStatus.is_running
              ? "TaleSpire en ejecución (Clic para conectar)"
              : talespireStatus.is_installed
              ? "TaleSpire Instalado (Cerrado)"
              : "TaleSpire No Detectado"
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
          title="Bandeja de Dados (Espacio)"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-crimson hover:bg-crimson-hover text-white rounded text-xs font-bold transition-all shadow-sm active:scale-95"
        >
          <Dice5 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Dados</span>
        </button>

        {/* Alternar Tema Claro/Oscuro */}
        <button
          onClick={toggleTheme}
          title={isDark ? "Cambiar a Modo Claro (Pergamino)" : "Cambiar a Modo Oscuro (Obsidiana)"}
          className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-200" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>

        {/* Ajustes */}
        <button
          onClick={openSettings}
          title="Configuración"
          className="p-2 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
