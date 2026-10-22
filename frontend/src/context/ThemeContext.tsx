import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ThemeOption } from "../api/types";

interface ThemeContextType {
  theme: string;
  isDark: boolean;
  availableThemes: ThemeOption[];
  setTheme: (themeId: string) => Promise<void>;
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

  const applyTheme = (themeId: string) => {
    setCurrentTheme(themeId);
    document.documentElement.setAttribute("data-theme", themeId);
  };

  useEffect(() => {
    async function loadTheme() {
      try {
        const settings = await api.getSettings();
        const themes = await api.getAvailableThemes();
        if (themes && themes.length > 0) {
          // Unir temas por defecto con posibles temas de bridge/disco
          const map = new Map<string, ThemeOption>();
          DEFAULT_THEMES.forEach((t) => map.set(t.id, t));
          themes.forEach((t) => map.set(t.id, t));
          setAvailableThemes(Array.from(map.values()));
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

  const isDark = theme.startsWith("dark-") || theme === "dark-obsidian";

  const toggleTheme = async () => {
    const nextTheme = THEME_PAIR_MAP[theme] || (isDark ? "light-obsidian" : "dark-obsidian");
    await setTheme(nextTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, isDark, availableThemes, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};
