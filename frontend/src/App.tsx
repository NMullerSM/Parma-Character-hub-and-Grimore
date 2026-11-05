import React, { useState, useEffect, useMemo, useCallback } from "react";
import { ThemeProvider } from "./context/ThemeContext";
import { CharacterProvider, useCharacter } from "./context/CharacterContext";
import { useTranslation } from "./i18n";
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
import { SpotlightTour } from "./components/SpotlightTour";
import type { TourStep } from "./components/SpotlightTour";
import { UpdateNotificationPill } from "./components/UpdateNotificationPill";
import { UpdateModal } from "./components/UpdateModal";
import { api } from "./api/client";
import type { GitHubReleaseInfo, UpdateProgress } from "./api/types";
import { Dice5 } from "lucide-react";
import { safeStorage } from "./utils/storage";

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

type TourType = "global" | "sheet" | "spells" | "compendium" | "forge" | null;

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("sheet");
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  const { executeRoll, activeCharacter, showToast } = useCharacter();
  const { t } = useTranslation();

  // Estados del Sistema de Onboarding & Foco Visual (Spotlight)
  const [activeTour, setActiveTour] = useState<TourType>(null);
  const [currentTourStep, setCurrentTourStep] = useState<number>(0);
  const [isWhatsNewOpen, setIsWhatsNewOpen] = useState<boolean>(false);

  const [hasCompletedInitial, setHasCompletedInitial] = useState<boolean>(() => {
    return safeStorage.getItem("parma_has_completed_onboarding") === "true";
  });
  const [isGlobalSkipped, setIsGlobalSkipped] = useState<boolean>(() => {
    return safeStorage.getItem("parma_tour_skipped_all") === "true";
  });
  const [completedSectionTours, setCompletedSectionTours] = useState<string[]>(() => {
    try {
      const cached = safeStorage.getItem("parma_completed_section_tours");
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  });

  // Estados de Actualizaciones GitHub y Auto-Updater Protocol
  const [availableRelease, setAvailableRelease] = useState<GitHubReleaseInfo | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState<boolean>(false);
  const [isUpdateDismissed, setIsUpdateDismissed] = useState<boolean>(false);
  const [updateProgress, setUpdateProgress] = useState<UpdateProgress>({
    status: "idle",
    percent: 0,
    downloaded_mb: 0,
    total_mb: 0,
  });

  // Sondeo en segundo plano del auto-updater cuando hay descarga activa
  useEffect(() => {
    if (updateProgress.status !== "downloading") return;
    const interval = setInterval(async () => {
      try {
        const prog = await api.getUpdateProgress();
        setUpdateProgress(prog);
      } catch (e) {
        console.warn("Error consultando progreso:", e);
      }
    }, 450);
    return () => clearInterval(interval);
  }, [updateProgress.status]);

  // Tirada de prueba física interactiva desde el tour de bienvenida
  const handleDemoRoll = useCallback(async () => {
    try {
      await executeRoll({
        dice: { "20": 1 },
        modifier: 3,
        label: t("onboarding.demoRollLabel"),
      });
      showToast(t("onboarding.demoRollLabel"), "info");
    } catch (err) {
      console.warn("Error en tirada demo del tour:", err);
    }
  }, [executeRoll, t, showToast]);

  // Pasos estructurados según la Ley de Hick y Heurísticas de Nielsen
  const currentTourSteps = useMemo<TourStep[]>(() => {
    if (activeTour === "global") {
      return [
        {
          targetId: "tour-logo",
          title: t("onboarding.globalStep1Title"),
          description: t("onboarding.globalStep1Desc"),
          badge: t("onboarding.globalStep1Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-edition",
          title: t("onboarding.globalStep2Title"),
          description: t("onboarding.globalStep2Desc"),
          badge: t("onboarding.globalStep2Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-character-select",
          title: t("onboarding.globalStep3Title"),
          description: t("onboarding.globalStep3Desc"),
          badge: t("onboarding.globalStep3Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-nav-tabs",
          title: t("onboarding.globalStep4Title"),
          description: t("onboarding.globalStep4Desc"),
          badge: t("onboarding.globalStep4Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-dice",
          title: t("onboarding.globalStep5Title"),
          description: t("onboarding.globalStep5Desc"),
          badge: t("onboarding.globalStep5Badge"),
          placement: "bottom",
          actionButton: {
            label: t("onboarding.demoRollBtn"),
            onClick: handleDemoRoll,
            icon: <Dice5 className="w-3.5 h-3.5" />,
          },
        },
        {
          targetId: "tour-talespire",
          title: t("onboarding.globalStep6Title"),
          description: t("onboarding.globalStep6Desc"),
          badge: t("onboarding.globalStep6Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-settings",
          title: t("onboarding.globalStep7Title"),
          description: t("onboarding.globalStep7Desc"),
          badge: t("onboarding.globalStep7Badge"),
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "spells") {
      return [
        {
          targetId: "tour-spell-filters",
          title: t("onboarding.spellsStep1Title"),
          description: t("onboarding.spellsStep1Desc"),
          badge: t("onboarding.spellsStep1Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-spell-slots",
          title: t("onboarding.spellsStep2Title"),
          description: t("onboarding.spellsStep2Desc"),
          badge: t("onboarding.spellsStep2Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-spell-manager",
          title: t("onboarding.spellsStep3Title"),
          description: t("onboarding.spellsStep3Desc"),
          badge: t("onboarding.spellsStep3Badge"),
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "sheet") {
      return [
        {
          targetId: "tour-sheet-hp",
          title: t("onboarding.sheetStep1Title"),
          description: t("onboarding.sheetStep1Desc"),
          badge: t("onboarding.sheetStep1Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-sheet-stats",
          title: t("onboarding.sheetStep2Title"),
          description: t("onboarding.sheetStep2Desc"),
          badge: t("onboarding.sheetStep2Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-sheet-actions",
          title: t("onboarding.sheetStep3Title"),
          description: t("onboarding.sheetStep3Desc"),
          badge: t("onboarding.sheetStep3Badge"),
          placement: "top",
        },
      ];
    }

    if (activeTour === "compendium") {
      return [
        {
          targetId: "tour-compendium-search",
          title: t("onboarding.compendiumStep1Title"),
          description: t("onboarding.compendiumStep1Desc"),
          badge: t("onboarding.compendiumStep1Badge"),
          placement: "bottom",
        },
        {
          targetId: "tour-compendium-categories",
          title: t("onboarding.compendiumStep2Title"),
          description: t("onboarding.compendiumStep2Desc"),
          badge: t("onboarding.compendiumStep2Badge"),
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "forge") {
      return [
        {
          targetId: "tour-forge-modes",
          title: t("onboarding.forgeStep1Title"),
          description: t("onboarding.forgeStep1Desc"),
          badge: t("onboarding.forgeStep1Badge"),
          placement: "bottom",
        },
      ];
    }

    return [];
  }, [activeTour, handleDemoRoll, t]);

  // Inicialización y comprobación de primer arranque vs actualización
  useEffect(() => {
    let isMounted = true;

    async function checkInit() {
      try {
        const settings = await api.getSettings();
        if (!isMounted) return;

        const lastSeen = settings.last_seen_version || "";
        const hasCompleted = settings.has_completed_onboarding;

        if (!lastSeen && !hasCompleted && !hasCompletedInitial && !isGlobalSkipped) {
          // Primera instalación: lanza el nuevo Onboarding visual con foco interactivo
          setActiveTour("global");
          setCurrentTourStep(0);
        } else if (lastSeen && isNewerVersion(APP_VERSION, lastSeen)) {
          // Actualización de versión: muestra la tarjeta What's New
          setIsWhatsNewOpen(true);
        }
      } catch (err) {
        console.warn("No se pudo cargar la configuración de onboarding:", err);
      }

      // Consulta no bloqueante de Releases en GitHub
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
            const ignoredVersion = safeStorage.getItem("parma_ignored_update_version");
            if (isNewerVersion(release.tag_name, APP_VERSION) && ignoredVersion !== release.tag_name) {
              setAvailableRelease(release);
            }
          }
        }
      } catch {
        // Red desconectada u offline: no interrumpe el uso
      }
    }

    checkInit();

    return () => {
      isMounted = false;
    };
  }, [hasCompletedInitial, isGlobalSkipped]);

  // Disparador de tours contextuales progresivos al navegar a una sección
  useEffect(() => {
    if (activeTour !== null) return;
    if (isGlobalSkipped) return;
    if (!hasCompletedInitial) return;

    if (activeTab === "spells" && !completedSectionTours.includes("spells")) {
      const timer = setTimeout(() => {
        setActiveTour("spells");
        setCurrentTourStep(0);
      }, 350);
      return () => clearTimeout(timer);
    } else if (activeTab === "sheet" && activeCharacter && !completedSectionTours.includes("sheet")) {
      const timer = setTimeout(() => {
        setActiveTour("sheet");
        setCurrentTourStep(0);
      }, 350);
      return () => clearTimeout(timer);
    } else if (activeTab === "compendium" && !completedSectionTours.includes("compendium")) {
      const timer = setTimeout(() => {
        setActiveTour("compendium");
        setCurrentTourStep(0);
      }, 350);
      return () => clearTimeout(timer);
    } else if (activeTab === "forge" && !completedSectionTours.includes("forge")) {
      const timer = setTimeout(() => {
        setActiveTour("forge");
        setCurrentTourStep(0);
      }, 350);
      return () => clearTimeout(timer);
    }
  }, [activeTab, activeTour, isGlobalSkipped, hasCompletedInitial, completedSectionTours, activeCharacter]);

  // Completar o avanzar el tour activo
  const handleCloseActiveTour = async () => {
    if (activeTour === "global") {
      setHasCompletedInitial(true);
      setActiveTour(null);
      setCurrentTourStep(0);
      try {
        await api.setSetting("last_seen_version", APP_VERSION);
        await api.setSetting("has_completed_onboarding", true);
        safeStorage.setItem("parma_has_completed_onboarding", "true");
      } catch (err) {
        console.error("Error al persistir estado de onboarding:", err);
      }
    } else if (activeTour) {
      const updated = [...completedSectionTours, activeTour];
      setCompletedSectionTours(updated);
      setActiveTour(null);
      setCurrentTourStep(0);
      safeStorage.setItem("parma_completed_section_tours", JSON.stringify(updated));
    }
  };

  // Saltar todo el onboarding de forma permanente
  const handleSkipAll = async () => {
    setActiveTour(null);
    setCurrentTourStep(0);
    setIsGlobalSkipped(true);
    setHasCompletedInitial(true);
    const allSections = ["spells", "sheet", "compendium", "forge", "combat", "journal", "network", "pdf"];
    setCompletedSectionTours(allSections);
    try {
      await api.setSetting("last_seen_version", APP_VERSION);
      await api.setSetting("has_completed_onboarding", true);
      safeStorage.setItem("parma_has_completed_onboarding", "true");
      safeStorage.setItem("parma_tour_skipped_all", "true");
      safeStorage.setItem("parma_completed_section_tours", JSON.stringify(allSections));
      showToast(t("onboarding.btnSkipAll"), "info");
    } catch (err) {
      console.error("Error al persistir skip all:", err);
    }
  };

  // Saltar únicamente la sección actual
  const handleSkipSection = () => {
    if (activeTour === "global") {
      handleCloseActiveTour();
    } else if (activeTour) {
      const updated = [...completedSectionTours, activeTour];
      setCompletedSectionTours(updated);
      setActiveTour(null);
      setCurrentTourStep(0);
      safeStorage.setItem("parma_completed_section_tours", JSON.stringify(updated));
    }
  };

  // Repetir el tour global desde Ajustes
  const handleReplayTour = () => {
    setActiveTour("global");
    setCurrentTourStep(0);
  };

  // Reiniciar los tutoriales de secciones desde Ajustes
  const handleResetSectionTours = () => {
    setCompletedSectionTours([]);
    setIsGlobalSkipped(false);
    safeStorage.removeItem("parma_completed_section_tours");
    safeStorage.removeItem("parma_tour_skipped_all");
  };

  const handleCloseWhatsNew = async () => {
    setIsWhatsNewOpen(false);
    try {
      await api.setSetting("last_seen_version", APP_VERSION);
    } catch (err) {
      console.error("Error al persistir versión:", err);
    }
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
          onResetSectionTours={handleResetSectionTours}
        />
      )}

      {/* 6. Destello de Viñeta Cinemática (Daño / Curación) */}
      <ScreenVignette />

      {/* 7. Sistema de Onboarding Interactivo por Foco (Spotlight Coach Marks) */}
      {activeTour !== null && currentTourSteps.length > 0 && (
        <SpotlightTour
          isOpen={true}
          steps={currentTourSteps}
          currentStepIndex={currentTourStep}
          onStepChange={setCurrentTourStep}
          onClose={handleCloseActiveTour}
          onSkipSection={handleSkipSection}
          isContextual={activeTour !== "global"}
        />
      )}

      {/* 8. Tarjeta de Novedades de la Versión (What's New) al Actualizar */}
      {isWhatsNewOpen && (
        <OnboardingModal
          version={APP_VERSION}
          onClose={handleCloseWhatsNew}
        />
      )}

      {/* 9. Píldora Flotante Inferior Izquierda de Notificación de Actualización */}
      {availableRelease && !isUpdateDismissed && (
        <UpdateNotificationPill
          release={availableRelease}
          progress={updateProgress}
          onOpenModal={() => setIsUpdateModalOpen(true)}
          onDismiss={() => setIsUpdateDismissed(true)}
        />
      )}

      {/* 10. Modal de Actualización con Enlaces de Descarga, Progreso y Reinicio Silencioso */}
      {isUpdateModalOpen && availableRelease && (
        <UpdateModal
          release={availableRelease}
          currentVersion={APP_VERSION}
          progress={updateProgress}
          onStartDownload={() => setUpdateProgress((p) => ({ ...p, status: "downloading" }))}
          onIgnoreVersion={(ver) => {
            try {
              safeStorage.setItem("parma_ignored_update_version", ver);
            } catch (e) {
              console.warn(e);
            }
            setIsUpdateModalOpen(false);
            setIsUpdateDismissed(true);
          }}
          onClose={() => setIsUpdateModalOpen(false)}
        />
      )}

      {/* 11. Contenedor de Notificaciones Toast */}
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
