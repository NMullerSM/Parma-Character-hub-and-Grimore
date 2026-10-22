/**
 * Utilidades de formateo para D&D 5e / 5.5e (Bilingüe ES / EN)
 * Reglas de conversión:
 * - Distancia/Alcance: 1.5 m = 1 casilla (tile) de 5 pies (TaleSpire / Tablero)
 * - Duración: 1 asalto = 6 segundos = 1 turno. 1 minuto = 10 turnos. 1 hora = 600 turnos.
 */

export type FormatLanguage = "es" | "en";

/**
 * Convierte distancias en metros o pies a casillas (tiles) tácticas.
 * Ej ES: "18 m" -> "18 m (12 casillas)" | "Toque" -> "Toque (1 casilla)"
 * Ej EN: "18 m" -> "60 ft (12 tiles)"   | "Touch" -> "Touch (1 tile)"
 */
export function formatRangeWithTiles(
  rawRange: string | undefined | null,
  lang: FormatLanguage = "es"
): string {
  if (!rawRange) {
    return lang === "en" ? "60 ft (12 tiles)" : "18 m (12 casillas)";
  }
  const str = String(rawRange).trim();

  // Si ya tiene especificada la casilla o tile, no duplicar
  if (lang === "en" && /tile/i.test(str)) return str;
  if (lang === "es" && /casilla/i.test(str)) return str;

  // Caso especial: Toque / Touch
  if (/^(?:toque|touch)$/i.test(str)) {
    return lang === "en" ? "Touch (1 tile)" : "Toque (1 casilla)";
  }

  // Detectar metros: ej "1.5 m", "18 m", "9 metros", "3m"
  const mRegex = /(\d+(?:[.,]\d+)?)\s*(?:m|metros|metro)\b/gi;
  if (mRegex.test(str)) {
    return str.replace(mRegex, (_, numStr) => {
      const meters = parseFloat(numStr.replace(",", "."));
      if (isNaN(meters) || meters <= 0) return `${numStr} m`;
      const tiles = Math.max(1, Math.round(meters / 1.5));
      if (lang === "en") {
        const feet = Math.round(tiles * 5);
        const tileLabel = tiles === 1 ? "tile" : "tiles";
        return `${feet} ft (${tiles} ${tileLabel})`;
      } else {
        const tileLabel = tiles === 1 ? "casilla" : "casillas";
        return `${meters} m (${tiles} ${tileLabel})`;
      }
    });
  }

  // Detectar pies: ej "30 ft", "60 feet", "30 pies"
  const ftRegex = /(\d+)\s*(?:ft|feet|pies|pie)\b/gi;
  if (ftRegex.test(str)) {
    return str.replace(ftRegex, (_, numStr) => {
      const feet = parseInt(numStr, 10);
      if (isNaN(feet) || feet <= 0) return `${numStr} ${lang === "en" ? "ft" : "pies"}`;
      const tiles = Math.max(1, Math.round(feet / 5));
      if (lang === "en") {
        const tileLabel = tiles === 1 ? "tile" : "tiles";
        return `${feet} ft (${tiles} ${tileLabel})`;
      } else {
        const meters = (tiles * 1.5).toFixed(1).replace(".0", "");
        const tileLabel = tiles === 1 ? "casilla" : "casillas";
        return `${meters} m (${tiles} ${tileLabel})`;
      }
    });
  }

  return str;
}

/**
 * Convierte duraciones a turnos/asaltos de combate cuando corresponda.
 * Ej ES: "Concentración, hasta 1 minuto" -> "Concentración, hasta 1 minuto (10 turnos)"
 * Ej EN: "Concentration, up to 1 minute" -> "Concentration, up to 1 minute (10 turns)"
 */
