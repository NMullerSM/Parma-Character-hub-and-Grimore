import React, { useState } from "react";
import { ThemeProvider } from "./context/ThemeContext";
import { CharacterProvider } from "./context/CharacterContext";
import { Header } from "./components/Header";
import { DiceDrawer } from "./components/DiceDrawer";
import { DiceRollAnimation } from "./components/DiceRollAnimation";
import { ToastContainer } from "./components/ToastContainer";

import { SheetView } from "./views/SheetView";
import { CombatView } from "./views/CombatView";
import { SpellsView } from "./views/SpellsView";
import { JournalView } from "./views/JournalView";
import { NetworkView } from "./views/NetworkView";
import { PdfViewerView } from "./views/PdfViewerView";
import { CompendiumView } from "./views/CompendiumView";
import { CharacterWizard } from "./views/CharacterWizard";
import { SettingsView } from "./views/SettingsView";

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("sheet");
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-canvas text-main font-body">
      {/* 1. Header Táctico Superior Ampliado */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openSettings={() => setIsSettingsOpen(true)}
      />

      {/* 2. Área Principal de Contenido */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "sheet" && <SheetView />}
        {activeTab === "combat" && <CombatView />}
        {activeTab === "spells" && <SpellsView />}
        {activeTab === "journal" && <JournalView />}
        {activeTab === "network" && <NetworkView />}
        {activeTab === "pdf" && <PdfViewerView />}
        {activeTab === "compendium" && <CompendiumView />}
        {activeTab === "forge" && <CharacterWizard onComplete={() => setActiveTab("sheet")} />}
      </main>

      {/* 3. Animación Cinemática de Dados al Centro de la Pantalla */}
      <DiceRollAnimation />

      {/* 4. Bandeja Lateral de Dados (Colapsable / Ley de Hick / Con Historial) */}
      <DiceDrawer />

      {/* 5. Modal de Configuración */}
      {isSettingsOpen && <SettingsView onClose={() => setIsSettingsOpen(false)} />}

      {/* 6. Contenedor de Notificaciones Toast */}
      <ToastContainer />
    </div>
  );
};

export default function App() {
  return (
    <ThemeProvider>
      <CharacterProvider>
        <AppContent />
      </CharacterProvider>
    </ThemeProvider>
  );
}
