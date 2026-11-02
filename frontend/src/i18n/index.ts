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
 * Soporta texto de respaldo (defaultText) opcional o diccionario de parámetros.
 */
export function translate(
  lang: Language,
  path: string,
  defaultTextOrParams?: string | Record<string, string | number>,
  params?: Record<string, string | number>
): string {
  let defaultText: string | undefined = undefined;
  let actualParams = params;

  if (typeof defaultTextOrParams === "string") {
    defaultText = defaultTextOrParams;
  } else if (defaultTextOrParams) {
    actualParams = defaultTextOrParams;
  }

  const dict = translations[lang] || translations.es;
  let text = getNestedTranslation(dict, path);

  if (!text) {
    // Fallback a español si no existe en el idioma seleccionado
    text = getNestedTranslation(translations.es, path);
  }

  if (!text) {
    // Si no existe en el diccionario:
    // Si se pasó defaultText explícito, lo usamos.
    // Si NO se pasó defaultText, devolvemos "" (cadena vacía) para que el operador || en:
    //   t("onboarding.btnNext") || "Siguiente"
    // evalúe al texto por defecto en lugar de mostrar la clave técnica cruda en pantalla.
    text = defaultText !== undefined ? defaultText : "";
  }

  if (actualParams && text) {
    for (const [key, val] of Object.entries(actualParams)) {
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
    (
      path: string,
      defaultTextOrParams?: string | Record<string, string | number>,
      params?: Record<string, string | number>
    ): string => {
      return translate(language, path, defaultTextOrParams, params);
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
    translateSpellName: (name: string) => translateSpellName(name, language),
    translateSpellDescription: (name: string, desc: string) => translateSpellDescription(name, desc, language),
    translateWeapon: (name: string) => translateWeapon(name, language),
    translateWeaponNotes: (notes: string) => translateWeaponNotes(notes, language),
    translateWeaponType: (type: string) => translateWeaponType(type, language),
    translateBackground: (name: string) => translateBackground(name, language),
    translateAlignment: (name: string) => translateAlignment(name, language),
    translateSubclass: (name: string) => translateSubclass(name, language),
    translateSense: (sense: string) => translateSense(sense, language),
    translateFeatureName: (name: string) => translateFeatureName(name, language),
    translateFeatureSource: (src: string) => translateFeatureSource(src, language),
    translateFeatureDescription: (name: string, desc: string) => translateFeatureDescription(name, desc, language),
    translateFeatureRecharge: (recharge: string) => translateFeatureRecharge(recharge, language),
  };
}
