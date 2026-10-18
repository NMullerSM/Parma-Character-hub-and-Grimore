import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { api } from "../api/client";
import type {
  CharacterSheetData,
  CharacterSummary,
  RollRequest,
  RollResult,
  RollHistoryEntry,
  TaleSpireStatus,
  SpellItemData,
} from "../api/types";

interface ToastMessage {
  id: string;
  text: string;
  type: "info" | "success" | "warn";
}

interface CharacterContextType {
  activeCharacter: CharacterSheetData | null;
  characters: CharacterSummary[];
  loading: boolean;
  talespireStatus: TaleSpireStatus;
  dndEdition: string;
  isDiceDrawerOpen: boolean;
  diceRequest: RollRequest;
  lastRollResult: RollResult | null;
  rollHistory: RollHistoryEntry[];
  toasts: ToastMessage[];

  // Animación física de dados
  isRollingAnimation: boolean;
  currentRollingData: RollResult | null;

  // Acciones
  setDndEdition: (edition: string) => Promise<void>;
  reloadCharacters: () => Promise<void>;
  selectCharacter: (id: number) => Promise<void>;
  updateActiveCharacter: (updates: Partial<CharacterSheetData>) => void;
  saveCurrentCharacter: () => Promise<boolean>;
  openDiceDrawer: (req?: Partial<RollRequest>) => void;
  closeDiceDrawer: () => void;
  executeRoll: (req: RollRequest) => Promise<RollResult>;
  fetchRollHistory: () => Promise<void>;
  clearRollHistory: () => Promise<void>;
  performRestAction: (restType: "short" | "long", hitDiceSpent?: number) => Promise<void>;
  refreshTaleSpire: () => Promise<void>;
  connectTaleSpire: () => Promise<void>;
  showToast: (text: string, type?: "info" | "success" | "warn") => void;
  addSpell: (spell: SpellItemData) => Promise<boolean>;
  removeSpell: (spellName: string) => Promise<boolean>;
  syncFeatures: () => Promise<void>;
}

const CharacterContext = createContext<CharacterContextType | undefined>(undefined);

