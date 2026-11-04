"""
Motor e ingestor del compendio D&D (2024 PHB / SRD 5.2 y 2014 SRD 5.1) a SQLite relacional.
Normaliza e indexa monstruos, conjuros y equipo (incluyendo Weapon Mastery)
provenientes de fuentes JSON de 5etools y paquetes YAML/JSON de Foundry VTT SRD dnd5e.
Soporte bilingüe completo (ES y EN) y etiquetado por edición (5.5e / 2024 y 5e / 2014).
"""
import os
import glob
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from yaml import CSafeLoader as YamlLoader
except ImportError:
    from yaml import SafeLoader as YamlLoader
import yaml

from core.db import DatabaseManager


CR_FRACTION_MAP: Dict[str, float] = {
    "0": 0.0,
    "1/8": 0.125,
    "1/4": 0.25,
    "1/2": 0.5,
}

VALID_WEAPON_MASTERIES = {
    "cleave", "graze", "nick", "push", "sap", "slow", "topple", "vex"
}

HTML_TAG_RE = re.compile(r'<[^>]+>')


def clean_html(html_text: str) -> str:
    """Elimina etiquetas HTML y las transforma en markdown legible."""
    if not html_text:
        return ""
    text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html_text, flags=re.DOTALL)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<li>(.*?)</li>', r'- \1\n', text)
    text = HTML_TAG_RE.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_cr_to_float(cr_val: Any) -> Tuple[float, str]:
    """Convierte un valor de Desafío (CR) arbitrario a (float, texto_canónico)."""
    if cr_val is None:
        return 0.0, "0"

    if isinstance(cr_val, dict):
        cr_val = cr_val.get("cr", "0")

    s = str(cr_val).strip()
    if s in CR_FRACTION_MAP:
        return CR_FRACTION_MAP[s], s

    if "/" in s:
        parts = s.split("/")
        try:
            num = float(parts[0])
            denom = float(parts[1])
            if denom > 0:
                val = num / denom
                return val, s
        except (ValueError, IndexError):
            pass

    try:
        val = float(s)
        cr_text = str(int(val)) if val.is_integer() else str(val)
        return val, cr_text
    except ValueError:
        return 0.0, "0"


# =========================================================================
# GLOSARIO Y TRADUCCIONES OFICIALES D&D (INGLÉS -> ESPAÑOL)
# =========================================================================

TYPE_TRANSLATIONS = {
    "aberration": "Aberración",
    "beast": "Bestia",
    "celestial": "Celestial",
    "construct": "Constructo",
    "dragon": "Dragón",
    "elemental": "Elemental",
    "fey": "Feérico",
    "fiend": "Infraser",
    "giant": "Gigante",
    "humanoid": "Humanoide",
    "monstrosity": "Monstruosidad",
    "ooze": "Cieno",
    "plant": "Planta",
    "undead": "Muerto Viviente",
}

ALIGN_TRANSLATIONS = {
    "chaotic evil": "Caótico Malvado",
    "lawful evil": "Legal Malvado",
    "neutral evil": "Neutral Malvado",
    "chaotic good": "Caótico Bueno",
    "lawful good": "Legal Bueno",
    "neutral good": "Neutral Bueno",
    "chaotic neutral": "Caótico Neutral",
    "lawful neutral": "Legal Neutral",
    "neutral": "Neutral",
    "unaligned": "Sin alineamiento",
    "any": "Cualquier alineamiento",
}

SIZE_TRANSLATIONS = {
    "tiny": "Diminuto",
    "small": "Pequeño",
    "med": "Mediano",
    "medium": "Mediano",
    "large": "Grande",
    "huge": "Enorme",
    "grg": "Gargantuesco",
    "gargantuan": "Gargantuesco",
}

SCHOOL_TRANSLATIONS_EN = {
    "abj": "Abjuration", "abjuration": "Abjuration",
    "con": "Conjuration", "conjuration": "Conjuration",
    "div": "Divination", "divination": "Divination",
    "enc": "Enchantment", "enchantment": "Enchantment",
    "evo": "Evocation", "evocation": "Evocation",
    "ill": "Illusion", "illusion": "Illusion",
    "nec": "Necromancy", "necromancy": "Necromancy",
    "trs": "Transmutation", "transmutation": "Transmutation",
}

SCHOOL_TRANSLATIONS_ES = {
    "abj": "Abjuración", "abjuration": "Abjuración",
    "con": "Conjuración", "conjuration": "Conjuración",
    "div": "Adivinación", "divination": "Adivinación",
    "enc": "Encantamiento", "enchantment": "Encantamiento",
    "evo": "Evocación", "evocation": "Evocación",
    "ill": "Ilusionismo", "illusion": "Ilusionismo",
    "nec": "Nigromancia", "necromancy": "Nigromancia",
    "trs": "Transmutación", "transmutation": "Transmutación",
}

SPELL_NAME_CORRECTIONS = {
    "escupo": "Escudo",
    "shield": "Escudo",
}

MASTERY_TRANSLATIONS = {
    "cleave": "Hender (Cleave)",
    "graze": "Rozar (Graze)",
    "nick": "Mella (Nick)",
    "push": "Empujar (Push)",
    "sap": "Incapacitar (Sap)",
    "slow": "Ralentizar (Slow)",
    "topple": "Derribar (Topple)",
    "vex": "Hostigar (Vex)",
}

