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
  session_id?: string;
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
  school_en?: string;
  cast_time: string;
  casting_time?: string;
  range_area: string;
  range?: string;
  components: string;
  duration: string;
  prepared: boolean;
  notes: string;
  notes_en?: string;
  description?: string;
  description_en?: string;
  concentration?: boolean;
  ritual?: boolean;
  classes?: string[];
  higher_levels?: string;
  source?: string;
  snippet?: string;
}

export interface SpellStatsData {
  casting_ability: string;
  spell_save_dc: number;
  spell_attack_bonus: number;
  ability_mod: number;
}

export interface FeatureItemData {
  id?: string;
  name: string;
  name_en?: string;
  source: string;
  source_en?: string;
  description: string;
  description_en?: string;
  uses_max?: number;
  uses_current?: number;
  recharge?: string;
  origin?: "class" | "subclass" | "species" | "background" | "feat" | "custom";
}

export interface SessionLogData {
  id?: number;
  date: string;
  title: string;
  summary: string;
  loot?: string;
  xp_gained?: number;
  session_id?: string;
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
  session_id?: string;
  network_nodes: NetworkNodeData[];
  network_edges: NetworkEdgeData[];
  senses?: string;
  languages?: string;
  proficiencies_extra?: string;
  appearance?: string;
  history?: string;
  personality_traits?: string;
  ideals?: string;
  bonds?: string;
  flaws?: string;
  portrait_path?: string;
  portrait_base64?: string;
  theme_override?: string;
}

export interface TaleSpireStatus {
  is_installed: boolean;
  is_running: boolean;
  is_connected: boolean;
  state_label: string;
  symbiote_connected?: boolean;
  symbiote_folder_installed?: boolean;
  symbiote_install_path?: string | null;
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
  lang?: "es" | "en" | "all";
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
  total_pages?: number;
  toc: PdfTocItem[];
  error?: string;
}

export interface PdfLinkItem {
  rect: [number, number, number, number];
  target_page?: number;
  uri?: string;
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
  language?: "es" | "en";
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

export interface DmSessionPlayer {
  session_id: string;
  player_token: string;
  character_id?: number;
  character_name: string;
  character_class?: string;
  character_level: number;
  hp_current: number;
  hp_max: number;
  ac: number;
  status: "ALIVE" | "UNCONSCIOUS" | "DEAD";
  joined_at: string;
  last_seen_at: string;
  is_online?: boolean;
  data_json?: string;
}

export interface DmSessionStatus {
  is_running: boolean;
  session_id: string | null;
  session_name: string;
  campaign_name: string;
  tunnel_url: string | null;
  qr_code: string;
  port: number;
  players: DmSessionPlayer[];
  connected_count: number;
}

export interface DmHomebrewItem {
  id?: string;
  name: string;
  category: "weapon" | "armor" | "wondrous" | "potion" | "ring" | "scroll" | "wand";
  rarity: "common" | "uncommon" | "rare" | "very_rare" | "legendary" | "artifact";
  requires_attunement: boolean;
  damage_dice?: string;
  damage_type?: string;
  secondary_dice?: string;
  secondary_type?: string;
  bonus_attack?: number;
  bonus_damage?: number;
  ac_bonus?: number;
  properties?: string[];
  description: string;
  created_at?: string;
}

export interface DmSessionEventLog {
  id: number;
  session_id: string;
  timestamp: string;
  event_type: string;
  actor_name: string;
  target_name?: string;
  details: Record<string, any>;
}