export const CharacterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeCharacter, setActiveCharacter] = useState<CharacterSheetData | null>(null);
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [dndEdition, setEditionState] = useState<string>("5.5e");
  const [talespireStatus, setTaleSpireStatus] = useState<TaleSpireStatus>({
    is_installed: false,
    is_running: false,
    is_connected: false,
    state_label: "unknown",
  });
  const [isDiceDrawerOpen, setIsDiceDrawerOpen] = useState<boolean>(false);
  const [diceRequest, setDiceRequest] = useState<RollRequest>({
    dice: { "20": 1 },
    modifier: 0,
    label: "Tirada Rápida",
    mode: "normal",
    send_to_talespire: true,
  });
  const [lastRollResult, setLastRollResult] = useState<RollResult | null>(null);
  const [rollHistory, setRollHistory] = useState<RollHistoryEntry[]>([]);
  const [isRollingAnimation, setIsRollingAnimation] = useState<boolean>(false);
  const [currentRollingData, setCurrentRollingData] = useState<RollResult | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestCharRef = useRef<CharacterSheetData | null>(null);

  useEffect(() => {
    latestCharRef.current = activeCharacter;
  }, [activeCharacter]);

  const showToast = useCallback((text: string, type: "info" | "success" | "warn" = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const fetchRollHistory = useCallback(async () => {
    try {
      const h = await api.getRollHistory();
      setRollHistory(h);
    } catch (e) {
      console.error("Error fetching roll history:", e);
    }
  }, []);

  const clearRollHistory = async () => {
    await api.clearRollHistory();
    setRollHistory([]);
    showToast("Historial de tiradas de la sesión purgado", "info");
  };

  const reloadCharacters = useCallback(async () => {
    try {
      const list = await api.listCharacters();
      setCharacters(list);
      const active = await api.getActiveCharacter();
      setActiveCharacter(active);
      const settings = await api.getSettings();
      if (settings.dnd_edition) setEditionState(settings.dnd_edition);
    } catch (e) {
      console.error("Error loading character data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshTaleSpire = useCallback(async () => {
    try {
      const status = await api.getTaleSpireStatus();
      setTaleSpireStatus(status);
    } catch (e) {
      console.error("Error checking TaleSpire:", e);
    }
  }, []);

  useEffect(() => {
    const initAll = () => {
      reloadCharacters();
      refreshTaleSpire();
      fetchRollHistory();
    };
    initAll();

    // Sincronizar en caso de que PyWebView inyecte el bridge tras montar el DOM
    window.addEventListener("pywebviewready", initAll);
    return () => {
      window.removeEventListener("pywebviewready", initAll);
    };
  }, [reloadCharacters, refreshTaleSpire, fetchRollHistory]);

  // Atajos globales: Espacio para bandeja de dados, Escape para cerrar bandeja
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isEditable =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);

      if (e.code === "Space" && !isEditable) {
        e.preventDefault();
        setIsDiceDrawerOpen((prev) => !prev);
      } else if (e.key === "Escape" && isDiceDrawerOpen) {
        setIsDiceDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isDiceDrawerOpen]);

  const setDndEdition = async (edition: string) => {
    setEditionState(edition);
    await api.setSetting("dnd_edition", edition);
    showToast(`Edición activa: D&D ${edition}`, "info");
  };

  const selectCharacter = async (id: number) => {
    if (autoSaveTimerRef.current && latestCharRef.current) {
      clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
      await api.saveCharacter(latestCharRef.current);
    }
    setLoading(true);
    try {
      const char = await api.setActiveCharacter(id);
      setActiveCharacter(char);
      const list = await api.listCharacters();
      setCharacters(list);
      showToast(`Personaje cargado: ${char?.name || "Sin Nombre"}`, "success");
    } catch (e) {
      showToast("Error al cambiar de personaje", "warn");
    } finally {
      setLoading(false);
    }
  };

  const updateActiveCharacter = (updates: Partial<CharacterSheetData>) => {
    setActiveCharacter((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...updates };
      latestCharRef.current = updated;

      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(async () => {
        autoSaveTimerRef.current = null;
        if (latestCharRef.current) {
          try {
            const res = await api.saveCharacter(latestCharRef.current);
            if (res.success) {
              const list = await api.listCharacters();
              setCharacters(list);
            }
          } catch (err) {
            console.error("Auto-save error:", err);
          }
        }
      }, 350);

      return updated;
    });
  };

  const saveCurrentCharacter = async (): Promise<boolean> => {
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
    }
    const charToSave = latestCharRef.current || activeCharacter;
    if (!charToSave) return false;
    try {
      const res = await api.saveCharacter(charToSave);
      if (res.success) {
        if (res.character) {
          setActiveCharacter(res.character);
        }
        showToast("Ficha guardada exitosamente", "success");
        await reloadCharacters();
        return true;
      }
      showToast("Error al guardar la ficha", "warn");
      return false;
    } catch (e) {
      showToast("Excepción al guardar", "warn");
      return false;
    }
  };

  const openDiceDrawer = (req?: Partial<RollRequest>) => {
    if (req) {
      setDiceRequest((prev) => ({ ...prev, mode: "normal", ...req }));
    }
    setIsDiceDrawerOpen(true);
  };

  const closeDiceDrawer = () => {
    setIsDiceDrawerOpen(false);
  };

  const executeRoll = async (req: RollRequest): Promise<RollResult> => {
    try {
      const result = await api.rollDice(req);
      setLastRollResult(result);

      await fetchRollHistory();

      if (result.talespire_sent) {
        showToast(`🎲 ${result.label}: Lanzado en mesa 3D (TaleSpire)`, "success");
      } else {
        setCurrentRollingData(result);
        setIsRollingAnimation(true);
        setTimeout(() => {
          setIsRollingAnimation(false);
        }, 2400);
        showToast(`🎲 ${result.label}: ${result.total}`, "info");
      }
      return result;
    } catch (e) {
      showToast("Error ejecutando tirada", "warn");
      throw e;
    }
  };

  const performRestAction = async (restType: "short" | "long", hitDiceSpent: number = 0) => {
    if (!activeCharacter?.id) return;
    try {
      if (autoSaveTimerRef.current && latestCharRef.current) {
        clearTimeout(autoSaveTimerRef.current);
        autoSaveTimerRef.current = null;
        await api.saveCharacter(latestCharRef.current);
      }
      const res = await api.performRest(activeCharacter.id, restType, hitDiceSpent);
      if (res.success && res.character) {
        setActiveCharacter(res.character);
        const list = await api.listCharacters();
        setCharacters(list);
        showToast(
          restType === "long"
            ? "Descanso Largo completado (PG, dados de golpe y ranuras restaurados)"
            : hitDiceSpent > 0
            ? `Descanso Corto completado (${hitDiceSpent} DG gastados)`
            : "Descanso Corto completado",
          "success"
        );
      }
    } catch (e) {
      showToast("Error al procesar descanso", "warn");
    }
  };

  const connectTaleSpire = async () => {
    try {
      const res = await api.connectTaleSpire();
      await refreshTaleSpire();
      showToast(res.message, res.success ? "success" : "warn");
    } catch (e) {
      showToast("Fallo al conectar con TaleSpire", "warn");
    }
  };

  const addSpell = async (spell: SpellItemData): Promise<boolean> => {
    if (!activeCharacter?.id) {
      const existing = (activeCharacter?.spells || []).some(
        (s) => s.name.toLowerCase() === spell.name.toLowerCase()
      );
      if (existing) {
        showToast(`El conjuro ${spell.name} ya está en el grimorio`, "warn");
        return false;
      }
      updateActiveCharacter({
        spells: [...(activeCharacter?.spells || []), spell],
      });
      showToast(`${spell.name} añadido al grimorio`, "success");
      return true;
    }

    try {
      const res = await api.addSpellToCharacter(activeCharacter.id, spell);
      if (res.success && res.character) {
        setActiveCharacter(res.character);
        latestCharRef.current = res.character;
        showToast(`${spell.name} añadido al grimorio`, "success");
        return true;
      } else {
        showToast(res.error || "Error al añadir conjuro", "warn");
        return false;
      }
    } catch (e) {
      showToast("Error de conexión al añadir conjuro", "warn");
      return false;
    }
  };

  const removeSpell = async (spellName: string): Promise<boolean> => {
    if (!activeCharacter?.id) {
      updateActiveCharacter({
        spells: (activeCharacter?.spells || []).filter((s) => s.name !== spellName),
      });
      showToast(`${spellName} eliminado del grimorio`, "info");
      return true;
    }

    try {
      const res = await api.removeSpellFromCharacter(activeCharacter.id, spellName);
      if (res.success && res.character) {
        setActiveCharacter(res.character);
        latestCharRef.current = res.character;
        showToast(`${spellName} eliminado del grimorio`, "info");
        return true;
      }
      return false;
    } catch (e) {
      showToast("Error al eliminar conjuro", "warn");
      return false;
    }
  };

  const syncFeatures = async () => {
    if (!activeCharacter?.id) return;
    try {
      const res = await api.syncCharacterFeatures(activeCharacter.id);
      if (res.success && res.character) {
        setActiveCharacter(res.character);
        latestCharRef.current = res.character;
        showToast("Rasgos de clase sincronizados", "success");
      }
    } catch (e) {
      console.error("Error syncing features:", e);
    }
  };

  return (
    <CharacterContext.Provider
      value={{
        activeCharacter,
        characters,
        loading,
        talespireStatus,
        dndEdition,
        isDiceDrawerOpen,
        diceRequest,
        lastRollResult,
        rollHistory,
        toasts,
        isRollingAnimation,
        currentRollingData,
        setDndEdition,
        reloadCharacters,
        selectCharacter,
        updateActiveCharacter,
        saveCurrentCharacter,
        openDiceDrawer,
        closeDiceDrawer,
        executeRoll,
        fetchRollHistory,
        clearRollHistory,
        performRestAction,
        refreshTaleSpire,
        connectTaleSpire,
        showToast,
        addSpell,
        removeSpell,
        syncFeatures,
      }}
    >
      {children}
    </CharacterContext.Provider>
  );
};

export const useCharacter = () => {
  const context = useContext(CharacterContext);
  if (!context) throw new Error("useCharacter must be used within a CharacterProvider");
  return context;
};