ITEM_TYPE_TRANSLATIONS = {
    "martialm": "Arma Marcial CaC",
    "martialr": "Arma Marcial a Distancia",
    "simplem": "Arma Simple CaC",
    "simpler": "Arma Simple a Distancia",
    "weapon": "Arma",
    "armor": "Armadura",
    "shield": "Escudo",
    "heavy": "Armadura Pesada",
    "medium": "Armadura Media",
    "light": "Armadura Ligera",
    "gear": "Equipo de Aventuras",
    "consumable": "Consumible",
    "potion": "Poción",
    "scroll": "Pergamino",
    "wand": "Varita",
    "rod": "Cetro",
    "staff": "Bastón Mágico",
    "ring": "Anillo Mágico",
    "wondrous": "Objeto Maravilloso",
    "tool": "Herramienta",
    "loot": "Tesoro / Valioso",
}

RARITY_TRANSLATIONS = {
    "common": "Común",
    "uncommon": "Poco común",
    "rare": "Raro",
    "veryrare": "Muy raro",
    "very rare": "Muy raro",
    "legendary": "Legendario",
    "artifact": "Artefacto",
}

MONSTER_ADJECTIVES = {
    "ancient": "Anciano",
    "adult": "Adulto",
    "young": "Joven",
    "wyrmling": "Cría de",
    "giant": "Gigante",
    "dire": "Tétrico",
    "greater": "Mayor",
    "lesser": "Menor",
    "elder": "Anciano",
    "warrior": "Guerrero",
    "captain": "Capitán",
    "leader": "Líder",
    "lord": "Señor",
}

MONSTER_NOUNS = {
    "dragon": "Dragón",
    "red dragon": "Dragón Rojo",
    "black dragon": "Dragón Negro",
    "blue dragon": "Dragón Azul",
    "green dragon": "Dragón Verde",
    "white dragon": "Dragón Blanco",
    "gold dragon": "Dragón Dorado",
    "silver dragon": "Dragón Plateado",
    "bronze dragon": "Dragón de Bronce",
    "brass dragon": "Dragón de Oropel",
    "copper dragon": "Dragón de Cobre",
    "goblin": "Goblin",
    "orc": "Orco",
    "ogre": "Ogro",
    "troll": "Trol",
    "skeleton": "Esqueleto",
    "zombie": "Zombi",
    "ghoul": "Necrófago",
    "wight": "Tumulario",
    "wraith": "Espectro",
    "ghost": "Fantasma",
    "mummy": "Momia",
    "vampire": "Vampiro",
    "lich": "Liche",
    "minotaur": "Minotauro",
    "medusa": "Medusa",
    "chimera": "Quimera",
    "manticore": "Mantícora",
    "gorgon": "Gorgona",
    "basilisk": "Basilisco",
    "cockatrice": "Cocatriz",
    "harpy": "Arpía",
    "hydra": "Hidra",
    "kraken": "Kraken",
    "beholder": "Contemplador",
    "mind flayer": "Azotamentes",
    "owlbear": "Oso Lechuza",
    "bulette": "Bulette",
    "displacer beast": "Bestia Trémula",
    "gelatinous cube": "Cubo Gelatinoso",
    "ochre jelly": "Gelatina Ocre",
    "black pudding": "Pudín Negro",
    "clay golem": "Golem de Arcilla",
    "flesh golem": "Golem de Carne",
    "iron golem": "Golem de Hierro",
    "stone golem": "Golem de Piedra",
    "bandit": "Bandido",
    "cultist": "Cultista",
    "knight": "Caballero",
    "mage": "Mago",
    "priest": "Clérigo",
    "guard": "Guardia",
    "commoner": "Plebeyo",
    "wolf": "Lobo",
    "spider": "Araña",
    "rat": "Rata",
    "bat": "Murciélago",
    "bear": "Oso",
    "hawk": "Halcón",
    "eagle": "Águila",
    "lion": "León",
    "tiger": "Tigre",
    "crocodile": "Cocodrilo",
    "snake": "Serpiente",
    "poisonous snake": "Serpiente Venenosa",
    "constrictor snake": "Serpiente Constrictora",
}

ITEM_NAMES_TRANSLATION = {
    "dagger": "Daga",
    "shortsword": "Espada Corta",
    "longsword": "Espada Larga",
    "greatsword": "Espadón",
    "scimitar": "Cimitarra",
    "rapier": "Estoque",
    "handaxe": "Hacha de Mano",
    "battleaxe": "Hacha de Batalla",
    "greataxe": "Gran Hacha",
    "halberd": "Alabarda",
    "glaive": "Guja",
    "pike": "Pica",
    "spear": "Lanza",
    "trident": "Tridente",
    "mace": "Maza",
    "morningstar": "Lucero del Alba",
    "war pick": "Pico de Guerra",
    "warhammer": "Martillo de Guerra",
    "flail": "Mayal",
    "whip": "Látigo",
    "quarterstaff": "Bastón",
    "club": "Garrote",
    "greatclub": "Gran Garrote",
    "shortbow": "Arco Corto",
    "longbow": "Arco Largo",
    "light crossbow": "Ballesta Ligera",
    "heavy crossbow": "Ballesta Pesada",
    "hand crossbow": "Ballesta de Mano",
    "sling": "Honda",
    "blowgun": "Cerbatana",
    "dart": "Dardo",
    "net": "Red",
    "shield": "Escudo",
    "padded armor": "Armadura Acolchada",
    "leather armor": "Armadura de Cuero",
    "studded leather armor": "Armadura de Cuero Tachonado",
    "hide armor": "Armadura de Pieles",
    "chain shirt": "Camisote de Malla",
    "scale mail": "Cota de Escamas",
    "breastplate": "Coraza",
    "half plate armor": "Semiplacas",
    "ring mail": "Cota de Anillas",
    "chain mail": "Cota de Malla",
    "splint armor": "Armadura de Bandas",
    "plate armor": "Armadura de Placas",
    "potion of healing": "Poción de Curación",
    "potion of greater healing": "Poción de Curación Mayor",
    "potion of superior healing": "Poción de Curación Superior",
    "potion of supreme healing": "Poción de Curación Suprema",
    "bag of holding": "Bolsa de Contención",
    "boots of elvenkind": "Botas de Élficas",
    "cloak of elvenkind": "Capa Élfica",
    "cloak of protection": "Capa de Protección",
    "ring of protection": "Anillo de Protección",
}