export function formatDurationWithTurns(
  rawDuration: string | undefined | null,
  lang: FormatLanguage = "es"
): string {
  if (!rawDuration) {
    return lang === "en" ? "Instantaneous" : "Instantáneo";
  }
  let str = String(rawDuration).trim();

  // Traducir palabras clave si está en inglés
  if (lang === "en") {
    str = str
      .replace(/Instantáneo/gi, "Instantaneous")
      .replace(/Concentración/gi, "Concentration")
      .replace(/hasta\s+/gi, "up to ");
  } else {
    str = str
      .replace(/Instantaneous/gi, "Instantáneo")
      .replace(/Concentration/gi, "Concentración")
      .replace(/up to\s+/gi, "hasta ");
  }

  // Si ya tiene indicado el número de turnos o asaltos, no duplicar
  if (/\(\d+\s*(?:turno|asalt|round|turn)/i.test(str)) {
    return str;
  }

  let result = str;
  const turnLabel = (count: number) => {
    if (lang === "en") {
      return count === 1 ? "1 turn" : `${count} turns`;
    }
    return count === 1 ? "1 turno" : `${count} turnos`;
  };

  // 1 minuto -> 10 turnos
  if (/\b1\s*(?:minuto|minute|min)\b/i.test(result)) {
    result = result.replace(/\b1\s*(?:minuto|minute|min)\b/gi, `1 ${lang === "en" ? "minute" : "minuto"} (${turnLabel(10)})`);
  }
  // 10 minutos -> 100 turnos
  else if (/\b10\s*(?:minutos|minutes|mins)\b/i.test(result)) {
    result = result.replace(/\b10\s*(?:minutos|minutes|mins)\b/gi, `10 ${lang === "en" ? "minutes" : "minutos"} (${turnLabel(100)})`);
  }
  // 1 hora -> 600 turnos
  else if (/\b1\s*(?:hora|hour|hr)\b/i.test(result)) {
    result = result.replace(/\b1\s*(?:hora|hour|hr)\b/gi, `1 ${lang === "en" ? "hour" : "hora"} (${turnLabel(600)})`);
  }
  // 8 horas -> 4800 turnos
  else if (/\b8\s*(?:horas|hours|hrs)\b/i.test(result)) {
    result = result.replace(/\b8\s*(?:horas|hours|hrs)\b/gi, `8 ${lang === "en" ? "hours" : "horas"} (${turnLabel(4800)})`);
  }
  // 24 horas -> 14400 turnos
  else if (/\b24\s*(?:horas|hours|hrs)\b/i.test(result)) {
    result = result.replace(/\b24\s*(?:horas|hours|hrs)\b/gi, `24 ${lang === "en" ? "hours" : "horas"} (${turnLabel(14400)})`);
  }
  // 1 asalto o 1 round
  else if (/\b1\s*(?:asalto|round)\b/i.test(result) && !/(?:turno|turn)/i.test(result)) {
    result = result.replace(/\b1\s*(?:asalto|round)\b/gi, `1 ${lang === "en" ? "round" : "asalto"} (${turnLabel(1)})`);
  }

  return result;
}

/**
 * Normaliza y formatea los componentes de conjuro (V, S, M).
 */
export function formatComponents(rawComponents: any): string {
  if (!rawComponents) return "V, S";

  if (typeof rawComponents === "string") {
    return rawComponents.trim() || "V, S";
  }

  if (typeof rawComponents === "object" && rawComponents !== null) {
    if (Array.isArray(rawComponents)) {
      return rawComponents.map((c) => String(c)).join(", ") || "V, S";
    }

    const parts: string[] = [];
    if (rawComponents.verbal || rawComponents.v) parts.push("V");
    if (rawComponents.somatico || rawComponents.s) parts.push("S");
    if (rawComponents.material || rawComponents.m) {
      const desc =
        rawComponents.material_desc ||
        rawComponents.descripcion_material ||
        rawComponents.desc ||
        "";
      if (desc) {
        parts.push(`M (${String(desc).trim()})`);
      } else {
        parts.push("M");
      }
    }

    return parts.length > 0 ? parts.join(", ") : "V, S";
  }

  return String(rawComponents);
}
