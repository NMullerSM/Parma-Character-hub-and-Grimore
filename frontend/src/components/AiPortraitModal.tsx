import React, { useState, useEffect } from "react";
import { X, Sparkles, Copy, Check, Wand2, Image as ImageIcon, Settings2, ExternalLink, ChevronDown, ChevronUp, RotateCcw } from "lucide-react";
import { api } from "../api/client";
import type { CharacterSheetData } from "../api/types";
import { useTranslation } from "../i18n";

interface AiPortraitModalProps {
  isOpen: boolean;
  onClose: () => void;
  character: CharacterSheetData;
  onPortraitGenerated: (base64OrUrl: string) => void;
  initialConfigOpen?: boolean;
}

export type CharacterGender = "male" | "female" | "androgynous" | "creature";

export interface GenderOption {
  id: CharacterGender;
  label: string;
  sub: string;
  icon: string;
  hint: string;
}

type ArtStyle = "pixelart" | "fantasy" | "oil" | "sketch" | "cinematic";
type AiProvider = "pollinations" | "google" | "openai" | "sd_local" | "custom";

interface StyleOption {
  id: ArtStyle;
  label: string;
  badge: string;
  hint: string;
}

function getStyleOptions(lang: "es" | "en"): StyleOption[] {
  if (lang === "en") {
    return [
      {
        id: "pixelart",
        label: "Pixel Art (16-bit RPG)",
        badge: "Retro",
        hint: "Crisp 16-bit sprite with defined pixels SNES / GBA style",
      },
      {
        id: "fantasy",
        label: "Digital Epic Fantasy",
        badge: "Digital Art",
        hint: "Modern official D&D 5e rulebook illustration",
      },
      {
        id: "oil",
        label: "Classical Oil Painting",
        badge: "Classic",
        hint: "Renaissance oil painting with chiaroscuro and canvas texture",
      },
      {
        id: "sketch",
        label: "Ink & Parchment Sketch",
        badge: "D&D Rulebook",
        hint: "Sepia ink engraving on aged parchment",
      },
      {
        id: "cinematic",
        label: "Cinematic Realistic",
        badge: "Photorealistic",
        hint: "Hyperrealistic 8k portrait with volumetric lighting",
      },
    ];
  }
  return [
    {
      id: "pixelart",
      label: "Pixel Art (16-bit RPG)",
      badge: "Retro",
      hint: "Sprite 16-bit nítido con píxeles definidos estilo SNES / GBA",
    },
    {
      id: "fantasy",
      label: "Fantasía Épica Digital",
      badge: "Digital Art",
      hint: "Ilustración oficial moderna de manual D&D 5e",
    },
    {
      id: "oil",
      label: "Pintura al Óleo Clásica",
      badge: "Clásico",
      hint: "Óleo renacentista con claroscuro y textura de lienzo",
    },
    {
      id: "sketch",
      label: "Boceto a Tinta / Pergamino",
      badge: "Manual D&D",
      hint: "Grabado a tinta sepia sobre pergamino envejecido",
    },
    {
      id: "cinematic",
      label: "Cinemático Realista",
      badge: "Fotorealista",
      hint: "Retrato hiperrealista en 8k con iluminación volumétrica",
    },
  ];
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

function getProviderOptions(lang: "es" | "en"): ProviderMeta[] {
  if (lang === "en") {
    return [
      {
        id: "pollinations",
        name: "Free / Instant (Recommended)",
        defaultUrl: "https://image.pollinations.ai",
        placeholderKey: "No API key required",
        helpText: "Free generator without account registration or credit limits. Ready to use.",
        isFree: true,
      },
      {
        id: "google",
        name: "Google AI Studio (Imagen 3)",
        defaultUrl: "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
        placeholderKey: "AIzaSy...",
        helpText: "Requires Google Cloud project with active billing for Imagen 3.",
        helpLink: "https://aistudio.google.com/app/apikey",
      },
      {
        id: "openai",
        name: "OpenAI (DALL-E 3)",
        defaultUrl: "https://api.openai.com/v1/images/generations",
        placeholderKey: "sk-...",
        helpText: "Use your official OpenAI key (platform.openai.com) with available credit.",
        helpLink: "https://platform.openai.com/api-keys",
      },
      {
        id: "sd_local",
        name: "Stable Diffusion Local (WebUI)",
        defaultUrl: "http://127.0.0.1:7860/sdapi/v1/txt2img",
        placeholderKey: "Optional",
        helpText: "A1111 or ComfyUI running locally on your PC with the --api argument.",
      },
      {
        id: "custom",
        name: "Custom Endpoint",
        defaultUrl: "",
        placeholderKey: "Token or API Key",
        helpText: "Any REST-compatible proxy or service.",
      },
    ];
  }
  return [
    {
      id: "pollinations",
      name: "Gratis / Instantáneo (Recomendado)",
      defaultUrl: "https://image.pollinations.ai",
      placeholderKey: "No requiere clave",
      helpText: "Generador gratuito sin registros ni límites de tarjeta. Listo para usar.",
      isFree: true,
    },
    {
      id: "google",
      name: "Google AI Studio (Imagen 3)",
      defaultUrl: "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
      placeholderKey: "AIzaSy...",
      helpText: "Requiere proyecto de Google Cloud con facturación activa para Imagen 3.",
      helpLink: "https://aistudio.google.com/app/apikey",
    },
    {
      id: "openai",
      name: "OpenAI (DALL-E 3)",
      defaultUrl: "https://api.openai.com/v1/images/generations",
      placeholderKey: "sk-...",
      helpText: "Usa tu clave oficial de OpenAI (platform.openai.com) con saldo disponible.",
      helpLink: "https://platform.openai.com/api-keys",
    },
    {
      id: "sd_local",
      name: "Stable Diffusion Local (WebUI)",
      defaultUrl: "http://127.0.0.1:7860/sdapi/v1/txt2img",
      placeholderKey: "Opcional",
      helpText: "A1111 o ComfyUI ejecutándose en tu PC con el argumento --api.",
    },
    {
      id: "custom",
      name: "Endpoint Personalizado",
      defaultUrl: "",
      placeholderKey: "Token o API Key",
      helpText: "Cualquier proxy o servicio compatible con REST.",
    },
  ];
}

const RACE_EN_MAP: Record<string, string> = {
  humano: "human",
  humana: "human",
  elfo: "elf",
  elfa: "elf",
  "alto elfo": "high elf",
  "alta elfa": "high elf",
  "elfo de los bosques": "wood elf",
  "elfa de los bosques": "wood elf",
  "elfo oscuro": "drow dark elf",
  "elfa oscura": "drow dark elf",
  drow: "drow dark elf",
  enano: "dwarf",
  enana: "dwarf",
  "enano de las colinas": "hill dwarf",
  "enana de las colinas": "hill dwarf",
  "enano de las montañas": "mountain dwarf",
  "enana de las montañas": "mountain dwarf",
  semielfo: "half-elf",
  semielfa: "half-elf",
  mediano: "halfling",
  mediana: "halfling",
  dracónido: "dragonborn",
  draconido: "dragonborn",
  gnomo: "gnome",
  gnoma: "gnome",
  orco: "orc",
  orca: "orc",
  semiorco: "half-orc",
  semiorca: "half-orc",
  tiefling: "tiefling",
  goliat: "goliath",
  goliath: "goliath",
  aasimar: "aasimar",
};

const CLASS_EN_MAP: Record<string, string> = {
  bárbaro: "barbarian",
  barbaro: "barbarian",
  bárbara: "barbarian",
  bardo: "bard",
  barda: "bard",
  clérigo: "cleric",
  clerigo: "cleric",
  clériga: "cleric",
  druida: "druid",
  explorador: "ranger",
  exploradora: "ranger",
  guerrero: "fighter warrior",
  guerrera: "fighter warrior",
  hechicero: "sorcerer",
  hechicera: "sorcerer",
  mago: "wizard",
  maga: "wizard",
  monje: "monk",
  monja: "monk",
  paladín: "paladin",
  paladin: "paladin",
  paladina: "paladin",
  pícaro: "rogue",
  picaro: "rogue",
  pícara: "rogue",
  brujo: "warlock",
  bruja: "warlock",
  artífice: "artificer",
  artifice: "artificer",
};

export function detectInitialGender(char: CharacterSheetData): CharacterGender {
  const combined = `${char.name || ""} ${char.appearance || ""} ${char.history || ""} ${char.char_class || ""} ${char.race || ""}`.toLowerCase();
  
  if (/\b(mujer|femenin[ao]|ella|dama|chica|maga|bruja|guerrera|paladina|barda|clériga|exploradora|female|woman|lady|girl|heroine)\b/i.test(combined)) {
    return "female";
  }
  if (/\b(hombre|masculin[ao]|él|el|varon|varón|chico|caballero|barba|bigote|mago|brujo|guerrero|paladín|bardo|clérigo|explorador|male|man|guy|lord|hero)\b/i.test(combined)) {
    return "male";
  }
  return "male";
}

export function getGenderOptions(t: (key: string) => string): GenderOption[] {
  return [
    {
      id: "male",
      label: t("modals.aiPortrait.genderMale"),
      sub: t("modals.aiPortrait.genderMaleSub"),
      icon: "♂",
      hint: t("modals.aiPortrait.genderMaleHint"),
    },
    {
      id: "female",
      label: t("modals.aiPortrait.genderFemale"),
      sub: t("modals.aiPortrait.genderFemaleSub"),
      icon: "♀",
      hint: t("modals.aiPortrait.genderFemaleHint"),
    },
    {
      id: "androgynous",
      label: t("modals.aiPortrait.genderAndro"),
      sub: t("modals.aiPortrait.genderAndroSub"),
      icon: "⚥",
      hint: t("modals.aiPortrait.genderAndroHint"),
    },
    {
      id: "creature",
      label: t("modals.aiPortrait.genderCreature"),
      sub: t("modals.aiPortrait.genderCreatureSub"),
      icon: "🐉",
      hint: t("modals.aiPortrait.genderCreatureHint"),
    },
  ];
}

// Generador de plantillas internas optimizadas para modelos de difusión con reforzamiento estricto de género
function buildInternalPrompt(
  style: ArtStyle,
  gender: CharacterGender,
  char: CharacterSheetData
): string {
  const name = char.name || "Adventurer";
  const rawRace = (char.race || "Humano").toLowerCase().trim();
  const rawClass = (char.char_class || "Guerrero").toLowerCase().trim();

  let raceEn = "human";
  for (const [esKey, enVal] of Object.entries(RACE_EN_MAP)) {
    if (rawRace.includes(esKey)) {
      raceEn = enVal;
      break;
    }
  }

  let classEn = "warrior adventurer";
  for (const [esKey, enVal] of Object.entries(CLASS_EN_MAP)) {
    if (rawClass.includes(esKey)) {
      classEn = enVal;
      break;
    }
  }

  // Tokens reforzados al inicio del prompt para fijar la atención del modelo de difusión
  let genderTokens = "";
  let subjectNoun = "";

  if (gender === "male") {
    genderTokens = "solo 1man, adult male hero, strong masculine facial features, handsome male, rugged";
    subjectNoun = `male ${raceEn} ${classEn}`;
  } else if (gender === "female") {
    genderTokens = "solo 1woman, adult female heroine, beautiful feminine facial features, female warrior";
    subjectNoun = `female ${raceEn} ${classEn}`;
  } else if (gender === "androgynous") {
    genderTokens = "solo androgynous adventurer, elegant neutral features, ethereal non-binary hero";
    subjectNoun = `androgynous ${raceEn} ${classEn}`;
  } else {
    genderTokens = "solo fantasy creature, non-humanoid beastly fantasy character, detailed anatomical features";
    subjectNoun = `monstrous ${raceEn} ${classEn}`;
  }

  const identity = `${genderTokens}, ${subjectNoun}, named "${name}"`;
  const rawAppearance = (char.appearance || "").trim();
  const appearanceText = rawAppearance
    ? `Character physical details, clothing and equipment: ${rawAppearance}.`
    : "";

  switch (style) {
    case "pixelart":
      return `16-bit pixel art character portrait of a ${subjectNoun}, authentic retro RPG sprite, crisp square pixels, pixelated art, detailed pixel shading, classic RPG sprite: ${identity}. ${appearanceText} Clean pixel outlines, sharp pixel details, vibrant 16-bit color palette, solid dark background, centered portrait icon.`;
    case "fantasy":
      return `Masterpiece digital fantasy illustration of a ${subjectNoun}, official D&D 5e character portrait art: ${identity}. ${appearanceText} Dramatic cinematic lighting, rich textures, sharp focus, highly detailed face and armor, epic fantasy atmosphere, ArtStation trending.`;
    case "oil":
      return `Classical Renaissance oil painting on canvas of a ${subjectNoun}, masterwork fantasy portrait: ${identity}. ${appearanceText} Dramatic chiaroscuro lighting, rich impasto brushstrokes, Rembrandt style, aged canvas texture, majestic pose.`;
    case "sketch":
      return `Detailed ink and graphite sketch on antique aged parchment of a ${subjectNoun}, vintage tabletop RPG manual illustration: ${identity}. ${appearanceText} Fine crosshatching, sepia and black ink wash, hand-drawn medieval etching, high contrast lineart.`;
    case "cinematic":
      return `Cinematic hyperrealistic fantasy portrait of a ${subjectNoun}, 8k resolution, Unreal Engine 5 render: ${identity}. ${appearanceText} Volumetric studio lighting, photorealistic skin and armor textures, shallow depth of field, atmospheric depth.`;
  }
}

export const AiPortraitModal: React.FC<AiPortraitModalProps> = ({
  isOpen,
  onClose,
  character,
  onPortraitGenerated,
  initialConfigOpen = false,
}) => {
  const { t, language } = useTranslation();
  const [selectedStyle, setSelectedStyle] = useState<ArtStyle>("pixelart");
  const [selectedGender, setSelectedGender] = useState<CharacterGender>(() => detectInitialGender(character));
  const [prompt, setPrompt] = useState<string>("");
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [showAdvancedProviders, setShowAdvancedProviders] = useState<boolean>(initialConfigOpen);

  const styleOptions = getStyleOptions(language);
  const providerOptions = getProviderOptions(language);
  const genderOptions = getGenderOptions(t);

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
      setShowAdvancedProviders(true);
    }
  }, [initialConfigOpen]);

  // Sincronizar prompt con la plantilla interna cuando cambia el estilo, género o apariencia
  useEffect(() => {
    const constructed = buildInternalPrompt(selectedStyle, selectedGender, character);
    setPrompt(constructed);
  }, [selectedStyle, selectedGender, character.name, character.race, character.char_class, character.appearance]);

  const handleResetPrompt = () => {
    const constructed = buildInternalPrompt(selectedStyle, selectedGender, character);
    setPrompt(constructed);
  };

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

  const handleProviderSelect = (newProv: AiProvider) => {
    setProvider(newProv);
    localStorage.setItem("dnd_ai_img_provider", newProv);
    const meta = providerOptions.find((p) => p.id === newProv);
    if (meta && meta.defaultUrl) {
      setApiUrl(meta.defaultUrl);
      localStorage.setItem("dnd_ai_img_api_url", meta.defaultUrl);
    }
  };

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

  const activeProviderMeta = providerOptions.find((p) => p.id === provider) || providerOptions[0];

  const handleGenerate = async () => {
    const cleanKey = apiKey.trim();

    if (!cleanKey && (provider === "google" || provider === "openai" || provider === "custom")) {
      setStatusMessage(t("modals.aiPortrait.enterKeyError", { provider: activeProviderMeta.name }));
      setShowAdvancedProviders(true);
      return;
    }

    setLoading(true);
    setStatusMessage(t("modals.aiPortrait.generatingWait"));

    try {
      const res = await api.generateAiPortrait({
        prompt,
        provider,
        apiKey: cleanKey,
        apiUrl: apiUrl.trim(),
        model: provider === "pollinations" ? "flux" : (provider === "openai" ? "dall-e-3" : "imagen-3.0-generate-002"),
      });

      if (res.success && res.image_base64) {
        setPreviewImage(res.image_base64);
        setStatusMessage(t("modals.aiPortrait.generateSuccess"));
      } else {
        throw new Error(res.error || (language === "es" ? "La API no devolvió una imagen válida." : "API returned no valid image."));
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
                {t("modals.aiPortrait.title")}
              </h2>
              <p className="text-xs text-muted">
                {t("modals.aiPortrait.subtitle", { name: character.name || (language === "es" ? "tu héroe" : "your hero") })}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
            title={t("common.close")}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Cuerpo del Modal */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* 1. Selector de Estilo Artístico */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                {t("modals.aiPortrait.visualStyle")}
              </label>
              <span className="text-[11px] text-gold/80 font-medium">
                {styleOptions.find(s => s.id === selectedStyle)?.hint}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {styleOptions.map((style) => {
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

          {/* 2. Selector de Género / Sexo del Personaje */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                {t("modals.aiPortrait.genderLabel")}
              </label>
              <span className="text-[11px] text-gold/80 font-medium">
                {genderOptions.find(g => g.id === selectedGender)?.hint}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {genderOptions.map((g) => {
                const isSelected = selectedGender === g.id;
                return (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => setSelectedGender(g.id)}
                    className={`p-2 rounded-lg border text-left flex items-center gap-2.5 transition-all ${
                      isSelected
                        ? "bg-gold/15 border-gold shadow-sm ring-1 ring-gold"
                        : "bg-surface/50 border-border-iron hover:border-gold/60 text-muted"
                    }`}
                  >
                    <span className={`text-base font-bold ${isSelected ? "text-gold" : "text-muted"}`}>{g.icon}</span>
                    <div className="flex flex-col min-w-0">
                      <span className={`text-xs font-semibold truncate ${isSelected ? "text-gold" : "text-main"}`}>
                        {g.label}
                      </span>
                      <span className="text-[10px] text-muted truncate">{g.sub}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Prompt Generado & Editor */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                  {t("modals.aiPortrait.optimizedPrompt")}
                </label>
                {character.appearance && (
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    {t("modals.aiPortrait.appearanceIntegrated")}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleResetPrompt}
                  className="text-xs text-muted hover:text-gold flex items-center gap-1 font-medium transition-colors"
                  title={t("modals.aiPortrait.resetPromptTooltip")}
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>{t("modals.aiPortrait.resetPrompt")}</span>
                </button>
                <button
                  onClick={handleCopyPrompt}
                  className="text-xs text-gold hover:text-gold-hover flex items-center gap-1 font-semibold transition-colors"
                  title={t("modals.aiPortrait.copyPrompt")}
                >
                  {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{isCopied ? t("modals.aiPortrait.promptCopied") : t("modals.aiPortrait.copyPrompt")}</span>
                </button>
              </div>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder={t("modals.aiPortrait.promptPlaceholder")}
              className="w-full bg-input text-main border border-border-iron rounded-lg p-2.5 text-xs focus:border-gold outline-none leading-relaxed transition-colors resize-none font-mono"
            />
            <p className="text-[10px] text-muted">
              {t("modals.aiPortrait.promptHint")}
            </p>
          </div>

          {/* 4. Panel de Previsualización & Pegar Imagen Externa */}
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
                    <p className="text-[11px] font-medium">{t("modals.aiPortrait.noPreview")}</p>
                    <p className="text-[10px] text-muted/70">
                      {t("modals.aiPortrait.noPreviewHint")}
                    </p>
                  </div>
                )}
                {loading && (
                  <div className="absolute inset-0 bg-black/75 flex flex-col items-center justify-center gap-2 p-2 text-center">
                    <div className="w-6 h-6 border-2 border-gold border-t-transparent rounded-full animate-spin" />
                    <span className="text-[11px] text-gold font-medium">{t("modals.aiPortrait.generatingArt")}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Alternativa: Pegar imagen externa o URL directa */}
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-main mb-1">
                  {t("modals.aiPortrait.orPasteDirect")}
                </h4>
                <p className="text-[11px] text-muted mb-2">
                  {t("modals.aiPortrait.pasteHint")}
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

          {/* 4. Opciones Avanzadas de Proveedores (Ocultas por defecto para evitar sobrecarga) */}
          <div className="pt-2 border-t border-border-iron/60">
            <button
              type="button"
              onClick={() => setShowAdvancedProviders(!showAdvancedProviders)}
              className="text-xs text-muted hover:text-gold flex items-center gap-1.5 font-medium transition-colors"
            >
              <Settings2 className="w-3.5 h-3.5" />
              <span>{t("modals.aiPortrait.advancedProviders")}</span>
              {showAdvancedProviders ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showAdvancedProviders && (
              <div className="mt-3 p-3 bg-surface/70 border border-border-iron rounded-lg space-y-3 animate-fade-in text-xs">
                <div>
                  <label className="block text-muted text-[11px] mb-1 font-medium">{t("modals.aiPortrait.selectProvider")}</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                    {providerOptions.map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => handleProviderSelect(opt.id)}
                        className={`px-2 py-1.5 text-xs rounded border text-center transition-all ${
                          provider === opt.id
                            ? "bg-gold text-canvas border-gold font-bold shadow-sm"
                            : "bg-card border-border-iron text-muted hover:text-main"
                        }`}
                      >
                        {opt.name.split(" ")[0]} {opt.id === "pollinations" ? `(${language === "es" ? "Gratis" : "Free"})` : ""}
                      </button>
                    ))}
                  </div>
                </div>

                {!activeProviderMeta.isFree ? (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-[11px] text-muted font-medium">API Key ({activeProviderMeta.name})</label>
                      {activeProviderMeta.helpLink && (
                        <a
                          href={activeProviderMeta.helpLink}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-gold hover:underline flex items-center gap-1"
                        >
                          <span>{t("modals.aiPortrait.getKey")}</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => handleKeyChange(e.target.value)}
                      placeholder={activeProviderMeta.placeholderKey}
                      className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none"
                    />
                    <p className="text-[10px] text-muted/80">{activeProviderMeta.helpText}</p>
                  </div>
                ) : (
                  <p className="text-[11px] text-emerald-400">
                    {t("modals.aiPortrait.freeProviderNotice")}
                  </p>
                )}
              </div>
            )}
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
              <span>{loading ? t("modals.aiPortrait.generatingWait") : t("modals.aiPortrait.generateButton")}</span>
            </button>
            <button
              onClick={handleCopyPrompt}
              className="px-3 py-2 rounded-lg bg-surface border border-border-iron hover:border-gold text-muted hover:text-main text-xs font-medium transition-colors flex items-center gap-1"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>{t("modals.aiPortrait.copyPrompt")}</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-2 rounded-lg border border-border-iron hover:border-gold text-xs text-muted hover:text-main font-medium transition-colors"
            >
              {t("common.cancel")}
            </button>
            <button
              onClick={handleApplyPreview}
              disabled={!previewImage && !pastedImage}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:pointer-events-none text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-sm active:scale-95"
            >
              <Check className="w-4 h-4" />
              <span>{t("modals.aiPortrait.applyToSheet")}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