def translate_monster_name(name_en: str) -> str:
    """Traduce el nombre de un monstruo de inglés a español."""
    norm = name_en.strip().lower()
    if norm in MONSTER_NOUNS:
        return MONSTER_NOUNS[norm]

    # Verificar si empieza con adjetivo (Adult Black Dragon -> Dragón Negro Adulto)
    for adj_en, adj_es in MONSTER_ADJECTIVES.items():
        if norm.startswith(f"{adj_en} "):
            rest = norm[len(adj_en) + 1:].strip()
            rest_es = MONSTER_NOUNS.get(rest, rest.title())
            if adj_en == "wyrmling":
                return f"Cría de {rest_es}"
            return f"{rest_es} {adj_es}"

    # Reemplazo por partes
    words = norm.split()
    translated_words = []
    for w in words:
        if w in MONSTER_NOUNS:
            translated_words.append(MONSTER_NOUNS[w])
        elif w in MONSTER_ADJECTIVES:
            translated_words.append(MONSTER_ADJECTIVES[w])
        else:
            translated_words.append(w.capitalize())

    return " ".join(translated_words)


def translate_item_name(name_en: str) -> str:
    """Traduce el nombre de un objeto de inglés a español."""
    norm = name_en.strip().lower()
    if norm in ITEM_NAMES_TRANSLATION:
        return ITEM_NAMES_TRANSLATION[norm]
    # Buscar coincidencia parcial
    for k, v in ITEM_NAMES_TRANSLATION.items():
        if k in norm:
            return norm.replace(k, v).title()
    return name_en


