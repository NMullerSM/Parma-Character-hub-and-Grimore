"""
Motor e ingestor del compendio D&D 5.5e (2024 PHB / SRD 5.2) a SQLite relacional.
Normaliza e indexa monstruos, conjuros y equipo (incluyendo Weapon Mastery)
provenientes de fuentes JSON de 5etools y Foundry VTT SRD.
"""
import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Union
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
        # Formatear números enteros limpiamente
        cr_text = str(int(val)) if val.is_integer() else str(val)
        return val, cr_text
    except ValueError:
        return 0.0, "0"


def normalize_monster(raw: Dict[str, Any], default_edition: str = "5.5e", default_lang: str = "en") -> Dict[str, Any]:
    """Normaliza una entrada de monstruo de 5etools / Foundry al esquema de compendium_monsters."""
    name = raw.get("name", "Unknown Creature")
    source = raw.get("source", "XPHB")
    edition = "5.5e" if any(k in str(source).upper() for k in ("XPHB", "2024", "5.5")) else default_edition
    entity_id = raw.get("entity_id") or raw.get("id") or f"{name.lower().replace(' ', '_')}_{edition.replace('.', '')}"

    cr_float, cr_text = parse_cr_to_float(raw.get("cr", "0"))

    # Extraer tipo de criatura
    raw_type = raw.get("type", "Monstrosity")
    if isinstance(raw_type, dict):
        m_type = raw_type.get("type", "Monstrosity")
    else:
        m_type = str(raw_type).split()[0].rstrip(",;").capitalize()

    # Tamaño
    size_raw = raw.get("size", "M")
    size_map = {
        "T": "Tiny", "S": "Small", "M": "Medium",
        "L": "Large", "H": "Huge", "G": "Gargantuan"
    }
    if isinstance(size_raw, list) and size_raw:
        size_raw = size_raw[0]
    size = size_map.get(str(size_raw).upper(), str(size_raw).capitalize() or "Medium")

    # Armadura (AC)
    ac_raw = raw.get("ac", 10)
    ac = 10
    if isinstance(ac_raw, list) and ac_raw:
        first_ac = ac_raw[0]
        ac = first_ac.get("ac", 10) if isinstance(first_ac, dict) else int(first_ac)
    elif isinstance(ac_raw, dict):
        ac = int(ac_raw.get("ac", 10))
    elif isinstance(ac_raw, (int, float, str)) and str(ac_raw).isdigit():
        ac = int(ac_raw)

    # Puntos de golpe (HP)
    hp_raw = raw.get("hp", {})
    hp_avg = 10
    hp_formula = ""
    if isinstance(hp_raw, dict):
        hp_avg = int(hp_raw.get("average", hp_raw.get("special", 10) if str(hp_raw.get("special", "")).isdigit() else 10))
        hp_formula = str(hp_raw.get("formula", ""))
    elif isinstance(hp_raw, (int, float, str)) and str(hp_raw).isdigit():
        hp_avg = int(hp_raw)

    # Velocidad
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

    # Tiempo de lanzamiento
    time_raw = raw.get("time") or raw.get("casting_time") or "1 action"
    if isinstance(time_raw, list) and time_raw:
        t0 = time_raw[0]
        time_str = f"{t0.get('number', 1)} {t0.get('unit', 'action')}" if isinstance(t0, dict) else str(t0)
    else:
        time_str = str(time_raw)

    # Alcance
    range_raw = raw.get("range") or raw.get("range_area") or "60 feet"
    if isinstance(range_raw, dict):
        dist = range_raw.get("distance", {})
        if isinstance(dist, dict):
            range_str = f"{dist.get('amount', '')} {dist.get('type', 'feet')}".strip() or "Self"
        else:
            range_str = str(range_raw.get("type", "Self"))
    else:
        range_str = str(range_raw)

    # Componentes
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

    # Duración y concentración
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

    # Clases
    classes_raw = raw.get("classes", [])
    if isinstance(classes_raw, dict):
        from_class = classes_raw.get("fromClassList", [])
        classes_list = [c.get("name") for c in from_class if isinstance(c, dict) and "name" in c]
    elif isinstance(classes_raw, list):
        classes_list = [str(c) for c in classes_raw]
    else:
        classes_list = [s.strip() for s in str(classes_raw).split(",") if s.strip()]

    # Descripción
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

    # Tipo de ítem
    raw_type = str(raw.get("type", "gear")).lower()
    item_type = "gear"
    if "weapon" in raw_type or raw.get("weaponCategory"):
        item_type = "weapon"
    elif "armor" in raw_type or raw.get("armorCategory"):
        item_type = "armor"
    elif raw.get("wondrous") or "magic" in raw_type:
        item_type = "magic_item"

    # Weapon Mastery (Regla 5.5e)
    mastery = str(raw.get("mastery") or raw.get("weapon_mastery", "")).strip().lower()
    if mastery not in VALID_WEAPON_MASTERIES:
        # Detectar si viene dentro de entries o notas
        mastery = ""
        for word in VALID_WEAPON_MASTERIES:
            if re.search(rf"\b{word}\b", str(raw.get("entries", "")).lower()):
                mastery = word
                break

    # Daño
    dmg1 = raw.get("dmg1", "")
    dmg_type = raw.get("dmgType", "")
    if dmg_type:
        type_map = {"S": "slashing", "P": "piercing", "B": "bludgeoning"}
        dmg_type = type_map.get(str(dmg_type).upper(), str(dmg_type))

    # Costo y peso
    cost_val = raw.get("value") or raw.get("cost", "")
    cost = f"{cost_val / 100:.1f} gp" if isinstance(cost_val, (int, float)) else str(cost_val)
    weight_val = raw.get("weight", "")
    weight = f"{weight_val} lb." if weight_val else ""

    # CA
    ac_bonus = int(raw.get("ac", 0) or raw.get("ac_bonus", 0))

    # Descripción
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


class CompendiumImporter:
    """Ingestor de compendios hacia SQLite DatabaseManager."""

    def __init__(self, db: DatabaseManager):
        self.db = db

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
        """Lee un archivo JSON estructurado (formato 5etools / Foundry) e ingesta su contenido."""
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
