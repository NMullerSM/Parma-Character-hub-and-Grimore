import type {
  CharacterSummary,
  CharacterSheetData,
  TaleSpireStatus,
  RollRequest,
  RollResult,
  RollHistoryEntry,
  PdfDocumentSummary,
  PdfDocumentInfo,
  PdfPageRenderResult,
  CompendiumCategory,
  CompendiumSearchResult,
  AppSettings,
  ThemeOption,
  BuilderCatalog,
  PointBuyValidationResult,
  SpellItemData,
  ClassProgressionLimits,
} from "./types";

declare global {
  interface Window {
    pywebview?: {
      api: any;
    };
  }
}

// Datos Mock para previsualización directa en navegador (npm run dev)
const mockCharacters: CharacterSummary[] = [
  {
    id: 1,
    name: "Artanis",
    char_class: "Paladín",
    subclass: "Juramento de Venganza",
    level: 4,
    race: "Semielfo",
    hp_current: 36,
    hp_max: 36,
    is_active: 1,
    updated_at: "2026-10-17 18:00:00",
  },
];

let mockActiveCharacter: CharacterSheetData = {
  id: 1,
  name: "Artanis",
  char_class: "Paladín",
  subclass: "Juramento de Venganza",
  level: 4,
  race: "Semielfo",
  subrace: "Estándar",
  background: "Soldado",
  alignment: "Legal Bueno",
  xp: 2700,
  inspiration: true,
  proficiency_bonus: 2,
  ac: 18,
  speed: 30,
  initiative: 0,
  hp_current: 36,
  hp_max: 36,
  hp_temp: 0,
  hit_dice_total: "4d10",
  hit_dice_current: "4d10",
  hit_dice_max: 4,
  hit_dice_faces: 10,
  death_save_successes: 0,
  death_save_failures: 0,
  conditions: [],
  abilities: {
    FUE: { base: 16, override: 0, bonus: 3, proficient: false, save_bonus: 3 },
    DES: { base: 10, override: 0, bonus: 0, proficient: false, save_bonus: 0 },
    CON: { base: 14, override: 0, bonus: 2, proficient: false, save_bonus: 2 },
    INT: { base: 10, override: 0, bonus: 0, proficient: false, save_bonus: 0 },
    SAB: { base: 12, override: 0, bonus: 1, proficient: true, save_bonus: 3 },
    CAR: { base: 16, override: 0, bonus: 3, proficient: true, save_bonus: 5 },
  },
  skills: {
    Acrobacias: { proficient: false, bonus: 0, expertise: false },
    Atletismo: { proficient: true, bonus: 5, expertise: false },
    "Conocimiento Arcano": { proficient: false, bonus: 0, expertise: false },
    Engaño: { proficient: false, bonus: 3, expertise: false },
    Historia: { proficient: false, bonus: 0, expertise: false },
    Interpretación: { proficient: false, bonus: 3, expertise: false },
    Intimidación: { proficient: true, bonus: 5, expertise: false },
    Investigación: { proficient: false, bonus: 0, expertise: false },
    "Juego de Manos": { proficient: false, bonus: 0, expertise: false },
    Medicina: { proficient: false, bonus: 1, expertise: false },
    Naturaleza: { proficient: false, bonus: 0, expertise: false },
    Percepción: { proficient: false, bonus: 1, expertise: false },
    Perspicacia: { proficient: true, bonus: 3, expertise: false },
    Persuasión: { proficient: true, bonus: 5, expertise: false },
    Religión: { proficient: false, bonus: 0, expertise: false },
    Sigilo: { proficient: false, bonus: 0, expertise: false },
    Supervivencia: { proficient: false, bonus: 1, expertise: false },
    "Trato con Animales": { proficient: false, bonus: 1, expertise: false },
  },
  spells: [
    {
      name: "Castigo Abrasador",
      level: 1,
      school: "Evocación",
      cast_time: "1 Acción Adicional",
      range_area: "Personal",
      components: "V",
      duration: "Concentración, hasta 1 minuto",
      prepared: true,
      notes: "+1d6 fuego en golpe cuerpo a cuerpo.",
    },
    {
      name: "Curar Heridas",
      level: 1,
      school: "Evocación",
      cast_time: "1 Acción",
      range_area: "Toque",
      components: "V, S",
      duration: "Instantáneo",
      prepared: true,
      notes: "Cura 1d8 + mod Carisma.",
    },
  ],
  spell_slots_total: { "1": 3 },
  spell_slots_used: { "1": 1 },
  spell_stats: {
    ability: "CAR",
    dc: 13,
    attack_bonus: 5,
    is_caster: true,
  },
  weapon_actions: [
    {
      name: "Espadón +1",
      type: "Cuerpo a cuerpo",
      range_val: "5 pies",
      hit_dc: "+6",
      damage_dice: "2d6+4",
      damage_type: "Cortante",
      notes: "Pesada, dos manos.",
      proficient: true,
    },
  ],
  features: [
    {
      name: "Sentido Divino",
      source: "Paladín Nvl 1",
      description: "Detecta celestiales, infernales y no muertos a 60 pies.",
      uses_max: 4,
      uses_current: 4,
      recharge: "LR",
    },
    {
      name: "Imposición de Manos",
      source: "Paladín Nvl 1",
      description: "Reserva de 20 PG de curación por descanso largo.",
      uses_max: 20,
      uses_current: 20,
      recharge: "LR",
    },
    {
      name: "Castigo Divino",
      source: "Paladín Nvl 2",
      description: "Gasta ranura de nivel 1 para infligir +2d8 radiante.",
      uses_max: 0,
      uses_current: 0,
      recharge: "At-Will",
    },
  ],
  sessions: [
    {
      id: 1,
      date: "2026-10-15",
      title: "La Cripta de los Reyes Olvidados",
      summary:
        "El grupo descendió por las catacumbas oscuras de Oakhaven. Enfrentamos a **4 esqueletos** y descubrimos una *puerta rúnica*.\n\n- Hallamos el sello de la Orden.\n- Recuperamos las reliquias del altar.",
      loot: "50 PO, Gema de cuarzo",
      xp_gained: 450,
    },
  ],
  network_nodes: [
    {
      id: "node_1",
      name: "Sir Roderick",
      role: "Mentor",
      description: "Comandante de la Orden del Roble Plateado.",
      x: 200,
      y: 150,
    },
    {
      id: "node_2",
      name: "Malakar",
      role: "Rival",
      description: "Caballero desterrado que busca venganza.",
      x: 450,
      y: 150,
    },
  ],
  network_edges: [{ source_id: "node_1", target_id: "node_2", relation: "Enemigo" }],
  senses: "Visión en la Oscuridad 60 pies",
  languages: "Común, Élfico, Celestial",
};

