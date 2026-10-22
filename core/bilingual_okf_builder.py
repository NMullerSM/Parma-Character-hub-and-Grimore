"""
Motor de Generación y Sincronización Bilingüe para el Compendio OKF (Open Knowledge Format) D&D 5e.
Clona, traduce y cataloga entidades en Español e Inglés con tags 'spanish' y 'english'.
Combina la base de datos oficial SRD 5e (2024 & 2014) con el motor semántico de reglas.
"""
import os
import sys
import json
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OKF_DIR = os.path.join(BASE_DIR, "okf_dnd5e")
INDEX_PATH = os.path.join(OKF_DIR, "index_metadata.json")
SRD_DIR = os.path.join(BASE_DIR, "data", "srd_en")

# Diccionarios de mapeo canónico
SCHOOLS_MAP = {
    "abjuración": "Abjuration",
    "abjuracion": "Abjuration",
    "conjuración": "Conjuration",
    "conjuracion": "Conjuration",
    "adivinación": "Divination",
    "adivinacion": "Divination",
    "encantamiento": "Enchantment",
    "evocación": "Evocation",
    "evocacion": "Evocation",
    "ilusión": "Illusion",
    "ilusion": "Illusion",
    "ilusionismo": "Illusion",
    "nigromancia": "Necromancy",
    "transmutación": "Transmutation",
    "transmutacion": "Transmutation",
}

CLASSES_MAP = {
    "bárbaro": "Barbarian",
    "barbaro": "Barbarian",
    "bardo": "Bard",
    "clérigo": "Cleric",
    "clerigo": "Cleric",
    "druida": "Druid",
    "guerrero": "Fighter",
    "monje": "Monk",
    "paladín": "Paladin",
    "paladin": "Paladin",
    "explorador": "Ranger",
    "pícaro": "Rogue",
    "picaro": "Rogue",
    "hechicero": "Sorcerer",
    "brujo": "Warlock",
    "mago": "Wizard",
    "artífice": "Artificer",
    "artifice": "Artificer",
}

SPECIES_MAP = {
    "humano": "Human",
    "elfo": "Elf",
    "enano": "Dwarf",
    "mediano": "Halfling",
    "gnomo": "Gnome",
    "dracónido": "Dragonborn",
    "draconido": "Dragonborn",
    "tiefling": "Tiefling",
    "orco": "Orc",
    "goliat": "Goliath",
    "aasimar": "Aasimar",
    "semielfo": "Half-Elf",
    "semiorco": "Half-Orc",
    # Linajes
    "alto elfo": "High Elf",
    "elfo de los bosques": "Wood Elf",
    "drow": "Drow",
    "enano de las colinas": "Hill Dwarf",
    "enano de las montañas": "Mountain Dwarf",
    "mediano piesligeros": "Lightfoot Halfling",
    "mediano fornido": "Stout Halfling",
    "gnomo de las rocas": "Rock Gnome",
    "gnomo de los bosques": "Forest Gnome",
    "linaje infernal": "Infernal Lineage",
    "linaje abisal": "Abyssal Lineage",
    "linaje ctónico": "Chthonic Lineage",
}

