import React, { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { AppSettings } from "../api/types";
import { X, Globe, Sparkles, FolderSync, Shield } from "lucide-react";

export const SettingsView: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { theme, setTheme, availableThemes } = useTheme();
  const { talespireStatus, connectTaleSpire, showToast, characters, reloadCharacters, selectCharacter } =
    useCharacter();

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
            <p className="text-xs text-muted">Personaliza tu entorno de juego, temas y conexiones externas.</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-muted hover:text-main hover:bg-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido con Scroll */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* 1. Selector de Tema Visual */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-gold" />
              <span>Tema Visual & Estilo</span>
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
                    {t.is_dark ? "Atmósfera oscura tipo Sanctum" : "Contraste claro tipo Pergamino"}
                  </div>
                </button>
              ))}
            </div>
            <p className="text-[11px] text-muted">
              Puedes agregar temas personalizados creando subcarpetas con un archivo <code className="text-gold">theme.json</code> en la carpeta <code className="text-gold">themes/</code>.
            </p>
          </section>

          {/* 2. Integración con TaleSpire */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
              <Shield className="w-4 h-4 text-gold" />
              <span>Conexión TaleSpire (Puente 3D)</span>
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-main">Estado del Puente IPC</div>
                  <div className="text-xs text-muted mt-0.5">
                    Estado: <span className="font-semibold text-gold">{talespireStatus.state_label}</span>
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
                <label className="block text-xs text-muted mb-1.5 font-medium">Calibración de Gesto Físico</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleModeChange("dm")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "dm"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    Modo DM / GM (17.5% Altura)
                  </button>
                  <button
                    onClick={() => handleModeChange("player")}
                    className={`flex-1 py-1.5 rounded border text-xs font-semibold transition-colors ${
                      settings.talespire_mode === "player"
                        ? "bg-gold text-canvas border-gold"
                        : "border-border-iron bg-surface text-muted"
                    }`}
                  >
                    Modo Jugador (15.5% Altura)
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

          {/* 3. Fuentes de Datos OKF & Propuesta AideDD */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
              <FolderSync className="w-4 h-4 text-gold" />
              <span>Fuentes de Datos & Compendios</span>
            </h3>

            <div className="p-4 rounded-xl border border-border-iron bg-card space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">Ruta de Archivos OKF:</span>
                <span className="font-stat text-main bg-surface px-2 py-0.5 rounded border border-border-iron">
                  {settings.okf_path}
                </span>
              </div>

              {/* Tarjeta Propuesta AideDD.org */}
              <div className="p-3 rounded-lg bg-surface/60 border border-border-iron/80 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-gold">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Sincronización con AideDD.org (Propuesta)</span>
                </div>
                <p className="text-[11px] text-muted leading-relaxed">
                  Arquitectura preparada para conectar con el catálogo de conjuros, invocaciones y objetos mágicos de <span className="text-main font-medium">aidedd.org</span> mediante un crawler asíncrono para generar ficheros Markdown OKF automáticamente.
                </p>
                <div className="pt-1">
                  <button
                    disabled
                    className="px-2.5 py-1 rounded bg-card border border-border-iron text-[11px] text-muted/60 cursor-not-allowed"
                  >
                    Sincronizar desde AideDD (Próximamente)
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* 4. Gestión de Personajes Guardados */}
          <section className="space-y-3 pt-3 border-t border-border-iron">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Personajes Guardados en SQLite
            </h3>
            <div className="bg-card border border-border-iron rounded-xl divide-y divide-border-iron/60 overflow-hidden">
              {characters.map((c) => (
                <div key={c.id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-main">{c.name}</span>
                    <span className="text-muted ml-2">Nvl {c.level} {c.char_class}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => selectCharacter(c.id)}
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
