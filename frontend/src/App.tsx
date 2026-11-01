import React, { useState, useEffect } from "react";
import { ThemeProvider } from "./context/ThemeContext";
import { CharacterProvider } from "./context/CharacterContext";
import { Header } from "./components/Header";
import { DiceDrawer } from "./components/DiceDrawer";
import { DiceRollAnimation } from "./components/DiceRollAnimation";
import { ToastContainer } from "./components/ToastContainer";
import { SplashScreen } from "./components/SplashScreen";
import { ScreenVignette } from "./components/ScreenVignette";

import { SheetView } from "./views/SheetView";
import { CombatView } from "./views/CombatView";
import { SpellsView } from "./views/SpellsView";
import { JournalView } from "./views/JournalView";
import { NetworkView } from "./views/NetworkView";
import { PdfViewerView } from "./views/PdfViewerView";
import { CompendiumView } from "./views/CompendiumView";
import { CharacterWizard } from "./views/CharacterWizard";
import { SettingsView } from "./views/SettingsView";
import { DMConsoleView } from "./views/DMConsoleView";
import { OnlinePlayerSync } from "./components/OnlinePlayerSync";

import { APP_VERSION } from "./version";
import { OnboardingModal } from "./components/OnboardingModal";
import { UpdateNotificationPill } from "./components/UpdateNotificationPill";
import { UpdateModal } from "./components/UpdateModal";
import { api } from "./api/client";
import type { GitHubReleaseInfo } from "./api/types";

function parseSemVer(v: string): [number, number, number] {
  const clean = v.replace(/^v/, "").trim();
  const parts = clean.split(".").map((n) => parseInt(n, 10) || 0);
  return [parts[0] || 0, parts[1] || 0, parts[2] || 0];
}

function isNewerVersion(remote: string, local: string): boolean {
  const [rMaj, rMin, rPat] = parseSemVer(remote);
  const [lMaj, lMin, lPat] = parseSemVer(local);
  if (rMaj > lMaj) return true;
  if (rMaj < lMaj) return false;
  if (rMin > lMin) return true;
  if (rMin < lMin) return false;
  return rPat > lPat;
}

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("sheet");
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Estados de Onboarding y Actualizaciones
  const [onboardingState, setOnboardingState] = useState<{
    isOpen: boolean;
    mode: "initial" | "whats_new";
  } | null>(null);

  const [availableRelease, setAvailableRelease] = useState<GitHubReleaseInfo | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState<boolean>(false);
  const [isUpdateDismissed, setIsUpdateDismissed] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    async function checkInit() {
      // 1. Evaluación de estado de Onboarding / Versión
      try {
        const settings = await api.getSettings();
        if (!isMounted) return;

        const lastSeen = settings.last_seen_version || "";
        const hasCompleted = settings.has_completed_onboarding;

        if (!lastSeen && !hasCompleted) {
          // Primera instalación del usuario: lanza Onboarding inicial guiado
          setOnboardingState({ isOpen: true, mode: "initial" });
        } else if (lastSeen && isNewerVersion(APP_VERSION, lastSeen)) {
          // El usuario ya usaba una versión anterior y actualizó a una versión más reciente:
          // Muestra únicamente la tarjeta de novedades de la versión ("What's New")
          setOnboardingState({ isOpen: true, mode: "whats_new" });
        }
      } catch (err) {
        console.warn("No se pudo cargar la configuración de onboarding:", err);
      }

      // 2. Consulta no bloqueante de Releases en GitHub
      try {
        const res = await fetch(
          "https://api.github.com/repos/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest",
          {
            headers: { Accept: "application/vnd.github.v3+json" },
          }
        );
        if (res.ok) {
          const release: GitHubReleaseInfo = await res.json();
          if (isMounted && release && release.tag_name) {
            if (isNewerVersion(release.tag_name, APP_VERSION)) {
              setAvailableRelease(release);
            }
          }
        }
      } catch {
        // Red desconectada o API rate limit: no interrumpe el uso offline de la aplicación
      }
    }

    checkInit();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleCloseOnboarding = async () => {
    setOnboardingState(null);
    try {
      await api.setSetting("last_seen_version", APP_VERSION);
      await api.setSetting("has_completed_onboarding", true);
    } catch (err) {
      console.error("Error al persistir estado de onboarding:", err);
    }
  };

  const handleReplayTour = () => {
    setOnboardingState({ isOpen: true, mode: "initial" });
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-canvas text-main font-body">
      {/* Sincronización en tiempo real para sesiones DM/Jugador */}
      <OnlinePlayerSync />

      {/* 0. Animación de Bienvenida / Splash Screen */}
      <SplashScreen />

      {/* 1. Header Táctico Superior Ampliado */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openSettings={() => setIsSettingsOpen(true)}
      />

      {/* 2. Área Principal de Contenido */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "sheet" && <SheetView onNavigateForge={() => setActiveTab("forge")} />}
        {activeTab === "combat" && <CombatView />}
        {activeTab === "spells" && <SpellsView />}
        {activeTab === "dm" && <DMConsoleView />}
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
      {isSettingsOpen && (
        <SettingsView
          onClose={() => setIsSettingsOpen(false)}
          onReplayTour={handleReplayTour}
        />
      )}

      {/* 6. Destello de Viñeta Cinemática (Daño / Curación) */}
      <ScreenVignette />

      {/* 7. Modal de Onboarding (Inicial o Novedades tras Actualizar) */}
      {onboardingState?.isOpen && (
        <OnboardingModal
          mode={onboardingState.mode}
          version={APP_VERSION}
          onClose={handleCloseOnboarding}
        />
      )}

      {/* 8. Píldora Flotante Inferior Izquierda de Notificación de Actualización */}
      {availableRelease && !isUpdateDismissed && (
        <UpdateNotificationPill
          release={availableRelease}
          onOpenModal={() => setIsUpdateModalOpen(true)}
          onDismiss={() => setIsUpdateDismissed(true)}
        />
      )}

      {/* 9. Modal de Actualización con Enlaces de Descarga y Notas del Parche */}
      {isUpdateModalOpen && availableRelease && (
        <UpdateModal
          release={availableRelease}
          currentVersion={APP_VERSION}
          onClose={() => setIsUpdateModalOpen(false)}
        />
      )}

      {/* 10. Contenedor de Notificaciones Toast */}
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