FEATS_MAP = {
    "afortunado": "Lucky",
    "toque feérico": "Fey Touched",
    "toque feerico": "Fey Touched",
    "don del ataque imparable": "Boon of the Unstoppable Attack",
    "don del destino": "Boon of Fate",
    "don del espíritu de la noche": "Boon of the Night Spirit",
    "don del espiritu de la noche": "Boon of the Night Spirit",
    "don del viaje dimensional": "Boon of Dimensional Travel",
    "don de la fortaleza": "Boon of Fortitude",
    "don de la habilidad": "Boon of Skill",
    "don de la pericia en combate": "Boon of Combat Prowess",
    "don de la recuperación": "Boon of Recovery",
    "don de la recuperacion": "Boon of Recovery",
    "don de la resistencia a energías": "Boon of Energy Resistance",
    "don de la resistencia a energias": "Boon of Energy Resistance",
    "don de la velocidad": "Boon of Speed",
    "don de la visión verdadera": "Boon of Truesight",
    "don de la vision verdadera": "Boon of Truesight",
    "combate con armas arrojadizas": "Thrown Weapon Fighting",
    "combate con armas a dos manos": "Great Weapon Fighting",
    "combate con dos armas": "Two-Weapon Fighting",
    "combate sin armas": "Unarmed Fighting",
    "defensa": "Defense",
    "duelo": "Dueling",
    "intercepción": "Interception",
    "intercepcion": "Interception",
    "lucha a ciegas": "Blind Fighting",
    "protección": "Protection",
    "proteccion": "Protection",
    "tiro con arco": "Archery",
    "acechador": "Skulker",
    "actor": "Actor",
    "alerta": "Alert",
    "atleta": "Athlete",
    "iniciación mágica": "Magic Initiate",
    "iniciacion magica": "Magic Initiate",
    "músico": "Musician",
    "musico": "Musician",
    "robusto": "Tough",
    "curandero": "Healer",
    "tirador certero": "Sharpshooter",
    "maestro en armas grandes": "Great Weapon Master",
    "centinela": "Sentinel",
    "combatiente con escudo": "Shield Master",
    "lanzador de conjuros de guerra": "War Caster",
    "rebanador": "Slasher",
    "aplastador": "Crusher",
    "perforador": "Piercer",
    "lanzador de conjuros rituales": "Ritual Caster",
    "resiliente": "Resilient",
    "observador": "Observant",
    "mente aguda": "Keen Mind",
    "líder inspirador": "Inspiring Leader",
    "lider inspirador": "Inspiring Leader",
    "movilidad": "Mobile",
    "matón": "Tavern Brawler",
    "maton": "Tavern Brawler",
    "experto en venenos": "Poisoner",
    "telequinético": "Telekinetic",
    "telequinetico": "Telekinetic",
    "telepático": "Telepathic",
    "telepatico": "Telepathic",
    "iniciado en sombras": "Shadow Touched",
    "especialista en ballestas": "Crossbow Expert",
    "maestro de armas de asta": "Polearm Master",
    "duelista defensivo": "Defensive Duelist",
    "acechador de mazmorras": "Dungeon Delver",
}

BACKGROUNDS_MAP = {
    "acólito": "Acolyte",
    "acolito": "Acolyte",
    "artesano gremial": "Guild Artisan",
    "charlatán": "Charlatan",
    "charlatan": "Charlatan",
    "criminal": "Criminal",
    "erudito": "Sage",
    "ermitaño": "Hermit",
    "ermitano": "Hermit",
    "forastero": "Outlander",
    "granjero": "Farmer",
    "guardia": "Guard",
    "guía": "Guide",
    "guia": "Guide",
    "héroe del pueblo": "Folk Hero",
    "heroe del pueblo": "Folk Hero",
    "huérfano": "Urchin",
    "huerfano": "Urchin",
    "marinero": "Sailor",
    "noble": "Noble",
    "salvaje": "Wayfarer",
    "escriba": "Scribe",
    "soldado": "Soldier",
    "mercader": "Merchant",
}

RULES_MAP = {
    "acciones en combate": "Actions in Combat",
    "condiciones y estados": "Conditions & States",
    "descansos": "Resting Rules",
    "lanzamiento de conjuros": "Spellcasting Rules",
    "tiradas de salvacion y ataque": "Attack Rolls & Saving Throws",
}

EQUIPMENT_MAP = {
    "armaduras": "Armor & Shields",
    "armas": "Weapons & Masteries",
    "equipo de aventurero": "Adventuring Gear",
    "herramientas": "Tools & Kits",
}

