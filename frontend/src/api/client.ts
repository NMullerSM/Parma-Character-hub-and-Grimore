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
  DmSessionStatus,
  DmHomebrewItem,
  DmSessionEventLog,
} from "./types";

declare global {
  interface Window {
    pywebview?: {
      api: {
        list_characters: () => Promise<CharacterSummary[]>;
        get_active_character: () => Promise<CharacterSheetData | null>;
        get_character_by_id: (id: number) => Promise<CharacterSheetData | null>;
        set_active_character: (id: number) => Promise<CharacterSheetData | null>;
        save_character: (charData: CharacterSheetData) => Promise<{ success: boolean; id: number; character?: CharacterSheetData }>;
        delete_character: (id: number) => Promise<boolean>;
        upload_character_portrait: (charId: number) => Promise<{ success: boolean; portrait_path?: string; portrait_base64?: string; character?: CharacterSheetData; error?: string }>;
        set_character_portrait_base64: (charId: number, imageBase64: string) => Promise<{ success: boolean; portrait_base64?: string; character?: CharacterSheetData; error?: string }>;
        generate_ai_portrait: (prompt: string, provider: string, apiKey: string, apiUrl: string, model: string) => Promise<{ success: boolean; image_base64?: string; error?: string }>;
        export_character_json: (charId: number) => Promise<{ success: boolean; path?: string; error?: string }>;
        import_character_json: () => Promise<{ success: boolean; id?: number; character?: CharacterSheetData; error?: string }>;
        export_character_pdf: (charId: number) => Promise<{ success: boolean; path?: string; error?: string; cancelled?: boolean }>;
        import_character_pdf: () => Promise<{ success: boolean; id?: number; character?: CharacterSheetData; error?: string }>;
        get_talespire_status: () => Promise<TaleSpireStatus>;
        connect_talespire: () => Promise<{ success: boolean; message: string }>;
        disconnect_talespire: () => Promise<void>;
        reinstall_talespire_symbiote?: () => Promise<{ success: boolean; message?: string; error?: string }>;
        open_talespire_symbiotes_folder?: () => Promise<{ success: boolean; error?: string }>;
        roll_dice: (request: RollRequest) => Promise<RollResult>;
        get_roll_history: () => Promise<RollHistoryEntry[]>;
        clear_roll_history: () => Promise<boolean>;
        trigger_talespire_gesture: () => Promise<boolean>;
        get_character_journals: (charId: number) => Promise<any[]>;
        save_character_journal: (charId: number, journalData: any) => Promise<any>;
        delete_character_journal: (charId: number, sessionId: number) => Promise<any>;
        get_character_network: (charId: number) => Promise<{ nodes: any[]; edges: any[] }>;
        save_network_node: (charId: number, nodeData: any) => Promise<any>;
        delete_network_node: (charId: number, nodeId: string) => Promise<any>;
        save_network_edge: (charId: number, edgeData: any) => Promise<any>;
        delete_network_edge: (charId: number, edgeData: any) => Promise<any>;
        list_pdf_documents: () => Promise<PdfDocumentSummary[]>;
        open_pdf_dialog: () => Promise<string | null>;
        open_pdf_document: (filePath: string) => Promise<PdfDocumentInfo>;
        render_pdf_page: (pageNum: number, zoom?: number, trimMargins?: boolean) => Promise<PdfPageRenderResult>;
        get_compendium_categories: (lang?: string) => Promise<CompendiumCategory[]>;
        search_compendium: (query: string, category?: string, lang?: string) => Promise<CompendiumSearchResult[]>;
        get_compendium_entry: (category: string, entryName: string, lang?: string) => Promise<any>;
        get_available_spells: (
          className: string | null,
          maxLevel: number | null,
          query: string,
          school: string | null,
          level: number | null,
          limit: number,
          lang: string
        ) => Promise<SpellItemData[]>;
        add_spell_to_character: (charId: number, spellData: any) => Promise<{ success: boolean; character?: CharacterSheetData; error?: string }>;
        remove_spell_from_character: (charId: number, spellName: string) => Promise<{ success: boolean; character?: CharacterSheetData; error?: string }>;
        sync_character_features: (charId: number, lang?: string) => Promise<{ success: boolean; character?: CharacterSheetData; error?: string }>;
        sync_compendium_from_srd: (edition?: string) => Promise<{ success: boolean; total_entities?: number; error?: string }>;
        get_builder_catalog: (edition?: string, lang?: string) => Promise<BuilderCatalog>;
        validate_point_buy: (scores: Record<string, number>) => Promise<PointBuyValidationResult>;
        build_character_from_wizard: (payload: any) => Promise<CharacterSheetData>;
        generate_quick_build_preview: (charClass: string, species?: string) => Promise<CharacterSheetData>;
        generate_random_character_preview: (charClass?: string, species?: string, level?: number) => Promise<{ character: CharacterSheetData; raw_rolls: Record<string, any> }>;
        perform_rest: (charId: number, restType: string, hitDiceSpent: number) => Promise<any>;
        get_settings: () => Promise<AppSettings>;
        set_setting: (key: string, value: any) => Promise<boolean>;
        get_available_themes: () => Promise<ThemeOption[]>;
        start_dm_session: (name?: string, campaignName?: string, sessionId?: string) => Promise<DmSessionStatus>;
        dm_list_sessions: () => Promise<any[]>;
        stop_dm_session: () => Promise<{ success: boolean }>;
        get_dm_session_status: () => Promise<DmSessionStatus>;
        dm_apply_hp_change: (playerToken: string, delta: number) => Promise<boolean>;
        dm_gift_item: (playerToken: string, itemData: any) => Promise<boolean>;
        dm_list_homebrew_items: () => Promise<DmHomebrewItem[]>;
        dm_save_homebrew_item: (itemData: any) => Promise<string>;
        dm_delete_homebrew_item: (itemId: string) => Promise<boolean>;
        dm_get_session_logs: (sessionId?: string) => Promise<DmSessionEventLog[]>;
        dm_save_session_notes: (notes: string, sessionId?: string) => Promise<boolean>;
        dm_get_session_notes: (sessionId?: string) => Promise<string>;
      };
    };
  }
}

