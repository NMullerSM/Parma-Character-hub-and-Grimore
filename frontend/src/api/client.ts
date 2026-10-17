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

const mockActiveCharacter: CharacterSheetData = {
  id: 1,
  name: "Artanis",
  char_class: "Paladín",
  subclass: "Juramento de Venganza",
  level: 4,
  race: "Semielfo",
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
  death_save_successes: 0,
  death_save_failures: 0,
  abilities: {
    FUE: { base: 16, override: 0, bonus: 3, proficient: false, save_bonus: 3 },
    DES: { base: 10, override: 0, bonus: 0, proficient: false, save_bonus: 0 },
    CON: { base: 14, override: 0, bonus: 2, proficient: false, save_bonus: 2 },
    INT: { base: 10, override: 0, bonus: 0, proficient: false, save_bonus: 0 },
    SAB: { base: 12, override: 0, bonus: 1, proficient: true, save_bonus: 3 },
    CAR: { base: 16, override: 0, bonus: 3, proficient: true, save_bonus: 5 },
  },
  skills: {
    Atletismo: { proficient: true, bonus: 5, expertise: false },
    Intimidación: { proficient: true, bonus: 5, expertise: false },
    Perspicacia: { proficient: true, bonus: 3, expertise: false },
    Religión: { proficient: false, bonus: 0, expertise: false },
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
  weapon_actions: [
    {
      name: "Espadón +1",
      type: "Cuerpo a cuerpo",
      range_val: "5 pies",
      hit_dc: "+6",
      damage_dice: "2d6+4",
      damage_type: "Cortante",
      notes: "Pesada, dos manos.",
    },
  ],
  features: [
    { name: "Sentido Divino", source: "Paladín Nvl 1", description: "Detecta celestiales, infernales y no muertos a 60 pies." },
    { name: "Imposición de Manos", source: "Paladín Nvl 1", description: "Reserva de 20 PG de curación por descanso largo." },
    { name: "Castigo Divino", source: "Paladín Nvl 2", description: "Gasta ranura de nivel 1 para infligir +2d8 radiante." },
  ],
  sessions: [
    {
      id: 1,
      date: "2026-10-15",
      title: "La Cripta de los Reyes Olvidados",
      summary: "El grupo descendió por las catacumbas oscuras de Oakhaven. Enfrentamos a 4 esqueletos y descubrimos una puerta rúnica.",
      loot: "50 PO, Gema de cuarzo",
      xp_gained: 450,
    },
  ],
  network_nodes: [
    { id: "node_1", name: "Sir Roderick", role: "Mentor", description: "Comandante de la Orden del Roble Plateado.", x: 200, y: 150 },
    { id: "node_2", name: "Malakar", role: "Rival", description: "Caballero desterrado que busca venganza.", x: 450, y: 150 },
  ],
  network_edges: [
    { source_id: "node_1", target_id: "node_2", relation: "Enemigo" },
  ],
};

let mockHistory: RollHistoryEntry[] = [];

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

  async saveCharacter(charData: CharacterSheetData): Promise<{ success: boolean; id: number }> {
    if (this.isNative()) return await window.pywebview!.api.save_character(charData);
    return { success: true, id: charData.id || 1 };
  },

  async deleteCharacter(id: number): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.delete_character(id);
    return true;
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

    const rolls: Array<{ sides: number; roll: number }> = [];
    let total = request.modifier;
    for (const [sidesStr, count] of Object.entries(request.dice)) {
      const sides = parseInt(sidesStr, 10);
      for (let i = 0; i < count; i++) {
        const val = Math.floor(Math.random() * sides) + 1;
        rolls.push({ sides, roll: val });
        total += val;
      }
    }
    const result: RollResult = {
      total,
      dice_rolls: rolls,
      modifier: request.modifier,
      label: request.label,
      timestamp: new Date().toLocaleTimeString(),
      talespire_sent: false,
    };
    mockHistory.unshift({
      id: Date.now(),
      time_str: result.timestamp,
      character_name: "Artanis",
      reason: request.label,
      formula: Object.entries(request.dice).map(([s, c]) => `${c}d${s}`).join("+") + (request.modifier ? `+${request.modifier}` : ""),
      detail: `[${rolls.map((r) => r.roll).join(", ")}]`,
      total,
      is_crit: rolls.some((r) => r.sides === 20 && r.roll === 20),
      is_fumble: rolls.some((r) => r.sides === 20 && r.roll === 1),
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
    return { success: true };
  },

  async deleteNetworkNode(charId: number, nodeId: string): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.delete_network_node(charId, nodeId);
    return { success: true };
  },

  async saveNetworkEdge(charId: number, edgeData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.save_network_edge(charId, edgeData);
    return { success: true };
  },

  async deleteNetworkEdge(charId: number, edgeData: any): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.delete_network_edge(charId, edgeData);
    return { success: true };
  },

  // --- Visor de PDFs ---
  async listPdfDocuments(): Promise<PdfDocumentSummary[]> {
    if (this.isNative()) return await window.pywebview!.api.list_pdf_documents();
    return [
      { name: "Artanis LVL 4.pdf", path: "data/characters/Artanis LVL 4.pdf" },
      { name: "Manual_Jugador_5e.pdf", path: "data/manuals/Manual_Jugador_5e.pdf" },
    ];
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

  async renderPdfPage(pageNum: number, zoom: number = 1.0): Promise<PdfPageRenderResult> {
    if (this.isNative()) return await window.pywebview!.api.render_pdf_page(pageNum, zoom);
    return {
      success: true,
      page_num: pageNum,
      image_base64: "", // Vacío en mock para fallback
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

  // --- Reglas & Ajustes ---
  async validatePointBuy(scores: Record<string, number>): Promise<{
    valid: boolean;
    points_spent: number;
    points_remaining: number;
    error?: string;
    standard_array: number[];
  }> {
    if (this.isNative()) return await window.pywebview!.api.validate_point_buy(scores);
    return {
      valid: true,
      points_spent: 27,
      points_remaining: 0,
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