def load_ts_maps() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Carga los mapas canónicos desde dndTranslations.ts."""
    ts_path = os.path.join(BASE_DIR, "frontend", "src", "i18n", "dndTranslations.ts")
    spells_map = {}
    subclasses_map = {}
    if os.path.exists(ts_path):
        with open(ts_path, "r", encoding="utf-8") as f:
            content = f.read()

        sp_match = re.search(r"export const SPELLS_MAP: Record<string, string> = {([^}]+)};", content, re.DOTALL)
        if sp_match:
            for line in sp_match.group(1).splitlines():
                m = re.match(r'^\s*"([^"]+)":\s*"([^"]+)",?', line)
                if m:
                    spells_map[m.group(1).lower().strip()] = m.group(2).strip()

        sub_match = re.search(r"export const SUBCLASSES_MAP: Record<string, string> = {([^}]+)};", content, re.DOTALL)
        if sub_match:
            for line in sub_match.group(1).splitlines():
                m = re.match(r'^\s*"([^"]+)":\s*"([^"]+)",?', line)
                if m:
                    subclasses_map[m.group(1).lower().strip()] = m.group(2).strip()

    return spells_map, subclasses_map

SPELLS_MAP, SUBCLASSES_MAP = load_ts_maps()

# Cargar el repositorio oficial SRD en memoria para máxima fidelidad
SRD_SPELLS: Dict[str, Dict[str, Any]] = {}
SRD_FEATS: Dict[str, Dict[str, Any]] = {}

def load_official_srd_data():
    global SRD_SPELLS, SRD_FEATS
    for year in ["2024", "2014"]:
        spells_file = os.path.join(SRD_DIR, year, "5e-SRD-Spells.json")
        if os.path.exists(spells_file):
            try:
                with open(spells_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        name_key = item.get("name", "").lower().strip()
                        index_key = item.get("index", "").lower().strip()
                        if name_key and name_key not in SRD_SPELLS:
                            SRD_SPELLS[name_key] = item
                        if index_key and index_key not in SRD_SPELLS:
                            SRD_SPELLS[index_key] = item
            except Exception as e:
                print(f"[BilingualOKF] Error al cargar {spells_file}: {e}")

        feats_file = os.path.join(SRD_DIR, year, "5e-SRD-Feats.json")
        if os.path.exists(feats_file):
            try:
                with open(feats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        name_key = item.get("name", "").lower().strip()
                        index_key = item.get("index", "").lower().strip()
                        if name_key and name_key not in SRD_FEATS:
                            SRD_FEATS[name_key] = item
                        if index_key and index_key not in SRD_FEATS:
                            SRD_FEATS[index_key] = item
            except Exception as e:
                print(f"[BilingualOKF] Error al cargar {feats_file}: {e}")

load_official_srd_data()
print(f"[BilingualOKF] SRD oficial cargado: {len(SRD_SPELLS)} conjuros, {len(SRD_FEATS)} dotes.")

def translate_time(val: Any) -> str:
    s = str(val or "1 acción").strip()
    s_low = s.lower()
    if "adicional" in s_low or "bonus" in s_low:
        return "1 bonus action"
    if "reacción" in s_low or "reaccion" in s_low or "reaction" in s_low:
        return "1 reaction"
    if "acción" in s_low or "accion" in s_low or "action" in s_low:
        return "1 action"
    if "10 minuto" in s_low:
        return "10 minutes"
    if "1 minuto" in s_low:
        return "1 minute"
    if "1 hora" in s_low:
        return "1 hour"
    if "8 hora" in s_low:
        return "8 hours"
    if "24 hora" in s_low:
        return "24 hours"
    return s

def translate_range(val: Any) -> str:
    s = str(val or "18 m").strip()
    s_low = s.lower()
    if "personal" in s_low or "self" in s_low:
        return "Self"
    if "toque" in s_low or "touch" in s_low:
        return "Touch (1 tile)"
    if re.search(r'\b150\s*(?:m|metros|metro)\b', s_low) or "500 pie" in s_low:
        return "500 ft (100 tiles)"
    if re.search(r'\b90\s*(?:m|metros|metro)\b', s_low) or "300 pie" in s_low:
        return "300 ft (60 tiles)"
    if re.search(r'\b45\s*(?:m|metros|metro)\b', s_low) or "150 pie" in s_low:
        return "150 ft (30 tiles)"
    if re.search(r'\b36\s*(?:m|metros|metro)\b', s_low) or "120 pie" in s_low:
        return "120 ft (24 tiles)"
    if re.search(r'\b27\s*(?:m|metros|metro)\b', s_low) or "90 pie" in s_low:
        return "90 ft (18 tiles)"
    if re.search(r'\b18\s*(?:m|metros|metro)\b', s_low) or "60 pie" in s_low:
        return "60 ft (12 tiles)"
    if re.search(r'\b9\s*(?:m|metros|metro)\b', s_low) or "30 pie" in s_low:
        return "30 ft (6 tiles)"
    if re.search(r'\b6\s*(?:m|metros|metro)\b', s_low) or "20 pie" in s_low:
        return "20 ft (4 tiles)"
    if re.search(r'\b4\.5\s*(?:m|metros|metro)\b', s_low) or "15 pie" in s_low:
        return "15 ft (3 tiles)"
    if re.search(r'\b3\s*(?:m|metros|metro)\b', s_low) or "10 pie" in s_low:
        return "10 ft (2 tiles)"
    if re.search(r'\b1\.5\s*(?:m|metros|metro)\b', s_low) or "5 pie" in s_low:
        return "5 ft (1 tile)"
    if "visual" in s_low or "vista" in s_low or "sight" in s_low:
        return "Sight"
    if "ilimitado" in s_low or "unlimited" in s_low:
        return "Unlimited"
    if "especial" in s_low or "special" in s_low:
        return "Special"
    return s

def translate_duration(val: Any) -> str:
    s = str(val or "Instantáneo").strip()
    s_low = s.lower()
    is_conc = "concentra" in s_low
    base = ""
    if "instant" in s_low:
        return "Instantaneous"
    if "1 minuto" in s_low or "1 min" in s_low:
        base = "1 minute"
    elif "10 minuto" in s_low or "10 min" in s_low:
        base = "10 minutes"
    elif "1 hora" in s_low or "1 hr" in s_low:
        base = "1 hour"
    elif "8 hora" in s_low or "8 hr" in s_low:
        base = "8 hours"
    elif "24 hora" in s_low or "24 hr" in s_low:
        base = "24 hours"
    elif "1 asalto" in s_low or "1 round" in s_low:
        base = "1 round"
    elif "hasta que se disipe" in s_low or "until dispelled" in s_low:
        return "Until dispelled"
    elif "especial" in s_low:
        return "Special"
    else:
        base = s

    if is_conc:
        return f"Concentration, up to {base}" if "up to" not in base else f"Concentration, {base}"
    return base

def translate_components(val: Any) -> str:
    s = str(val or "V, S").strip()
    s = re.sub(r'\(una pizca de fósforo\)', '(a pinch of phosphorus)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(un trozo de vellón\)', '(a bit of fleece)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(polvo de diamante por valor de (\d+) po\)', r'(diamond dust worth \1 gp)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(un diamante por valor de (\d+) po\)', r'(a diamond worth \1 gp)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(una pluma de búho\)', '(an owl feather)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(una gota de sangre\)', '(a drop of blood)', s, flags=re.IGNORECASE)
    s = re.sub(r'\(una pestaña atrapada en goma\)', '(an eyelash encased in gum)', s, flags=re.IGNORECASE)
    return s

def translate_markdown_body(body: str, entity_name_en: str, entity_type: str, srd_entry: Optional[Dict[str, Any]] = None) -> str:
    """
    Traduce el cuerpo Markdown al inglés de D&D 5e:
    1. Si existe entrada oficial SRD en inglés, usa la descripción canónica de Wizards of the Coast.
    2. Si es contenido ampliado o personalizado, aplica traducción léxica y sintáctica precisa de D&D 5e.
    """
    if srd_entry:
        desc_list = srd_entry.get("description") or srd_entry.get("desc")
        if desc_list:
            if isinstance(desc_list, list):
                main_desc = "\n\n".join(str(d) for d in desc_list)
            else:
                main_desc = str(desc_list)

            hl = srd_entry.get("higher_level") or srd_entry.get("higher_levels")
            if hl:
                hl_str = "\n\n".join(str(h) for h in hl) if isinstance(hl, list) else str(hl)
                return f"# {entity_name_en}\n\n{main_desc}\n\n### At Higher Levels\n{hl_str}"
            return f"# {entity_name_en}\n\n{main_desc}"

    if not body:
        return f"# {entity_name_en}\n\nOfficial D&D 5e compendium entry."

    lines = body.splitlines()
    translated_lines = []

    for line in lines:
        t_line = line

        # Encabezados principales
        if t_line.startswith("# "):
            t_line = f"# {entity_name_en}"
        elif t_line.startswith("## Rasgos de Subclase"):
            t_line = "## Subclass Features"
        elif t_line.startswith("## Rasgos de Clase"):
            t_line = "## Class Features"
        elif t_line.startswith("## Características de Especie") or t_line.startswith("## Rasgos Principales"):
            t_line = "## Core Species Traits"
        elif t_line.startswith("## Subclases Disponibles"):
            t_line = "## Available Subclasses"
        elif t_line.startswith("### Nivel "):
            t_line = re.sub(r"### Nivel (\d+):?", r"### Level \1:", t_line)

        # Metadatos en formato viñetas
        t_line = re.sub(r"- \*\*Característica Principal\*\*:", "- **Primary Ability**:", t_line)
        t_line = re.sub(r"- \*\*Dado de Puntos de Golpe\*\*:", "- **Hit Die**:", t_line)
        t_line = re.sub(r"- \*\*Tiradas de Salvación con Competencia\*\*:", "- **Saving Throw Proficiencies**:", t_line)
        t_line = re.sub(r"- \*\*Competencias con Armaduras\*\*:", "- **Armor Proficiencies**:", t_line)
        t_line = re.sub(r"- \*\*Competencias con Armas\*\*:", "- **Weapon Proficiencies**:", t_line)
        t_line = re.sub(r"- \*\*Habilidades Competentes\*\*:", "- **Skill Proficiencies**:", t_line)
        t_line = re.sub(r"- \*\*Dote Concedida\*\*:", "- **Granted Feat**:", t_line)
        t_line = re.sub(r"- \*\*Herramientas\*\*:", "- **Tool Proficiencies**:", t_line)
        t_line = re.sub(r"- \*\*Equipo Inicial\*\*:", "- **Equipment**:", t_line)

        # Reglas clave y términos de juego D&D 5e
        t_line = re.sub(r"\*Dote de origen\*", "*Origin Feat*", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\*Dote general\*", "*General Feat*", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\*Dote de estilo de combate\*", "*Fighting Style Feat*", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\*Dote épica\*", "*Epic Boon Feat*", t_line, flags=re.IGNORECASE)

        # Vocabulario de combate y acción
        t_line = re.sub(r"\bCon una acción adicional\b", "As a bonus action", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bComo acción adicional\b", "As a bonus action", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bComo acción\b", "As an action", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bCon una acción\b", "As an action", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bComo reacción\b", "As a reaction", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\buna vez por turno\b", "once per turn", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\b1 vez por asalto\b", "once per round", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\b1 vez por turno\b", "once per turn", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\ba voluntad\b", "at will", t_line, flags=re.IGNORECASE)

        # Descansos y dados
        t_line = re.sub(r"\bDescanso Corto o Largo\b", "Short or Long Rest", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bDescanso Largo\b", "Long Rest", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bDescanso Corto\b", "Short Rest", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bRecarga en\b", "Recharges on", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bRecarga con\b", "Recharges on", t_line, flags=re.IGNORECASE)

        # Salvaciones y Ataques
        t_line = re.sub(r"\btirada de salvación de ([A-Za-z]+)\b", r"\1 saving throw", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\btiradas de salvación\b", "saving throws", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\btirada de salvación\b", "saving throw", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\btiradas de ataque\b", "attack rolls", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\btirada de ataque\b", "attack roll", t_line, flags=re.IGNORECASE)

        # Daños
        t_line = re.sub(r"\bdaño psíquico adicional\b", "extra psychic damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño psíquico\b", "psychic damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño contundente\b", "bludgeoning damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño perforante\b", "piercing damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño cortante\b", "slashing damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de fuego\b", "fire damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño por fuego\b", "fire damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de frío\b", "cold damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de relámpago\b", "lightning damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de trueno\b", "thunder damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño radiante\b", "radiant damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño necrótico\b", "necrotic damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de fuerza\b", "force damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de veneno\b", "poison damage", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bdaño de ácido\b", "acid damage", t_line, flags=re.IGNORECASE)

        # Puntos de golpe y estados
        t_line = re.sub(r"\bpuntos de golpe temporales\b", "temporary hit points", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bpuntos de golpe\b", "hit points", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bvisión en la oscuridad\b", "darkvision", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bInspiración Bárdica\b", "Bardic Inspiration", t_line, flags=re.IGNORECASE)
        t_line = re.sub(r"\bInspiracion Bardica\b", "Bardic Inspiration", t_line, flags=re.IGNORECASE)

        # Alcances comunes en metros a pies
        t_line = re.sub(r"\ba 18 m\b", "within 60 feet", t_line)
        t_line = re.sub(r"\ba 9 m\b", "within 30 feet", t_line)
        t_line = re.sub(r"\ba 36 m\b", "within 120 feet", t_line)
        t_line = re.sub(r"\ba 4.5 m\b", "within 15 feet", t_line)
        t_line = re.sub(r"\ba 1.5 m\b", "within 5 feet", t_line)
        t_line = re.sub(r"\ba 3 m\b", "within 10 feet", t_line)
        t_line = re.sub(r"\bradio de 6 m\b", "20-foot radius", t_line)
        t_line = re.sub(r"\bradio de 3 m\b", "10-foot radius", t_line)
        t_line = re.sub(r"\bradio de 9 m\b", "30-foot radius", t_line)

        translated_lines.append(t_line)

    return "\n".join(translated_lines)

def process_entity_file(file_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Procesa un archivo .md de OKF:
    1. Asegura que el archivo en Español tenga tag 'spanish' y idioma 'es'.
    2. Genera y guarda su contraparte bilingüe en Inglés (*_en.md) con tag 'english' y idioma 'en'.
    Retorna la tupla de metadatos (entry_es, entry_en) para el índice maestro.
    """
    rel_path = os.path.relpath(file_path, OKF_DIR).replace("\\", "/")
    if rel_path.endswith("_en.md") or rel_path.upper() == "README.MD":
        return None, None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith("---"):
            return None, None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None, None

        meta_es = yaml.safe_load(parts[1]) or {}
        body_es = parts[2].strip()

        # Determinar tipo
        tipo = meta_es.get("tipo")
        if not tipo:
            if "conjuros" in rel_path:
                tipo = "conjuro"
            elif "dotes" in rel_path:
                tipo = "dote"
            elif "subclases" in rel_path:
                tipo = "subclase"
            elif "clases" in rel_path:
                tipo = "clase"
            elif "especies" in rel_path:
                tipo = "especie"
            elif "linajes" in rel_path:
                tipo = "linaje"
            elif "trasfondos" in rel_path:
                tipo = "trasfondo"
            elif "equipo" in rel_path:
                tipo = "equipo"
            else:
                tipo = "regla"

        entity_id = meta_es.get("id", Path(file_path).stem)
        nombre_es = meta_es.get("nombre", Path(file_path).stem.replace("_", " ").title())
        nombre_es_clean = nombre_es.lower().strip()

        # Resolver nombre en inglés
        nombre_en = meta_es.get("nombre_ingles")
        if not nombre_en or nombre_en.lower() == nombre_es_clean:
            if tipo == "conjuro":
                nombre_en = SPELLS_MAP.get(nombre_es_clean, SPELLS_MAP.get(entity_id.lower(), nombre_es))
            elif tipo == "subclase":
                nombre_en = SUBCLASSES_MAP.get(nombre_es_clean, SUBCLASSES_MAP.get(entity_id.lower(), nombre_es))
            elif tipo == "clase":
                nombre_en = CLASSES_MAP.get(nombre_es_clean, nombre_es)
            elif tipo in ("especie", "linaje"):
                nombre_en = SPECIES_MAP.get(nombre_es_clean, nombre_es)
            elif tipo == "dote":
                nombre_en = FEATS_MAP.get(nombre_es_clean, nombre_es)
            elif tipo == "trasfondo":
                nombre_en = BACKGROUNDS_MAP.get(nombre_es_clean, nombre_es)
            elif tipo == "regla":
                nombre_en = RULES_MAP.get(nombre_es_clean, nombre_es)
            elif tipo == "equipo":
                nombre_en = EQUIPMENT_MAP.get(nombre_es_clean, nombre_es)
            else:
                nombre_en = nombre_es

        # Buscar coincidencia oficial en el SRD
        srd_entry = None
        if tipo == "conjuro":
            srd_entry = SRD_SPELLS.get(nombre_en.lower().strip()) or SRD_SPELLS.get(entity_id.replace("_", "-").lower())
        elif tipo == "dote":
            srd_entry = SRD_FEATS.get(nombre_en.lower().strip()) or SRD_FEATS.get(entity_id.replace("_", "-").lower())

        # 1. ACTUALIZAR ENTIDAD EN ESPAÑOL
        tags_es = list(meta_es.get("tags") or [])
        for t in ["spanish", "es", "español"]:
            if t not in tags_es:
                tags_es.append(t)

        meta_es["tags"] = tags_es
        meta_es["idioma"] = "es"
        meta_es["tipo"] = tipo
        meta_es["nombre_ingles"] = nombre_en

        # Guardar archivo en español actualizado
        new_frontmatter_es = yaml.dump(meta_es, allow_unicode=True, sort_keys=False).strip()
        new_content_es = f"---\n{new_frontmatter_es}\n---\n\n{body_es}\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content_es)

        # 2. GENERAR ENTIDAD EN INGLÉS
        en_file_path = file_path[:-3] + "_en.md"
        en_rel_path = rel_path[:-3] + "_en.md"

        tags_en = ["english", "en"]
        if tipo:
            tags_en.append(tipo)

        # Traducir frontmatter para versión en inglés
        meta_en = dict(meta_es)
        meta_en["id"] = f"{entity_id}_en"
        meta_en["nombre"] = nombre_en
        meta_en["nombre_original"] = nombre_es
        meta_en["idioma"] = "en"
        meta_en["tags"] = tags_en

        # Escuela de magia
        if "escuela" in meta_es and meta_es["escuela"]:
            esc_es = str(meta_es["escuela"]).lower().strip()
            meta_en["escuela"] = SCHOOLS_MAP.get(esc_es, meta_es["escuela"])

        # Clases asociadas
        if "clases" in meta_es and isinstance(meta_es["clases"], list):
            meta_en["clases"] = [CLASSES_MAP.get(str(c).lower().strip(), c) for c in meta_es["clases"]]

        # Tiempos de lanzamiento, alcance y duración
        if srd_entry and tipo == "conjuro":
            meta_en["tiempo_lanzamiento"] = srd_entry.get("casting_time", meta_es.get("tiempo_lanzamiento"))
            meta_en["alcance"] = translate_range(srd_entry.get("range", meta_es.get("alcance")))
            meta_en["duracion"] = srd_entry.get("duration", meta_es.get("duracion"))
            if srd_entry.get("concentration"):
                meta_en["duracion"] = f"Concentration, {meta_en['duracion']}" if "concentration" not in meta_en['duracion'].lower() else meta_en['duracion']
            comps = srd_entry.get("components", ["V", "S"])
            comp_str = ", ".join(comps)
            if srd_entry.get("material"):
                comp_str += f" ({srd_entry['material']})"
            meta_en["componentes"] = comp_str
        else:
            if "tiempo_lanzamiento" in meta_es:
                meta_en["tiempo_lanzamiento"] = translate_time(meta_es["tiempo_lanzamiento"])
            if "alcance" in meta_es:
                meta_en["alcance"] = translate_range(meta_es["alcance"])
            if "duracion" in meta_es:
                meta_en["duracion"] = translate_duration(meta_es["duracion"])
            if "componentes" in meta_es:
                meta_en["componentes"] = translate_components(meta_es["componentes"])

        # Traducir cuerpo markdown
        body_en = translate_markdown_body(body_es, nombre_en, tipo, srd_entry=srd_entry)

        # Guardar archivo en inglés
        new_frontmatter_en = yaml.dump(meta_en, allow_unicode=True, sort_keys=False).strip()
        new_content_en = f"---\n{new_frontmatter_en}\n---\n\n{body_en}\n"
        with open(en_file_path, "w", encoding="utf-8") as f:
            f.write(new_content_en)

        # Construir entradas para el índice maestro
        entry_es = {
            "id": entity_id,
            "nombre": nombre_es,
            "nombre_ingles": nombre_en,
            "idioma": "es",
            "tipo": tipo,
            "nivel": meta_es.get("nivel"),
            "escuela": meta_es.get("escuela"),
            "clases": meta_es.get("clases", []),
            "fuente": meta_es.get("fuente", "PHB 2024"),
            "tags": tags_es,
            "path": rel_path,
        }
        for k in ["dote_concedida", "caracteristicas_clave", "habilidades_competentes", "dado_golpe", "tiempo_lanzamiento", "alcance", "duracion", "concentracion", "ritual"]:
            if k in meta_es:
                entry_es[k] = meta_es[k]

        entry_en = {
            "id": f"{entity_id}_en",
            "original_id": entity_id,
            "nombre": nombre_en,
            "nombre_ingles": nombre_en,
            "nombre_espanol": nombre_es,
            "idioma": "en",
            "tipo": tipo,
            "nivel": meta_en.get("nivel"),
            "escuela": meta_en.get("escuela"),
            "clases": meta_en.get("clases", []),
            "fuente": meta_en.get("fuente", "PHB 2024"),
            "tags": tags_en,
            "path": en_rel_path,
        }
        for k in ["dote_concedida", "caracteristicas_clave", "habilidades_competentes", "dado_golpe", "tiempo_lanzamiento", "alcance", "duracion", "concentracion", "ritual"]:
            if k in meta_en:
                entry_en[k] = meta_en[k]

        return entry_es, entry_en

    except Exception as e:
        print(f"[BilingualOKF] Error al procesar {rel_path}: {e}")
        return None, None

def build_full_bilingual_compendium():
    """Recorre todos los archivos del compendio y genera el catálogo dual ES/EN."""
    print("[BilingualOKF] Iniciando generación bilingüe de OKF D&D 5e...")
    entities = []
    processed_count = 0

    for root, _, files in os.walk(OKF_DIR):
        for file in files:
            if not file.endswith(".md") or file.endswith("_en.md") or file.upper() == "README.MD":
                continue

            full_path = os.path.join(root, file)
            e_es, e_en = process_entity_file(full_path)
            if e_es and e_en:
                entities.append(e_es)
                entities.append(e_en)
                processed_count += 1

    # Guardar en index_metadata.json
    index_payload = {
        "version": "2.1.0",
        "total_entities": len(entities),
        "total_spanish_entities": processed_count,
        "total_english_entities": processed_count,
        "entities": entities,
    }

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    print(f"[BilingualOKF] ¡Éxito! Procesadas {processed_count} entidades base -> {len(entities)} entradas en índice maestro.")
    return len(entities)

if __name__ == "__main__":
    build_full_bilingual_compendium()
