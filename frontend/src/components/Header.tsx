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
  const { activeCharacter, characters, selectCharacter, talespireStatus, connectTaleSpire, openDiceDrawer } =
    useCharacter();
  const { isDark, toggleTheme } = useTheme();

  const tabs = [
    { id: "sheet", label: "Ficha" },
    { id: "combat", label: "Combate" },
    { id: "spells", label: "Grimorio" },
    { id: "compendium", label: "Compendio" },
    { id: "forge", label: "Forja" },
  ];

  return (
    <header className="h-14 border-b border-border-iron bg-surface px-4 flex items-center justify-between shrink-0 select-none">
      {/* Título de Marca y Selector de Personaje */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveTab("sheet")}>
          <span className="font-display font-bold text-xl text-gold tracking-wide">D&D Sanctum</span>
          <span className="text-[10px] uppercase tracking-widest text-muted border border-border-iron px-1.5 py-0.5 rounded">
            5e
          </span>
        </div>

        {/* Selector de personaje activo */}
        {characters.length > 0 && (
          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-border-iron">
            <select
              value={activeCharacter?.id || ""}
              onChange={(e) => selectCharacter(Number(e.target.value))}
              className="bg-card text-main border border-border-iron rounded px-2.5 py-1 text-sm focus:border-gold outline-none transition-colors"
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

      {/* Navegación Principal Táctica (Ley de Hick: Sin iconos redundantes, tipografía limpia) */}
      <nav className="flex items-center gap-1 bg-card/60 border border-border-iron/80 rounded-lg p-0.5">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1 rounded text-xs font-medium tracking-wide transition-all ${
                isActive
                  ? "bg-gold text-canvas font-semibold shadow-sm"
                  : "text-muted hover:text-main hover:bg-surface/50"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Controles de Utilidad Derecha */}
      <div className="flex items-center gap-2">
        {/* Estado TaleSpire */}
        <button
          onClick={connectTaleSpire}
          title={
            talespireStatus.is_connected
              ? "TaleSpire Conectado (Clic para actualizar)"
              : talespireStatus.is_running
              ? "TaleSpire en ejecución (Clic para conectar sesión)"
              : talespireStatus.is_installed
              ? "TaleSpire Instalado (Cerrado)"
              : "TaleSpire No Detectado"
          }
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded border border-border-iron hover:border-gold/50 bg-card transition-colors"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              talespireStatus.is_connected
                ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                : talespireStatus.is_running
                ? "bg-amber-400"
                : "bg-slate-500"
            }`}
          />
          <span className="hidden md:inline text-muted font-stat text-[11px]">TaleSpire</span>
        </button>

        {/* Botón Lanzador de Dados (Drawer) */}
        <button
          onClick={() => openDiceDrawer()}
          title="Bandeja de Dados (Espacio)"
          className="flex items-center gap-1.5 px-3 py-1 bg-crimson hover:bg-crimson-hover text-white rounded text-xs font-medium transition-all shadow-sm active:scale-95"
        >
          <Dice5 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Dados</span>
        </button>

        {/* Botón Cambiar Tema Claro/Oscuro */}
        <button
          onClick={toggleTheme}
          title={isDark ? "Cambiar a Modo Claro (Pergamino)" : "Cambiar a Modo Oscuro (Obsidiana)"}
          className="p-1.5 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>

        {/* Botón Ajustes */}
        <button
          onClick={openSettings}
          title="Configuración"
          className="p-1.5 text-muted hover:text-main hover:bg-card border border-transparent hover:border-border-iron rounded transition-colors"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
