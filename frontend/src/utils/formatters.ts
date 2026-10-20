/**
 * Utilidades de formateo para D&D 5e
 * Reglas de conversión:
 * - Distancia/Alcance: 1.5 m = 1 casilla (tile) de 5 pies (TaleSpire / Tablero)
 * - Duración: 1 asalto = 6 segundos = 1 turno. 1 minuto = 10 turnos. 1 hora = 600 turnos.
 */

/**
 * Convierte distancias en metros o pies a casillas (tiles) tácticas.
 * Ej: "18 m" -> "18 m (12 casillas)"
 *     "1.5 m" -> "1.5 m (1 casilla)"
 *     "Toque" -> "Toque (1 casilla)"
 */
export function formatRangeWithTiles(rawRange: string | undefined | null): string {
  if (!rawRange) return "18 m (12 casillas)";
  const str = String(rawRange).trim();

  // Si ya tiene especificada la casilla o tile, no duplicar
  if (/casilla|tile/i.test(str)) {
    return str;
  }

  // Caso especial: Toque
  if (/^toque$/i.test(str)) {
    return "Toque (1 casilla)";
  }

  // Detectar metros: ej "1.5 m", "18 m", "9 metros", "3m"
  const mRegex = /(\d+(?:[.,]\d+)?)\s*(?:m|metros|metro)\b/gi;
  if (mRegex.test(str)) {
    return str.replace(mRegex, (_, numStr) => {
      const meters = parseFloat(numStr.replace(",", "."));
      if (isNaN(meters) || meters <= 0) return `${numStr} m`;
      const tiles = Math.max(1, Math.round(meters / 1.5));
      const tileLabel = tiles === 1 ? "casilla" : "casillas";
      return `${meters} m (${tiles} ${tileLabel})`;
    });
  }

  // Detectar pies si viniera en inglés: ej "30 ft", "60 feet", "30 pies"
  const ftRegex = /(\d+)\s*(?:ft|feet|pies|pie)\b/gi;
  if (ftRegex.test(str)) {
    return str.replace(ftRegex, (_, numStr) => {
      const feet = parseInt(numStr, 10);
      if (isNaN(feet) || feet <= 0) return `${numStr} pies`;
      const tiles = Math.max(1, Math.round(feet / 5));
      const meters = (tiles * 1.5).toFixed(1).replace(".0", "");
      const tileLabel = tiles === 1 ? "casilla" : "casillas";
      return `${meters} m (${tiles} ${tileLabel})`;
    });
  }

  return str;
}

/**
 * Convierte duraciones a turnos/asaltos de combate cuando corresponda.
 * Ej: "Concentración, hasta 1 minuto" -> "Concentración, hasta 1 minuto (10 turnos)"
 *     "10 minutos" -> "10 minutos (100 turnos)"
 *     "1 hora" -> "1 hora (600 turnos)"
 *     "1 asalto" -> "1 asalto (1 turno)"
 */
export function formatDurationWithTurns(rawDuration: string | undefined | null): string {
  if (!rawDuration) return "Instantáneo";
  const str = String(rawDuration).trim();

  // Si ya tiene indicado el número de turnos o asaltos, no duplicar
  if (/\(\d+\s*(?:turno|asalt|round)/i.test(str)) {
    return str;
  }

  let result = str;

  // 1 minuto -> 10 turnos
  if (/\b1\s*(?:minuto|min)\b/i.test(result)) {
    result = result.replace(/\b1\s*(?:minuto|min)\b/gi, "1 minuto (10 turnos)");
  }
  // 10 minutos -> 100 turnos
  else if (/\b10\s*(?:minutos|mins)\b/i.test(result)) {
    result = result.replace(/\b10\s*(?:minutos|mins)\b/gi, "10 minutos (100 turnos)");
  }
  // 1 hora -> 600 turnos
  else if (/\b1\s*(?:hora|hr)\b/i.test(result)) {
    result = result.replace(/\b1\s*(?:hora|hr)\b/gi, "1 hora (600 turnos)");
  }
  // 8 horas -> 4800 turnos
  else if (/\b8\s*(?:horas|hrs)\b/i.test(result)) {
    result = result.replace(/\b8\s*(?:horas|hrs)\b/gi, "8 horas (4800 turnos)");
  }
  // 24 horas -> 14400 turnos
  else if (/\b24\s*(?:horas|hrs)\b/i.test(result)) {
    result = result.replace(/\b24\s*(?:horas|hrs)\b/gi, "24 horas (14400 turnos)");
  }
  // 1 asalto o 1 round
  else if (/\b1\s*(?:asalto|round)\b/i.test(result) && !/turno/i.test(result)) {
    result = result.replace(/\b1\s*(?:asalto|round)\b/gi, "1 asalto (1 turno)");
  }

  return result;
}

/**
 * Normaliza y formatea de manera segura los componentes de conjuro,
 * evitando que objetos diccionarios de YAML rompan el render de React.
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

    // Es un diccionario con llaves verbal, somatico, material, etc.
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