def load_okf_spells_dictionary(okf_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Carga los conjuros de OKF para reutilizar descripciones y nombres oficiales en español."""
    spells_map: Dict[str, Dict[str, Any]] = {}
    if not okf_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        okf_dir = os.path.join(base_dir, "okf_dnd5e")

    meta_path = os.path.join(okf_dir, "index_metadata.json")
    if not os.path.exists(meta_path):
        return spells_map

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entities = data.get("entities", [])
        for e in entities:
            if e.get("tipo") == "conjuro" and e.get("idioma") == "es":
                en_name = str(e.get("nombre_ingles", "")).strip().lower()
                if en_name:
                    spells_map[en_name] = e
    except Exception as err:
        print(f"[CompendiumImporter] Advertencia al cargar catálogo OKF: {err}")

    return spells_map


# =========================================================================
# NORMALIZADORES FOUNDRY VTT (SRD 5.2 / SRD 5.1)
# =========================================================================

def normalize_foundry_monster(
    raw: Dict[str, Any],
    edition: str = "5.5e",
    lang: str = "en"
) -> Dict[str, Any]:
    """Normaliza un actor YAML de Foundry VTT a compendium_monsters."""
    name_en = raw.get("name", "Unknown Creature").strip()
    sys = raw.get("system", {})

    cr_val = sys.get("details", {}).get("cr", 0)
    cr_float, cr_text = parse_cr_to_float(cr_val)

    type_data = sys.get("details", {}).get("type", {})
    type_val = type_data.get("value", "humanoid") if isinstance(type_data, dict) else str(type_data)
    type_en = str(type_val or "humanoid").capitalize()
    type_es = TYPE_TRANSLATIONS.get(type_en.lower(), type_en)

    align_raw = sys.get("details", {}).get("alignment", "Unaligned")
    align_en = str(align_raw or "Unaligned").capitalize()
    align_es = ALIGN_TRANSLATIONS.get(align_en.lower(), align_en)

    size_raw = sys.get("traits", {}).get("size") if isinstance(sys.get("traits"), dict) else None
    if isinstance(size_raw, dict):
        size_raw = size_raw.get("value")
    if not size_raw:
        size_raw = sys.get("attributes", {}).get("size") if isinstance(sys.get("attributes"), dict) else "med"
    if not size_raw or not isinstance(size_raw, str):
        size_raw = "med"
    size_en = str(size_raw).capitalize()
    size_es = SIZE_TRANSLATIONS.get(str(size_raw).lower(), size_en)

    # Armadura (AC)
    ac_data = sys.get("attributes", {}).get("ac", {}) if isinstance(sys.get("attributes"), dict) else {}
    ac = 10
    if isinstance(ac_data, dict):
        val = ac_data.get("flat") or ac_data.get("value")
        try:
            ac = int(val) if val is not None else 10
        except (ValueError, TypeError):
            ac = 10
    elif isinstance(ac_data, (int, float, str)) and str(ac_data).isdigit():
        ac = int(ac_data)

    # Puntos de golpe (HP)
    hp_data = sys.get("attributes", {}).get("hp", {}) if isinstance(sys.get("attributes"), dict) else {}
    hp_avg = 10
    hp_formula = ""
    if isinstance(hp_data, dict):
        val = hp_data.get("max") or hp_data.get("value")
        try:
            hp_avg = int(val) if val is not None else 10
        except (ValueError, TypeError):
            hp_avg = 10
        hp_formula = str(hp_data.get("formula", "") or "")
    elif isinstance(hp_data, (int, float, str)) and str(hp_data).isdigit():
        hp_avg = int(hp_data)

    # Velocidad
    mov = sys.get("attributes", {}).get("movement", {}) if isinstance(sys.get("attributes"), dict) else {}
    speed_parts = []
    if isinstance(mov, dict):
        for k in ["walk", "fly", "swim", "burrow", "climb"]:
            val = mov.get(k)
            if val is not None and val != "":
                speed_parts.append(f"{val} ft." if k == "walk" else f"{k} {val} ft.")
    speed_en = ", ".join(speed_parts) or "30 ft."
    speed_es = speed_en.replace("walk", "caminar").replace("fly", "volar").replace("swim", "nadar").replace("climb", "escalar").replace("burrow", "excavar").replace("ft.", "pies")

    # Atributos
    abilities = {}
    for ab, data in sys.get("abilities", {}).items():
        if isinstance(data, dict):
            abilities[ab.lower()] = int(data.get("value", 10))

    # Rasgos y acciones
    traits = []
    actions = []
    reactions = []
    legendary = []

    for it in raw.get("items", []):
        if not isinstance(it, dict):
            continue
        it_name = it.get("name", "Action")
        it_desc = clean_html(it.get("system", {}).get("description", {}).get("value", ""))
        act_type = it.get("system", {}).get("activation", {}).get("type", "")
        entry = {"name": it_name, "desc": it_desc}
        if act_type == "reaction":
            reactions.append(entry)
        elif act_type in ("action", "bonus"):
            actions.append(entry)
        elif it.get("system", {}).get("activation", {}).get("cost") and "legendary" in str(act_type):
            legendary.append(entry)
        else:
            traits.append(entry)

    # Edición canónica
    edition_tag = "2024" if edition in ("5.5e", "2024") else "5e"
    base_slug = re.sub(r'[^a-z0-9]+', '_', name_en.lower()).strip('_')
    entity_id = f"{base_slug}_{edition_tag}_{lang}"

    is_es = (lang == "es")
    display_name = translate_monster_name(name_en) if is_es else name_en

    details = {
        "abilities": abilities,
        "str": abilities.get("str", 10),
        "dex": abilities.get("dex", 10),
        "con": abilities.get("con", 10),
        "int": abilities.get("int", 10),
        "wis": abilities.get("wis", 10),
        "cha": abilities.get("cha", 10),
        "trait": traits,
        "action": actions,
        "reactions": reactions,
        "legendary": legendary,
        "source": sys.get("source", {}),
    }

    return {
        "entity_id": entity_id,
        "name": display_name,
        "name_en": name_en,
        "cr": cr_float,
        "cr_text": cr_text,
        "size": size_es if is_es else size_en,
        "monster_type": type_es if is_es else type_en,
        "alignment": align_es if is_es else align_en,
        "ac": ac,
        "hp_avg": hp_avg,
        "hp_formula": hp_formula,
        "speed": speed_es if is_es else speed_en,
        "edition": edition,
        "language": lang,
        "data_json": json.dumps(details, ensure_ascii=False),
    }


def normalize_foundry_spell(
    raw: Dict[str, Any],
    edition: str = "5.5e",
    lang: str = "en",
    okf_spells: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Normaliza un conjuro YAML de Foundry VTT a compendium_spells."""
    name_en = raw.get("name", "Unknown Spell").strip()
    sys = raw.get("system", {})
    level = int(sys.get("level", 0))

    school_code = str(sys.get("school", "evo")).lower()
    school_en = SCHOOL_TRANSLATIONS_EN.get(school_code, school_code.capitalize())
    school_es = SCHOOL_TRANSLATIONS_ES.get(school_code, school_en)

    act = sys.get("activation", {})
    act_type = act.get("type", "action")
    act_val = act.get("value") or 1
    time_en = f"{act_val} {act_type}".strip()
    time_es = time_en.replace("action", "acción").replace("bonus", "acción adicional").replace("reaction", "reacción").replace("minute", "minuto").replace("hour", "hora")

    rng = sys.get("range", {})
    range_en = f"{rng.get('value', '')} {rng.get('units', 'ft')}".strip() or "Self"
    range_es = range_en.replace("Self", "Personal").replace("Touch", "Toque").replace("ft", "pies").replace("feet", "pies")

    props = sys.get("properties", [])
    comps = []
    if "vocal" in props: comps.append("V")
    if "somatic" in props: comps.append("S")
    if "material" in props:
        mat = sys.get("materials", {}).get("value", "")
        comps.append(f"M ({mat})" if mat else "M")
    comp_str = ", ".join(comps) or "V, S"

    dur = sys.get("duration", {})
    dur_units = str(dur.get("units", "inst")).lower()
    dur_val = dur.get("value", "")
    dur_en = f"{dur_val} {dur_units}".strip() if dur_val else dur_units
    if dur_en in ("inst", "instant"):
        dur_en = "Instantaneous"
    dur_es = dur_en.replace("Instantaneous", "Instantáneo").replace("minute", "minuto").replace("hour", "hora").replace("round", "asalto").replace("day", "día")

    is_conc = 1 if "concentration" in props else 0
    is_rit = 1 if "ritual" in props else 0

    desc_en = clean_html(sys.get("description", {}).get("value", ""))

    # Verificar si tenemos traducción exacta en OKF
    is_es = (lang == "es")
    name_es = name_en
    desc_es = desc_en
    classes_str = ""

    if okf_spells:
        okf_entry = okf_spells.get(name_en.lower())
        if okf_entry:
            name_es = okf_entry.get("nombre", name_en)
            if name_es.lower() in SPELL_NAME_CORRECTIONS:
                name_es = SPELL_NAME_CORRECTIONS[name_es.lower()]
            elif name_en.lower() in SPELL_NAME_CORRECTIONS:
                name_es = SPELL_NAME_CORRECTIONS[name_en.lower()]
            if is_es:
                time_es = okf_entry.get("tiempo_lanzamiento", time_es)
                range_es = okf_entry.get("alcance", range_es)
                dur_es = okf_entry.get("duracion", dur_es)
                comp_str = okf_entry.get("componentes", comp_str)
                # Intentar leer descripción en español del archivo OKF
                rel_path = okf_entry.get("path")
                if rel_path:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    full_p = os.path.join(base_dir, "okf_dnd5e", rel_path)
                    if os.path.exists(full_p):
                        try:
                            with open(full_p, "r", encoding="utf-8") as sf:
                                s_content = sf.read()
                                if "---" in s_content:
                                    parts = s_content.split("---", 2)
                                    if len(parts) >= 3:
                                        desc_es = parts[2].strip()
                        except Exception:
                            pass
            classes_arr = okf_entry.get("clases", [])
            classes_str = ", ".join(classes_arr) if isinstance(classes_arr, list) else str(classes_arr)

    edition_tag = "2024" if edition in ("5.5e", "2024") else "5e"
    base_slug = re.sub(r'[^a-z0-9]+', '_', name_en.lower()).strip('_')
    entity_id = f"{base_slug}_{edition_tag}_{lang}"

    details = {
        "source": sys.get("source", {}),
        "target": sys.get("target", {}),
        "damage": sys.get("damage", {}),
        "save": sys.get("save", {}),
    }

    return {
        "entity_id": entity_id,
        "name": name_es if is_es else name_en,
        "name_en": name_en,
        "level": level,
        "school": school_es if is_es else school_en,
        "casting_time": time_es if is_es else time_en,
        "range_area": range_es if is_es else range_en,
        "components": comp_str,
        "duration": dur_es if is_es else dur_en,
        "is_concentration": is_conc,
        "is_ritual": is_rit,
        "classes": classes_str,
        "edition": edition,
        "language": lang,
        "description": desc_es if is_es else desc_en,
        "data_json": json.dumps(details, ensure_ascii=False),
    }


def normalize_foundry_item(
    raw: Dict[str, Any],
    edition: str = "5.5e",
    lang: str = "en"
) -> Dict[str, Any]:
    """Normaliza un objeto/arma/armadura YAML de Foundry VTT a compendium_items."""
    name_en = raw.get("name", "Unknown Item").strip()
    raw_type = str(raw.get("type", "gear")).lower()
    sys = raw.get("system", {})

    mastery = sys.get("mastery", "")
    if mastery:
        mastery = str(mastery).capitalize()

    price_data = sys.get("price", {})
    cost_val = price_data.get("value", 0) if isinstance(price_data, dict) else 0
    denom = price_data.get("denomination", "gp") if isinstance(price_data, dict) else "gp"
    cost_en = f"{cost_val} {denom}"
    cost_es = cost_en.replace("gp", "po").replace("sp", "pp").replace("cp", "pc").replace("ep", "pe").replace("pp", "pt")

    weight_data = sys.get("weight", {})
    weight_val = weight_data.get("value", 0) if isinstance(weight_data, dict) else 0
    weight_units = weight_data.get("units", "lb") if isinstance(weight_data, dict) else "lb"
    weight_en = f"{weight_val} {weight_units}" if weight_val else ""
    weight_es = weight_en.replace("lb", "lb.")

    rarity_raw = str(sys.get("rarity", "common")).lower()
    rarity_en = rarity_raw.capitalize() if rarity_raw else "Common"
    rarity_es = RARITY_TRANSLATIONS.get(rarity_raw, rarity_en)

    type_data = sys.get("type", {})
    item_type_code = type_data.get("value", raw_type).lower() if isinstance(type_data, dict) else str(type_data).lower()
    item_type_en = ITEM_TYPE_TRANSLATIONS.get(item_type_code, raw_type.capitalize())
    item_type_es = ITEM_TYPE_TRANSLATIONS.get(item_type_code, item_type_en)

    dmg_base = sys.get("damage", {}).get("base", {})
    dmg_formula = ""
    dmg_type_str = ""
    if isinstance(dmg_base, dict):
        num = dmg_base.get("number", 1)
        den = dmg_base.get("denomination", 8)
        if den:
            dmg_formula = f"{num}d{den}"
        types = dmg_base.get("types", [])
        dmg_type_str = ", ".join(types)

    dmg_type_es = dmg_type_str.replace("slashing", "cortante").replace("piercing", "perforante").replace("bludgeoning", "contundente")

    # CA
    armor_data = sys.get("armor", {})
    ac_bonus = 0
    if isinstance(armor_data, dict):
        ac_bonus = int(armor_data.get("value", 0) or 0)

    desc_en = clean_html(sys.get("description", {}).get("value", ""))

    edition_tag = "2024" if edition in ("5.5e", "2024") else "5e"
    base_slug = re.sub(r'[^a-z0-9]+', '_', name_en.lower()).strip('_')
    entity_id = f"{base_slug}_{edition_tag}_{lang}"

    is_es = (lang == "es")
    name_display = translate_item_name(name_en) if is_es else name_en
    mastery_display = MASTERY_TRANSLATIONS.get(mastery.lower(), mastery) if is_es else mastery

    details = {
        "properties": sys.get("properties", []),
        "source": sys.get("source", {}),
        "equippable": sys.get("equippable", True),
        "attunement": sys.get("attunement"),
    }

    return {
        "entity_id": entity_id,
        "name": name_display,
        "name_en": name_en,
        "item_type": item_type_es if is_es else item_type_en,
        "rarity": rarity_es if is_es else rarity_en,
        "cost": cost_es if is_es else cost_en,
        "weight": weight_es if is_es else weight_en,
        "weapon_mastery": mastery_display,
        "damage": dmg_formula,
        "damage_type": dmg_type_es if is_es else dmg_type_str,
        "ac_bonus": ac_bonus,
        "edition": edition,
        "language": lang,
        "description": desc_en,
        "data_json": json.dumps(details, ensure_ascii=False),
    }


# =========================================================================
# NORMALIZADORES LEGACY (5ETOOLS / JSON PLANO)
# =========================================================================

def normalize_monster(raw: Dict[str, Any], default_edition: str = "5.5e", default_lang: str = "en") -> Dict[str, Any]:
    """Normaliza una entrada de monstruo de 5etools / JSON plano."""
    name = raw.get("name", "Unknown Creature")
    source = raw.get("source", "XPHB")
    edition = "5.5e" if any(k in str(source).upper() for k in ("XPHB", "2024", "5.5")) else default_edition
    entity_id = raw.get("entity_id") or raw.get("id") or f"{name.lower().replace(' ', '_')}_{edition.replace('.', '')}"

    cr_float, cr_text = parse_cr_to_float(raw.get("cr", "0"))

    raw_type = raw.get("type", "Monstrosity")
    if isinstance(raw_type, dict):
        m_type = raw_type.get("type", "Monstrosity")
    else:
        m_type = str(raw_type).split()[0].rstrip(",;").capitalize()

    size_raw = raw.get("size", "M")
    size_map = {
        "T": "Tiny", "S": "Small", "M": "Medium",
        "L": "Large", "H": "Huge", "G": "Gargantuan"
    }
    if isinstance(size_raw, list) and size_raw:
        size_raw = size_raw[0]
    size = size_map.get(str(size_raw).upper(), str(size_raw).capitalize() or "Medium")

    ac_raw = raw.get("ac", 10)
    ac = 10
    if isinstance(ac_raw, list) and ac_raw:
        first_ac = ac_raw[0]
        ac = first_ac.get("ac", 10) if isinstance(first_ac, dict) else int(first_ac)
    elif isinstance(ac_raw, dict):
        ac = int(ac_raw.get("ac", 10))
    elif isinstance(ac_raw, (int, float, str)) and str(ac_raw).isdigit():
        ac = int(ac_raw)

    hp_raw = raw.get("hp", {})
    hp_avg = 10
    hp_formula = ""
    if isinstance(hp_raw, dict):
        hp_avg = int(hp_raw.get("average", hp_raw.get("special", 10) if str(hp_raw.get("special", "")).isdigit() else 10))
        hp_formula = str(hp_raw.get("formula", ""))
    elif isinstance(hp_raw, (int, float, str)) and str(hp_raw).isdigit():
        hp_avg = int(hp_raw)

    speed_raw = raw.get("speed", "30 ft.")
    if isinstance(speed_raw, dict):
        parts = []
        for k, v in speed_raw.items():
            if isinstance(v, (int, str)):
                parts.append(f"{k} {v}" if k != "walk" else f"{v} ft.")
        speed = ", ".join(parts) or "30 ft."
    else:
        speed = str(speed_raw)

    alignment = raw.get("alignment", "Unaligned")
    if isinstance(alignment, list):
        alignment = " ".join([str(a) for a in alignment])

    return {
        "entity_id": entity_id,
        "name": name,
        "name_en": raw.get("name_en", name),
        "cr": cr_float,
        "cr_text": cr_text,
        "size": size,
        "monster_type": m_type,
        "alignment": alignment,
        "ac": ac,
        "hp_avg": hp_avg,
        "hp_formula": hp_formula,
        "speed": speed,
        "edition": edition,
        "language": raw.get("language", default_lang),
        "data_json": json.dumps(raw, ensure_ascii=False),
    }


def normalize_spell(raw: Dict[str, Any], default_edition: str = "5.5e", default_lang: str = "en") -> Dict[str, Any]:
    """Normaliza una entrada de conjuro al esquema de compendium_spells."""
    name = raw.get("name", "Unknown Spell")
    source = raw.get("source", "XPHB")
    edition = "5.5e" if any(k in str(source).upper() for k in ("XPHB", "2024", "5.5")) else default_edition
    entity_id = raw.get("entity_id") or raw.get("id") or f"{name.lower().replace(' ', '_')}_{edition.replace('.', '')}"

    level = int(raw.get("level", 0))
    school = str(raw.get("school", "Evocation")).capitalize()
    school_map = {
        "A": "Abjuration", "C": "Conjuration", "D": "Divination", "E": "Enchantment",
        "V": "Evocation", "I": "Illusion", "N": "Necromancy", "T": "Transmutation"
    }
    school = school_map.get(school.upper(), school)

    time_raw = raw.get("time") or raw.get("casting_time") or "1 action"
    if isinstance(time_raw, list) and time_raw:
        t0 = time_raw[0]
        time_str = f"{t0.get('number', 1)} {t0.get('unit', 'action')}" if isinstance(t0, dict) else str(t0)
    else:
        time_str = str(time_raw)

    range_raw = raw.get("range") or raw.get("range_area") or "60 feet"
    if isinstance(range_raw, dict):
        dist = range_raw.get("distance", {})
        if isinstance(dist, dict):
            range_str = f"{dist.get('amount', '')} {dist.get('type', 'feet')}".strip() or "Self"
        else:
            range_str = str(range_raw.get("type", "Self"))
    else:
        range_str = str(range_raw)

    comp_raw = raw.get("components", "V, S")
    if isinstance(comp_raw, dict):
        comps = []
        if comp_raw.get("v"): comps.append("V")
        if comp_raw.get("s"): comps.append("S")
        if comp_raw.get("m"):
            m_val = comp_raw.get("m")
            comps.append(f"M ({m_val})" if isinstance(m_val, str) else "M")
        components = ", ".join(comps) or "None"
    else:
        components = str(comp_raw)

    dur_raw = raw.get("duration") or "Instantaneous"
    is_conc = 0
    if isinstance(dur_raw, list) and dur_raw:
        d0 = dur_raw[0]
        if isinstance(d0, dict):
            is_conc = 1 if d0.get("concentration") else 0
            dur_type = d0.get("type", "instant")
            dur_amount = d0.get("duration", {})
            if isinstance(dur_amount, dict):
                dur_str = f"{dur_amount.get('amount', '')} {dur_amount.get('type', '')}".strip()
            else:
                dur_str = dur_type
        else:
            dur_str = str(d0)
    elif isinstance(dur_raw, dict):
        is_conc = 1 if dur_raw.get("concentration") else 0
        dur_str = str(dur_raw.get("type", "instant"))
    else:
        dur_str = str(dur_raw)

    classes_raw = raw.get("classes", [])
    if isinstance(classes_raw, dict):
        from_class = classes_raw.get("fromClassList", [])
        classes_list = [c.get("name") for c in from_class if isinstance(c, dict) and "name" in c]
    elif isinstance(classes_raw, list):
        classes_list = [str(c) for c in classes_raw]
    else:
        classes_list = [s.strip() for s in str(classes_raw).split(",") if s.strip()]

    desc_raw = raw.get("entries") or raw.get("description") or ""
    if isinstance(desc_raw, list):
        desc = "\n\n".join([str(e) for e in desc_raw if isinstance(e, str)])
    else:
        desc = str(desc_raw)

    return {
        "entity_id": entity_id,
        "name": name,
        "name_en": raw.get("name_en", name),
        "level": level,
        "school": school,
        "casting_time": time_str,
        "range_area": range_str,
        "components": components,
        "duration": dur_str,
        "is_concentration": is_conc,
        "is_ritual": 1 if raw.get("meta", {}).get("ritual") or raw.get("ritual") else 0,
        "classes": ", ".join(classes_list),
        "edition": edition,
        "language": raw.get("language", default_lang),
        "description": desc,
        "data_json": json.dumps(raw, ensure_ascii=False),
    }


def normalize_item(raw: Dict[str, Any], default_edition: str = "5.5e", default_lang: str = "en") -> Dict[str, Any]:
    """Normaliza un objeto, arma (con Weapon Mastery 5.5e) o armadura al esquema de compendium_items."""
    name = raw.get("name", "Unknown Item")
    source = raw.get("source", "XPHB")
    edition = "5.5e" if any(k in str(source).upper() for k in ("XPHB", "2024", "5.5")) else default_edition
    entity_id = raw.get("entity_id") or raw.get("id") or f"{name.lower().replace(' ', '_')}_{edition.replace('.', '')}"

    raw_type = str(raw.get("type", "gear")).lower()
    item_type = "gear"
    if "weapon" in raw_type or raw.get("weaponCategory"):
        item_type = "weapon"
    elif "armor" in raw_type or raw.get("armorCategory"):
        item_type = "armor"
    elif raw.get("wondrous") or "magic" in raw_type:
        item_type = "magic_item"

    mastery = str(raw.get("mastery") or raw.get("weapon_mastery", "")).strip().lower()
    if mastery not in VALID_WEAPON_MASTERIES:
        mastery = ""
        for word in VALID_WEAPON_MASTERIES:
            if re.search(rf"\b{word}\b", str(raw.get("entries", "")).lower()):
                mastery = word
                break

    dmg1 = raw.get("dmg1", "")
    dmg_type = raw.get("dmgType", "")
    if dmg_type:
        type_map = {"S": "slashing", "P": "piercing", "B": "bludgeoning"}
        dmg_type = type_map.get(str(dmg_type).upper(), str(dmg_type))

    cost_val = raw.get("value") or raw.get("cost", "")
    cost = f"{cost_val / 100:.1f} gp" if isinstance(cost_val, (int, float)) else str(cost_val)
    weight_val = raw.get("weight", "")
    weight = f"{weight_val} lb." if weight_val else ""

    ac_bonus = int(raw.get("ac", 0) or raw.get("ac_bonus", 0))

    entries = raw.get("entries") or raw.get("description", "")
    if isinstance(entries, list):
        desc = "\n\n".join([str(e) for e in entries if isinstance(e, str)])
    else:
        desc = str(entries)

    return {
        "entity_id": entity_id,
        "name": name,
        "name_en": raw.get("name_en", name),
        "item_type": item_type,
        "rarity": str(raw.get("rarity", "common")).lower(),
        "cost": cost,
        "weight": weight,
        "weapon_mastery": mastery,
        "damage": str(dmg1),
        "damage_type": str(dmg_type),
        "ac_bonus": ac_bonus,
        "edition": edition,
        "language": raw.get("language", default_lang),
        "description": desc,
        "data_json": json.dumps(raw, ensure_ascii=False),
    }


# =========================================================================
# CLASE PRINCIPAL: COMPENDIUM IMPORTER
# =========================================================================

class CompendiumImporter:
    """Ingestor de compendios hacia SQLite DatabaseManager."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._okf_spells_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def _get_okf_spells(self) -> Dict[str, Dict[str, Any]]:
        if self._okf_spells_cache is None:
            self._okf_spells_cache = load_okf_spells_dictionary()
        return self._okf_spells_cache

    def ingest_monsters(self, monsters: List[Dict[str, Any]], edition: str = "5.5e", lang: str = "en") -> int:
        """Normaliza e inserta una lista de monstruos."""
        count = 0
        for m in monsters:
            norm = normalize_monster(m, default_edition=edition, default_lang=lang)
            self.db.upsert_compendium_monster(norm)
            count += 1
        return count

    def ingest_spells(self, spells: List[Dict[str, Any]], edition: str = "5.5e", lang: str = "en") -> int:
        """Normaliza e inserta una lista de conjuros."""
        count = 0
        for s in spells:
            norm = normalize_spell(s, default_edition=edition, default_lang=lang)
            self.db.upsert_compendium_spell(norm)
            count += 1
        return count

    def ingest_items(self, items: List[Dict[str, Any]], edition: str = "5.5e", lang: str = "en") -> int:
        """Normaliza e inserta una lista de objetos y armas."""
        count = 0
        for it in items:
            norm = normalize_item(it, default_edition=edition, default_lang=lang)
            self.db.upsert_compendium_item(norm)
            count += 1
        return count

    def ingest_from_json_file(self, file_path: str, category: str, edition: str = "5.5e", lang: str = "en") -> int:
        """Lee un archivo JSON estructurado e ingesta su contenido."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo de compendio no encontrado: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if category == "monsters":
            items = data.get("monster", data) if isinstance(data, dict) else data
            return self.ingest_monsters(items, edition=edition, lang=lang)
        elif category == "spells":
            items = data.get("spell", data) if isinstance(data, dict) else data
            return self.ingest_spells(items, edition=edition, lang=lang)
        elif category == "items":
            items = data.get("item", data) if isinstance(data, dict) else data
            return self.ingest_items(items, edition=edition, lang=lang)
        else:
            raise ValueError(f"Categoría desconocida para ingesta: {category}")

    def ingest_foundry_pack(
        self,
        pack_dir: str,
        category: str,
        edition: str = "5.5e",
        bilingue: bool = True
    ) -> int:
        """
        Escanea recursivamente una carpeta de paquete YAML de Foundry VTT e ingesta
        cada entidad en la base SQLite. Si bilingue=True, crea tanto la fila en inglés
        como la fila correspondiente en español.
        """
        if not os.path.exists(pack_dir):
            raise FileNotFoundError(f"Directorio de paquete Foundry no encontrado: {pack_dir}")

        yaml_files = glob.glob(os.path.join(pack_dir, "**", "*.yml"), recursive=True)
        # Excluir archivos de control de carpetas
        yaml_files = [f for f in yaml_files if not os.path.basename(f).startswith("_folder")]

        okf_spells = self._get_okf_spells() if category == "spells" else None
        count = 0

        for yf_path in yaml_files:
            try:
                with open(yf_path, "r", encoding="utf-8") as yf:
                    data = yaml.load(yf, Loader=YamlLoader)
                if not isinstance(data, dict) or not data.get("name"):
                    continue

                if category == "monsters":
                    # Fila en inglés
                    norm_en = normalize_foundry_monster(data, edition=edition, lang="en")
                    self.db.upsert_compendium_monster(norm_en)
                    count += 1
                    # Fila en español
                    if bilingue:
                        norm_es = normalize_foundry_monster(data, edition=edition, lang="es")
                        self.db.upsert_compendium_monster(norm_es)
                        count += 1

                elif category == "spells":
                    norm_en = normalize_foundry_spell(data, edition=edition, lang="en", okf_spells=okf_spells)
                    self.db.upsert_compendium_spell(norm_en)
                    count += 1
                    if bilingue:
                        norm_es = normalize_foundry_spell(data, edition=edition, lang="es", okf_spells=okf_spells)
                        self.db.upsert_compendium_spell(norm_es)
                        count += 1

                elif category == "items":
                    norm_en = normalize_foundry_item(data, edition=edition, lang="en")
                    self.db.upsert_compendium_item(norm_en)
                    count += 1
                    if bilingue:
                        norm_es = normalize_foundry_item(data, edition=edition, lang="es")
                        self.db.upsert_compendium_item(norm_es)
                        count += 1

            except Exception as err:
                print(f"[CompendiumImporter] Error al procesar {yf_path}: {err}")

        return count

    def ingest_all_foundry_packs(
        self,
        packs_root: str,
        bilingue: bool = True
    ) -> Dict[str, int]:
        """
        Ingesta masiva de paquetes oficiales Foundry VTT SRD 5.2 (2024) y SRD 5.1 (2014):
        - actors24 (2024) + monsters (2014)
        - spells24 (2024) + spells (2014)
        - equipment24 (2024) + items (2014)
        """
        results: Dict[str, int] = {}

        # 1. Edición 2024 (5.5e / SRD 5.2)
        actors24_path = os.path.join(packs_root, "actors24")
        if os.path.exists(actors24_path):
            cnt = self.ingest_foundry_pack(actors24_path, category="monsters", edition="5.5e", bilingue=bilingue)
            results["monsters_2024"] = cnt

        spells24_path = os.path.join(packs_root, "spells24")
        if os.path.exists(spells24_path):
            cnt = self.ingest_foundry_pack(spells24_path, category="spells", edition="5.5e", bilingue=bilingue)
            results["spells_2024"] = cnt

        equipment24_path = os.path.join(packs_root, "equipment24")
        if os.path.exists(equipment24_path):
            cnt = self.ingest_foundry_pack(equipment24_path, category="items", edition="5.5e", bilingue=bilingue)
            results["items_2024"] = cnt

        # 2. Edición 2014 (5e / SRD 5.1)
        monsters14_path = os.path.join(packs_root, "monsters")
        if os.path.exists(monsters14_path):
            cnt = self.ingest_foundry_pack(monsters14_path, category="monsters", edition="5e", bilingue=bilingue)
            results["monsters_2014"] = cnt

        spells14_path = os.path.join(packs_root, "spells")
        if os.path.exists(spells14_path):
            cnt = self.ingest_foundry_pack(spells14_path, category="spells", edition="5e", bilingue=bilingue)
            results["spells_2014"] = cnt

        items14_path = os.path.join(packs_root, "items")
        if os.path.exists(items14_path):
            cnt = self.ingest_foundry_pack(items14_path, category="items", edition="5e", bilingue=bilingue)
            results["items_2014"] = cnt

        return results
