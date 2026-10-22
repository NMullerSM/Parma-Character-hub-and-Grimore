import { useCallback } from "react";
import { es, type Translations } from "./es";
import { en } from "./en";
import { useCharacter } from "../context/CharacterContext";
import {
  translateSpellName,
  translateSpellDescription,
  translateWeapon,
  translateWeaponNotes,
  translateWeaponType,
  translateBackground,
  translateAlignment,
  translateSubclass,
  translateSense,
  translateFeatureName,
  translateFeatureSource,
  translateFeatureDescription,
  translateFeatureRecharge,
} from "./dndTranslations";

export * from "./dndTranslations";

export type Language = "es" | "en";

export const translations: Record<Language, Translations> = {
  es,
  en,
};

/**
 * Acceso anidado a claves tipo "common.save" o "sheet.hpMax".
 */
export function getNestedTranslation(obj: any, path: string): string | undefined {
  const parts = path.split(".");
  let current = obj;
  for (const part of parts) {
    if (current === undefined || current === null) return undefined;
    current = current[part];
  }
  return typeof current === "string" ? current : undefined;
}

/**
 * Traduce una clave reemplazando placeholders tipo {name}.
 */
export function translate(
  lang: Language,
  path: string,
  params?: Record<string, string | number>
): string {
  const dict = translations[lang] || translations.es;
  let text = getNestedTranslation(dict, path);

  if (!text) {
    // Fallback a español si no existe en el idioma seleccionado
    text = getNestedTranslation(translations.es, path) || path;
  }

  if (params) {
    for (const [key, val] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${key}\\}`, "g"), String(val));
    }
  }

  return text;
}

/**
 * Hook de React para traducciones en tiempo real conectadas al estado global.
 */
export function useTranslation() {
  const { language, setLanguage } = useCharacter();

  const t = useCallback(
    (path: string, params?: Record<string, string | number>): string => {
      return translate(language, path, params);
    },
    [language]
  );

  return {
    t,
    language,
    setLanguage,
    dict: translations[language],
    // D&D Helpers
    translateAbility: (key: string) => translateAbility(key, language),
    translateAbilityShort: (key: string) => translateAbilityShort(key, language),
    translateSkill: (name: string) => translateSkill(name, language),
    translateCondition: (name: string) => translateCondition(name, language),
    translateDamageType: (name: string) => translateDamageType(name, language),
    translateClass: (name: string) => translateClass(name, language),
    translateRace: (name: string) => translateRace(name, language),
    translateSchool: (name: string) => translateSchool(name, language),
    translateCategory: (catId: string) => translateCategory(catId, language),
    // Dynamic Content Helpers
    translateSpellName: (name: string, lang?: Language) => translateSpellName(name, lang || language),
    translateSpellDescription: (spell: any, lang?: Language) => translateSpellDescription(spell, lang || language),
    translateWeapon: (name: string, lang?: Language) => translateWeapon(name, lang || language),
    translateWeaponNotes: (notes: string, lang?: Language) => translateWeaponNotes(notes, lang || language),
    translateWeaponType: (type: string, lang?: Language) => translateWeaponType(type, lang || language),
    translateBackground: (name: string, lang?: Language) => translateBackground(name, lang || language),
    translateAlignment: (align: string, lang?: Language) => translateAlignment(align, lang || language),
    translateSubclass: (sub: string, lang?: Language) => translateSubclass(sub, lang || language),
    translateSense: (sense: string, lang?: Language) => translateSense(sense, lang || language),
    translateFeatureName: (name: string, lang?: Language) => translateFeatureName(name, lang || language),
    translateFeatureSource: (source?: string, lang?: Language) => translateFeatureSource(source, lang || language),
    translateFeatureDescription: (desc?: string, lang?: Language) => translateFeatureDescription(desc, lang || language),
    translateFeatureRecharge: (recharge?: string, lang?: Language) => translateFeatureRecharge(recharge, lang || language),
  };
}

/**
 * Traduce el nombre completo de una característica (Fuerza / Strength).
 */
export function translateAbility(key: string, lang: Language): string {
  const normalized = (key || "").toUpperCase().trim();
  const dict = translations[lang]?.dndTerms?.abilities;
  if (!dict) return key;

  return dict[normalized as keyof typeof dict] || key;
}

/**
 * Traduce la abreviatura de una característica (FUE -> STR en EN, STR -> FUE en ES).
 */
export function translateAbilityShort(key: string, lang: Language): string {
  const normalized = (key || "").toUpperCase().trim();
  if (lang === "en") {
    switch (normalized) {
      case "FUE":
        return "STR";
      case "DES":
        return "DEX";
      case "CON":
        return "CON";
      case "INT":
        return "INT";
      case "SAB":
        return "WIS";
      case "CAR":
        return "CHA";
      default:
        return normalized;
    }
  } else {
    switch (normalized) {
      case "STR":
        return "FUE";
      case "DEX":
        return "DES";
      case "WIS":
        return "SAB";
      case "CHA":
        return "CAR";
      default:
        return normalized;
    }
  }
}

/**
 * Traduce una habilidad de D&D (Atletismo -> Athletics).
 */
export function translateSkill(name: string, lang: Language): string {
  if (!name) return "";
  const dict = translations[lang]?.dndTerms?.skills as Record<string, string>;
  if (!dict) return name;

  // Si se busca en inglés, busca por nombre o por su mapeo inverso
  if (lang === "en") {
    return dict[name] || name;
  } else {
    // Si estamos en español y nos pasaron el nombre en inglés, buscamos en el dict en inglés y devolvemos la clave
    const enDict = translations.en.dndTerms.skills as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict)) {
      if (enVal.toLowerCase() === name.toLowerCase()) {
        return esKey;
      }
    }
    return dict[name] || name;
  }
}

/**
 * Traduce un estado o condición (Apresado -> Grappled).
 */
export function translateCondition(name: string, lang: Language): string {
  if (!name) return "";
  const dict = translations[lang]?.dndTerms?.conditions as Record<string, string>;
  if (!dict) return name;

  if (lang === "en") {
    return dict[name] || name;
  } else {
    const enDict = translations.en.dndTerms.conditions as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict)) {
      if (enVal.toLowerCase() === name.toLowerCase()) {
        return esKey;
      }
    }
    return dict[name] || name;
  }
}

/**
 * Traduce un tipo de daño (fuego -> fire).
 */
export function translateDamageType(type: string, lang: Language): string {
  if (!type) return "";
  const normalized = type.toLowerCase().trim();
  const dict = translations[lang]?.dndTerms?.damageTypes as Record<string, string>;
  if (!dict) return type;

  if (lang === "en") {
    return dict[normalized] || type;
  } else {
    const enDict = translations.en.dndTerms.damageTypes as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict)) {
      if (enVal.toLowerCase() === normalized) {
        return esKey;
      }
    }
    return dict[normalized] || type;
  }
}

/**
 * Traduce la clase de un personaje (Guerrero -> Fighter).
 */
export function translateClass(name: string, lang: Language): string {
  if (!name) return "";
  const dict = translations[lang]?.dndTerms?.classes as Record<string, string>;
  if (!dict) return name;

  if (lang === "en") {
    return dict[name] || name;
  } else {
    const enDict = translations.en.dndTerms.classes as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict)) {
      if (enVal.toLowerCase() === name.toLowerCase()) {
        return esKey;
      }
    }
    return dict[name] || name;
  }
}

/**
 * Traduce la especie de un personaje (Humano -> Human).
 */
export function translateRace(name: string, lang: Language): string {
  if (!name) return "";
  const dict = translations[lang]?.dndTerms?.races as Record<string, string>;
  if (!dict) return name;

  if (lang === "en") {
    return dict[name] || name;
  } else {
    const enDict = translations.en.dndTerms.races as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict)) {
      if (enVal.toLowerCase() === name.toLowerCase()) {
        return esKey;
      }
    }
    return dict[name] || name;
  }
}

/**
 * Traduce una escuela de magia (Evocación -> Evocation).
 */
export function translateSchool(name: string, lang: Language): string {
  if (!name) return "";
  const norm = name.trim();
  const lower = norm.toLowerCase();

  if (lang === "en") {
    if (lower === "ilusionismo" || lower === "ilusión" || lower === "ilusion" || lower === "illusion" || lower === "illusionism") {
      return "Illusion";
    }
    const dict = translations.en?.dndTerms?.schools as Record<string, string>;
    for (const [key, val] of Object.entries(dict || {})) {
      if (key.toLowerCase() === lower || val.toLowerCase() === lower) {
        return val;
      }
    }
    return norm;
  } else {
    if (lower === "illusion" || lower === "illusionism" || lower === "ilusionismo" || lower === "ilusion" || lower === "ilusión") {
      return "Ilusión";
    }
    const enDict = translations.en?.dndTerms?.schools as Record<string, string>;
    for (const [esKey, enVal] of Object.entries(enDict || {})) {
      if (enVal.toLowerCase() === lower || esKey.toLowerCase() === lower) {
        return esKey;
      }
    }
    return norm;
  }
}

/**
 * Traduce las categorías del compendio oficial.
 */
export function translateCategory(catId: string, lang: Language): string {
  const dict = translations[lang]?.compendium;
  switch (catId) {
    case "clases":
      return dict.catClasses;
    case "especies_y_linajes":
      return dict.catSpecies;
    case "conjuros":
      return dict.catSpells;
    case "trasfondos":
      return dict.catBackgrounds;
    case "dotes":
      return dict.catFeats;
    case "equipo_y_armamento":
      return dict.catEquipment;
    case "reglas_y_mecanicas":
      return dict.catRules;
    default:
      return catId;
  }
}
