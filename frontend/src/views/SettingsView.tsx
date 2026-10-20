import React, { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { AppSettings } from "../api/types";
import { X, Upload } from "lucide-react";

export const SettingsView: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { theme, setTheme, availableThemes } = useTheme();
  const {
    talespireStatus,
    connectTaleSpire,
    showToast,
    characters,
    reloadCharacters,
    selectCharacter,
    language,
    setLanguage,
  } = useCharacter();

  const [settings, setSettings] = useState<AppSettings>({
    theme: "dark-obsidian",
    talespire_mode: "dm",
    talespire_enabled: true,
    okf_path: "okf_dnd5e",
    custom_themes_dir: "themes",
  });

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getSettings();
        setSettings(s);
      } catch (e) {
        console.error("Error loading settings:", e);
      }
    }
    load();
  }, []);

  // Ley de Hick: Salida rápida con tecla Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleModeChange = async (mode: "dm" | "player") => {
    setSettings((prev) => ({ ...prev, talespire_mode: mode }));
    await api.setSetting("talespire_mode", mode);
    showToast(`Modo TaleSpire actualizado a: ${mode.toUpperCase()}`, "info");
  };

  const handleTestGesture = async () => {
    showToast("Probando micro-gesto físico en TaleSpire...", "info");
    const success = await api.triggerTaleSpireGesture();
    if (success) {
      showToast("Gesto ejecutado exitosamente en TaleSpire.", "success");
    } else {
      showToast("No se pudo ejecutar el gesto (verifica si el juego está abierto).", "warn");
    }
  };

  const handleDeleteCharacter = async (id: number, charName: string) => {
    if (window.confirm(`¿Estás seguro de eliminar el personaje "${charName}"?`)) {
      await api.deleteCharacter(id);
      await reloadCharacters();
      showToast(`Personaje "${charName}" eliminado.`, "info");
    }
  };

  const handleImportPdf = async () => {
    try {
      const res = await api.importCharacterPdf();
      if (res.success && res.character) {
        await reloadCharacters();
        showToast(`Ficha importada desde PDF: ${res.character.name}`, "success");
      } else if (res.error && res.error !== "Importación cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast("Error al importar PDF", "warn");
    }
  };

  const handleImportJson = async () => {
    try {
      const res = await api.importCharacterJson();
      if (res.success && res.character) {
        await reloadCharacters();
        showToast(`Ficha importada desde JSON: ${res.character.name}`, "success");
      } else if (res.error && res.error !== "Importación cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast("Error al importar JSON", "warn");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-xs" onClick={onClose} />

      {/* Modal Centrado */}
      <div className="relative w-full max-w-2xl bg-surface border border-border-iron rounded-2xl shadow-2xl flex flex-col max-h-[85vh] z-10 select-none overflow-hidden">
        {/* Header del Modal */}
        <div className="px-6 py-4 border-b border-border-iron flex items-center justify-between">
          <div>
            <h2 className="font-display font-bold text-xl text-gold">Ajustes & Configuración</h2>
            <p className="text-xs text-muted">
              Personaliza tu entorno de juego, temas y conexiones externas.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-muted hover:text-main hover:bg-card transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido con Scroll */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* 1. Selector de Tema Visual */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Tema Visual & Estilo
            </h3>

            <div className="grid grid-cols-2 gap-3">
              {availableThemes.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id)}
                  className={`p-3.5 rounded-lg border text-left transition-all ${
                    theme === t.id
                      ? "border-gold bg-card shadow-[0_0_12px_rgba(201,164,92,0.15)] ring-1 ring-gold"
                      : "border-border-iron bg-card/40 hover:bg-card hover:border-gold/50"
                  }`}
                >
                  <div className="font-semibold text-sm text-main">{t.name}</div>
                  <div className="text-xs text-muted mt-0.5">
                    {t.is_dark
                      ? "Atmósfera oscura tipo Sanctum"
                      : "Contraste claro tipo Pergamino"}
                  </div>
                </button>
              ))}
            </div>
            <p className="text-[11px] text-muted">
              Puedes agregar temas personalizados creando subcarpetas con un archivo{" "}
              <code className="text-gold">theme.json</code> en la carpeta{" "}
              <code className="text-gold">themes/</code>.
            </p>
          </section>

          {/* Idioma del Compendio & Tarjetas (ES / EN) */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Idioma del Compendio & Tarjetas (Language)
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setLanguage("es")}
                className={`p-3 rounded-lg border text-left transition-all ${
                  language === "es"
                    ? "border-gold bg-card ring-1 ring-gold shadow-sm"
                    : "border-border-iron bg-card/40 hover:bg-card hover:border-gold/50"
                }`}
              >
                <div className="font-semibold text-sm text-main flex items-center justify-between">
                  <span>Español (ES)</span>
                  {language === "es" && <span className="text-[10px] text-gold font-bold">Activo</span>}
                </div>
                <div className="text-xs text-muted mt-0.5">Nombres y descripciones en español</div>
              </button>
              <button
                onClick={() => setLanguage("en")}
                className={`p-3 rounded-lg border text-left transition-all ${
                  language === "en"
                    ? "border-gold bg-card ring-1 ring-gold shadow-sm"
                    : "border-border-iron bg-card/40 hover:bg-card hover:border-gold/50"
                }`}
              >
                <div className="font-semibold text-sm text-main flex items-center justify-between">
                  <span>English (EN)</span>
                  {language === "en" && <span className="text-[10px] text-gold font-bold">Active</span>}
                </div>
                <div className="text-xs text-muted mt-0.5">Original SRD English naming and rules</div>
              </button>
            </div>
          </section>

          {/* 2. Integración con TaleSpire */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Conexión TaleSpire (Puente 3D)
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-main">Estado del Puente IPC</div>
                  <div className="text-xs text-muted mt-0.5">
                    Estado:{" "}
                    <span className="font-semibold text-gold">{talespireStatus.state_label}</span>
                  </div>
                </div>
                <button
                  onClick={connectTaleSpire}
                  className="px-3 py-1.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main transition-colors"
                >
                  Conectar / Actualizar
                </button>
              </div>

              {/* Modo de Altura del Cursor */}
              <div className="pt-2 border-t border-border-iron/40">
                <label className="block text-xs text-muted mb-1.5 font-medium">
                  Calibración de Gesto Físico (Eje Y relativo a la ventana de TaleSpire)
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleModeChange("dm")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "dm"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    Modo DM / GM (30.0% Altura)
                  </button>
                  <button
                    onClick={() => handleModeChange("player")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "player"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    Modo Jugador (24.0% Altura)
                  </button>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleTestGesture}
                  className="text-xs text-gold hover:underline font-medium"
                >
                  Probar gesto de lanzamiento en TaleSpire ↗
                </button>
              </div>
            </div>
          </section>

          {/* 3. Fuentes de Datos OKF */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Fuentes de Datos & Compendios
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">Ruta de Archivos OKF:</span>
                <span className="font-stat text-main bg-surface px-2 py-0.5 rounded border border-border-iron">
                  {settings.okf_path}
                </span>
              </div>
            </div>
          </section>

          {/* 4. Gestión e Importación de Personajes */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                Personajes en Base de Datos SQLite
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleImportPdf}
                  className="px-2.5 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Importar PDF AcroForm</span>
                </button>
                <button
                  onClick={handleImportJson}
                  className="px-2.5 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Importar JSON</span>
                </button>
              </div>
            </div>

            <div className="bg-card border border-border-iron rounded-xl divide-y divide-border-iron/60 overflow-hidden">
              {characters.map((c) => (
                <div key={c.id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-main">{c.name}</span>
                    <span className="text-muted ml-2">
                      Nvl {c.level} {c.char_class}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        selectCharacter(c.id);
                        onClose();
                      }}
                      className="px-2.5 py-1 rounded bg-surface border border-border-iron hover:border-gold text-muted hover:text-main"
                    >
                      Cargar
                    </button>
                    <button
                      onClick={() => handleDeleteCharacter(c.id, c.name)}
                      className="px-2 py-1 rounded text-crimson hover:bg-crimson/10 border border-transparent hover:border-crimson/40"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Footer del Modal */}
        <div className="px-6 py-3 border-t border-border-iron flex justify-end bg-card/40">
          <button
            onClick={onClose}
            className="px-5 py-1.5 rounded bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs transition-colors shadow-sm"
          >
            Aceptar y Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
