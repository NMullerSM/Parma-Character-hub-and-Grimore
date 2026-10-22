import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ThemeOption } from "../api/types";

export interface ThemeFamily {
  id: string;
  name: string;
  darkId: string;
  lightId: string;
}

export const BASE_THEME_FAMILIES: ThemeFamily[] = [
  { id: "obsidian", name: "Obsidian & Steel", darkId: "dark-obsidian", lightId: "light-obsidian" },
  { id: "parchment", name: "Illuminated Parchment", darkId: "dark-parchment", lightId: "light-parchment" },
  { id: "amethyst", name: "Arcane Amethyst", darkId: "dark-amethyst", lightId: "light-amethyst" },
  { id: "mithril", name: "Mithril Scribe", darkId: "dark-mithril", lightId: "light-mithril" },
];

interface ThemeContextType {
  theme: string;
  isDark: boolean;
  activeFamily: string;
  themeFamilies: ThemeFamily[];
  availableThemes: ThemeOption[];
  setTheme: (themeId: string) => Promise<void>;
  setActiveFamily: (familyId: string) => Promise<void>;
  toggleTheme: () => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const DEFAULT_THEMES: ThemeOption[] = [
  { id: "dark-obsidian", name: "Obsidian & Steel (Oscuro)", is_dark: true },
  { id: "light-obsidian", name: "Obsidian & Steel (Claro)", is_dark: false },
  { id: "dark-parchment", name: "Illuminated Parchment (Oscuro)", is_dark: true },
  { id: "light-parchment", name: "Illuminated Parchment (Claro)", is_dark: false },
  { id: "dark-amethyst", name: "Arcane Amethyst (Oscuro)", is_dark: true },
  { id: "light-amethyst", name: "Arcane Amethyst (Claro)", is_dark: false },
  { id: "dark-mithril", name: "Mithril Scribe (Oscuro)", is_dark: true },
  { id: "light-mithril", name: "Mithril Scribe (Claro)", is_dark: false },
];

const THEME_PAIR_MAP: Record<string, string> = {
  "dark-obsidian": "light-obsidian",
  "light-obsidian": "dark-obsidian",
  "dark-parchment": "light-parchment",
  "light-parchment": "dark-parchment",
  "dark-amethyst": "light-amethyst",
  "light-amethyst": "dark-amethyst",
  "dark-mithril": "light-mithril",
  "light-mithril": "dark-mithril",
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setCurrentTheme] = useState<string>("dark-obsidian");
  const [availableThemes, setAvailableThemes] = useState<ThemeOption[]>(DEFAULT_THEMES);
  const [themeFamilies, setThemeFamilies] = useState<ThemeFamily[]>(BASE_THEME_FAMILIES);

  const applyTheme = (themeId: string) => {
    setCurrentTheme(themeId);
    document.documentElement.setAttribute("data-theme", themeId);
  };

  const isDark = theme.startsWith("dark-") || theme === "dark-obsidian";

  // Determinar la familia actual basada en el ID del tema
  const activeFamily = (() => {
    for (const fam of themeFamilies) {
      if (fam.darkId === theme || fam.lightId === theme || fam.id === theme) {
        return fam.id;
      }
    }
    return "obsidian";
  })();

  useEffect(() => {
    async function loadTheme() {
      try {
        const settings = await api.getSettings();
        const themes = await api.getAvailableThemes();
        if (themes && themes.length > 0) {
          const map = new Map<string, ThemeOption>();
          DEFAULT_THEMES.forEach((t) => map.set(t.id, t));
          themes.forEach((t) => map.set(t.id, t));
          const allList = Array.from(map.values());
          setAvailableThemes(allList);

          // Construir lista de familias incluyendo posibles temas Homebrew de themes/
          const families = [...BASE_THEME_FAMILIES];
          allList.forEach((t) => {
            const isBase = families.some((f) => f.darkId === t.id || f.lightId === t.id);
            if (!isBase) {
              const baseId = t.id.replace(/^(dark-|light-)/, "");
              const existingFam = families.find((f) => f.id === baseId);
              if (existingFam) {
                if (t.is_dark) existingFam.darkId = t.id;
                else existingFam.lightId = t.id;
              } else {
                families.push({
                  id: baseId,
                  name: t.name.replace(/\s*\((Oscuro|Claro)\)/i, ""),
                  darkId: t.is_dark ? t.id : `dark-${baseId}`,
                  lightId: !t.is_dark ? t.id : `light-${baseId}`,
                });
              }
            }
          });
          setThemeFamilies(families);
        }
        if (settings.theme) {
          applyTheme(settings.theme);
        }
      } catch (e) {
        console.error("Error loading theme settings:", e);
      }
    }
    loadTheme();
    window.addEventListener("pywebviewready", loadTheme);
    return () => window.removeEventListener("pywebviewready", loadTheme);
  }, []);

  const setTheme = async (themeId: string) => {
    applyTheme(themeId);
    await api.setSetting("theme", themeId);
  };

  const setActiveFamily = async (familyId: string) => {
    const fam = themeFamilies.find((f) => f.id === familyId);
    if (fam) {
      const nextTheme = isDark ? fam.darkId : fam.lightId;
      await setTheme(nextTheme);
    }
  };

  const toggleTheme = async () => {
    const fam = themeFamilies.find((f) => f.id === activeFamily);
    const nextTheme = fam
      ? (isDark ? fam.lightId : fam.darkId)
      : (THEME_PAIR_MAP[theme] || (isDark ? "light-obsidian" : "dark-obsidian"));
    await setTheme(nextTheme);
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        isDark,
        activeFamily,
        themeFamilies,
        availableThemes,
        setTheme,
        setActiveFamily,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};
