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
}

export interface SpellItemData {
  name: string;
  level: number;
  school: string;
  cast_time: string;
  range_area: string;
  components: string;
  duration: string;
  prepared: boolean;
  notes: string;
}

export interface CharacterSheetData {
  id?: number;
  name: string;
  char_class: string;
  subclass: string;
  level: number;
  race: string;
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
  death_save_successes: number;
  death_save_failures: number;
  abilities: Record<string, AbilityScoreData>;
  skills: Record<string, { proficient: boolean; bonus: number; expertise: boolean }>;
  spells: SpellItemData[];
  spell_slots_total: Record<string, number>;
  spell_slots_used: Record<string, number>;
  weapon_actions: WeaponActionData[];
  features: Array<{ name: string; source: string; description: string }>;
  portrait_path?: string;
}

export interface TaleSpireStatus {
  is_installed: boolean;
  is_running: boolean;
  is_connected: boolean;
  state_label: string;
}

export interface RollRequest {
  dice: Record<string, number>; // ej: { "20": 1, "6": 2 }
  modifier: number;
  label: string;
  send_to_talespire?: boolean;
}

export interface RollResult {
  total: number;
  dice_rolls: Array<{ sides: number; roll: number }>;
  modifier: number;
  label: string;
  timestamp: string;
  talespire_sent: boolean;
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
