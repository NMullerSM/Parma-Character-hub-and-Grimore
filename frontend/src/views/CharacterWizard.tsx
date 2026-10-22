import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type {
  BuilderCatalog,
  CharacterSheetData,
  PointBuyValidationResult,
  SpellItemData,
  WeaponActionData,
} from "../api/types";
import {
  X,
  Shield,
  Zap,
  Dice5,
  Sparkles,
  BookOpen,
  Swords,
  ChevronRight,
  ChevronLeft,
  RotateCcw,
  Check,
  Info,
} from "lucide-react";

const DEFAULT_CLASSES = [
  "Bardo", "Bárbaro", "Clérigo", "Druida", "Explorador", "Guerrero",
  "Hechicero", "Mago", "Monje", "Paladín", "Pícaro", "Brujo"
];

const DEFAULT_SPECIES = [
  "Humano", "Elfo", "Enano", "Mediano", "Aasimar", "Dracónido",
  "Gnomo", "Goliat", "Orco", "Tiefling"
];

type CreationMode = "hub" | "standard" | "quick" | "random";

// Componente de Tarjeta de Conjuro Estilo D&D 5e
const SpellCard: React.FC<{
  spell: SpellItemData;
  selectable?: boolean;
  selected?: boolean;
  onToggle?: () => void;
}> = ({ spell, selectable, selected, onToggle }) => {
  const { language } = useCharacter();
  const { translateSchool, translateSpellName } = useTranslation();
  const isCantrip = spell.level === 0;
  const spellDisplayName = (language === "en" && spell.name_en && spell.name_en !== spell.name) ? spell.name_en : translateSpellName(spell.name);
  return (
    <div
      onClick={selectable && onToggle ? onToggle : undefined}
      className={`relative p-3.5 rounded-lg border transition-all text-left flex flex-col justify-between ${
        selectable ? "cursor-pointer" : ""
      } ${
        selected
          ? "border-gold bg-gold/10 shadow-sm"
          : "border-border-iron bg-surface hover:border-gold/50"
      }`}
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                isCantrip ? "bg-cyan-400" : "bg-purple-400"
              }`}
            />
            <h4 className="font-display font-bold text-sm text-main truncate">{spellDisplayName}</h4>
          </div>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-stat font-semibold tracking-wider uppercase shrink-0 ${
              isCantrip
                ? "bg-cyan-950/60 border border-cyan-800 text-cyan-300"
                : "bg-purple-950/60 border border-purple-800 text-purple-300"
            }`}
          >
            {isCantrip ? (language === "en" ? "Cantrip" : "Truco") : (language === "en" ? `Level ${spell.level}` : `Nivel ${spell.level}`)}
          </span>
        </div>

        <div className="text-[11px] text-muted space-y-1 mb-2">
          <div className="flex flex-wrap gap-x-3 gap-y-0.5">
            <span>
              <strong className="text-zinc-300">{language === "en" ? "School:" : "Escuela:"}</strong> {translateSchool(spell.school)}
            </span>
            <span>
              <strong className="text-zinc-300">{language === "en" ? "Time:" : "Tiempo:"}</strong> {spell.cast_time}
            </span>
            <span>
              <strong className="text-zinc-300">{language === "en" ? "Range:" : "Alcance:"}</strong> {spell.range_area}
            </span>
            <span>
              <strong className="text-zinc-300">{language === "en" ? "Comp:" : "Comp:"}</strong> {spell.components}
            </span>
          </div>
        </div>

        {spell.notes && (
          <p className="text-xs text-zinc-300/90 leading-relaxed line-clamp-3 hover:line-clamp-none transition-all">
            {spell.notes}
          </p>
        )}
      </div>

      {selectable && (
        <div className="mt-2.5 pt-2 border-t border-border-iron/40 flex items-center justify-between text-[11px]">
          <span className="text-muted">
            {selected
              ? (language === "en" ? "Prepared" : "Preparado")
              : (language === "en" ? "Click to prepare" : "Click para preparar")}
          </span>
          <span
            className={`w-4 h-4 rounded flex items-center justify-center border ${
              selected
                ? "bg-gold border-gold text-canvas"
                : "border-border-iron bg-card text-transparent"
            }`}
          >
            <Check className="w-3 h-3 stroke-[3]" />
          </span>
        </div>
      )}
    </div>
  );
};

// Componente de Tarjeta de Rasgo
const FeatureCard: React.FC<{
  title: string;
  source: string;
  description: string;
}> = ({ title, source, description }) => {
  return (
    <div className="p-3 rounded-lg border border-border-iron bg-surface text-left space-y-1">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-display font-semibold text-xs text-gold truncate">{title}</h4>
        <span className="px-1.5 py-0.5 rounded text-[9px] font-stat bg-card border border-border-iron text-muted shrink-0">
          {source}
        </span>
      </div>
      <p className="text-xs text-muted leading-relaxed line-clamp-3 hover:line-clamp-none transition-all">
        {description}
      </p>
    </div>
  );
};

