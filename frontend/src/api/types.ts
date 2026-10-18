export interface CharacterSummary {
  id: number;
  name: string;
  char_class: string;
  subclass?: string;
  level: number;
  race: string;
  hp_current: number;
  hp_max: number;
  portrait_path?: string;
  is_active: number;
  updated_at: string;
}

export interface AbilityScoreData {
  base: number;
  override: number;
  bonus: number;
  proficient: boolean;
  save_bonus: number;
}

export interface WeaponActionData {
  name: string;
  type: string;
  range_val: string;
  hit_dc: string;
  damage_dice: string;
  damage_type: string;
  notes: string;
  proficient?: boolean;
}

export interface SpellItemData {
  id?: string;
  name: string;
  name_en?: string;
  level: number;
  school: string;
  cast_time: string;
  casting_time?: string;
  range_area: string;
  range?: string;
  components: string;
  duration: string;
  prepared: boolean;
  notes: string;
  description?: string;
  concentration?: boolean;
  ritual?: boolean;
  classes?: string[];
  higher_levels?: string;
  source?: string;
  snippet?: string;
}

export interface FeatureItemData {
  id?: string;
  name: string;
  source: string;
  description: string;
  uses_max?: number;
  uses_current?: number;
  recharge?: string;
}

export interface SpellStatsData {
  ability: string;
  dc: number;
  attack_bonus: number;
  is_caster?: boolean;
}

export interface SessionLogData {
  id: number;
  date: string;
  title: string;
  summary: string;
  loot: string;
  xp_gained: number;
}

export interface NetworkNodeData {
  id: string;
  name: string;
  role: string;
  description: string;
  avatar_base64?: string;
  x: number;
  y: number;
}

export interface NetworkEdgeData {
  source_id: string;
  target_id: string;
  relation: string;
}

export interface CharacterSheetData {
  id?: number;
  name: string;
  char_class: string;
  subclass: string;
  level: number;
  race: string;
  subrace?: string;
  background: string;
  alignment: string;
  xp: number;
  inspiration: boolean;
  proficiency_bonus: number;
  ac: number;
  speed: number;
  initiative: number;
  hp_current: number;
  hp_max: number;
  hp_temp: number;
  hit_dice_total: string;
  hit_dice_current: string;
  hit_dice_max?: number;
  hit_dice_faces?: number;
  death_save_successes: number;
  death_save_failures: number;
  conditions?: string[];
  abilities: Record<string, AbilityScoreData>;
  skills: Record<string, { proficient: boolean; bonus: number; expertise: boolean }>;
  spells: SpellItemData[];
  spell_slots_total: Record<string, number>;
  spell_slots_used: Record<string, number>;
  spell_stats?: SpellStatsData;
  weapon_actions: WeaponActionData[];
  features: FeatureItemData[];
  sessions: SessionLogData[];
  network_nodes: NetworkNodeData[];
  network_edges: NetworkEdgeData[];
  senses?: string;
  languages?: string;
  portrait_path?: string;
  portrait_base64?: string;
  theme_override?: string;
}

export interface TaleSpireStatus {
  is_installed: boolean;
  is_running: boolean;
  is_connected: boolean;
  state_label: string;
}

export type RollMode = "normal" | "advantage" | "disadvantage";

export interface RollRequest {
  dice: Record<string, number>; // ej: { "20": 1, "6": 2 }
  modifier: number;
  label: string;
  mode?: RollMode;
  send_to_talespire?: boolean;
  dc?: number;
  is_saving_throw?: boolean;
  is_death_save?: boolean;
}

export interface RollResult {
  total: number;
  dice_rolls: Array<{ sides: number; roll: number }>;
  modifier: number;
  label: string;
  formula?: string;
  detail?: string;
  is_crit?: boolean;
  is_fumble?: boolean;
  mode?: RollMode;
  timestamp: string;
  talespire_sent: boolean;
  dc?: number;
  is_saving_throw?: boolean;
  is_death_save?: boolean;
  success?: boolean;
  success_count?: number;
  failure_count?: number;
}

export interface RollHistoryEntry {
  id: number;
  time_str: string;
  character_name: string;
  reason: string;
  formula: string;
  detail: string;
  total: number;
  is_crit: boolean;
  is_fumble: boolean;
  channel: string;
}

export interface PdfDocumentSummary {
  name: string;
  path: string;
}

export interface PdfTocItem {
  level: number;
  title: string;
  page: number;
}

export interface PdfDocumentInfo {
  success: boolean;
  path: string;
  filename: string;
  page_count: number;
  toc: PdfTocItem[];
  error?: string;
}

export interface PdfLinkItem {
  rect: [number, number, number, number];
  target_page: number;
}

export interface PdfPageRenderResult {
  success: boolean;
  page_num: number;
  image_base64?: string;
  links?: PdfLinkItem[];
  width?: number;
  height?: number;
  error?: string;
}

export interface CompendiumCategory {
  id: string;
  label: string;
  count: number;
}

export interface CompendiumSearchResult {
  id: string;
  name: string;
  category: string;
  snippet: string;
  path: string;
}

export interface AppSettings {
  theme: string;
  dnd_edition?: string;
  talespire_mode: "dm" | "player";
  talespire_enabled: boolean;
  okf_path: string;
  custom_themes_dir: string;
}

export interface ThemeOption {
  id: string;
  name: string;
  is_dark: boolean;
}

export interface BuilderSpeciesItem {
  name: string;
  subraces: string[];
  speed: number;
  bonuses: Record<string, number>;
  traits: Array<{ name: string; desc: string }>;
}

export interface BuilderClassItem {
  name: string;
  hit_die: number;
  primary_ability: string;
  saves: string[];
  skill_choices_count: number;
  skill_options: string[];
  subclasses: string[];
  subclass_unlock_level: number;
  is_caster: boolean;
}

export interface BuilderBackgroundItem {
  name: string;
  skills: string[];
  feature_name: string;
  feature_desc: string;
}

export interface BuilderCatalog {
  edition: string;
  species: BuilderSpeciesItem[];
  classes: BuilderClassItem[];
  backgrounds: BuilderBackgroundItem[];
  all_skills: string[];
}

export interface PointBuyValidationResult {
  valid: boolean;
  points_spent: number;
  points_remaining: number;
  can_increment?: Record<string, boolean>;
  can_decrement?: Record<string, boolean>;
  error?: string;
  standard_array: number[];
}
