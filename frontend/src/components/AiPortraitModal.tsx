import React, { useState, useEffect } from "react";
import { X, Sparkles, Copy, Check, Wand2, Image as ImageIcon, Settings2, ExternalLink } from "lucide-react";
import { api } from "../api/client";
import type { CharacterSheetData } from "../api/types";

interface AiPortraitModalProps {
  isOpen: boolean;
  onClose: () => void;
  character: CharacterSheetData;
  onPortraitGenerated: (base64OrUrl: string) => void;
  initialConfigOpen?: boolean;
}

type ArtStyle = "pixelart" | "fantasy" | "oil" | "sketch" | "cinematic";
type AiProvider = "pollinations" | "google" | "openai" | "sd_local" | "custom";

interface StyleOption {
  id: ArtStyle;
  label: string;
  badge: string;
  promptModifier: string;
}

interface ProviderMeta {
  id: AiProvider;
  name: string;
  defaultUrl: string;
  placeholderKey: string;
  helpText: string;
  helpLink?: string;
  isFree?: boolean;
}

const PROVIDER_OPTIONS: ProviderMeta[] = [
  {
    id: "pollinations",
    name: "Gratis / Sin Clave (Pollinations)",
    defaultUrl: "https://image.pollinations.ai",
    placeholderKey: "No requiere clave",
    helpText: "Generador instantáneo y gratuito. No requiere registro, tarjeta ni API Key.",
    isFree: true,
  },
  {
    id: "google",
    name: "Google AI Studio (Imagen 3)",
    defaultUrl: "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
    placeholderKey: "AIzaSy...",
    helpText: "Requiere proyecto de Google Cloud con facturación activa para Imagen 3 (de lo contrario da 403 PERMISSION_DENIED).",
    helpLink: "https://aistudio.google.com/app/apikey",
  },
  {
    id: "openai",
    name: "OpenAI (DALL-E 3)",
    defaultUrl: "https://api.openai.com/v1/images/generations",
    placeholderKey: "sk-...",
    helpText: "Usa tu clave oficial de OpenAI (platform.openai.com) con saldo de créditos.",
    helpLink: "https://platform.openai.com/api-keys",
  },
  {
    id: "sd_local",
    name: "Stable Diffusion Local (WebUI)",
    defaultUrl: "http://127.0.0.1:7860/sdapi/v1/txt2img",
    placeholderKey: "Opcional",
    helpText: "Ejecutando en tu PC (requiere A1111 o ComfyUI con argumento --api).",
  },
  {
    id: "custom",
    name: "Endpoint Personalizado",
    defaultUrl: "",
    placeholderKey: "Token o API Key",
    helpText: "Configura manualmente cualquier proxy o API compatible.",
  },
];

const STYLE_OPTIONS: StyleOption[] = [
  {
    id: "pixelart",
    label: "Pixel Art (16-bit RPG)",
    badge: "Retro",
    promptModifier: "16-bit pixel art portrait, retro RPG character sprite, vibrant palette, detailed pixel shading, fantasy icon style, solid dark background",
  },
  {
    id: "fantasy",
    label: "Fantasía Épica Digital",
    badge: "Digital Art",
    promptModifier: "Detailed digital fantasy illustration, high quality character portrait, D&D 5e official art style, dramatic lighting, artstation trending",
  },
  {
    id: "oil",
    label: "Pintura al Óleo Clásica",
    badge: "Clásico",
    promptModifier: "Renaissance oil painting, chiaroscuro lighting, rich canvas texture, majestic fantasy hero portrait, Rembrandt style",
  },
  {
    id: "sketch",
    label: "Boceto a Tinta / Pergamino",
    badge: "Manual D&D",
    promptModifier: "Detailed ink and graphite sketch on aged parchment, crosshatching, classic tabletop RPG manual illustration",
  },
  {
    id: "cinematic",
    label: "Cinemático Realista",
    badge: "Fotorealista",
    promptModifier: "Cinematic portrait, realistic fantasy character, 8k resolution, photorealistic skin and armor texture, volumetric lighting, unreal engine render",
  },
];