export const CharacterWizard: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const { reloadCharacters, showToast, dndEdition, language } = useCharacter();
  const {
    t,
    translateClass,
    translateRace,
    translateAbility,
    translateAbilityShort,
    translateSkill,
    translateDamageType,
    translateWeapon,
    translateBackground,
    translateAlignment,
    translateSubclass,
  } = useTranslation();

  const [mode, setMode] = useState<CreationMode>("hub");
  const [step, setStep] = useState<number>(1);
  const [catalog, setCatalog] = useState<BuilderCatalog | null>(null);

  // Estado del nuevo personaje (Paso a Paso)
  const [name, setName] = useState<string>("");
  const [level, setLevel] = useState<number>(1);
  const [race, setRace] = useState<string>("Humano");
  const [subrace, setSubrace] = useState<string>("Estándar");
  const [charClass, setCharClass] = useState<string>("Guerrero");
  const [subclass, setSubclass] = useState<string>("");
  const [background, setBackground] = useState<string>("Soldado");
  const [alignment, setAlignment] = useState<string>("Neutral Bueno");
  const [selectedSkills, setSelectedSkills] = useState<string[]>(["Atletismo", "Percepción"]);
  const [availableSpells, setAvailableSpells] = useState<SpellItemData[]>([]);
  const [selectedSpells, setSelectedSpells] = useState<string[]>([]);

  // Atributos y Point Buy
  const [scores, setScores] = useState<Record<string, number>>({
    FUE: 15,
    DES: 14,
    CON: 13,
    INT: 12,
    SAB: 10,
    CAR: 8,
  });

  const [pointBuyValidation, setPointBuyValidation] = useState<PointBuyValidationResult>({
    valid: true,
    points_spent: 27,
    points_remaining: 0,
    can_increment: { FUE: false, DES: false, CON: false, INT: false, SAB: false, CAR: false },
    can_decrement: { FUE: true, DES: true, CON: true, INT: true, SAB: true, CAR: false },
    standard_array: [15, 14, 13, 12, 10, 8],
  });

  // Previsualización en modos Rápido / Aleatorio
  const [previewChar, setPreviewChar] = useState<CharacterSheetData | null>(null);
  const [randomRollsLog, setRandomRollsLog] = useState<Record<string, any>>({});
  const [randomBiography, setRandomBiography] = useState<{
    trait: string;
    ideal: string;
    bond: string;
    flaw: string;
  } | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Filtros del generador aleatorio
  const [randomLevel, setRandomLevel] = useState<number>(1);
  const [randomClassFilter, setRandomClassFilter] = useState<string>("any");
  const [randomSpeciesFilter, setRandomSpeciesFilter] = useState<string>("any");

  // Cargar catálogo según edición activa (5.5e vs 5e)
  useEffect(() => {
    let mounted = true;
    async function loadCatalog() {
      try {
        const cat = await api.getBuilderCatalog(dndEdition || "5.5e");
        if (!mounted) return;
        setCatalog(cat);
        if (cat.species.length > 0) {
          const sp = cat.species.find((s) => s.name === race) || cat.species[0];
          setRace(sp.name);
          setSubrace(sp.subraces[0] || "");
        }
        if (cat.classes.length > 0) {
          const cl = cat.classes.find((c) => c.name === charClass) || cat.classes[0];
          setCharClass(cl.name);
          setSubclass(cl.subclasses[0] || "");
          setSelectedSkills(cl.skill_options.slice(0, cl.skill_choices_count));
        }
      } catch (e) {
        console.error("Error loading builder catalog:", e);
      }
    }
    loadCatalog();
    return () => {
      mounted = false;
    };
  }, [dndEdition]);

  // Cargar conjuros disponibles cuando cambia la clase o se llega al paso de conjuros
  useEffect(() => {
    let mounted = true;
    async function loadSpells() {
      try {
        const spells = await api.getClassSpells(charClass, 1);
        if (!mounted) return;
        setAvailableSpells(spells);
        // Preseleccionar los primeros como preparados
        if (selectedSpells.length === 0 && spells.length > 0) {
          setSelectedSpells(spells.slice(0, 4).map((s) => s.name));
        }
      } catch (e) {
        console.error("Error loading class spells:", e);
      }
    }
    loadSpells();
    return () => {
      mounted = false;
    };
  }, [charClass]);

  // Validar Point Buy inicial
  useEffect(() => {
    api.validatePointBuy(scores).then(setPointBuyValidation).catch(console.error);
  }, []);

  // Cerrar con Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onComplete();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onComplete]);

  const currentSpeciesObj = catalog?.species.find((r) => r.name === race);
  const currentClassObj = catalog?.classes.find((c) => c.name === charClass);
  const currentBgObj = catalog?.backgrounds.find((b) => b.name === background);
  const unlockLevel = currentClassObj?.subclass_unlock_level ?? 3;
  const isSubclassUnlocked = level >= unlockLevel;

  const handleScoreChange = async (attr: string, delta: number) => {
    const currentVal = scores[attr] || 8;
    const nextVal = Math.max(8, Math.min(15, currentVal + delta));
    if (nextVal === currentVal) return;

    const nextScores = { ...scores, [attr]: nextVal };
    try {
      const res = await api.validatePointBuy(nextScores);
      if (delta > 0 && res.points_remaining < 0) {
        return; // No permitir exceder presupuesto de 27 puntos
      }
      setScores(nextScores);
      setPointBuyValidation(res);
    } catch (e) {
      console.error("Error validating point buy:", e);
    }
  };

  const applyStandardArray = async () => {
    const primary = currentClassObj?.primary_ability || "FUE";
    const order = [primary, "CON", "DES", "SAB", "INT", "CAR"].filter(
      (v, i, a) => a.indexOf(v) === i
    );
    const fullOrder = [...order, ...["FUE", "DES", "CON", "INT", "SAB", "CAR"].filter((k) => !order.includes(k))];
    const std = [15, 14, 13, 12, 10, 8];
    const nextScores: Record<string, number> = {};
    fullOrder.forEach((ab, idx) => {
      nextScores[ab] = std[idx];
    });
    setScores(nextScores);
    const res = await api.validatePointBuy(nextScores);
    setPointBuyValidation(res);
  };

  const toggleClassSkill = (sk: string) => {
    const maxSkills = currentClassObj?.skill_choices_count || 2;
    setSelectedSkills((prev) => {
      if (prev.includes(sk)) {
        return prev.filter((s) => s !== sk);
      }
      if (prev.length >= maxSkills) {
        return [...prev.slice(1), sk];
      }
      return [...prev, sk];
    });
  };

  const toggleSpellSelection = (spellName: string) => {
    setSelectedSpells((prev) => {
      if (prev.includes(spellName)) {
        return prev.filter((s) => s !== spellName);
      }
      return [...prev, spellName];
    });
  };

  const handleGenerateQuickPreview = async (targetClass: string, targetSpecies: string) => {
    setIsGenerating(true);
    try {
      const char = await api.generateQuickBuildPreview(targetClass, targetSpecies);
      if (name.trim()) char.name = name.trim();
      setPreviewChar(char);
    } catch (e) {
      showToast("Error generando previsualización rápida", "warn");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateRandomPreview = async () => {
    setIsGenerating(true);
    try {
      const targetClass = randomClassFilter === "any" ? undefined : randomClassFilter;
      const targetSpecies = randomSpeciesFilter === "any" ? undefined : randomSpeciesFilter;
      const res = await api.generateRandomCharacterPreview(targetClass, targetSpecies, randomLevel);
      if (name.trim()) res.character.name = name.trim();
      setPreviewChar(res.character);
      setRandomRollsLog(res.raw_rolls || {});
      const bio = (res as any).biography;
      if (bio) {
        setRandomBiography(bio);
      }
    } catch (e) {
      showToast("Error generando personaje aleatorio", "warn");
    } finally {
      setIsGenerating(false);
    }
  };

  // Disparar carga de preview al cambiar de modo
  useEffect(() => {
    if (mode === "quick") {
      handleGenerateQuickPreview(charClass, race);
    } else if (mode === "random" && !previewChar) {
      handleGenerateRandomPreview();
    }
  }, [mode]);

  const handleCreate = async () => {
    try {
      let charToSave: CharacterSheetData;

      if (mode === "standard") {
        if (!name.trim()) {
          showToast("Ingresa un nombre para el personaje", "warn");
          setStep(1);
          return;
        }
        charToSave = await api.buildCharacterFromWizard({
          name: name.trim(),
          level,
          race,
          subrace,
          char_class: charClass,
          subclass: isSubclassUnlocked ? subclass : "",
          background,
          alignment,
          scores,
          selected_skills: selectedSkills,
          spells: selectedSpells,
          edition: dndEdition,
        });
      } else {
        if (!previewChar) return;
        charToSave = {
          ...previewChar,
          name: name.trim() || previewChar.name,
        };
      }

      const res = await api.saveCharacter(charToSave);
      if (res.success) {
        showToast(`¡${charToSave.name} ha sido forjado exitosamente!`, "success");
        await reloadCharacters();
        onComplete();
      }
    } catch (e) {
      showToast("Error al forjar personaje", "warn");
    }
  };

  const calcModStr = (val: number) => {
    const m = Math.floor((val - 10) / 2);
    return m >= 0 ? `+${m}` : `${m}`;
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      {/* 1. Cabecera con Salida Clara (Hick's Law) */}
      <div className="border-b border-border-iron pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="font-display font-bold text-2xl md:text-3xl text-gold flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-gold" />
              Forja de Héroes
            </h1>
            <span className="px-2 py-0.5 rounded bg-surface border border-gold/40 text-[11px] font-stat font-semibold text-gold">
              D&D {dndEdition}
            </span>
          </div>
          <p className="text-xs text-muted mt-1">
            Motor de creación oficial con cálculo de reglas, competencias, conjuros y equipo.
          </p>
        </div>

        <button
          onClick={onComplete}
          className="self-start sm:self-auto px-3 py-1.5 rounded border border-border-iron text-xs font-semibold text-muted hover:text-main hover:bg-card flex items-center gap-1.5 transition-colors"
          title="Cancelar y volver (Esc)"
        >
          <X className="w-4 h-4" />
          <span>Cancelar</span>
        </button>
      </div>

      {/* 2. Selector de los 3 Modos (Estilo D&D Beyond) */}
      {mode === "hub" ? (
        <div className="space-y-4">
          <div className="text-center max-w-xl mx-auto mb-6">
            <h2 className="font-display font-bold text-xl text-main mb-1">
              ¿Cómo deseas forjar a tu aventurero?
            </h2>
            <p className="text-xs text-muted">
              Elige entre la personalización detallada paso a paso, una plantilla optimizada en 60 segundos,
              o deja que las tiradas de dados decidan tu destino.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Tarjeta Modo 1: Paso a Paso */}
            <div
              onClick={() => {
                setMode("standard");
                setStep(1);
              }}
              className="group cursor-pointer p-6 rounded-xl border border-border-iron bg-card hover:border-gold hover:shadow-lg hover:shadow-gold/5 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-lg bg-surface border border-gold/30 flex items-center justify-center text-gold group-hover:bg-gold group-hover:text-canvas transition-colors">
                  <Shield className="w-6 h-6" />
                </div>
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-bold text-lg text-gold group-hover:text-gold-hover">
                    {t("forge.modeStepTitle")}
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-stat bg-surface border border-border-iron text-muted">
                    {t("forge.modeStepTag")}
                  </span>
                </div>
                <p className="text-xs text-muted leading-relaxed">
                  {t("forge.modeStepDesc")}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-border-iron/60 flex items-center justify-between text-xs font-semibold text-gold">
                <span>{t("forge.modeStepButton")}</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Tarjeta Modo 2: Creación Rápida */}
            <div
              onClick={() => {
                setMode("quick");
                handleGenerateQuickPreview(charClass, race);
              }}
              className="group cursor-pointer p-6 rounded-xl border border-border-iron bg-card hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/5 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-lg bg-surface border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-500 group-hover:text-canvas transition-colors">
                  <Zap className="w-6 h-6" />
                </div>
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-bold text-lg text-cyan-400 group-hover:text-cyan-300">
                    {t("forge.modeQuickTitle")}
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-stat bg-cyan-950/40 border border-cyan-800 text-cyan-300">
                    {t("forge.modeQuickTag")}
                  </span>
                </div>
                <p className="text-xs text-muted leading-relaxed">
                  {t("forge.modeQuickDesc")}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-border-iron/60 flex items-center justify-between text-xs font-semibold text-cyan-400">
                <span>{t("forge.modeQuickButton")}</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Tarjeta Modo 3: Aleatorio 4d6 */}
            <div
              onClick={() => {
                setMode("random");
                handleGenerateRandomPreview();
              }}
              className="group cursor-pointer p-6 rounded-xl border border-border-iron bg-card hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/5 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-lg bg-surface border border-purple-500/30 flex items-center justify-center text-purple-400 group-hover:bg-purple-500 group-hover:text-canvas transition-colors">
                  <Dice5 className="w-6 h-6" />
                </div>
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-bold text-lg text-purple-400 group-hover:text-purple-300">
                    {t("forge.modeRandomTitle")}
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-stat bg-purple-950/40 border border-purple-800 text-purple-300">
                    {t("forge.modeRandomTag")}
                  </span>
                </div>
                <p className="text-xs text-muted leading-relaxed">
                  {t("forge.modeRandomDesc")}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-border-iron/60 flex items-center justify-between text-xs font-semibold text-purple-400">
                <span>{t("forge.modeRandomButton")}</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Barra de Pestañas Activa para cambiar de modo */
        <div className="flex items-center justify-between gap-2 bg-surface p-1.5 rounded-lg border border-border-iron">
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setMode("hub")}
              className="px-2.5 py-1.5 rounded text-xs font-semibold text-muted hover:text-main hover:bg-card flex items-center gap-1 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>{t("forge.backToMenu")}</span>
            </button>
            <div className="h-4 w-px bg-border-iron" />
            <button
              onClick={() => setMode("standard")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                mode === "standard"
                  ? "bg-card border border-gold text-gold shadow-xs"
                  : "text-muted hover:text-main"
              }`}
            >
              1. {t("forge.modeStepTitle")}
            </button>
            <button
              onClick={() => setMode("quick")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                mode === "quick"
                  ? "bg-card border border-cyan-500 text-cyan-400 shadow-xs"
                  : "text-muted hover:text-main"
              }`}
            >
              2. {t("forge.modeQuickTitle")}
            </button>
            <button
              onClick={() => setMode("random")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                mode === "random"
                  ? "bg-card border border-purple-500 text-purple-400 shadow-xs"
                  : "text-muted hover:text-main"
              }`}
            >
              3. {t("forge.modeRandomTitle")}
            </button>
          </div>

          <span className="text-[11px] text-muted hidden md:inline-block pr-2">
            {t("forge.activeMode")} <strong className="text-main uppercase">{mode}</strong>
          </span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODO 1: PASO A PASO ESTÁNDAR                                              */}
      {/* ========================================================================= */}
      {mode === "standard" && (
        <div className="space-y-5">
          {/* Stepper Progresivo de 5 Pasos */}
          <div className="flex items-center justify-between max-w-2xl bg-surface/50 p-2 rounded-lg border border-border-iron">
            {[
              { num: 1, label: t("forge.step1") },
              { num: 2, label: t("forge.step2") },
              { num: 3, label: t("forge.step3") },
              { num: 4, label: t("forge.step4") },
              { num: 5, label: t("forge.step5") },
            ].map((s) => (
              <button
                key={s.num}
                onClick={() => setStep(s.num)}
                className="flex items-center gap-2 group px-2 py-1 rounded hover:bg-card transition-colors"
              >
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center font-stat font-bold text-xs transition-all ${
                    step === s.num
                      ? "bg-gold text-canvas shadow-[0_0_8px_rgba(201,164,92,0.5)]"
                      : step > s.num
                      ? "bg-surface border border-gold text-gold"
                      : "bg-surface border border-border-iron text-muted"
                  }`}
                >
                  {s.num}
                </span>
                <span
                  className={`text-xs hidden sm:inline ${
                    step === s.num ? "font-semibold text-main" : "text-muted group-hover:text-main"
                  }`}
                >
                  {s.label}
                </span>
              </button>
            ))}
          </div>

          <div className="bg-card border border-border-iron rounded-xl p-6 min-h-[400px]">
            {/* PASO 1: Concepto, Nivel y Trasfondo */}
            {step === 1 && (
              <div className="space-y-5 max-w-2xl">
                <div>
                  <h2 className="font-display font-semibold text-lg text-gold">
                    {t("forge.step1Title")}
                  </h2>
                  <p className="text-xs text-muted mt-0.5">
                    {t("forge.step1Desc")}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                    {t("forge.charName")}
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t("forge.charNamePlaceholder")}
                    className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-gold outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                      {t("forge.charLevel")}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={level}
                      onChange={(e) =>
                        setLevel(Math.max(1, Math.min(20, parseInt(e.target.value, 10) || 1)))
                      }
                      className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm font-stat font-bold focus:border-gold outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                      {t("forge.charAlignment")}
                    </label>
                    <select
                      value={alignment}
                      onChange={(e) => setAlignment(e.target.value)}
                      className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-gold outline-none"
                    >
                      {[
                        "Legal Bueno",
                        "Neutral Bueno",
                        "Caótico Bueno",
                        "Legal Neutral",
                        "Neutral Auténtico",
                        "Caótico Neutral",
                        "Legal Malvado",
                        "Neutral Malvado",
                        "Caótico Malvado",
                      ].map((a) => (
                        <option key={a} value={a}>
                          {translateAlignment(a)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
                    {t("forge.charBackground")}
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {(catalog?.backgrounds || []).map((bg) => (
                      <button
                        key={bg.name}
                        onClick={() => setBackground(bg.name)}
                        className={`p-3 rounded-lg border text-left transition-all ${
                          background === bg.name
                            ? "border-gold bg-surface text-gold font-semibold shadow-xs"
                            : "border-border-iron bg-surface/40 text-muted hover:text-main"
                        }`}
                      >
                        <div className="text-xs font-bold">{translateBackground(bg.name)}</div>
                        <div className="text-[10px] text-muted truncate mt-0.5">
                          {bg.skills.map((s) => translateSkill(s)).join(", ")}
                        </div>
                      </button>
                    ))}
                  </div>
                  {currentBgObj && (
                    <div className="mt-3 p-3 rounded-lg bg-surface/80 border border-border-iron text-xs space-y-1">
                      <div className="flex items-center gap-1.5 text-gold font-semibold">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>{language === "en" ? "Origin Feat:" : "Dote de Origen:"} {currentBgObj.feature_name}</span>
                      </div>
                      <p className="text-muted leading-relaxed">{currentBgObj.feature_desc}</p>
                      <div className="text-[11px] text-zinc-400">
                        {language === "en" ? "Granted Proficiencies:" : "Competencias concedidas:"}{" "}
                        <span className="text-main font-semibold">
                          {currentBgObj.skills.map((s) => translateSkill(s)).join(", ")}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* PASO 2: Especie y Linaje */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <h2 className="font-display font-semibold text-lg text-gold">
                    {t("forge.step2Title")}
                  </h2>
                  <p className="text-xs text-muted mt-0.5">
                    {t("forge.step2Desc")}
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
                  {(catalog?.species || []).map((r) => (
                    <button
                      key={r.name}
                      onClick={() => {
                        setRace(r.name);
                        setSubrace(r.subraces[0] || "");
                      }}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        race === r.name
                          ? "border-gold bg-surface font-semibold text-gold shadow-xs"
                          : "border-border-iron bg-surface/40 text-muted hover:text-main"
                      }`}
                    >
                      <div className="text-sm font-bold">{translateRace(r.name)}</div>
                      <div className="text-[11px] text-muted mt-1 font-stat">
                        {t("sheet.speed")}: {r.speed} {t("sheet.speedFeet")} ·{" "}
                        {Object.entries(r.bonuses)
                          .map(([k, v]) => `${translateAbilityShort(k)} +${v}`)
                          .join(", ")}
                      </div>
                    </button>
                  ))}
                </div>

                {/* Subraza contextual */}
                {currentSpeciesObj && currentSpeciesObj.subraces.length > 0 && (
                  <div className="pt-3 border-t border-border-iron/60 space-y-2">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gold">
                      {t("forge.selectSubrace")}: {translateRace(race)}
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {currentSpeciesObj.subraces.map((sub) => (
                        <button
                          key={sub}
                          onClick={() => setSubrace(sub)}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                            subrace === sub
                              ? "border-gold bg-gold text-canvas"
                              : "border-border-iron bg-surface text-muted hover:text-main"
                          }`}
                        >
                          {sub === "Estándar" ? (language === "en" ? "Standard" : "Estándar") : sub}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Rasgos de Especie */}
                {currentSpeciesObj && currentSpeciesObj.traits.length > 0 && (
                  <div className="p-3.5 rounded-lg bg-surface/60 border border-border-iron space-y-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-gold">
                      {t("sheet.traitsTitle")}: {translateRace(race)}
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {currentSpeciesObj.traits.map((tr) => (
                        <div key={tr.name} className="text-xs">
                          <strong className="text-main">{tr.name}:</strong>{" "}
                          <span className="text-muted">{tr.desc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* PASO 3: Clase, Subclase y Habilidades */}
            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <h2 className="font-display font-semibold text-lg text-gold">
                    {t("forge.step3Title")}
                  </h2>
                  <p className="text-xs text-muted mt-0.5">
                    {t("forge.step3Desc")}
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
                  {(catalog?.classes || []).map((c) => (
                    <button
                      key={c.name}
                      onClick={() => {
                        setCharClass(c.name);
                        setSubclass(c.subclasses[0] || "");
                        setSelectedSkills(c.skill_options.slice(0, c.skill_choices_count));
                      }}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        charClass === c.name
                          ? "border-gold bg-surface font-semibold text-gold shadow-xs"
                          : "border-border-iron bg-surface/40 text-muted hover:text-main"
                      }`}
                    >
                      <div className="text-sm font-bold flex items-center justify-between">
                        <span>{translateClass(c.name)}</span>
                        {c.is_caster && <Sparkles className="w-3.5 h-3.5 text-purple-400" />}
                      </div>
                      <div className="text-[10px] text-muted font-stat mt-1">
                        HD: d{c.hit_die} · {t("sheet.savingThrow")}: {c.saves.map(s => translateAbilityShort(s)).join("/")}
                      </div>
                    </button>
                  ))}
                </div>

                {/* Subclase con Desbloqueo Condicional */}
                <div className="pt-3 border-t border-border-iron/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted">
                      {t("forge.selectSubclass")} (Nvl {unlockLevel} - {dndEdition})
                    </label>
                    <span className="text-[11px] text-muted">
                      {isSubclassUnlocked ? t("common.active") : `${t("common.level")} ${unlockLevel}`}
                    </span>
                  </div>

                  {isSubclassUnlocked ? (
                    <div className="flex flex-wrap gap-2">
                      {currentClassObj?.subclasses.map((sub) => (
                        <button
                          key={sub}
                          onClick={() => setSubclass(sub)}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                            subclass === sub
                              ? "border-gold bg-gold text-canvas"
                              : "border-border-iron bg-surface text-muted hover:text-main"
                          }`}
                        >
                          {translateSubclass(sub)}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-surface/50 border border-border-iron text-xs text-muted flex items-center gap-2">
                      <Info className="w-4 h-4 text-gold shrink-0" />
                      <span>
                        {translateClass(charClass)}: {t("forge.selectSubclass")} ({level} / {unlockLevel}).
                      </span>
                    </div>
                  )}
                </div>

                {/* Selección de Habilidades de Clase */}
                {currentClassObj && (
                  <div className="pt-3 border-t border-border-iron/60 space-y-2">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted">
                      {t("sheet.skillsTitle")} ({currentClassObj.skill_choices_count} — {t("common.active")}:{" "}
                      <span className="text-gold font-bold">
                        {selectedSkills.length}/{currentClassObj.skill_choices_count}
                      </span>
                      )
                    </label>
                    <div className="flex flex-wrap gap-1.5">
                      {currentClassObj.skill_options.map((sk) => {
                        const isSelected = selectedSkills.includes(sk);
                        return (
                          <button
                            key={sk}
                            onClick={() => toggleClassSkill(sk)}
                            className={`px-3 py-1 rounded-md border text-xs transition-colors ${
                              isSelected
                                ? "border-gold bg-gold/20 text-gold font-bold"
                                : "border-border-iron bg-surface text-muted hover:text-main"
                            }`}
                          >
                            {translateSkill(sk)}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* PASO 4: Atributos y Point-Buy */}
            {step === 4 && (
              <div className="space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="font-display font-semibold text-lg text-gold">
                      {t("forge.step4Title")}
                    </h2>
                    <p className="text-xs text-muted">
                      {t("forge.step4Desc")}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={applyStandardArray}
                      className="px-3 py-1.5 rounded-lg border border-border-iron bg-surface text-xs text-muted hover:text-gold hover:border-gold transition-colors font-semibold"
                    >
                      {t("forge.methodStandardArray")}
                    </button>
                    <div className="text-right">
                      <span className="text-xs text-muted uppercase font-semibold">{t("forge.remainingPoints")} </span>
                      <span
                        className={`font-stat font-bold text-xl ${
                          pointBuyValidation.points_remaining === 0
                            ? "text-emerald-400"
                            : pointBuyValidation.points_remaining < 0
                            ? "text-crimson"
                            : "text-gold"
                        }`}
                      >
                        {pointBuyValidation.points_remaining}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {Object.entries(scores).map(([attr, val]) => {
                    const racialBonus = currentSpeciesObj?.bonuses[attr] || 0;
                    const finalScore = val + racialBonus;
                    const canInc =
                      pointBuyValidation.can_increment !== undefined
                        ? pointBuyValidation.can_increment[attr]
                        : val < 15 && pointBuyValidation.points_remaining > 0;
                    const canDec =
                      pointBuyValidation.can_decrement !== undefined
                        ? pointBuyValidation.can_decrement[attr]
                        : val > 8;

                    return (
                      <div
                        key={attr}
                        className="bg-surface border border-border-iron rounded-xl p-3.5 text-center flex flex-col justify-between"
                      >
                        <span className="text-xs font-stat font-bold uppercase tracking-widest text-muted" title={translateAbility(attr)}>
                          {translateAbilityShort(attr)}
                        </span>
                        <div className="my-2">
                          <div className="font-stat font-bold text-3xl text-main">{finalScore}</div>
                          <div className="text-[11px] font-stat text-gold font-semibold">
                            Mod {calcModStr(finalScore)}
                            {racialBonus > 0 ? ` (${val}+${racialBonus})` : ""}
                          </div>
                        </div>
                        <div className="flex items-center justify-center gap-2 mt-1">
                          <button
                            onClick={() => handleScoreChange(attr, -1)}
                            disabled={!canDec}
                            className="w-7 h-7 rounded border border-border-iron hover:border-gold disabled:opacity-25 disabled:pointer-events-none flex items-center justify-center text-xs font-bold transition-colors"
                          >
                            -
                          </button>
                          <button
                            onClick={() => handleScoreChange(attr, 1)}
                            disabled={!canInc}
                            className="w-7 h-7 rounded border border-border-iron hover:border-gold disabled:opacity-25 disabled:pointer-events-none flex items-center justify-center text-xs font-bold transition-colors"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* PASO 5: Tarjetas de Conjuros y Rasgos Heroicos */}
            {step === 5 && (
              <div className="space-y-6">
                <div>
                  <h2 className="font-display font-semibold text-lg text-gold flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-gold" />
                    {t("forge.step5Title")}
                  </h2>
                  <p className="text-xs text-muted mt-0.5">
                    {t("forge.step5Desc")}
                  </p>
                </div>

                {/* Conjuros de Clase si es lanzador */}
                {availableSpells.length > 0 ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-display font-semibold text-sm text-gold">
                        Grimorio de {charClass} (Haz clic para preparar)
                      </h3>
                      <span className="text-xs text-muted">
                        Preparados: <strong className="text-gold">{selectedSpells.length}</strong>
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                      {availableSpells.map((sp) => (
                        <SpellCard
                          key={sp.name}
                          spell={sp}
                          selectable
                          selected={selectedSpells.includes(sp.name)}
                          onToggle={() => toggleSpellSelection(sp.name)}
                        />
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-surface border border-border-iron text-xs text-muted flex items-center gap-2">
                    <Shield className="w-4 h-4 text-gold shrink-0" />
                    <span>
                      {charClass} no requiere preparación inicial de conjuros a nivel {level}. Sus proezas provienen de su pericia en armas y dotes marciales.
                    </span>
                  </div>
                )}

                {/* Rasgos y Dotes */}
                <div className="space-y-3 pt-3 border-t border-border-iron/60">
                  <h3 className="font-display font-semibold text-sm text-gold">
                    {language === "en" ? "Traits & Origin Feats" : "Rasgos & Dotes de Origen"}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {currentBgObj && (
                      <FeatureCard
                        title={`${language === "en" ? "Origin Feat:" : "Dote de Origen:"} ${currentBgObj.feature_name}`}
                        source={`${language === "en" ? "Background" : "Trasfondo"} (${translateBackground(background)})`}
                        description={currentBgObj.feature_desc}
                      />
                    )}
                    {currentSpeciesObj?.traits.map((t) => (
                      <FeatureCard
                        key={t.name}
                        title={t.name}
                        source={`${language === "en" ? "Species" : "Especie"} (${translateRace(race)})`}
                        description={t.desc}
                      />
                    ))}
                    <FeatureCard
                      title={language === "en" ? `${translateClass(charClass)} Proficiencies` : `Competencias de ${charClass}`}
                      source={t("common.charClass")}
                      description={language === "en"
                        ? `Saving Throws: ${currentClassObj?.saves.map(s => translateAbilityShort(s)).join(", ")}. Skills: ${selectedSkills.map(s => translateSkill(s)).join(", ")}.`
                        : `Salvaciones competentes: ${currentClassObj?.saves.map(s => translateAbilityShort(s)).join(", ")}. Habilidades: ${selectedSkills.map(s => translateSkill(s)).join(", ")}.`}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Acciones de Navegación del Wizard */}
          <div className="flex items-center justify-between pt-1">
            <button
              onClick={() => (step === 1 ? setMode("hub") : setStep((s) => Math.max(1, s - 1)))}
              className="px-4 py-2 rounded-lg border border-border-iron text-xs font-semibold text-muted hover:text-main hover:bg-card transition-colors flex items-center gap-1.5"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>{step === 1 ? t("forge.backToMenu") : t("common.back")}</span>
            </button>

            {step < 5 ? (
              <button
                onClick={() => setStep((s) => Math.min(5, s + 1))}
                className="px-5 py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas text-xs font-bold transition-all shadow-sm active:scale-95 flex items-center gap-1.5"
              >
                <span>{t("common.next")}</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleCreate}
                disabled={!pointBuyValidation.valid}
                className="px-6 py-2 rounded-lg bg-crimson hover:bg-crimson-hover disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md active:scale-95 flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>{t("forge.forgeHero")}</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODO 2: CREACIÓN RÁPIDA EN 60 SEGUNDOS                                     */}
      {/* ========================================================================= */}
      {mode === "quick" && (
        <div className="bg-card border border-border-iron rounded-xl p-6 space-y-6">
          <div>
            <h2 className="font-display font-semibold text-lg text-cyan-400 flex items-center gap-2">
              <Zap className="w-5 h-5 text-cyan-400" />
              {t("forge.modeQuickTitle")}
            </h2>
            <p className="text-xs text-muted mt-0.5">
              {t("forge.modeQuickDesc")}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                {language === "en" ? "Name (Optional)" : "Nombre (Opcional)"}
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={language === "en" ? "Automatic name if left empty" : "Nombre automático si se deja vacío"}
                className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-cyan-400 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                {t("common.charClass")}
              </label>
              <select
                value={charClass}
                onChange={(e) => {
                  setCharClass(e.target.value);
                  handleGenerateQuickPreview(e.target.value, race);
                }}
                className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-cyan-400 outline-none"
              >
                {((catalog?.classes && catalog.classes.length > 0)
                  ? catalog.classes.map((c) => c.name)
                  : DEFAULT_CLASSES
                ).map((cName) => (
                  <option key={cName} value={cName}>
                    {translateClass(cName)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                {t("common.race")}
              </label>
              <select
                value={race}
                onChange={(e) => {
                  setRace(e.target.value);
                  handleGenerateQuickPreview(charClass, e.target.value);
                }}
                className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-cyan-400 outline-none"
              >
                {((catalog?.species && catalog.species.length > 0)
                  ? catalog.species.map((s) => s.name)
                  : DEFAULT_SPECIES
                ).map((sName) => (
                  <option key={sName} value={sName}>
                    {translateRace(sName)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Previsualización Enriquecida con Tarjetas de Conjuros y Rasgos */}
          {previewChar && (
            <div className="p-5 rounded-xl bg-surface border border-border-iron space-y-4">
              <div className="flex flex-wrap items-center justify-between border-b border-border-iron pb-3 gap-2">
                <div>
                  <h3 className="font-display font-bold text-xl text-cyan-400">
                    {name.trim() || previewChar.name}
                  </h3>
                  <p className="text-xs text-muted">
                    {translateRace(previewChar.race)} · {translateClass(previewChar.char_class)} {t("common.level")} {previewChar.level} ·{" "}
                    {translateBackground(previewChar.background)} ({translateAlignment(previewChar.alignment)})
                  </p>
                </div>
                <div className="flex gap-2 font-stat text-xs">
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    PG: <strong className="text-emerald-400">{previewChar.hp_max}</strong>
                  </span>
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    CA: <strong className="text-gold">{previewChar.ac}</strong>
                  </span>
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    {t("sheet.speed")}: <strong className="text-main">{previewChar.speed}</strong>
                  </span>
                </div>
              </div>

              {/* Grid de Atributos */}
              <div className="grid grid-cols-6 gap-2 text-center">
                {Object.entries(previewChar.abilities || {}).map(([ab, data]) => (
                  <div key={ab} className="p-2 rounded bg-card border border-border-iron">
                    <div className="text-[10px] text-muted font-stat">{translateAbilityShort(ab)}</div>
                    <div className="font-stat font-bold text-base text-main">{data.base}</div>
                    <div className="text-[10px] font-stat text-cyan-400 font-semibold">
                      {data.bonus >= 0 ? `+${data.bonus}` : data.bonus}
                    </div>
                  </div>
                ))}
              </div>

              {/* Tarjetas de Conjuros si tiene */}
              {previewChar.spells && previewChar.spells.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-border-iron/60">
                  <h4 className="font-display font-semibold text-xs text-cyan-400 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>{language === "en" ? `Assigned Spell Cards (${previewChar.spells.length})` : `Tarjetas de Conjuros Asignados (${previewChar.spells.length})`}</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                    {previewChar.spells.map((sp) => (
                      <SpellCard key={sp.name} spell={sp} />
                    ))}
                  </div>
                </div>
              )}

              {/* Tarjetas de Rasgos / Armas */}
              {previewChar.weapon_actions && previewChar.weapon_actions.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-border-iron/60">
                  <h4 className="font-display font-semibold text-xs text-muted flex items-center gap-1.5">
                    <Swords className="w-3.5 h-3.5" />
                    <span>{language === "en" ? "Assigned Starting Equipment" : "Armamento Inicial Asignado"}</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {previewChar.weapon_actions.map((w: WeaponActionData) => (
                      <div
                        key={w.name}
                        className="p-2.5 rounded bg-card border border-border-iron text-xs flex justify-between"
                      >
                        <span className="font-semibold text-main">{translateWeapon(w.name)}</span>
                        <span className="font-stat text-muted">
                          {w.hit_dc} {language === "en" ? "to hit" : "a impactar"} · {w.damage_dice} {translateDamageType(w.damage_type)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setMode("hub")}
              className="px-4 py-2 rounded-lg border border-border-iron text-xs font-semibold text-muted hover:text-main"
            >
              {t("forge.backToMenu")}
            </button>
            <button
              onClick={handleCreate}
              disabled={isGenerating || !previewChar}
              className="px-6 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-canvas text-xs font-bold shadow-md flex items-center gap-2"
            >
              <Zap className="w-4 h-4" />
              <span>{t("forge.modeQuickButton")}</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODO 3: GENERADOR ALEATORIO (4d6 Drop Lowest)                             */}
      {/* ========================================================================= */}
      {mode === "random" && (
        <div className="bg-card border border-border-iron rounded-xl p-6 space-y-6">
          <div>
            <h2 className="font-display font-semibold text-lg text-purple-400 flex items-center gap-2">
              <Dice5 className="w-5 h-5 text-purple-400" />
              {t("forge.modeRandomTitle")}
            </h2>
            <p className="text-xs text-muted mt-0.5">
              {t("forge.modeRandomDesc")}
            </p>
          </div>

          {/* Filtros de Control y Botón Re-Tirar */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-surface p-3 rounded-lg border border-border-iron items-end">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1">
                {language === "en" ? "Class Filter" : "Filtro de Clase"}
              </label>
              <select
                value={randomClassFilter}
                onChange={(e) => setRandomClassFilter(e.target.value)}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs outline-none"
              >
                <option value="any">{language === "en" ? "Any Class (Random)" : "Cualquier Clase (Aleatoria)"}</option>
                {(catalog?.classes || []).map((c) => (
                  <option key={c.name} value={c.name}>
                    {translateClass(c.name)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1">
                {language === "en" ? "Species Filter" : "Filtro de Especie"}
              </label>
              <select
                value={randomSpeciesFilter}
                onChange={(e) => setRandomSpeciesFilter(e.target.value)}
                className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs outline-none"
              >
                <option value="any">{language === "en" ? "Any Species" : "Cualquier Especie"}</option>
                {(catalog?.species || []).map((s) => (
                  <option key={s.name} value={s.name}>
                    {translateRace(s.name)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1">
                {t("common.level")} (1 - 20): <strong className="text-purple-400 font-stat">{randomLevel}</strong>
              </label>
              <input
                type="range"
                min={1}
                max={20}
                value={randomLevel}
                onChange={(e) => setRandomLevel(parseInt(e.target.value, 10))}
                className="w-full accent-purple-500 cursor-pointer"
              />
            </div>

            <button
              onClick={handleGenerateRandomPreview}
              disabled={isGenerating}
              className="w-full py-2 px-3 rounded-lg border border-purple-500 bg-purple-950/40 hover:bg-purple-600 hover:text-white text-purple-300 text-xs font-bold transition-all flex items-center justify-center gap-1.5"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isGenerating ? "animate-spin" : ""}`} />
              <span>{t("forge.rerollRandom")}</span>
            </button>
          </div>

          {/* Previsualización Enriquecida */}
          {previewChar && (
            <div className="p-5 rounded-xl bg-surface border border-border-iron space-y-4">
              <div className="flex flex-wrap items-center justify-between border-b border-border-iron pb-3 gap-2">
                <div>
                  <h3 className="font-display font-bold text-xl text-purple-400">
                    {name.trim() || previewChar.name}
                  </h3>
                  <p className="text-xs text-muted">
                    {translateRace(previewChar.race)} · {translateClass(previewChar.char_class)} {t("common.level")} {previewChar.level} ·{" "}
                    {translateBackground(previewChar.background)} ({translateAlignment(previewChar.alignment)})
                  </p>
                </div>
                <div className="flex gap-2 font-stat text-xs">
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    PG: <strong className="text-emerald-400">{previewChar.hp_max}</strong>
                  </span>
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    CA: <strong className="text-gold">{previewChar.ac}</strong>
                  </span>
                  <span className="px-2.5 py-1 rounded bg-card border border-border-iron">
                    Bono Comp:{" "}
                    <strong className="text-main">+{previewChar.proficiency_bonus}</strong>
                  </span>
                </div>
              </div>

              {/* Grid de Puntuaciones con Tiradas 4d6 Reales */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center">
                {Object.entries(previewChar.abilities || {}).map(([ab, data]) => {
                  const rollVal = randomRollsLog[ab];
                  return (
                    <div key={ab} className="p-2.5 rounded-lg bg-card border border-border-iron">
                      <div className="text-[10px] text-muted font-stat font-bold">{translateAbilityShort(ab)}</div>
                      <div className="font-stat font-bold text-xl text-main my-0.5">
                        {data.base}
                      </div>
                      <div className="text-[11px] font-stat text-purple-400 font-semibold">
                        Mod {data.bonus >= 0 ? `+${data.bonus}` : data.bonus}
                      </div>
                      {rollVal && (
                        <div className="text-[9px] font-stat text-muted mt-1">
                          Base: {rollVal}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Biografía y Rasgos de Personalidad Generados */}
              {randomBiography && (
                <div className="p-3 rounded-lg bg-card border border-border-iron text-xs space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
                    Perfil Narrativo del Destino
                  </span>
                  <p className="text-muted">
                    <strong className="text-zinc-300">Rasgo:</strong> {randomBiography.trait}
                  </p>
                  <p className="text-muted">
                    <strong className="text-zinc-300">Ideal:</strong> {randomBiography.ideal}
                  </p>
                  <p className="text-muted">
                    <strong className="text-zinc-300">Vínculo:</strong> {randomBiography.bond}
                  </p>
                </div>
              )}

              {/* Tarjetas de Conjuros si es clase mágica */}
              {previewChar.spells && previewChar.spells.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-border-iron/60">
                  <h4 className="font-display font-semibold text-xs text-purple-400 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Tarjetas de Conjuros del Destino ({previewChar.spells.length})</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                    {previewChar.spells.map((sp) => (
                      <SpellCard key={sp.name} spell={sp} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setMode("hub")}
              className="px-4 py-2 rounded-lg border border-border-iron text-xs font-semibold text-muted hover:text-main"
            >
              {t("forge.backToMenu")}
            </button>
            <button
              onClick={handleCreate}
              disabled={isGenerating || !previewChar}
              className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-md flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{t("forge.forgeHero")}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
