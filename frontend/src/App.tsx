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
import type { GitHubReleaseInfo } from "./api/types";
import { Dice5 } from "lucide-react";

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
    return localStorage.getItem("parma_has_completed_onboarding") === "true";
  });
  const [isGlobalSkipped, setIsGlobalSkipped] = useState<boolean>(() => {
    return localStorage.getItem("parma_tour_skipped_all") === "true";
  });
  const [completedSectionTours, setCompletedSectionTours] = useState<string[]>(() => {
    try {
      const cached = localStorage.getItem("parma_completed_section_tours");
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  });

  // Estados de Actualizaciones GitHub
  const [availableRelease, setAvailableRelease] = useState<GitHubReleaseInfo | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState<boolean>(false);
  const [isUpdateDismissed, setIsUpdateDismissed] = useState<boolean>(false);

  // Tirada de prueba física interactiva desde el tour de bienvenida
  const handleDemoRoll = useCallback(async () => {
    try {
      await executeRoll({
        dice: { "20": 1 },
        modifier: 3,
        label: t("onboarding.demoRollLabel") || "Tirada de prueba del Tour",
      });
      showToast(t("onboarding.demoRollLabel") || "¡Tirada d20 ejecutada!", "info");
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
          title: t("onboarding.globalStep1Title") || "¡Bienvenido a Parma!",
          description:
            t("onboarding.globalStep1Desc") ||
            "Tu suite táctica de escritorio 100% offline para jugadores y DMs de D&D 2024 y 5e. Todo se guarda de forma local y privada en tu máquina.",
          badge: t("onboarding.globalStep1Badge") || "Bienvenida",
          placement: "bottom",
        },
        {
          targetId: "tour-edition",
          title: t("onboarding.globalStep2Title") || "Reglas D&D 2024 y 5e",
          description:
            t("onboarding.globalStep2Desc") ||
            "Alterna al instante entre las nuevas reglas oficiales 2024 (5.5e) y las clásicas de 5e. Las dotes, conjuros y razas se adaptan en tiempo real.",
          badge: t("onboarding.globalStep2Badge") || "Reglas Oficiales",
          placement: "bottom",
        },
        {
          targetId: "tour-character-select",
          title: t("onboarding.globalStep3Title") || "Tus Héroes y la Forja",
          description:
            t("onboarding.globalStep3Desc") ||
            "Selecciona a tu aventurero activo o accede a la Forja de Héroes para crear personajes paso a paso, en 60 segundos o con tiradas aleatorias.",
          badge: t("onboarding.globalStep3Badge") || "Gestión de Héroes",
          placement: "bottom",
        },
        {
          targetId: "tour-nav-tabs",
          title: t("onboarding.globalStep4Title") || "Navegación Táctica",
          description:
            t("onboarding.globalStep4Desc") ||
            "Accede con un clic a tu Hoja, Combate en vivo, Grimorio, Diario de campaña, Conexión en red, Visor de manuales PDF y Compendio OKF.",
          badge: t("onboarding.globalStep4Badge") || "Secciones",
          placement: "bottom",
        },
        {
          targetId: "tour-dice",
          title: t("onboarding.globalStep5Title") || "Lanzador de Dados Táctico",
          description:
            t("onboarding.globalStep5Desc") ||
            "Tira dados 2D y 3D cinemáticos con ventaja, desventaja, modificadores automáticos e historial. ¡Haz clic abajo para probar una tirada!",
          badge: t("onboarding.globalStep5Badge") || "Tiradas de Dados",
          placement: "bottom",
          actionButton: {
            label: t("onboarding.demoRollBtn") || "¡Probar tirada d20!",
            onClick: handleDemoRoll,
            icon: <Dice5 className="w-3.5 h-3.5" />,
          },
        },
        {
          targetId: "tour-talespire",
          title: t("onboarding.globalStep6Title") || "TaleSpire 3D y Modo DM",
          description:
            t("onboarding.globalStep6Desc") ||
            "Sincroniza tus tiradas en tableros 3D mediante Symbiote y activa el Modo DM para liderar sesiones multijugador con túnel seguro.",
          badge: t("onboarding.globalStep6Badge") || "Mesa Virtual",
          placement: "bottom",
        },
        {
          targetId: "tour-settings",
          title: t("onboarding.globalStep7Title") || "Temas y Configuración",
          description:
            t("onboarding.globalStep7Desc") ||
            "Personaliza la paleta (Obsidian, Parchment, Amethyst, Mithril), efectos de sonido, idioma y repite este tour cuando quieras desde Ajustes.",
          badge: t("onboarding.globalStep7Badge") || "Personalización",
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "spells") {
      return [
        {
          targetId: "tour-spell-filters",
          title: t("onboarding.spellsStep1Title") || "Filtro por Nivel de Conjuro",
          description:
            t("onboarding.spellsStep1Desc") ||
            "Organiza rápidamente tus hechizos desde Trucos hasta Nivel 9 para no perder tiempo buscando en mitad del turno de combate.",
          badge: t("onboarding.spellsStep1Badge") || "Filtros",
          placement: "bottom",
        },
        {
          targetId: "tour-spell-slots",
          title: t("onboarding.spellsStep2Title") || "Ranuras de Conjuro Gastables",
          description:
            t("onboarding.spellsStep2Desc") ||
            "Haz clic en las gemas doradas para marcar tus espacios mágicos usados. Se recuperan automáticamente tras un descanso largo.",
          badge: t("onboarding.spellsStep2Badge") || "Ranuras Mágicas",
          placement: "bottom",
        },
        {
          targetId: "tour-spell-manager",
          title: t("onboarding.spellsStep3Title") || "Gestor Arcano y Compendio",
          description:
            t("onboarding.spellsStep3Desc") ||
            "Añade conjuros oficiales desde el compendio o registra conjuros caseros personalizados (homebrew) para tu personaje.",
          badge: t("onboarding.spellsStep3Badge") || "Gestor Arcano",
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "sheet") {
      return [
        {
          targetId: "tour-sheet-hp",
          title: t("onboarding.sheetStep1Title") || "Puntos de Vida y Vitales",
          description:
            t("onboarding.sheetStep1Desc") ||
            "Ajusta tus PG al instante con los botones +/-. Las viñetas de pantalla reaccionarán visualmente cuando sufras daño o te cures.",
          badge: t("onboarding.sheetStep1Badge") || "Salud y Vitales",
          placement: "bottom",
        },
        {
          targetId: "tour-sheet-stats",
          title: t("onboarding.sheetStep2Title") || "Puntuaciones y Salvaciones",
          description:
            t("onboarding.sheetStep2Desc") ||
            "Haz clic sobre cualquier característica o tirada de salvación para lanzar los dados automáticamente con los bonificadores calculados.",
          badge: t("onboarding.sheetStep2Badge") || "Características",
          placement: "bottom",
        },
        {
          targetId: "tour-sheet-actions",
          title: t("onboarding.sheetStep3Title") || "Acciones de Ataque y Armas",
          description:
            t("onboarding.sheetStep3Desc") ||
            "Calcula impacto y daño con un solo toque. Consulta el alcance en casillas para moverte con precisión en el mapa táctico.",
          badge: t("onboarding.sheetStep3Badge") || "Combate Táctico",
          placement: "top",
        },
      ];
    }

    if (activeTour === "compendium") {
      return [
        {
          targetId: "tour-compendium-search",
          title: t("onboarding.compendiumStep1Title") || "Búsqueda Atómica Universal",
          description:
            t("onboarding.compendiumStep1Desc") ||
            "Escribe cualquier término (monstruo, dote, condición o regla) para consultar de inmediato su ficha oficial sin conexión.",
          badge: t("onboarding.compendiumStep1Badge") || "Buscador Universal",
          placement: "bottom",
        },
        {
          targetId: "tour-compendium-categories",
          title: t("onboarding.compendiumStep2Title") || "Índice de Categorías",
          description:
            t("onboarding.compendiumStep2Desc") ||
            "Filtra por linajes, clases, equipo o trasfondos para explorar el compendio de reglas Open Knowledge Fantasy.",
          badge: t("onboarding.compendiumStep2Badge") || "Índice de Reglas",
          placement: "bottom",
        },
      ];
    }

    if (activeTour === "forge") {
      return [
        {
          targetId: "tour-forge-modes",
          title: t("onboarding.forgeStep1Title") || "Elige tu Método de Creación",
          description:
            t("onboarding.forgeStep1Desc") ||
            "Asistente guiado paso a paso, generador rápido optimizado en 60 segundos, o tirada aleatoria clásica con 4d6 descartando el menor.",
          badge: t("onboarding.forgeStep1Badge") || "Forja de Héroes",
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
            if (isNewerVersion(release.tag_name, APP_VERSION)) {
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
        localStorage.setItem("parma_has_completed_onboarding", "true");
      } catch (err) {
        console.error("Error al persistir estado de onboarding:", err);
      }
    } else if (activeTour) {
      const updated = [...completedSectionTours, activeTour];
      setCompletedSectionTours(updated);
      setActiveTour(null);
      setCurrentTourStep(0);
      localStorage.setItem("parma_completed_section_tours", JSON.stringify(updated));
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
      localStorage.setItem("parma_has_completed_onboarding", "true");
      localStorage.setItem("parma_tour_skipped_all", "true");
      localStorage.setItem("parma_completed_section_tours", JSON.stringify(allSections));
      showToast(t("onboarding.btnSkipAll") || "Onboarding completado", "info");
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
      localStorage.setItem("parma_completed_section_tours", JSON.stringify(updated));
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
    localStorage.removeItem("parma_completed_section_tours");
    localStorage.removeItem("parma_tour_skipped_all");
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
          mode="whats_new"
          version={APP_VERSION}
          onClose={handleCloseWhatsNew}
        />
      )}

      {/* 9. Píldora Flotante Inferior Izquierda de Notificación de Actualización */}
      {availableRelease && !isUpdateDismissed && (
        <UpdateNotificationPill
          release={availableRelease}
          onOpenModal={() => setIsUpdateModalOpen(true)}
          onDismiss={() => setIsUpdateDismissed(true)}
        />
      )}

      {/* 10. Modal de Actualización con Enlaces de Descarga y Notas del Parche */}
      {isUpdateModalOpen && availableRelease && (
        <UpdateModal
          release={availableRelease}
          currentVersion={APP_VERSION}
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
