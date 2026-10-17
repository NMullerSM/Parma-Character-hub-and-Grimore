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

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setCurrentTheme] = useState<string>("dark-obsidian");
  const [availableThemes, setAvailableThemes] = useState<ThemeOption[]>([
    { id: "dark-obsidian", name: "Obsidian Sanctum (Oscuro)", is_dark: true },
    { id: "light-parchment", name: "Illuminated Grimoire (Claro)", is_dark: false },
  ]);

  useEffect(() => {
    async function loadTheme() {
      try {
        const settings = await api.getSettings();
        const themes = await api.getAvailableThemes();
        if (themes && themes.length > 0) setAvailableThemes(themes);
        if (settings.theme) {
          applyTheme(settings.theme);
        }
      } catch (e) {
        console.error("Error loading theme settings:", e);
      }
    }
    loadTheme();
  }, []);

  const applyTheme = (themeId: string) => {
    setCurrentTheme(themeId);
    document.documentElement.setAttribute("data-theme", themeId);
  };

  const setTheme = async (themeId: string) => {
    applyTheme(themeId);
    await api.setSetting("theme", themeId);
  };

  const toggleTheme = async () => {
    const nextTheme = theme === "dark-obsidian" ? "light-parchment" : "dark-obsidian";
    await setTheme(nextTheme);
  };

  const isDark = theme.includes("dark") || theme === "dark-obsidian";

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