let mockHistory: RollHistoryEntry[] = [];

const POINT_BUY_COSTS: Record<number, number> = {
  8: 0,
  9: 1,
  10: 2,
  11: 3,
  12: 4,
  13: 5,
  14: 7,
  15: 9,
};

// Cliente unificado
export const api = {
  isNative: (): boolean => {
    return typeof window !== "undefined" && !!window.pywebview?.api;
  },

  async listCharacters(): Promise<CharacterSummary[]> {
    if (this.isNative()) return await window.pywebview!.api.list_characters();
    return mockCharacters;
  },

  async getActiveCharacter(): Promise<CharacterSheetData | null> {
    if (this.isNative()) return await window.pywebview!.api.get_active_character();
    return mockActiveCharacter;
  },

  async getCharacterById(id: number): Promise<CharacterSheetData | null> {
    if (this.isNative()) return await window.pywebview!.api.get_character_by_id(id);
    return mockActiveCharacter;
  },

  async setActiveCharacter(id: number): Promise<CharacterSheetData | null> {
    if (this.isNative()) return await window.pywebview!.api.set_active_character(id);
    return mockActiveCharacter;
  },

  async saveCharacter(charData: CharacterSheetData): Promise<{ success: boolean; id: number; character?: CharacterSheetData }> {
    if (this.isNative()) return await window.pywebview!.api.save_character(charData);
    mockActiveCharacter = { ...mockActiveCharacter, ...charData };
    return { success: true, id: charData.id || 1, character: mockActiveCharacter };
  },

  async deleteCharacter(id: number): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.delete_character(id);
    return true;
  },

  async uploadCharacterPortrait(charId: number): Promise<{ success: boolean; portrait_path?: string; portrait_base64?: string; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.upload_character_portrait(charId);
    return { success: false, error: "Función de diálogo nativo disponible solo en escritorio." };
  },

  async exportCharacterJson(charId: number): Promise<{ success: boolean; path?: string; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.export_character_json(charId);
    return { success: true, path: "Artanis.json" };
  },

  async importCharacterJson(): Promise<{ success: boolean; id?: number; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.import_character_json();
    return { success: true, id: 1, character: mockActiveCharacter };
  },

  async importCharacterPdf(): Promise<{ success: boolean; id?: number; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.import_character_pdf();
    return { success: true, id: 1, character: mockActiveCharacter };
  },

  async getTaleSpireStatus(): Promise<TaleSpireStatus> {
    if (this.isNative()) return await window.pywebview!.api.get_talespire_status();
    return {
      is_installed: true,
      is_running: false,
      is_connected: false,
      state_label: "installed_closed",
    };
  },

  async connectTaleSpire(): Promise<{ success: boolean; message: string }> {
    if (this.isNative()) return await window.pywebview!.api.connect_talespire();
    return { success: true, message: "Conexión simulada con TaleSpire." };
  },

  async disconnectTaleSpire(): Promise<void> {
    if (this.isNative()) await window.pywebview!.api.disconnect_talespire();
  },

  async rollDice(request: RollRequest): Promise<RollResult> {
    if (this.isNative()) return await window.pywebview!.api.roll_dice(request);

    const mode = request.mode || "normal";
    const rolls: Array<{ sides: number; roll: number }> = [];
    let subtotal = 0;

    for (const [sidesStr, count] of Object.entries(request.dice)) {
      const sides = parseInt(sidesStr, 10);
      if (sides === 20 && count === 1 && (mode === "advantage" || mode === "disadvantage")) {
        const r1 = Math.floor(Math.random() * 20) + 1;
        const r2 = Math.floor(Math.random() * 20) + 1;
        const chosen = mode === "advantage" ? Math.max(r1, r2) : Math.min(r1, r2);
        rolls.push({ sides: 20, roll: chosen });
        subtotal += chosen;
      } else {
        for (let i = 0; i < count; i++) {
          const val = Math.floor(Math.random() * sides) + 1;
          rolls.push({ sides, roll: val });
          subtotal += val;
        }
      }
    }

    const total = subtotal + request.modifier;
    const is_crit = rolls.some((r) => r.sides === 20 && r.roll === 20);
    const is_fumble = rolls.some((r) => r.sides === 20 && r.roll === 1);
    const formula =
      Object.entries(request.dice)
        .map(([s, c]) => `${c}d${s}`)
        .join(" + ") + (request.modifier ? (request.modifier > 0 ? ` + ${request.modifier}` : ` - ${Math.abs(request.modifier)}`) : "");
    const detail = `[${rolls.map((r) => r.roll).join(", ")}]`;

    const result: RollResult = {
      total,
      dice_rolls: rolls,
      modifier: request.modifier,
      label: request.label,
      formula,
      detail,
      is_crit,
      is_fumble,
      mode,
      timestamp: new Date().toLocaleTimeString(),
      talespire_sent: false,
    };
    mockHistory.unshift({
      id: Date.now(),
      time_str: result.timestamp,
      character_name: mockActiveCharacter.name,
      reason: request.label,
      formula,
      detail,
      total,
      is_crit,
      is_fumble,
      channel: "Motor Local",
    });
    return result;
  },

  async getRollHistory(): Promise<RollHistoryEntry[]> {
    if (this.isNative()) return await window.pywebview!.api.get_roll_history();
    return mockHistory;
  },

  async clearRollHistory(): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.clear_roll_history();
    mockHistory = [];
    return true;
  },

  async triggerTaleSpireGesture(): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.trigger_talespire_gesture();
    return true;
  },

  // --- Diario de Campaña ---
  async getCharacterJournals(charId: number): Promise<any[]> {
    if (this.isNative()) return await window.pywebview!.api.get_character_journals(charId);
    return mockActiveCharacter.sessions;
  },

  async saveCharacterJournal(charId: number, journalData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.save_character_journal(charId, journalData);
    return { success: true, sessions: mockActiveCharacter.sessions };
  },

  async deleteCharacterJournal(charId: number, sessionId: number): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.delete_character_journal(charId, sessionId);
    return { success: true, sessions: [] };
  },

  // --- Red de Personajes ---
  async getCharacterNetwork(charId: number): Promise<{ nodes: any[]; edges: any[] }> {
    if (this.isNative()) return await window.pywebview!.api.get_character_network(charId);
    return { nodes: mockActiveCharacter.network_nodes, edges: mockActiveCharacter.network_edges };
  },

  async saveNetworkNode(charId: number, nodeData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.save_network_node(charId, nodeData);
    const existing = mockActiveCharacter.network_nodes.find((n) => n.id === nodeData.id);
    if (existing) {
      Object.assign(existing, nodeData);
    } else {
      mockActiveCharacter.network_nodes.push(nodeData);
    }
    return {
      success: true,
      network: {
        nodes: [...mockActiveCharacter.network_nodes],
        edges: [...mockActiveCharacter.network_edges],
      },
    };
  },

  async deleteNetworkNode(charId: number, nodeId: string): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.delete_network_node(charId, nodeId);
    mockActiveCharacter.network_nodes = mockActiveCharacter.network_nodes.filter((n) => n.id !== nodeId);
    mockActiveCharacter.network_edges = mockActiveCharacter.network_edges.filter(
      (e) => e.source_id !== nodeId && e.target_id !== nodeId
    );
    return {
      success: true,
      network: {
        nodes: [...mockActiveCharacter.network_nodes],
        edges: [...mockActiveCharacter.network_edges],
      },
    };
  },

  async saveNetworkEdge(charId: number, edgeData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.save_network_edge(charId, edgeData);
    mockActiveCharacter.network_edges.push(edgeData);
    return {
      success: true,
      network: {
        nodes: [...mockActiveCharacter.network_nodes],
        edges: [...mockActiveCharacter.network_edges],
      },
    };
  },

  async deleteNetworkEdge(charId: number, edgeData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.delete_network_edge(charId, edgeData);
    mockActiveCharacter.network_edges = mockActiveCharacter.network_edges.filter(
      (e) => !(e.source_id === edgeData.source_id && e.target_id === edgeData.target_id)
    );
    return {
      success: true,
      network: {
        nodes: [...mockActiveCharacter.network_nodes],
        edges: [...mockActiveCharacter.network_edges],
      },
    };
  },

  // --- Visor de PDFs ---
  async listPdfDocuments(): Promise<PdfDocumentSummary[]> {
    if (this.isNative()) return await window.pywebview!.api.list_pdf_documents();
    return [
      { name: "Artanis LVL 4.pdf", path: "data/characters/Artanis LVL 4.pdf" },
      { name: "Manual_Jugador_5e.pdf", path: "data/manuals/Manual_Jugador_5e.pdf" },
    ];
  },

  async openPdfDialog(): Promise<string | null> {
    if (this.isNative()) return await window.pywebview!.api.open_pdf_dialog();
    return null;
  },

  async openPdfDocument(filePath: string): Promise<PdfDocumentInfo> {
    if (this.isNative()) return await window.pywebview!.api.open_pdf_document(filePath);
    return {
      success: true,
      path: filePath,
      filename: "Artanis LVL 4.pdf",
      page_count: 3,
      toc: [
        { level: 1, title: "Características y Habilidades", page: 1 },
        { level: 1, title: "Trasfondo y Rasgos", page: 2 },
        { level: 1, title: "Grimorio y Conjuros", page: 3 },
      ],
    };
  },

  async renderPdfPage(pageNum: number, zoom: number = 1.0, trimMargins?: boolean): Promise<PdfPageRenderResult> {
    if (this.isNative()) return await window.pywebview!.api.render_pdf_page(pageNum, zoom, trimMargins);
    return {
      success: true,
      page_num: pageNum,
      image_base64: "",
      links: [],
    };
  },

  async exportPdf(charId: number): Promise<{ success: boolean; path?: string; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.export_character_pdf(charId);
    return { success: true, path: "C:/fake/path/Artanis_Sheet.pdf" };
  },

  // --- Compendio OKF ---
  async getCompendiumCategories(): Promise<CompendiumCategory[]> {
    if (this.isNative()) return await window.pywebview!.api.get_compendium_categories();
    return [
      { id: "clases", label: "Clases y Subclases", count: 12 },
      { id: "especies_y_linajes", label: "Especies y Linajes", count: 9 },
      { id: "conjuros", label: "Grimorio de Conjuros", count: 320 },
      { id: "trasfondos", label: "Trasfondos", count: 16 },
      { id: "dotes", label: "Dotes", count: 42 },
      { id: "equipo_y_armamento", label: "Equipo y Armamento", count: 85 },
      { id: "reglas_y_mecanicas", label: "Reglas y Mecánicas", count: 28 },
    ];
  },

  async searchCompendium(query: string, category?: string): Promise<CompendiumSearchResult[]> {
    if (this.isNative()) return await window.pywebview!.api.search_compendium(query, category);
    return [
      {
        id: "castigo-divino",
        name: "Castigo Divino",
        category: "clases",
        snippet: "A partir del nivel 2, cuando golpeas con un arma cuerpo a cuerpo...",
        path: "okf_dnd5e/clases/paladin.md",
      },
    ];
  },

  async getCompendiumEntry(category: string, entryName: string): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.get_compendium_entry(category, entryName);
    return {
      name: entryName,
      category,
      content: `# ${entryName}\n\nDescripción detallada de reglas simulada para previsualización web.`,
    };
  },

  // --- Creador de Personajes & Reglas ---
  async getBuilderCatalog(edition: string = "5.5e"): Promise<BuilderCatalog> {
    if (this.isNative()) return await window.pywebview!.api.get_builder_catalog(edition);
    return {
      edition,
      species: [
        { name: "Humano", subraces: ["Estándar", "Variante (Dote)"], speed: 30, bonuses: { FUE: 1, DES: 1, CON: 1, INT: 1, SAB: 1, CAR: 1 }, traits: [{ name: "Versatilidad Humana", desc: "+1 a todas las características." }] },
        { name: "Elfo", subraces: ["Alto Elfo", "Elfo de los Bosques", "Elfo Oscuro (Drow)"], speed: 30, bonuses: { DES: 2, INT: 1 }, traits: [{ name: "Visión en la Oscuridad", desc: "60 pies." }, { name: "Sentidos Agudos", desc: "Competencia en Percepción." }] },
        { name: "Enano", subraces: ["Enano de las Colinas", "Enano de las Montañas"], speed: 25, bonuses: { CON: 2, SAB: 1 }, traits: [{ name: "Resistencia Enana", desc: "Ventaja contra veneno." }] },
        { name: "Semielfo", subraces: ["Estándar"], speed: 30, bonuses: { CAR: 2, FUE: 1, CON: 1 }, traits: [{ name: "Ancestro Feérico", desc: "Ventaja contra ser hechizado." }] },
        { name: "Tiefling", subraces: ["Linaje Infernal"], speed: 30, bonuses: { CAR: 2, INT: 1 }, traits: [{ name: "Resistencia Infernal", desc: "Resistencia al daño por fuego." }] },
      ],
      classes: [
        { name: "Guerrero", hit_die: 10, primary_ability: "FUE", saves: ["FUE", "CON"], skill_choices_count: 2, skill_options: ["Acrobacias", "Atletismo", "Historia", "Intimidación", "Percepción", "Perspicacia", "Supervivencia"], subclasses: ["Campeón", "Maestro de Batalla", "Caballero Arcano"], subclass_unlock_level: 3, is_caster: false },
        { name: "Mago", hit_die: 6, primary_ability: "INT", saves: ["INT", "SAB"], skill_choices_count: 2, skill_options: ["Conocimiento Arcano", "Historia", "Investigación", "Medicina", "Perspicacia", "Religión"], subclasses: ["Escuela de Evocación", "Escuela de Abjuración", "Escuela de Adivinación"], subclass_unlock_level: 3, is_caster: true },
        { name: "Clérigo", hit_die: 8, primary_ability: "SAB", saves: ["SAB", "CAR"], skill_choices_count: 2, skill_options: ["Historia", "Medicina", "Perspicacia", "Persuasión", "Religión"], subclasses: ["Dominio de la Vida", "Dominio de la Luz", "Dominio de la Guerra"], subclass_unlock_level: edition === "5.5e" ? 3 : 1, is_caster: true },
        { name: "Pícaro", hit_die: 8, primary_ability: "DES", saves: ["DES", "INT"], skill_choices_count: 4, skill_options: ["Acrobacias", "Atletismo", "Engaño", "Intimidación", "Investigación", "Juego de Manos", "Percepción", "Perspicacia", "Persuasión", "Sigilo"], subclasses: ["Ladrón", "Asesino", "Bribón Arcano"], subclass_unlock_level: 3, is_caster: false },
        { name: "Paladín", hit_die: 10, primary_ability: "FUE", saves: ["SAB", "CAR"], skill_choices_count: 2, skill_options: ["Atletismo", "Intimidación", "Medicina", "Perspicacia", "Persuasión", "Religión"], subclasses: ["Juramento de Devoción", "Juramento de Venganza", "Juramento de los Antiguos"], subclass_unlock_level: 3, is_caster: true },
      ],
      backgrounds: [
        { name: "Soldado", skills: ["Atletismo", "Intimidación"], feature_name: "Rango Militar", feature_desc: "Reconocimiento e influencia entre soldados." },
        { name: "Sabio", skills: ["Conocimiento Arcano", "Historia"], feature_name: "Investigador", feature_desc: "Sabes dónde obtener información erudita." },
        { name: "Acólito", skills: ["Perspicacia", "Religión"], feature_name: "Refugio de los Fieles", feature_desc: "Asistencia en templos de tu fe." },
        { name: "Criminal", skills: ["Engaño", "Sigilo"], feature_name: "Contacto Criminal", feature_desc: "Enlace con los bajos fondos." },
      ],
      all_skills: Object.keys(mockActiveCharacter.skills),
    };
  },

  async getClassSpells(className: string, maxLevel: number = 1): Promise<SpellItemData[]> {
    if (this.isNative()) return await window.pywebview!.api.get_class_spells(className, maxLevel);
    return mockActiveCharacter.spells.filter((s) => s.level <= maxLevel);
  },

  async getAvailableSpells(options: {
    className?: string;
    maxLevel?: number;
    level?: number;
    query?: string;
    school?: string;
  } = {}): Promise<SpellItemData[]> {
    if (this.isNative()) {
      return await window.pywebview!.api.get_available_spells(
        options.className || null,
        options.maxLevel ?? null,
        options.query || "",
        options.school || null,
        options.level ?? null
      );
    }
    let filtered = [...mockActiveCharacter.spells];
    if (options.level !== undefined) filtered = filtered.filter((s) => s.level === options.level);
    if (options.query) filtered = filtered.filter((s) => s.name.toLowerCase().includes(options.query!.toLowerCase()));
    return filtered;
  },

  async getClassProgressionLimits(className: string, level: number, edition: string = "5.5e"): Promise<ClassProgressionLimits> {
    if (this.isNative()) {
      return await window.pywebview!.api.get_class_progression_limits(className, level, edition);
    }
    return {
      is_caster: true,
      edition,
      cantrips_limit: 3,
      spells_limit: 7,
      max_spell_level: 2,
      spell_slots: { "1": 4, "2": 3 },
      weapon_mastery_slots: 0,
      casting_ability: "CAR",
    };
  },

  async addSpellToCharacter(charId: number, spell: SpellItemData): Promise<{ success: boolean; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.add_spell_to_character(charId, spell);
    if (!mockActiveCharacter.spells.some((s) => s.name === spell.name)) {
      mockActiveCharacter = {
        ...mockActiveCharacter,
        spells: [...mockActiveCharacter.spells, spell],
      };
    }
    return { success: true, character: mockActiveCharacter };
  },

  async removeSpellFromCharacter(charId: number, spellName: string): Promise<{ success: boolean; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.remove_spell_from_character(charId, spellName);
    mockActiveCharacter = {
      ...mockActiveCharacter,
      spells: mockActiveCharacter.spells.filter((s) => s.name !== spellName),
    };
    return { success: true, character: mockActiveCharacter };
  },

  async syncCharacterFeatures(charId: number): Promise<{ success: boolean; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.sync_character_features(charId);
    return { success: true, character: mockActiveCharacter };
  },

  async syncCompendiumFromSrd(edition: string = "PHB 2024"): Promise<{ success: boolean; total_entities?: number; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.sync_compendium_from_srd(edition);
    return { success: true, total_entities: 574 };
  },

  async buildCharacterFromWizard(payload: any): Promise<CharacterSheetData> {
    if (this.isNative()) return await window.pywebview!.api.build_character_from_wizard(payload);
    return {
      ...mockActiveCharacter,
      id: undefined,
      name: payload.name || "Nuevo Héroe",
      race: payload.race || "Humano",
      subrace: payload.subrace || "Estándar",
      char_class: payload.char_class || "Guerrero",
      subclass: payload.subclass || "",
      level: payload.level || 1,
      background: payload.background || "Soldado",
      alignment: payload.alignment || "Neutral",
    };
  },

  async generateQuickBuildPreview(charClass: string, species: string = "Humano"): Promise<CharacterSheetData> {
    if (this.isNative()) return await window.pywebview!.api.generate_quick_build_preview(charClass, species);
    return {
      ...mockActiveCharacter,
      id: undefined,
      name: `${charClass} Rápido`,
      char_class: charClass,
      race: species,
      level: 1,
    };
  },

  async generateRandomCharacterPreview(
    charClass?: string,
    species?: string,
    level: number = 1
  ): Promise<{ character: CharacterSheetData; raw_rolls: Record<string, any> }> {
    if (this.isNative()) return await window.pywebview!.api.generate_random_character_preview(charClass, species, level);
    return {
      character: {
        ...mockActiveCharacter,
        id: undefined,
        name: "Héroe del Destino",
        char_class: charClass || "Guerrero",
        race: species || "Humano",
        level,
      },
      raw_rolls: {},
    };
  },

  async validatePointBuy(scores: Record<string, number>): Promise<PointBuyValidationResult> {
    if (this.isNative()) return await window.pywebview!.api.validate_point_buy(scores);
    let spent = 0;
    for (const val of Object.values(scores)) {
      spent += POINT_BUY_COSTS[val] ?? 0;
    }
    const remaining = 27 - spent;
    const can_increment: Record<string, boolean> = {};
    const can_decrement: Record<string, boolean> = {};
    for (const [ab, val] of Object.entries(scores)) {
      const nextCost = (POINT_BUY_COSTS[val + 1] ?? 99) - (POINT_BUY_COSTS[val] ?? 0);
      can_increment[ab] = val < 15 && remaining >= nextCost;
      can_decrement[ab] = val > 8;
    }
    return {
      valid: remaining >= 0,
      points_spent: spent,
      points_remaining: remaining,
      can_increment,
      can_decrement,
      standard_array: [15, 14, 13, 12, 10, 8],
    };
  },

  async performRest(charId: number, restType: "short" | "long", hitDiceSpent: number = 0): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.perform_rest(charId, restType, hitDiceSpent);
    return { success: true };
  },

  async getSettings(): Promise<AppSettings> {
    if (this.isNative()) return await window.pywebview!.api.get_settings();
    return {
      theme: "dark-obsidian",
      dnd_edition: "5.5e",
      talespire_mode: "dm",
      talespire_enabled: true,
      okf_path: "okf_dnd5e",
      custom_themes_dir: "themes",
    };
  },

  async setSetting(key: string, value: any): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.set_setting(key, value);
    return true;
  },

  async getAvailableThemes(): Promise<ThemeOption[]> {
    if (this.isNative()) return await window.pywebview!.api.get_available_themes();
    return [
      { id: "dark-obsidian", name: "Obsidian & Steel (Oscuro)", is_dark: true },
      { id: "light-parchment", name: "Illuminated Parchment (Claro)", is_dark: false },
    ];
  },
};