export const AiPortraitModal: React.FC<AiPortraitModalProps> = ({
  isOpen,
  onClose,
  character,
  onPortraitGenerated,
  initialConfigOpen = false,
}) => {
  const [selectedStyle, setSelectedStyle] = useState<ArtStyle>("fantasy");
  const [prompt, setPrompt] = useState<string>("");
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(initialConfigOpen);
  const [showAdvancedUrl, setShowAdvancedUrl] = useState<boolean>(false);

  const [provider, setProvider] = useState<AiProvider>(() => {
    return (localStorage.getItem("dnd_ai_img_provider") as AiProvider) || "pollinations";
  });
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem("dnd_ai_img_api_key") || "");
  const [apiUrl, setApiUrl] = useState<string>(() => {
    return localStorage.getItem("dnd_ai_img_api_url") || "https://image.pollinations.ai";
  });

  const [pastedImage, setPastedImage] = useState<string>("");
  const [previewImage, setPreviewImage] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  useEffect(() => {
    if (initialConfigOpen) {
      setShowConfig(true);
    }
  }, [initialConfigOpen]);

  // Auto-detectar proveedor si la clave pegada es de Google u OpenAI
  const handleKeyChange = (val: string) => {
    const trimmed = val.trim();
    setApiKey(trimmed);
    localStorage.setItem("dnd_ai_img_api_key", trimmed);

    if (trimmed.startsWith("AIzaSy") && provider !== "google") {
      setProvider("google");
      setApiUrl("https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict");
      localStorage.setItem("dnd_ai_img_provider", "google");
      localStorage.setItem("dnd_ai_img_api_url", "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict");
    } else if (trimmed.startsWith("sk-") && provider !== "openai") {
      setProvider("openai");
      setApiUrl("https://api.openai.com/v1/images/generations");
      localStorage.setItem("dnd_ai_img_provider", "openai");
      localStorage.setItem("dnd_ai_img_api_url", "https://api.openai.com/v1/images/generations");
    }
  };

  const handleProviderSelect = (newProv: AiProvider) => {
    setProvider(newProv);
    localStorage.setItem("dnd_ai_img_provider", newProv);
    const meta = PROVIDER_OPTIONS.find((p) => p.id === newProv);
    if (meta && meta.defaultUrl) {
      setApiUrl(meta.defaultUrl);
      localStorage.setItem("dnd_ai_img_api_url", meta.defaultUrl);
    }
  };

  // Construir prompt dinámico según estilo y datos del personaje
  useEffect(() => {
    const styleObj = STYLE_OPTIONS.find((s) => s.id === selectedStyle) || STYLE_OPTIONS[0];
    const identity = `${character.name || "Aventurero"}, ${character.race || "Humano"} ${character.char_class || "Guerrero"}`;
    const appearanceText = character.appearance ? ` Apariencia física: ${character.appearance.trim()}.` : "";
    
    const constructed = `Retrato de personaje de D&D 5e: ${identity}.${appearanceText} Estilo: ${styleObj.promptModifier}. Centrado, primer plano del rostro y torso, iluminación dramática.`;
    setPrompt(constructed);
  }, [selectedStyle, character.name, character.race, character.char_class, character.appearance]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(prompt);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleSaveConfig = () => {
    localStorage.setItem("dnd_ai_img_provider", provider);
    localStorage.setItem("dnd_ai_img_api_url", apiUrl.trim());
    localStorage.setItem("dnd_ai_img_api_key", apiKey.trim());
    setShowConfig(false);
    setStatusMessage("Configuración de API guardada.");
    setTimeout(() => setStatusMessage(""), 3000);
  };

  // Generación por llamada nativa sin problemas de CORS
  const handleGenerate = async () => {
    const cleanKey = apiKey.trim();

    if (!cleanKey && (provider === "google" || provider === "openai" || provider === "custom")) {
      setStatusMessage(`Ingresa tu API Key de ${activeProviderMeta.name} o selecciona la opción 'Gratis / Sin Clave'.`);
      setShowConfig(true);
      return;
    }

    setLoading(true);
    setStatusMessage(`Generando retrato mediante ${activeProviderMeta.name}...`);

    try {
      const res = await api.generateAiPortrait({
        prompt,
        provider,
        apiKey: cleanKey,
        apiUrl: apiUrl.trim(),
        model: provider === "openai" ? "dall-e-3" : "imagen-3.0-generate-002",
      });

      if (res.success && res.image_base64) {
        setPreviewImage(res.image_base64);
        setStatusMessage("¡Retrato generado exitosamente!");
      } else {
        throw new Error(res.error || "La API no devolvió una imagen válida.");
      }
    } catch (e: any) {
      console.error("Error generating portrait:", e);
      setStatusMessage(`Error: ${e.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPreview = async () => {
    const imgToUse = previewImage || pastedImage;
    if (!imgToUse) return;

    if (character.id) {
      try {
        await api.setCharacterPortraitBase64(character.id, imgToUse);
      } catch (e) {
        console.error("Error saving portrait to backend:", e);
      }
    }
    onPortraitGenerated(imgToUse);
    onClose();
  };

  const activeProviderMeta = PROVIDER_OPTIONS.find((p) => p.id === provider) || PROVIDER_OPTIONS[0];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-canvas/85 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-card border border-border-iron rounded-xl shadow-2xl flex flex-col overflow-hidden max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="flex items-center justify-between p-4 border-b border-border-iron bg-surface/50 shrink-0">
          <div className="flex items-center gap-2.5">
            <Wand2 className="w-5 h-5 text-gold" />
            <div>
              <h2 className="font-display font-bold text-lg text-gold">
                Generador de Retrato IA de Personaje
              </h2>
              <p className="text-xs text-muted">
                Crea ilustraciones personalizadas para {character.name || "tu héroe"} usando IA.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className={`px-2.5 py-1.5 rounded-lg border text-xs transition-colors flex items-center gap-1.5 ${
                showConfig
                  ? "bg-gold text-canvas border-gold font-semibold"
                  : "bg-surface border-border-iron text-muted hover:text-main hover:border-gold"
              }`}
              title="Configurar Proveedor y API Key"
            >
              <Settings2 className="w-4 h-4" />
              <span>Configuración</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
              title="Cerrar (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Panel de Configuración de API (Colapsable o Inicial) */}
        {showConfig && (
          <div className="p-4 bg-surface border-b border-border-iron space-y-3.5 shrink-0 animate-fade-in">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gold flex items-center gap-1.5">
                <Settings2 className="w-3.5 h-3.5" />
                Configuración del Proveedor IA
              </h3>
              {activeProviderMeta.helpLink && (
                <a
                  href={activeProviderMeta.helpLink}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-gold hover:underline flex items-center gap-1 font-medium"
                >
                  <span>Obtener clave aquí</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            {/* Selector de Proveedor */}
            <div>
              <label className="block text-muted text-[11px] mb-1 font-medium">Proveedor de Imagen</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {PROVIDER_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => handleProviderSelect(opt.id)}
                    type="button"
                    className={`px-2.5 py-1.5 text-xs rounded border text-center transition-all ${
                      provider === opt.id
                        ? "bg-gold text-canvas border-gold font-bold shadow-sm"
                        : "bg-card border-border-iron text-muted hover:text-main hover:border-gold/50"
                    }`}
                  >
                    {opt.id === "pollinations" && "Gratis / Sin Clave"}
                    {opt.id === "google" && "Google AI Studio"}
                    {opt.id === "openai" && "OpenAI"}
                    {opt.id === "sd_local" && "Stable Diffusion"}
                    {opt.id === "custom" && "Personalizado"}
                  </button>
                ))}
              </div>
            </div>

            {/* Campo Clave de API (si el proveedor la requiere) */}
            {!activeProviderMeta.isFree ? (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-muted text-[11px] font-medium">
                    API Key de {activeProviderMeta.name}
                  </label>
                  <span className="text-[10px] text-muted/80">Guardada localmente de forma segura</span>
                </div>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => handleKeyChange(e.target.value)}
                  placeholder={activeProviderMeta.placeholderKey}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                />
                <p className="text-[11px] text-muted/90 mt-1">
                  {activeProviderMeta.helpText}
                </p>
              </div>
            ) : (
              <div className="p-2.5 rounded bg-card/60 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                <Check className="w-4 h-4 shrink-0" />
                <span>
                  <strong>Listo para generar:</strong> Esta opción es 100% gratuita y no requiere ninguna clave ni tarjeta.
                </span>
              </div>
            )}

            {/* Opciones Avanzadas: Endpoint URL */}
            <div>
              <button
                type="button"
                onClick={() => setShowAdvancedUrl(!showAdvancedUrl)}
                className="text-[11px] text-muted hover:text-gold transition-colors flex items-center gap-1"
              >
                <span>{showAdvancedUrl ? "▾ Ocultar URL del Endpoint" : "▸ Ver / Editar URL del Endpoint"}</span>
              </button>
              {showAdvancedUrl && (
                <div className="mt-2 pt-2 border-t border-border-iron/40 animate-fade-in space-y-1">
                  <label className="block text-muted text-[10px]">URL del Endpoint API</label>
                  <input
                    type="text"
                    value={apiUrl}
                    onChange={(e) => {
                      setApiUrl(e.target.value);
                      localStorage.setItem("dnd_ai_img_api_url", e.target.value.trim());
                    }}
                    placeholder="https://..."
                    className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none font-mono"
                  />
                  <p className="text-[10px] text-muted/70">
                    Google AI Studio Imagen 3: <code className="text-gold">https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict</code>
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                onClick={handleSaveConfig}
                className="px-3 py-1 bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs rounded transition-colors"
              >
                Guardar Configuración
              </button>
            </div>
          </div>
        )}

        {/* Cuerpo del Modal */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* 1. Selector de Estilo Artístico */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-2">
              Estilo Visual de Ilustración
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {STYLE_OPTIONS.map((style) => {
                const isSelected = selectedStyle === style.id;
                return (
                  <button
                    key={style.id}
                    onClick={() => setSelectedStyle(style.id)}
                    className={`p-2.5 rounded-lg border text-left flex flex-col justify-between transition-all ${
                      isSelected
                        ? "bg-gold/15 border-gold shadow-sm ring-1 ring-gold"
                        : "bg-surface/50 border-border-iron hover:border-gold/60 text-muted"
                    }`}
                  >
                    <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded w-max mb-1.5 ${
                      isSelected ? "bg-gold text-canvas" : "bg-card text-muted"
                    }`}>
                      {style.badge}
                    </span>
                    <span className={`text-xs font-semibold ${isSelected ? "text-gold" : "text-main"}`}>
                      {style.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Prompt Generado & Editor */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                Prompt de Generación (Editable)
              </label>
              <button
                onClick={handleCopyPrompt}
                className="text-xs text-gold hover:text-gold-hover flex items-center gap-1 font-semibold transition-colors"
                title="Copiar prompt al portapapeles"
              >
                {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{isCopied ? "¡Copiado!" : "Copiar Prompt"}</span>
              </button>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder="Describe los rasgos visuales, vestimenta, colores y pose de tu personaje..."
              className="w-full bg-input text-main border border-border-iron rounded-lg p-2.5 text-xs focus:border-gold outline-none leading-relaxed transition-colors resize-none"
            />
          </div>

          {/* 3. Panel de Previsualización & Pegar Imagen Externa */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center bg-surface/30 p-3 rounded-lg border border-border-iron">
            {/* Contenedor de la Imagen */}
            <div className="flex flex-col items-center justify-center">
              <div className="w-40 h-40 sm:w-48 sm:h-48 rounded-xl border-2 border-dashed border-border-iron bg-card/60 overflow-hidden flex items-center justify-center relative shadow-inner">
                {previewImage || pastedImage ? (
                  <img
                    src={previewImage || pastedImage}
                    alt="Retrato Generado"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="p-4 text-center text-muted space-y-1">
                    <ImageIcon className="w-8 h-8 mx-auto opacity-40 text-gold" />
                    <p className="text-[11px] font-medium">Sin previsualización</p>
                    <p className="text-[10px] text-muted/70">
                      Genera con {activeProviderMeta.name} o pega una URL/Base64.
                    </p>
                  </div>
                )}
                {loading && (
                  <div className="absolute inset-0 bg-black/75 flex flex-col items-center justify-center gap-2 p-2 text-center">
                    <div className="w-6 h-6 border-2 border-gold border-t-transparent rounded-full animate-spin" />
                    <span className="text-[11px] text-gold font-medium">Generando ilustración...</span>
                  </div>
                )}
              </div>
            </div>

            {/* Alternativa: Pegar imagen externa o URL directa */}
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-main mb-1">
                  O pega una URL o Base64 directamente:
                </h4>
                <p className="text-[11px] text-muted mb-2">
                  Si generaste tu imagen en Midjourney, ChatGPT o NovelAI, pega el enlace o código aquí:
                </p>
                <input
                  type="text"
                  value={pastedImage}
                  onChange={(e) => setPastedImage(e.target.value)}
                  placeholder="https://... o data:image/png;base64,..."
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                />
              </div>

              {statusMessage && (
                <div className="p-2.5 rounded bg-surface border border-border-iron text-[11px] text-gold font-medium leading-relaxed">
                  {statusMessage}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pie del Modal con Acciones */}
        <div className="p-3 border-t border-border-iron bg-surface/50 flex flex-wrap items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-gold hover:bg-gold-hover disabled:opacity-50 text-canvas font-bold text-xs flex items-center gap-1.5 transition-all shadow-sm active:scale-95"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? "Generando..." : `Generar con ${provider === "pollinations" ? "IA Gratis" : provider === "google" ? "Google Imagen 3" : provider === "openai" ? "DALL-E 3" : "IA"}`}</span>
            </button>
            <button
              onClick={handleCopyPrompt}
              className="px-3 py-2 rounded-lg bg-surface border border-border-iron hover:border-gold text-muted hover:text-main text-xs font-medium transition-colors flex items-center gap-1"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copiar Prompt</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-2 rounded-lg border border-border-iron hover:border-gold text-xs text-muted hover:text-main font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleApplyPreview}
              disabled={!previewImage && !pastedImage}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:pointer-events-none text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-sm active:scale-95"
            >
              <Check className="w-4 h-4" />
              <span>Aplicar a la Ficha</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