let mockCharacters: CharacterSummary[] = [
  {
    id: 1,
    name: "Artanis de Caelum",
    char_class: "Paladín",
    subclass: "Juramento de Venganza",
    level: 4,
    race: "Humano",
    hp_current: 36,
    hp_max: 36,
    is_active: 1,
    session_id: "sess_mock",
    updated_at: new Date().toISOString(),
  },
];

let mockActiveCharacter: CharacterSheetData = {
  id: 1,
  name: "Artanis de Caelum",
  char_class: "Paladín",
  subclass: "Juramento de Venganza",
  level: 4,
  race: "Humano",
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
      notes: "Cura 1d8 + Modificador de Lanzamiento.",
    },
    {
      name: "Protección contra el Bien y el Mal",
      level: 1,
      school: "Abjuración",
      cast_time: "1 Acción",
      range_area: "Toque",
      components: "V, S, M",
      duration: "Concentración, hasta 10 minutos",
      prepared: false,
      notes: "Protege contra aberraciones, celestiales, etc.",
    },
  ],
  spell_slots_total: { "1": 3 },
  spell_slots_used: { "1": 1 },
  spell_stats: {
    casting_ability: "CAR",
    spell_save_dc: 13,
    spell_attack_bonus: 5,
    ability_mod: 3,
  },
  weapon_actions: [
    {
      name: "Espada Larga Radiante",
      type: "Cuerpo a cuerpo",
      range_val: "5 pies (1 tile)",
      hit_dc: "+5",
      damage_dice: "1d8+3",
      damage_type: "cortante",
      notes: "Versátil (1d10+3)",
      proficient: true,
    },
    {
      name: "Jabalina de Repuesto",
      type: "A distancia",
      range_val: "30/120 pies",
      hit_dc: "+5",
      damage_dice: "1d6+3",
      damage_type: "perforante",
      notes: "Arrojadiza",
      proficient: true,
    },
  ],
  features: [
    {
      id: "feat_1",
      name: "Sentido Divino",
      source: "Paladín (Clase)",
      description: "Detectas presencia de celestiales, infernales o muertos vivientes.",
      uses_max: 4,
      uses_current: 2,
      recharge: "Descanso Largo",
      origin: "class",
    },
    {
      id: "feat_2",
      name: "Imposición de Manos",
      source: "Paladín (Clase)",
      description: "Reserva curativa sagrada igual a Nivel × 5 (20 PV).",
      uses_max: 20,
      uses_current: 15,
      recharge: "Descanso Largo",
      origin: "class",
    },
  ],
  sessions: [
    {
      id: 1,
      date: "14 de Flamerule, 1492 CV",
      title: "El Asedio de Phandalin",
      summary: "Emboscada exitosa contra los trasgos.",
      loot: "50 po, Poción de Curación",
      xp_gained: 450,
      session_id: "sess_mock",
    },
  ],
  network_nodes: [
    { id: "node_1", name: "Artanis", role: "Protagonista", description: "Héroe juramentado", x: 100, y: 150 },
    { id: "node_2", name: "Lord Saren", role: "Némesis", description: "Caballero caído", x: 350, y: 150 },
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
    return (
      typeof window !== "undefined" &&
      typeof window.pywebview?.api?.list_characters === "function"
    );
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

  async uploadCharacterPortrait(charId: number): Promise<{ success: boolean; portrait_path?: string; portrait_base64?: string; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.upload_character_portrait(charId);
    return { success: false, error: "Función de diálogo nativo disponible solo en escritorio." };
  },

  async setCharacterPortraitBase64(charId: number, imageBase64: string): Promise<{ success: boolean; portrait_base64?: string; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.set_character_portrait_base64(charId, imageBase64);
    if (mockActiveCharacter) {
      mockActiveCharacter = { ...mockActiveCharacter, portrait_base64: imageBase64 };
    }
    return { success: true, portrait_base64: imageBase64, character: mockActiveCharacter };
  },

  async generateAiPortrait(params: {
    prompt: string;
    provider?: string;
    apiKey?: string;
    apiUrl?: string;
    model?: string;
  }): Promise<{ success: boolean; image_base64?: string; error?: string }> {
    if (this.isNative()) {
      return await window.pywebview!.api.generate_ai_portrait(
        params.prompt,
        params.provider || "google",
        params.apiKey || "",
        params.apiUrl || "",
        params.model || ""
      );
    }
    return {
      success: false,
      error: "Para generar imágenes por IA directamente, utiliza la aplicación de escritorio.",
    };
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

  async reinstallTaleSpireSymbiote(): Promise<{ success: boolean; message?: string; error?: string }> {
    if (this.isNative() && window.pywebview?.api?.reinstall_talespire_symbiote) {
      return await window.pywebview.api.reinstall_talespire_symbiote();
    }
    return { success: true, message: "Symbiote cargado (modo navegador)" };
  },

  async openTaleSpireSymbiotesFolder(): Promise<{ success: boolean; error?: string }> {
    if (this.isNative() && window.pywebview?.api?.open_talespire_symbiotes_folder) {
      return await window.pywebview.api.open_talespire_symbiotes_folder();
    }
    return { success: true };
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

  async exportPdf(charId: number): Promise<{ success: boolean; path?: string; error?: string; cancelled?: boolean }> {
    if (this.isNative()) return await window.pywebview!.api.export_character_pdf(charId);
    return { success: true, path: "C:/fake/path/Artanis_Sheet.pdf" };
  },

  // --- Compendio OKF ---
  async getCompendiumCategories(lang: string = "es"): Promise<CompendiumCategory[]> {
    if (this.isNative()) return await window.pywebview!.api.get_compendium_categories(lang);
    return [
      { id: "clases", label: lang === "en" ? "Classes & Subclasses" : "Clases y Subclases", count: 70 },
      { id: "especies_y_linajes", label: lang === "en" ? "Species & Lineages" : "Especies y Linajes", count: 10 },
      { id: "conjuros", label: lang === "en" ? "Spell Grimoire" : "Grimorio de Conjuros", count: 380 },
      { id: "trasfondos", label: lang === "en" ? "Backgrounds" : "Trasfondos", count: 17 },
      { id: "dotes", label: lang === "en" ? "Character Feats" : "Dotes", count: 75 },
      { id: "equipo_y_armamento", label: lang === "en" ? "Equipment & Weapons" : "Equipo y Armamento", count: 4 },
      { id: "reglas_y_mecanicas", label: lang === "en" ? "Rules & Mechanics" : "Reglas y Mecánicas", count: 5 },
    ];
  },

  async searchCompendium(query: string, category?: string, lang: string = "es"): Promise<CompendiumSearchResult[]> {
    if (this.isNative()) return await window.pywebview!.api.search_compendium(query, category, lang);
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

  async getCompendiumEntry(category: string, entryName: string, lang: string = "es"): Promise<any> {
    if (this.isNative()) return await window.pywebview!.api.get_compendium_entry(category, entryName, lang);
    return {
      name: entryName,
      category,
      content: `# ${entryName}\n\nDescripción detallada de reglas simulada para previsualización web.`,
    };
  },

  // --- Creador de Personajes & Reglas ---
  async getBuilderCatalog(edition: string = "5.5e", lang: string = "es"): Promise<BuilderCatalog> {
    if (this.isNative()) return await window.pywebview!.api.get_builder_catalog(edition, lang);
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
      ],
      backgrounds: [
        { name: "Soldado", skills: ["Atletismo", "Intimidación"], feature_name: "Rango Militar", feature_desc: "Reconocimiento y alojamiento en campamentos afines." },
        { name: "Sabio", skills: ["Conocimiento Arcano", "Historia"], feature_name: "Investigador", feature_desc: "Sabes dónde encontrar cualquier manuscrito o fuente." },
      ],
      all_skills: [
        "Acrobacias", "Atletismo", "Conocimiento Arcano", "Engaño", "Historia",
        "Interpretación", "Intimidación", "Investigación", "Juego de Manos", "Medicina",
        "Naturaleza", "Percepción", "Perspicacia", "Persuasión", "Religión",
        "Sigilo", "Supervivencia", "Trato con Animales"
      ],
    };
  },

  async getAvailableSpells(options: {
    className?: string;
    maxLevel?: number;
    level?: number;
    query?: string;
    school?: string;
    lang?: string;
  } = {}): Promise<SpellItemData[]> {
    if (this.isNative()) {
      const res = await window.pywebview!.api.get_available_spells(
        options.className || null,
        options.maxLevel ?? null,
        options.query || "",
        options.school || null,
        options.level ?? null,
        150,
        options.lang || "es"
      );
      return Array.isArray(res) ? res : [];
    }
    let filtered = [...mockActiveCharacter.spells];
    if (options.level !== undefined) filtered = filtered.filter((s) => s.level === options.level);
    if (options.query) filtered = filtered.filter((s) => s.name.toLowerCase().includes(options.query!.toLowerCase()));
    return filtered;
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

  async syncCharacterFeatures(charId: number, lang: string = "es"): Promise<{ success: boolean; character?: CharacterSheetData; error?: string }> {
    if (this.isNative()) return await window.pywebview!.api.sync_character_features(charId, lang);
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
      language: ((localStorage.getItem("dnd_sanctum_lang") as "es" | "en") || "es"),
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

  // =========================================================================
  // DM ONLINE & CLOUDFLARE TUNNELS
  // =========================================================================

  async startDmSession(name: string = "Sesión de Campaña", campaignName: string = "Campaña Principal", sessionId?: string): Promise<DmSessionStatus> {
    if (this.isNative()) return await window.pywebview!.api.start_dm_session(name, campaignName, sessionId);
    return {
      is_running: true,
      session_id: sessionId || "mock_session_1",
      session_name: name,
      campaign_name: campaignName,
      tunnel_url: "https://parma-preview.trycloudflare.com",
      qr_code: "",
      port: 8765,
      players: [],
      connected_count: 0,
    };
  },

  async dmListSessions(): Promise<any[]> {
    if (this.isNative()) return await window.pywebview!.api.dm_list_sessions();
    return [];
  },

  async stopDmSession(): Promise<{ success: boolean }> {
    if (this.isNative()) return await window.pywebview!.api.stop_dm_session();
    return { success: true };
  },

  async getDmSessionStatus(): Promise<DmSessionStatus> {
    if (this.isNative()) return await window.pywebview!.api.get_dm_session_status();
    return {
      is_running: false,
      session_id: null,
      session_name: "Sesión",
      campaign_name: "Campaña Principal",
      tunnel_url: null,
      qr_code: "",
      port: 8765,
      players: [],
      connected_count: 0,
    };
  },

  async dmApplyHpChange(playerToken: string, delta: number): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.dm_apply_hp_change(playerToken, delta);
    return true;
  },

  async dmGiftItem(playerToken: string, item: DmHomebrewItem): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.dm_gift_item(playerToken, item);
    return true;
  },

  async dmListHomebrewItems(): Promise<DmHomebrewItem[]> {
    if (this.isNative()) return await window.pywebview!.api.dm_list_homebrew_items();
    return [];
  },

  async dmSaveHomebrewItem(item: DmHomebrewItem): Promise<string> {
    if (this.isNative()) return await window.pywebview!.api.dm_save_homebrew_item(item);
    return "hb_mock_1";
  },

  async dmDeleteHomebrewItem(itemId: string): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.dm_delete_homebrew_item(itemId);
    return true;
  },

  async dmGetSessionLogs(sessionId?: string): Promise<DmSessionEventLog[]> {
    if (this.isNative()) return await window.pywebview!.api.dm_get_session_logs(sessionId);
    return [];
  },

  async dmSaveSessionNotes(notes: string, sessionId?: string): Promise<boolean> {
    if (this.isNative()) return await window.pywebview!.api.dm_save_session_notes(notes, sessionId);
    return true;
  },

  async dmGetSessionNotes(sessionId?: string): Promise<string> {
    if (this.isNative()) return await window.pywebview!.api.dm_get_session_notes(sessionId);
    return "";
  },
};
