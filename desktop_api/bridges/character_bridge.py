"""
Sub-puente para gestión de personajes (CRUD, wizard, forja, compendio OKF, diarios, red y configuración).
"""
import os
import sys
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import webview

from core.models import (
    CharacterSheet,
    WeaponAction,
    EquipmentItem,
    SpellItem,
    SpellSlotTier,
    CharacterFeature,
    SessionLog,
    NetworkNode,
    NetworkEdge,
)
from core.point_buy import PointBuyCalculator, TOTAL_BUDGET, MIN_SCORE, MAX_SCORE
from core.quick_build import QuickBuildEngine, CLASS_QUICK_PRESETS, STANDARD_ARRAY
from core.random_generator import (
    RandomCharacterGenerator,
    CLASSES_LIST,
    SPECIES_LIST,
    ALIGNMENTS_LIST,
)
from core.rules import (
    SKILLS_MAP,
    CLASS_HIT_DICE,
    CLASS_CASTING_ABILITY,
    DND_CONDITIONS,
    calc_modifier,
    calc_proficiency_bonus,
    get_skill_modifier,
    get_saving_throw_modifier,
    get_character_spell_stats,
    perform_short_rest,
    perform_long_rest,
    compute_dynamic_features,
    get_class_progression_limits,
    CLASS_NAMES_EN_TO_ES,
)
from core.srd_importer import SrdImporter


# Tabla de ranuras de conjuro para lanzadores completos (Nvl 1-20)
FULL_CASTER_SLOTS: Dict[int, Dict[str, int]] = {
    1: {"1": 2},
    2: {"1": 3},
    3: {"1": 4, "2": 2},
    4: {"1": 4, "2": 3},
    5: {"1": 4, "2": 3, "3": 2},
    6: {"1": 4, "2": 3, "3": 3},
    7: {"1": 4, "2": 3, "3": 3, "4": 1},
    8: {"1": 4, "2": 3, "3": 3, "4": 2},
    9: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    10: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    11: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    12: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    13: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    16: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1},
}


def _compute_spell_slots_for_class(char_class: str, level: int) -> Dict[str, SpellSlotTier]:
    """Calcula las ranuras de conjuro oficiales según la clase y nivel."""
    tiers = {str(i): SpellSlotTier(level=i, total=0, current=0) for i in range(1, 10)}
    c_norm = char_class.strip()
    full_casters = {"Bardo", "Clérigo", "Druida", "Hechicero", "Mago"}
    half_casters = {"Paladín", "Explorador", "Artífice"}

    if c_norm in full_casters:
        slot_map = FULL_CASTER_SLOTS.get(max(1, min(20, level)), {})
        for lvl_str, count in slot_map.items():
            tiers[lvl_str] = SpellSlotTier(level=int(lvl_str), total=count, current=count)
    elif c_norm in half_casters:
        eff_level = max(1, (level + 1) // 2)
        slot_map = FULL_CASTER_SLOTS.get(min(10, eff_level), {})
        for lvl_str, count in slot_map.items():
            tiers[lvl_str] = SpellSlotTier(level=int(lvl_str), total=count, current=count)
    elif c_norm == "Brujo":
        pact_lvl = min(5, (level + 1) // 2)
        pact_slots = 1 if level == 1 else (2 if level < 11 else (3 if level < 17 else 4))
        tiers[str(pact_lvl)] = SpellSlotTier(level=pact_lvl, total=pact_slots, current=pact_slots)

    return tiers


class CharacterBridgeMixin:
    """Métodos de personajes: CRUD, asistente de creación, compendio OKF, redes y configuración."""

    def _is_active_character_id(self, char_id: int) -> bool:
        active = self._db.get_active_character()
        return bool(active and active.id == char_id)

    @staticmethod
    def _parse_speed_feet(speed_val: Any) -> int:
        if isinstance(speed_val, (int, float)):
            return int(speed_val)
        s = str(speed_val or "30").lower()
        if "7.5" in s or "7,5" in s or "25" in s:
            return 25
        if "10.5" in s or "10,5" in s or "35" in s:
            return 35
        if "12" in s or "40" in s:
            return 40
        return 30

    def _serialize_character(self, char: Optional[CharacterSheet], lang: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Adaptador bidireccional: transforma un CharacterSheet de Python en el contrato
        enriquecido y precalculado que consume el frontend de React, conservando también
        todos los campos canónicos del modelo y soportando campos bilingües.
        """
        if not char:
            return None

        active_lang = lang or self._db.get_setting("language", "es")
        prof_bonus = calc_proficiency_bonus(char.level)
        char.proficiency_bonus = prof_bonus

        # 1. Atributos enriquecidos (FUE, DES, CON, INT, SAB, CAR)
        stat_order = ["FUE", "DES", "CON", "INT", "SAB", "CAR"]
        abilities_out: Dict[str, Dict[str, Any]] = {}
        for st in stat_order:
            raw_val = char.abilities.get(st, 10)
            score = int(raw_val) if not isinstance(raw_val, dict) else int(raw_val.get("base", 10))
            char.abilities[st] = score
            mod = calc_modifier(score)
            is_prof = st in (char.saving_throw_profs or [])
            save_bon = get_saving_throw_modifier(char, st)
            abilities_out[st] = {
                "base": score,
                "override": 0,
                "bonus": mod,
                "proficient": is_prof,
                "save_bonus": save_bon,
            }

        # 2. Las 18 habilidades oficiales calculadas con reglas 5e
        skills_out: Dict[str, Dict[str, Any]] = {}
        for sk_name in sorted(SKILLS_MAP.keys()):
            prof_type = char.skills.get(sk_name, "none")
            sk_bonus = get_skill_modifier(char, sk_name)
            skills_out[sk_name] = {
                "stat": SKILLS_MAP[sk_name],
                "proficient": prof_type in ("proficient", "expertise"),
                "expertise": prof_type == "expertise",
                "bonus": sk_bonus,
            }

        # 3. Armas / Acciones de Combate
        weapon_actions_out = []
        for w in char.weapons:
            is_ranged = any(k in (w.notes or "").lower() or k in w.name.lower() for k in ("arco", "ballesta", "munición", "arrojadiza", "honda", "dardo"))
            weapon_actions_out.append({
                "name": w.name,
                "type": "A distancia / Arrojadiza" if is_ranged else "Cuerpo a cuerpo",
                "range_val": "Variable" if is_ranged else "1.5 m (5 pies)",
                "hit_dc": w.attack_bonus,
                "damage_dice": w.damage,
                "damage_type": w.damage_type,
                "notes": w.notes,
            })

        # 4. Ranuras de Conjuro y Lista de Conjuros
        slots_total: Dict[str, int] = {}
        slots_used: Dict[str, int] = {}
        for lvl_str, tier in (char.spell_slots or {}).items():
            t_tot = tier.total if hasattr(tier, "total") else int(tier.get("total", 0))
            t_cur = tier.current if hasattr(tier, "current") else int(tier.get("current", 0))
            if t_tot > 0:
                slots_total[str(lvl_str)] = t_tot
                slots_used[str(lvl_str)] = max(0, t_tot - t_cur)

        # 4b. Equipamiento e Inventario
        equipment_out = []
        for eq in getattr(char, "equipment", []) or []:
            equipment_out.append({
                "id": getattr(eq, "id", "") or str(getattr(eq, "name", "")).lower().replace(" ", "_"),
                "name": getattr(eq, "name", ""),
                "name_en": getattr(eq, "name_en", "") or getattr(eq, "name", ""),
                "item_type": getattr(eq, "item_type", "Equipo"),
                "quantity": int(getattr(eq, "quantity", 1) or 1),
                "weight": getattr(eq, "weight", "") or "",
                "cost": getattr(eq, "cost", "") or "",
                "rarity": getattr(eq, "rarity", "común") or "común",
                "description": getattr(eq, "description", "") or "",
                "notes": getattr(eq, "notes", "") or "",
                "ac_bonus": int(getattr(eq, "ac_bonus", 0) or 0),
                "equipped": bool(getattr(eq, "equipped", False)),
            })

        # 4c. Límites canónicos de conjuros según clase y nivel
        prog_limits = get_class_progression_limits(char.char_class, char.level, edition="5.5e")
        cantrips_max = prog_limits.get("cantrips_limit", prog_limits.get("cantrips_known", 0))
        spells_prep_max = prog_limits.get("spells_limit", prog_limits.get("spells_prepared", 0))
        cantrips_current = sum(1 for sp in char.spells if int(getattr(sp, "level", 0)) == 0)
        spells_prep_current = sum(1 for sp in char.spells if int(getattr(sp, "level", 0)) > 0)
        spell_limits = {
            "cantrips_max": cantrips_max,
            "cantrips_current": cantrips_current,
            "spells_prepared_max": spells_prep_max,
            "spells_prepared_current": spells_prep_current,
        }

        spells_out = []
        for sp in char.spells:
            en_spell = self._okf.get_spell_item(sp.id or sp.name, lang="en")
            desc_en = en_spell.description if en_spell else ""
            name_en = en_spell.name if en_spell else (sp.name_en or sp.name)
            school_en = en_spell.school if en_spell else sp.school

            spells_out.append({
                "id": sp.id,
                "name": sp.name,
                "name_en": name_en,
                "level": sp.level,
                "school": sp.school,
                "school_en": school_en,
                "cast_time": sp.casting_time,
                "casting_time": sp.casting_time,
                "range_area": sp.range,
                "range": sp.range,
                "components": sp.components,
                "duration": sp.duration,
                "concentration": sp.concentration,
                "ritual": sp.ritual,
                "prepared": True,
                "notes": sp.description,
                "description": sp.description,
                "notes_en": desc_en or sp.description,
                "description_en": desc_en or sp.description,
                "higher_levels": sp.higher_levels,
                "source": sp.source,
            })

        # 5. Rasgos y Recursos de Clase (actualizados dinámicamente según reglas 5e e idioma)
        updated_features = compute_dynamic_features(char, lang=active_lang)
        char.features = updated_features
        features_out = [
            {
                "id": f.id or f"feat_{idx}",
                "name": f.name,
                "source": f.source,
                "description": f.description,
                "uses_max": f.uses_max,
                "uses_current": f.uses_current,
                "recharge": f.recharge,
            }
            for idx, f in enumerate(updated_features)
        ]

        # 6. Retrato en base64 si existe archivo local
        portrait_b64 = char.portrait_base64 or ""
        if not portrait_b64 and char.portrait_path and os.path.exists(char.portrait_path):
            try:
                ext = Path(char.portrait_path).suffix.lower().lstrip(".") or "png"
                if ext == "jpg":
                    ext = "jpeg"
                with open(char.portrait_path, "rb") as img_f:
                    b64_raw = base64.b64encode(img_f.read()).decode("ascii")
                    portrait_b64 = f"data:image/{ext};base64,{b64_raw}"
            except Exception:
                pass

        hd_max = max(1, getattr(char, "hit_dice_max", char.level) or char.level)
        hd_curr = getattr(char, "hit_dice_current", hd_max)
        hd_faces = getattr(char, "hit_dice_faces", CLASS_HIT_DICE.get(char.char_class, 8))

        raw_spell_stats = get_character_spell_stats(char)
        atk_bon_raw = raw_spell_stats.get("attack_bonus", 0)
        try:
            atk_bon_int = int(str(atk_bon_raw).replace("+", "").strip() or "0")
        except ValueError:
            atk_bon_int = 0
        dc_int = int(raw_spell_stats.get("save_dc", raw_spell_stats.get("dc", 10)))
        is_caster = (
            char.char_class in CLASS_CASTING_ABILITY
            or bool(slots_total)
            or bool(spells_out)
        )
        spell_stats = {
            "ability": raw_spell_stats.get("ability", "CAR"),
            "dc": dc_int,
            "save_dc": dc_int,
            "attack_bonus": atk_bon_int,
            "is_caster": is_caster,
        }

        return {
            "id": char.id,
            "name": char.name,
            "char_class": char.char_class,
            "subclass": char.subclass,
            "level": char.level,
            "race": char.race,
            "background": char.background,
            "alignment": char.alignment,
            "xp": char.xp,
            "inspiration": bool(char.inspiration),
            "proficiency_bonus": prof_bonus,
            "ac": int(char.armor_class),
            "armor_class": int(char.armor_class),
            "speed": self._parse_speed_feet(char.speed),
            "initiative": int(char.initiative_bonus),
            "initiative_bonus": int(char.initiative_bonus),
            "hp_current": int(char.hp_current),
            "hp_max": int(char.hp_max),
            "hp_temp": int(char.hp_temp),
            "hit_dice_max": int(hd_max),
            "hit_dice_current": f"{int(hd_curr)}d{int(hd_faces)}",
            "hit_dice_faces": int(hd_faces),
            "hit_dice_total": f"{int(hd_max)}d{int(hd_faces)}",
            "conditions": list(char.conditions or []),
            "death_save_successes": int(char.death_saves_success),
            "death_save_failures": int(char.death_saves_failure),
            "saving_throw_profs": list(char.saving_throw_profs or []),
            "abilities": abilities_out,
            "skills": skills_out,
            "spells": spells_out,
            "equipment": equipment_out,
            "spell_limits": spell_limits,
            "spell_slots_total": slots_total,
            "spell_slots_used": slots_used,
            "spell_stats": spell_stats,
            "weapon_actions": weapon_actions_out,
            "features": features_out,
            "senses": char.senses,
            "languages": char.languages,
            "proficiencies_extra": char.proficiencies_extra,
            "appearance": char.appearance,
            "history": char.history,
            "personality_traits": char.personality_traits,
            "ideals": char.ideals,
            "bonds": char.bonds,
            "flaws": char.flaws,
            "portrait_path": char.portrait_path,
            "portrait_base64": portrait_b64,
            "sessions": [
                {
                    "id": int(s.id) if str(s.id).isdigit() else idx + 1,
                    "date": s.date,
                    "title": s.title,
                    "summary": s.summary,
                    "loot": s.loot,
                    "xp_gained": int(s.xp_gained),
                }
                for idx, s in enumerate(char.sessions)
            ],
            "network_nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "role": n.role,
                    "description": n.description,
                    "avatar_base64": n.avatar_base64,
                    "x": float(n.x),
                    "y": float(n.y),
                }
                for n in char.network_nodes
            ],
            "network_edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation,
                }
                for e in char.network_edges
            ],
        }

    # =========================================================================
    # GESTIÓN DE PERSONAJES (CRUD)
    # =========================================================================

    def list_characters(self) -> List[Dict[str, Any]]:
        """Lista resumen de todos los personajes guardados."""
        return self._db.list_characters()

    def get_active_character(self) -> Optional[Dict[str, Any]]:
        """Obtiene el personaje activo actual en formato diccionario enriquecido."""
        char = self._db.get_active_character()
        return self._serialize_character(char)

    def get_character_by_id(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Carga un personaje por ID."""
        char = self._db.get_character_by_id(char_id)
        return self._serialize_character(char)

    def set_active_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Establece el personaje activo por ID y lo retorna."""
        char = self._db.set_active_character_by_id(char_id)
        return self._serialize_character(char)

    def save_character(self, character_dict: Dict[str, Any], set_active: bool = True) -> Dict[str, Any]:
        """Guarda o actualiza un personaje en SQLite y devuelve la ficha sincronizada."""
        try:
            # Si el personaje ya existe en BD, preservar campos que no vengan en updates parciales
            existing_id = character_dict.get("id")
            if existing_id is not None:
                existing_char = self._db.get_character_by_id(int(existing_id))
                if existing_char:
                    merged = existing_char.to_dict()
                    merged.update(character_dict)
                    character_dict = merged

            char = CharacterSheet.from_dict(character_dict)
            char_id = self._db.save_character(char, set_active=set_active)
            saved_char = self._db.get_character_by_id(char_id)
            return {
                "success": True,
                "id": char_id,
                "character": self._serialize_character(saved_char),
                "error": None,
            }
        except Exception as e:
            return {"success": False, "id": None, "error": str(e)}

    def delete_character(self, char_id: int) -> bool:
        """Elimina un personaje."""
        return self._db.delete_character(char_id)

    def export_character_json(self, char_id: int) -> Dict[str, Any]:
        """Exporta un personaje a un archivo JSON en data/characters/ (o mediante diálogo nativo)."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        clean_name = "".join(c for c in char.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        default_filename = f"{clean_name}_dnd5e.json"
        target_path = None
        char_dir = os.path.join(self._user_data_dir, "characters")
        os.makedirs(char_dir, exist_ok=True)

        if self._window:
            try:
                res = self._window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    directory=char_dir,
                    save_filename=default_filename,
                    file_types=("Archivos JSON (*.json)", "Todos los Archivos (*.*)"),
                )
                if res:
                    target_path = res[0] if isinstance(res, (list, tuple)) else str(res)
            except Exception:
                pass

        if not target_path:
            target_path = os.path.join(char_dir, default_filename)

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(char.to_dict(), f, ensure_ascii=False, indent=2)
            return {"success": True, "path": target_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_character_json(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Importa un personaje desde un archivo JSON y lo guarda en SQLite."""
        if not file_path:
            if not self._window:
                return {"success": False, "error": "Ventana nativa no disponible."}
            res = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("Archivos JSON (*.json)", "Todos los Archivos (*.*)"),
            )
            if not res or len(res) == 0:
                return {"success": False, "cancelled": True}
            file_path = res[0]

        if not os.path.exists(file_path):
            return {"success": False, "error": f"Archivo no encontrado: {file_path}"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.pop("id", None)
            char = CharacterSheet.from_dict(data)
            char_id = self._db.save_character(char, set_active=True)
            saved = self._db.get_character_by_id(char_id)
            return {"success": True, "id": char_id, "character": self._serialize_character(saved)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # FORJA DE PERSONAJES (OKF + POINT BUY + QUICK BUILD + RANDOMIZE)
    # =========================================================================

    def get_builder_catalog(self, edition: Optional[str] = None, lang: str = "es", expansions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Devuelve el catálogo dinámico completo desde OkfEngine y SQLite para poblar la Forja:
        especies, linajes, clases, subclases, trasfondos, dotes de origen y condiciones.
        Adapta niveles de subclase y filtra según edición y expansiones activas.
        """
        ed = edition or self._db.get_setting("dnd_edition", "5.5e")
        is_2024 = (ed == "5.5e")

        subclass_lvl_2014 = {
            "Clérigo": 1,
            "Brujo": 1,
            "Hechicero": 1,
            "Druida": 2,
            "Mago": 2,
        }

        default_bonuses = {
            "Humano": {"FUE": 1, "DES": 1, "CON": 1, "INT": 1, "SAB": 1, "CAR": 1},
            "Elfo": {"DES": 2, "INT": 1},
            "Enano": {"CON": 2, "SAB": 1},
            "Mediano": {"DES": 2, "CAR": 1},
            "Tiefling": {"CAR": 2, "INT": 1},
            "Dracónido": {"FUE": 2, "CAR": 1},
            "Semielfo": {"CAR": 2, "DES": 1, "CON": 1},
            "Orco": {"FUE": 2, "CON": 1},
            "Semiorco": {"FUE": 2, "CON": 1},
            "Gnomo": {"INT": 2, "DES": 1},
            "Goliath": {"FUE": 2, "CON": 1},
            "Aasimar": {"CAR": 2, "SAB": 1},
        }

        # Consultar entidades desde SQLite (compendium_entities) con fallback a OkfEngine
        db_species = self._db.search_compendium_entities(categories=["especie"], language=lang, limit=100)
        db_lineages = self._db.search_compendium_entities(categories=["especie_linaje", "linaje"], language=lang, limit=100)
        db_classes = self._db.search_compendium_entities(categories=["clase"], language=lang, limit=100)
        db_subclasses = self._db.search_compendium_entities(categories=["subclase"], language=lang, limit=200)
        db_backgrounds = self._db.search_compendium_entities(categories=["trasfondo"], language=lang, limit=100)

        # 1. ESPECIES Y LINEAJES
        species_out = []
        if db_species:
            for row in db_species:
                try:
                    sp_data = json.loads(row.get("data_json") or "{}")
                except Exception:
                    sp_data = {}
                sp_name = row.get("name") or sp_data.get("nombre") or row.get("entity_id")
                sp_id = sp_data.get("id") or row.get("entity_id")
                
                # Buscar linajes asociados
                subrace_names = []
                for lin_row in db_lineages:
                    try:
                        lin_data = json.loads(lin_row.get("data_json") or "{}")
                    except Exception:
                        lin_data = {}
                    padre = lin_data.get("especie_padre") or lin_data.get("especie") or ""
                    if padre.lower() in (sp_name.lower(), str(sp_data.get("nombre_espanol", "")).lower(), str(sp_data.get("nombre_ingles", "")).lower(), sp_id.lower().replace("_en", "")):
                        subrace_names.append(lin_row.get("name") or lin_data.get("nombre"))
                if not subrace_names:
                    subrace_names = ["Estándar" if lang == "es" else "Standard"]

                raw_traits = sp_data.get("rasgos_principales", "")
                if isinstance(raw_traits, list):
                    trait_items = [{"name": str(t), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits]
                elif isinstance(raw_traits, str) and raw_traits.strip():
                    trait_items = [{"name": t.strip(), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits.split(",") if t.strip()]
                else:
                    trait_items = [{"name": f"Herencia de {sp_name}" if lang == "es" else f"{sp_name} Heritage", "desc": sp_data.get("sentidos", "Visión Normal" if lang == "es" else "Normal Vision")}]

                species_out.append({
                    "id": sp_id,
                    "name": sp_name,
                    "subraces": subrace_names,
                    "speed": self._parse_speed_feet(sp_data.get("velocidad", "9 m")),
                    "bonuses": default_bonuses.get(sp_name, default_bonuses.get(sp_data.get("nombre_original", ""), {"FUE": 1, "CON": 1})),
                    "traits": trait_items,
                })
        else:
            raw_species = self._okf.get_species(lang=lang)
            for sp in raw_species:
                sp_name = sp["nombre"]
                lineages = self._okf.get_lineages(sp["id"], lang=lang) or self._okf.get_lineages(sp_name, lang=lang)
                subrace_names = [lin["nombre"] for lin in lineages] if lineages else ["Estándar" if lang == "es" else "Standard"]
                raw_traits = sp.get("rasgos_principales", "")
                if isinstance(raw_traits, list):
                    trait_items = [{"name": str(t), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits]
                elif isinstance(raw_traits, str) and raw_traits.strip():
                    trait_items = [{"name": t.strip(), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits.split(",") if t.strip()]
                else:
                    trait_items = [{"name": f"Herencia de {sp_name}" if lang == "es" else f"{sp_name} Heritage", "desc": sp.get("sentidos", "Visión Normal" if lang == "es" else "Normal Vision")}]

                species_out.append({
                    "id": sp["id"],
                    "name": sp_name,
                    "subraces": subrace_names,
                    "speed": self._parse_speed_feet(sp.get("velocidad", "9 m")),
                    "bonuses": default_bonuses.get(sp_name, {"FUE": 1, "CON": 1}),
                    "traits": trait_items,
                })

        all_skill_names = list(SKILLS_MAP.keys())
        classes_out = []

        # 2. CLASES Y SUBCLASES
        if db_classes:
            for c_row in db_classes:
                try:
                    c_data = json.loads(c_row.get("data_json") or "{}")
                except Exception:
                    c_data = {}
                c_name = c_row.get("name") or c_data.get("nombre")
                c_id = c_data.get("id") or c_row.get("entity_id")
                sub_lvl = 3 if is_2024 else subclass_lvl_2014.get(c_name, 3)

                # Subclases desde db_subclasses o c_data.subclases_oficiales
                sub_names = []
                for sc_row in db_subclasses:
                    try:
                        sc_data = json.loads(sc_row.get("data_json") or "{}")
                    except Exception:
                        sc_data = {}
                    padre = sc_data.get("clase_padre") or ""
                    if padre.lower() in (c_name.lower(), str(c_data.get("nombre_espanol", "")).lower(), str(c_data.get("nombre_ingles", "")).lower(), c_id.lower().replace("_en", "")):
                        s_fuente = str(sc_data.get("fuente", "")).lower()
                        if expansions and "all" not in [e.lower() for e in expansions]:
                            exp_set = {e.lower() for e in expansions}
                            if "tasha" in s_fuente and "tce" not in exp_set and "tasha's cauldron of everything" not in exp_set:
                                continue
                            if "xanathar" in s_fuente and "xge" not in exp_set and "xanathar's guide to everything" not in exp_set:
                                continue
                        sub_names.append(sc_row.get("name") or sc_data.get("nombre"))

                if not sub_names and c_data.get("subclases_oficiales"):
                    sub_names = list(c_data.get("subclases_oficiales", []))

                if not sub_names:
                    sub_names = [f"Arquetipo de {c_name}" if lang == "es" else f"{c_name} Archetype"]

                preset = CLASS_QUICK_PRESETS.get(c_name, CLASS_QUICK_PRESETS.get("Guerrero", {}))
                rec_skills = list(preset.get("skills", ["Atletismo", "Percepción"]))
                extra_skills = [sk for sk in all_skill_names if sk not in rec_skills][:6]
                skill_opts = rec_skills + extra_skills
                hit_die_raw = str(c_data.get("dado_golpe", "1d8"))
                hd_match = re.search(r'd(\d+)', hit_die_raw)
                hit_die_val = int(hd_match.group(1)) if hd_match else 8
                is_caster = c_name in CLASS_CASTING_ABILITY or str(c_data.get("nombre_original", "")) in CLASS_CASTING_ABILITY

                classes_out.append({
                    "id": c_id,
                    "name": c_name,
                    "hit_die": hit_die_val,
                    "primary_ability": c_data.get("caracteristica_principal", "FUE" if lang == "es" else "STR"),
                    "saves": list(c_data.get("salvaciones_competentes", ["FUE", "CON"] if lang == "es" else ["STR", "CON"])),
                    "skill_choices_count": 4 if c_name in ("Pícaro", "Rogue") else (3 if c_name in ("Bardo", "Bard", "Explorador", "Ranger") else 2),
                    "skill_options": skill_opts,
                    "subclasses": sub_names,
                    "subclass_unlock_level": sub_lvl,
                    "is_caster": is_caster,
                })
        else:
            raw_classes = self._okf.get_classes(lang=lang)
            for c in raw_classes:
                c_name = c["nombre"]
                sub_lvl = 3 if is_2024 else subclass_lvl_2014.get(c_name, 3)
                subs = self._okf.get_subclasses(c_name, lang=lang)
                if expansions and "all" not in [e.lower() for e in expansions]:
                    exp_set = {e.lower() for e in expansions}
                    filtered_subs = []
                    for s in subs:
                        s_fuente = str(s.get("fuente", "")).lower()
                        if "tasha" in s_fuente and "tce" not in exp_set and "tasha's cauldron of everything" not in exp_set:
                            continue
                        if "xanathar" in s_fuente and "xge" not in exp_set and "xanathar's guide to everything" not in exp_set:
                            continue
                        filtered_subs.append(s)
                    subs = filtered_subs
                sub_names = [s["nombre"] for s in subs] if subs else [f"Arquetipo de {c_name}" if lang == "es" else f"{c_name} Archetype"]
                preset = CLASS_QUICK_PRESETS.get(c_name, CLASS_QUICK_PRESETS.get("Guerrero", {}))
                rec_skills = list(preset.get("skills", ["Atletismo", "Percepción"]))
                extra_skills = [sk for sk in all_skill_names if sk not in rec_skills][:6]
                skill_opts = rec_skills + extra_skills
                hit_die_val = int(c.get("hit_dice", CLASS_HIT_DICE.get(c_name, 8)))
                is_caster = c_name in CLASS_CASTING_ABILITY

                classes_out.append({
                    "id": c["id"],
                    "name": c_name,
                    "hit_die": hit_die_val,
                    "primary_ability": c.get("caracteristica_principal", "FUE"),
                    "saves": list(c.get("saves", ["FUE", "CON"])),
                    "skill_choices_count": 4 if c_name in ("Pícaro", "Rogue") else (3 if c_name in ("Bardo", "Bard", "Explorador", "Ranger") else 2),
                    "skill_options": skill_opts,
                    "subclasses": sub_names,
                    "subclass_unlock_level": sub_lvl,
                    "is_caster": is_caster,
                })

        # 3. TRASFONDOS
        backgrounds_out = []
        if db_backgrounds:
            for b_row in db_backgrounds:
                try:
                    b_data = json.loads(b_row.get("data_json") or "{}")
                except Exception:
                    b_data = {}
                b_name = b_row.get("name") or b_data.get("nombre")
                raw_sk = b_data.get("habilidades_competentes", "Atletismo, Percepción")
                if isinstance(raw_sk, list):
                    sk_list = [str(s).strip() for s in raw_sk if str(s).strip()]
                else:
                    sk_list = [s.strip() for s in str(raw_sk).split(",") if s.strip()]
                backgrounds_out.append({
                    "id": b_data.get("id") or b_row.get("entity_id"),
                    "name": b_name,
                    "skills": sk_list[:2] if sk_list else ["Atletismo", "Percepción"],
                    "feature_name": b_data.get("dote_concedida", "Dote de Origen" if lang == "es" else "Origin Feat"),
                    "feature_desc": f"Atributos clave: {b_data.get('caracteristicas_clave', 'FUE, CON')}." if lang == "es" else f"Key Abilities: {b_data.get('caracteristicas_clave', 'STR, CON')}.",
                })
        else:
            for b in self._okf.get_backgrounds(lang=lang):
                raw_sk = b.get("habilidades_competentes", "Atletismo, Percepción")
                if isinstance(raw_sk, list):
                    sk_list = [str(s).strip() for s in raw_sk if str(s).strip()]
                else:
                    sk_list = [s.strip() for s in str(raw_sk).split(",") if s.strip()]
                backgrounds_out.append({
                    "id": b["id"],
                    "name": b["nombre"],
                    "skills": sk_list[:2] if sk_list else ["Atletismo", "Percepción"],
                    "feature_name": b.get("dote_concedida", "Dote de Origen" if lang == "es" else "Origin Feat"),
                    "feature_desc": f"Atributos clave: {b.get('caracteristicas_clave', 'FUE, CON')}." if lang == "es" else f"Key Abilities: {b.get('caracteristicas_clave', 'STR, CON')}.",
                })

        return {
            "edition": ed,
            "species": species_out,
            "classes": classes_out,
            "backgrounds": backgrounds_out,
            "all_skills": all_skill_names,
        }

    def _spell_row_to_dict(self, row: Dict[str, Any], lang: str = "es") -> Dict[str, Any]:
        """Convierte una fila de compendium_spells (SQLite) al formato de salida de conjuros del frontend."""
        classes_list = [c.strip() for c in str(row.get("classes") or "").split(",") if c.strip()]
        # Reusa el formateo de casillas/turnos ya validado en OkfEngine (son @staticmethod, sin estado propio).
        range_fmt = self._okf._format_range_with_tiles(row.get("range_area", "18 m"), lang=lang)
        duration_fmt = self._okf._format_duration_with_turns(row.get("duration", "Instantáneo"), lang=lang)
        return {
            "id": row.get("entity_id"),
            "name": row.get("name", ""),
            "name_en": row.get("name_en", row.get("name", "")),
            "level": int(row.get("level", 0)),
            "school": row.get("school", "Evocación"),
            "cast_time": row.get("casting_time", "1 acción"),
            "casting_time": row.get("casting_time", "1 acción"),
            "range_area": range_fmt,
            "range": range_fmt,
            "components": row.get("components", "V, S"),
            "duration": duration_fmt,
            "concentration": bool(row.get("is_concentration", 0)),
            "ritual": bool(row.get("is_ritual", 0)),
            "classes": classes_list,
            "prepared": True,
            "notes": row.get("description", ""),
            "description": row.get("description", ""),
            "source": row.get("source", ""),
        }

    def get_class_spells(self, class_name: str, max_level: int = 1, lang: str = "es") -> List[Dict[str, Any]]:
        """Obtiene los trucos y conjuros disponibles para una clase desde SQLite con fallback a OkfEngine."""
        c_raw = (class_name or "").strip()
        c_clean = CLASS_NAMES_EN_TO_ES.get(c_raw.lower(), c_raw)
        ed = self._db.get_setting("dnd_edition", "5.5e")
        rows = self._db.search_compendium_spells(class_name=c_clean, max_level=max_level, language=lang, edition=ed, limit=200)
        if rows:
            return [self._spell_row_to_dict(r, lang=lang) for r in rows]

        # Fallback a OKF si la tabla no tiene datos para esta combinación (no debería pasar en la práctica)
        items = self._okf.get_spells_for_class(class_name, max_spell_level=max_level, min_spell_level=0, lang=lang)
        return [
            {
                "name": s.get("nombre", ""),
                "level": int(s.get("nivel", 0)),
                "school": s.get("escuela", "Evocación"),
                "cast_time": s.get("tiempo_lanzamiento", "1 acción"),
                "range_area": s.get("alcance", "18 m"),
                "components": s.get("componentes", "V, S"),
                "duration": s.get("duracion", "Instantáneo"),
                "prepared": True,
                "notes": s.get("descripcion", ""),
            }
            for s in items
        ]

    def get_class_progression_limits(
        self,
        class_name: str,
        level: int,
        edition: str = "5.5e",
        ability_mod: int = 0,
        has_magic_initiate: bool = False
    ) -> Dict[str, Any]:
        """Calcula los límites canónicos de conjuros conocidos/preparados y ranuras mágicas."""
        return get_class_progression_limits(
            class_name=class_name,
            level=level,
            edition=edition,
            ability_mod=ability_mod,
            has_magic_initiate=has_magic_initiate
        )

    def get_available_spells(
        self,
        class_name: Optional[str] = None,
        max_level: Optional[int] = None,
        query: str = "",
        school: Optional[str] = None,
        level: Optional[int] = None,
        limit: int = 150,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Busca conjuros enriquecidos en SQLite (compendium_spells) con fallback a OkfEngine."""
        c_clean = None
        if class_name:
            c_raw = class_name.strip()
            c_clean = CLASS_NAMES_EN_TO_ES.get(c_raw.lower(), c_raw)
        ed = self._db.get_setting("dnd_edition", "5.5e")

        rows = self._db.search_compendium_spells(
            query=query, class_name=c_clean, level=level, max_level=max_level,
            school=school, language=lang, edition=ed, limit=limit
        )
        if rows:
            return [self._spell_row_to_dict(r, lang=lang) for r in rows]

        # Fallback a OKF si la tabla no tiene datos para esta combinación
        return self._okf.search_available_spells(
            query=query, class_name=class_name, level=level, max_level=max_level,
            school=school, limit=limit, lang=lang
        )

    def add_spell_to_character(self, char_id: int, spell_data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade un conjuro a la ficha del personaje y lo guarda en SQLite."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        s_name = str(spell_data.get("name", "")).strip()
        if not s_name:
            return {"success": False, "error": "Nombre de conjuro inválido"}

        for existing in char.spells:
            if existing.name.lower().strip() == s_name.lower():
                return {"success": True, "already_exists": True, "character": self._serialize_character(char)}

        # Validación canónica de límites de conjuros según clase y nivel
        spell_level = int(spell_data.get("level", 0))
        prog_limits = get_class_progression_limits(char.char_class, char.level, edition="5.5e")
        cantrips_max = prog_limits.get("cantrips_limit", prog_limits.get("cantrips_known", 0))
        spells_prep_max = prog_limits.get("spells_limit", prog_limits.get("spells_prepared", 0))

        cantrips_current = sum(1 for sp in char.spells if int(getattr(sp, "level", 0)) == 0)
        spells_prep_current = sum(1 for sp in char.spells if int(getattr(sp, "level", 0)) > 0)

        if spell_level == 0:
            if cantrips_max > 0 and cantrips_current >= cantrips_max:
                return {
                    "success": False,
                    "error": f"Límite de trucos alcanzado ({cantrips_current}/{cantrips_max}) para {char.char_class} nivel {char.level}"
                }
        else:
            if spells_prep_max > 0 and spells_prep_current >= spells_prep_max:
                return {
                    "success": False,
                    "error": f"Límite de conjuros preparados alcanzado ({spells_prep_current}/{spells_prep_max}) para {char.char_class} nivel {char.level}"
                }

        new_spell = SpellItem(
            id=spell_data.get("id", s_name.lower().replace(" ", "_")),
            name=s_name,
            name_en=spell_data.get("name_en", s_name),
            level=int(spell_data.get("level", 0)),
            school=spell_data.get("school", "Evocación"),
            casting_time=spell_data.get("cast_time") or spell_data.get("casting_time", "1 acción"),
            range=spell_data.get("range_area") or spell_data.get("range", "18 m"),
            components=spell_data.get("components", "V, S"),
            duration=spell_data.get("duration", "Instantáneo"),
            concentration=bool(spell_data.get("concentration", False)),
            ritual=bool(spell_data.get("ritual", False)),
            description=spell_data.get("description") or spell_data.get("notes", ""),
            higher_levels=spell_data.get("higher_levels", ""),
            source=spell_data.get("source", "PHB 2024"),
            classes=spell_data.get("classes", [])
        )
        char.spells.append(new_spell)
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def remove_spell_from_character(self, char_id: int, spell_name: str) -> Dict[str, Any]:
        """Elimina un conjuro de la ficha del personaje y guarda en SQLite."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        s_clean = spell_name.lower().strip()
        char.spells = [s for s in char.spells if s.name.lower().strip() != s_clean]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def add_item_to_character(self, char_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade un objeto/arma/armadura a la ficha del personaje y lo guarda en SQLite."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        i_name = str(item_data.get("name", "")).strip()
        if not i_name:
            return {"success": False, "error": "Nombre de ítem inválido"}

        item_type = str(item_data.get("item_type", "")).lower()
        is_weapon = "arma" in item_type or "weapon" in item_type or bool(item_data.get("damage"))

        # Si es un arma, añadir también a char.weapons para Acciones de Combate
        if is_weapon:
            existing_wpn = next((w for w in char.weapons if w.name.lower().strip() == i_name.lower()), None)
            if not existing_wpn:
                dmg = item_data.get("damage") or "1d6"
                dmg_type = item_data.get("damage_type") or "Cortante"
                mastery = item_data.get("weapon_mastery") or ""
                notes = f"Dominio: {mastery}" if mastery else str(item_data.get("notes") or "")

                fue_mod = calc_modifier(char.abilities.get("FUE", 10))
                des_mod = calc_modifier(char.abilities.get("DES", 10))
                is_finesse_or_ranged = any(k in str(item_data.get("notes") or "").lower() for k in ("sutil", "finesse", "distancia", "ranged"))
                best_mod = max(fue_mod, des_mod) if is_finesse_or_ranged else fue_mod
                atk_bon = best_mod + calc_proficiency_bonus(char.level)
                atk_bon_str = f"+{atk_bon}" if atk_bon >= 0 else str(atk_bon)

                char.weapons.append(WeaponAction(
                    name=i_name,
                    attack_bonus=atk_bon_str,
                    damage=f"{dmg}+{best_mod}" if best_mod > 0 else dmg,
                    damage_type=dmg_type,
                    notes=notes
                ))

        # Añadir al inventario de equipo
        if not hasattr(char, "equipment") or char.equipment is None:
            char.equipment = []

        existing_item = next((eq for eq in char.equipment if eq.name.lower().strip() == i_name.lower()), None)
        if existing_item:
            existing_item.quantity = getattr(existing_item, "quantity", 1) + int(item_data.get("quantity", 1) or 1)
        else:
            new_item = EquipmentItem(
                id=item_data.get("id") or item_data.get("entity_id") or i_name.lower().replace(" ", "_"),
                name=i_name,
                name_en=item_data.get("name_en", i_name),
                item_type=item_data.get("item_type", "Equipo"),
                quantity=int(item_data.get("quantity", 1) or 1),
                weight=str(item_data.get("weight") or ""),
                cost=str(item_data.get("cost") or ""),
                rarity=str(item_data.get("rarity") or "común"),
                description=str(item_data.get("description") or ""),
                notes=str(item_data.get("notes") or ""),
                ac_bonus=int(item_data.get("ac_bonus") or 0),
                equipped=bool(item_data.get("equipped", False))
            )
            char.equipment.append(new_item)

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def remove_item_from_character(self, char_id: int, item_name: str, category: str = "all") -> Dict[str, Any]:
        """Elimina un objeto/arma del inventario del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        i_name_clean = item_name.strip().lower()
        if hasattr(char, "equipment") and char.equipment:
            char.equipment = [eq for eq in char.equipment if eq.name.strip().lower() != i_name_clean]

        if category in ("all", "weapon"):
            char.weapons = [w for w in char.weapons if w.name.strip().lower() != i_name_clean]

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def sync_character_features(self, char_id: int, lang: str = "es") -> Dict[str, Any]:
        """Recalcula y sincroniza dinámicamente todos los rasgos de clase, dotes y linaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        char.features = compute_dynamic_features(char, lang=lang)
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char, lang=lang)}

    def sync_compendium_from_srd(self, edition: str = "PHB 2024") -> Dict[str, Any]:
        """Reconstruye e indexa la base de datos de tarjetas atómicas OKF."""
        try:
            importer = SrdImporter(self._okf.okf_dir)
            count = importer.rebuild_master_index()
            self._okf._load_index()
            return {"success": True, "total_entities": count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def build_character_from_wizard(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye un CharacterSheet 100% legal a partir de las elecciones del asistente
        y retorna el diccionario CharacterSheetData serializado para React.
        """
        name = str(payload.get("name", "Nuevo Héroe")).strip() or "Nuevo Héroe"
        char_class = str(payload.get("char_class", "Guerrero")).strip()
        subclass = str(payload.get("subclass", "")).strip()
        level = max(1, min(20, int(payload.get("level", 1))))
        race = str(payload.get("race", "Humano")).strip()
        subrace = str(payload.get("subrace", "")).strip()
        full_race = f"{race} ({subrace})" if subrace and subrace not in race and subrace != "Estándar" else race
        background = str(payload.get("background", "Soldado")).strip()
        alignment = str(payload.get("alignment", "Neutral Bueno")).strip()
        edition = str(payload.get("edition") or self._db.get_setting("dnd_edition", "5.5e"))

        catalog = self.get_builder_catalog(edition)
        sp_entry = next((s for s in catalog["species"] if s["name"].lower() == race.lower()), None)
        bg_entry = next((b for b in catalog["backgrounds"] if b["name"].lower() == background.lower()), None)

        # 1. Puntuaciones de característica base + bonos de especie/trasfondo
        raw_scores = payload.get("scores", {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8})
        abilities: Dict[str, int] = {k: int(v) for k, v in raw_scores.items()}

        if payload.get("bg_plus2") or payload.get("bg_plus1"):
            bg_plus2 = payload.get("bg_plus2", "")
            bg_plus1 = payload.get("bg_plus1", "")
            if bg_plus2 in abilities:
                abilities[bg_plus2] = min(20, abilities[bg_plus2] + 2)
            if bg_plus1 in abilities and bg_plus1 != bg_plus2:
                abilities[bg_plus1] = min(20, abilities[bg_plus1] + 1)
        elif sp_entry and not payload.get("scores_already_adjusted"):
            for ab_k, bonus_v in sp_entry.get("bonuses", {}).items():
                if ab_k in abilities:
                    abilities[ab_k] = min(20, abilities[ab_k] + int(bonus_v))

        # 2. Dados de Golpe y Puntos de Golpe reales por clase y nivel
        hd_faces = CLASS_HIT_DICE.get(char_class, 8)
        con_mod = calc_modifier(abilities.get("CON", 10))
        avg_per_lvl = (hd_faces // 2) + 1 + con_mod
        hp_max = max(1, hd_faces + con_mod) + (max(0, level - 1) * max(1, avg_per_lvl))

        # 3. Velocidad y Sentidos desde especie OKF
        speed_str = "9 m"
        senses_str = "Visión Normal"
        for sp in self._okf.get_species():
            if sp["nombre"].lower() == race.lower():
                speed_str = sp.get("velocidad", "9 m")
                senses_str = sp.get("sentidos", "Visión Normal")
                break

        # 4. Salvaciones competentes de la clase
        saving_profs = ["FUE", "CON"]
        for cl in self._okf.get_classes():
            if cl["nombre"].lower() == char_class.lower():
                saving_profs = list(cl.get("saves", ["FUE", "CON"]))
                break

        # 5. Habilidades competentes (Clase + Trasfondo)
        preset = CLASS_QUICK_PRESETS.get(char_class, CLASS_QUICK_PRESETS.get("Guerrero", {}))
        chosen_skills: List[str] = list(
            payload.get("selected_skills")
            or payload.get("skills")
            or preset.get("skills", ["Atletismo", "Percepción"])
        )
        if bg_entry:
            for b_sk in bg_entry.get("skills", []):
                if b_sk not in chosen_skills:
                    chosen_skills.append(b_sk)
        skills_dict: Dict[str, str] = {sk: "proficient" for sk in chosen_skills}

        # 6. Clase de Armadura e Iniciativa
        dex_mod = calc_modifier(abilities.get("DES", 10))
        wis_mod = calc_modifier(abilities.get("SAB", 10))
        str_mod = calc_modifier(abilities.get("FUE", 10))
        prof_bonus = calc_proficiency_bonus(level)

        if char_class == "Bárbaro":
            ac = 10 + dex_mod + con_mod
        elif char_class == "Monje":
            ac = 10 + dex_mod + wis_mod
        elif char_class in ("Guerrero", "Paladín"):
            ac = 16
        elif char_class in ("Clérigo", "Druida", "Explorador"):
            ac = 14 + min(2, dex_mod)
        elif char_class in ("Bardo", "Pícaro", "Brujo"):
            ac = 11 + dex_mod
        else:
            ac = 10 + dex_mod

        # 7. Armas iniciales con bonos reales calculados
        weapons_list: List[WeaponAction] = []
        for w_name, w_dmg, w_notes in preset.get("weapons", [("Espada Larga", "1d8 cortante", "Versátil")]):
            if "+2 CA" in w_dmg:
                ac += 2
                continue
            uses_dex = any(k in w_notes.lower() or k in w_name.lower() for k in ("sutil", "arco", "ballesta", "honda"))
            atk_stat_mod = max(str_mod, dex_mod) if "sutil" in w_notes.lower() else (dex_mod if uses_dex else str_mod)
            hit_tot = atk_stat_mod + prof_bonus
            hit_str = f"+{hit_tot}" if hit_tot >= 0 else str(hit_tot)
            dmg_parts = w_dmg.split(" ", 1)
            dice_part = dmg_parts[0]
            dmg_type = dmg_parts[1].capitalize() if len(dmg_parts) > 1 else "Físico"
            mod_suffix = f"+{atk_stat_mod}" if atk_stat_mod > 0 else (f"{atk_stat_mod}" if atk_stat_mod < 0 else "")
            weapons_list.append(
                WeaponAction(
                    name=w_name,
                    attack_bonus=hit_str,
                    damage=f"{dice_part}{mod_suffix}",
                    damage_type=dmg_type,
                    notes=w_notes,
                )
            )

        # 8. Conjuros y Ranuras Mágicas desde OkfEngine
        spell_slots = _compute_spell_slots_for_class(char_class, level)
        selected_spell_names: List[str] = payload.get("spells") or (
            preset.get("cantrips", []) + preset.get("spells_known", [])
        )
        spells_list: List[SpellItem] = []
        for sp_name in selected_spell_names:
            matched = self._okf.search_entities(query=sp_name, tipo="conjuro", limit=1)
            if matched:
                sp_item = self._okf.get_spell_item(matched[0]["id"])
                if sp_item:
                    spells_list.append(sp_item)
                    continue
            spells_list.append(SpellItem(name=sp_name, level=0 if sp_name in preset.get("cantrips", []) else 1))

        # 9. Rasgos iniciales (Clase, Especie y Trasfondo)
        features_list: List[CharacterFeature] = [
            CharacterFeature(
                id="feat_class_core",
                name=f"Rasgos de {char_class} (Nivel {level})",
                source=char_class,
                description=f"Competencias en salvaciones: {', '.join(saving_profs)}. Dado de golpe: 1d{hd_faces}.",
            ),
            CharacterFeature(
                id="feat_species_core",
                name=f"Herencia de {full_race}",
                source=full_race,
                description=f"Velocidad {speed_str}. Sentidos: {senses_str}.",
            ),
        ]
        if subclass:
            features_list.append(
                CharacterFeature(
                    id="feat_subclass",
                    name=f"Subclase: {subclass}",
                    source=char_class,
                    description=f"Especialización de {char_class} desbloqueada.",
                )
            )
        if bg_entry:
            features_list.append(
                CharacterFeature(
                    id="feat_bg",
                    name=bg_entry.get("feature_name", "Dote de Origen"),
                    source=f"Trasfondo ({background})",
                    description=bg_entry.get("feature_desc", ""),
                )
            )

        char = CharacterSheet(
            name=name,
            char_class=char_class,
            subclass=subclass,
            level=level,
            race=full_race,
            background=background,
            alignment=alignment,
            xp=0,
            hp_current=hp_max,
            hp_max=hp_max,
            hp_temp=0,
            hit_dice_max=level,
            hit_dice_current=level,
            hit_dice_faces=hd_faces,
            armor_class=ac,
            initiative_bonus=dex_mod,
            speed=speed_str,
            proficiency_bonus=prof_bonus,
            abilities=abilities,
            saving_throw_profs=saving_profs,
            skills=skills_dict,
            weapons=weapons_list,
            spell_slots=spell_slots,
            spells=spells_list,
            features=features_list,
            senses=senses_str,
        )
        return self._serialize_character(char)

    def generate_quick_build_preview(self, char_class: str, species: str = "Humano") -> Dict[str, Any]:
        """Calcula la previsualización completa de Quick Build (60s) usando core/quick_build.py."""
        raw_scores, final_scores, bg, plus2, plus1 = QuickBuildEngine.generate_quick_stats(char_class, species)
        preset = QuickBuildEngine.get_preset_for_class(char_class)
        spells_list = preset.get("cantrips", []) + preset.get("spells_known", [])
        return self.build_character_from_wizard({
            "name": f"{char_class} {species}",
            "char_class": char_class,
            "race": species,
            "level": 1,
            "background": bg,
            "scores": final_scores,
            "scores_already_adjusted": True,
            "selected_skills": preset.get("skills", []),
            "spells": spells_list,
        })

    def generate_random_character_preview(
        self,
        forced_class: Optional[str] = None,
        forced_species: Optional[str] = None,
        forced_level: int = 1,
    ) -> Dict[str, Any]:
        """Genera una previsualización completa con tiradas 4d6 drop lowest usando core/random_generator.py."""
        rnd = RandomCharacterGenerator.generate_random_character(
            forced_class=forced_class or None,
            forced_species=forced_species or None,
            forced_level=int(forced_level or 1),
        )
        scores_map = rnd.get("final_abilities") or rnd.get("final_scores") or rnd.get("raw_scores", {})
        preset = rnd.get("preset", {})
        skills_list = rnd.get("skills") or preset.get("skills", ["Atletismo", "Percepción"])
        spells_list = preset.get("cantrips", []) + preset.get("spells_known", [])

        char_dict = self.build_character_from_wizard({
            "name": rnd.get("name", "Héroe del Destino"),
            "char_class": rnd.get("char_class", forced_class or "Guerrero"),
            "subclass": rnd.get("subclass", ""),
            "race": rnd.get("species", forced_species or "Humano"),
            "subrace": rnd.get("subrace", ""),
            "level": rnd.get("level", int(forced_level or 1)),
            "background": rnd.get("background", "Soldado"),
            "alignment": rnd.get("alignment", "Neutral"),
            "scores": scores_map,
            "scores_already_adjusted": True,
            "selected_skills": skills_list,
            "spells": spells_list,
        })
        return {
            "character": char_dict,
            "raw_rolls": rnd.get("raw_scores", {}),
            "biography": {
                "trait": rnd.get("personality_trait", ""),
                "ideal": rnd.get("ideal", ""),
                "bond": rnd.get("bond", ""),
                "flaw": rnd.get("flaw", ""),
            },
        }

    # =========================================================================
    # DIARIO DE CAMPAÑA & RED DE PERSONAJES
    # =========================================================================

    def get_character_journals(self, char_id: int) -> List[Dict[str, Any]]:
        """Retorna las crónicas de sesión del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return []
        return [
            {
                "id": int(s.id) if str(s.id).isdigit() else idx + 1,
                "date": s.date,
                "title": s.title,
                "summary": s.summary,
                "loot": s.loot,
                "xp_gained": int(s.xp_gained),
                "session_id": getattr(s, "session_id", "") or "",
            }
            for idx, s in enumerate(char.sessions)
        ]

    def save_character_journal(self, char_id: int, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade o actualiza una sesión en el diario del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        sess_id = str(journal_data.get("id", len(char.sessions) + 1))
        existing = next((s for s in char.sessions if str(s.id) == sess_id), None)
        active_session_id = str(journal_data.get("session_id") or getattr(self._session_server, "current_session_id", "") or "")

        if existing:
            existing.date = journal_data.get("date", existing.date)
            existing.title = journal_data.get("title", existing.title)
            existing.summary = journal_data.get("summary", existing.summary)
            existing.loot = journal_data.get("loot", existing.loot)
            existing.xp_gained = int(journal_data.get("xp_gained", existing.xp_gained))
            if "session_id" in journal_data or active_session_id:
                existing.session_id = str(journal_data.get("session_id", getattr(existing, "session_id", active_session_id)))
        else:
            char.sessions.append(
                SessionLog(
                    id=sess_id,
                    date=journal_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                    title=journal_data.get("title", "Nueva Crónica"),
                    summary=journal_data.get("summary", ""),
                    loot=journal_data.get("loot", ""),
                    xp_gained=int(journal_data.get("xp_gained", 0)),
                    session_id=str(journal_data.get("session_id", active_session_id)),
                )
            )

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "sessions": self.get_character_journals(char_id)}

    def delete_character_journal(self, char_id: int, session_id: int) -> Dict[str, Any]:
        """Elimina una sesión del diario del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        char.sessions = [s for s in char.sessions if str(s.id) != str(session_id)]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "sessions": self.get_character_journals(char_id)}

    def get_character_network(self, char_id: int) -> Dict[str, Any]:
        """Retorna nodos y vínculos de la red social/campaña del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"nodes": [], "edges": []}
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "role": n.role,
                    "description": n.description,
                    "avatar_base64": n.avatar_base64,
                    "x": n.x,
                    "y": n.y,
                }
                for n in char.network_nodes
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation,
                }
                for e in char.network_edges
            ],
        }

    def save_network_node(self, char_id: int, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda o actualiza un nodo (PNJ/Aliado) en la red."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        raw_id = node_data.get("id")
        node_id = str(raw_id) if raw_id else f"node_{char_id}_{int(datetime.now().timestamp() * 1000)}"
        existing = next((n for n in char.network_nodes if n.id == node_id), None)
        if existing:
            existing.name = node_data.get("name", existing.name)
            existing.role = node_data.get("role", existing.role)
            existing.description = node_data.get("description", existing.description)
            existing.x = float(node_data.get("x", existing.x))
            existing.y = float(node_data.get("y", existing.y))
        else:
            char.network_nodes.append(
                NetworkNode(
                    id=node_id,
                    name=node_data.get("name", "PNJ"),
                    role=node_data.get("role", "Neutral"),
                    description=node_data.get("description", ""),
                    avatar_base64=node_data.get("avatar_base64", ""),
                    x=float(node_data.get("x", 0.0)),
                    y=float(node_data.get("y", 0.0)),
                )
            )

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def delete_network_node(self, char_id: int, node_id: str) -> Dict[str, Any]:
        """Elimina un nodo y sus aristas asociadas."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        char.network_nodes = [n for n in char.network_nodes if n.id != node_id]
        char.network_edges = [e for e in char.network_edges if e.source_id != node_id and e.target_id != node_id]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def save_network_edge(self, char_id: int, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un vínculo relacional entre dos personajes."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        src = edge_data.get("source_id")
        tgt = edge_data.get("target_id")
        rel = edge_data.get("relation", "Aliado")

        if src == tgt:
            return {"success": False, "error": "No puedes vincular un personaje consigo mismo."}

        char.network_edges = [
            e for e in char.network_edges
            if not ((e.source_id == src and e.target_id == tgt) or (e.source_id == tgt and e.target_id == src))
        ]
        char.network_edges.append(NetworkEdge(source_id=src, target_id=tgt, relation=rel))

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def delete_network_edge(self, char_id: int, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un vínculo relacional."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        src = edge_data.get("source_id")
        tgt = edge_data.get("target_id")
        char.network_edges = [
            e for e in char.network_edges
            if not ((e.source_id == src and e.target_id == tgt) or (e.source_id == tgt and e.target_id == src))
        ]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    # =========================================================================
    # COMPENDIO SQLITE (CANÓNICO) & OKF (CATÁLOGO BUILDER)
    # =========================================================================

    COMPENDIUM_CATEGORY_TYPES = {
        "clases": ["clase", "subclase"],
        "especies_y_linajes": ["especie", "linaje", "especie_linaje"],
        "trasfondos": ["trasfondo"],
        "dotes": ["dote"],
        "reglas_y_mecanicas": ["regla"],
    }

    def get_compendium_categories(self, lang: str = "es", edition: Optional[str] = None, expansions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Lista las categorías disponibles en el compendio SQLite con su conteo unificado por idioma, edición y expansiones."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        
        # Conteo SQLite canónico
        sql_monsters = self._db.count_compendium_entries("monsters", edition=edition, language=target_lang, expansions=expansions)
        sql_spells = self._db.count_compendium_entries("spells", edition=edition, language=target_lang, expansions=expansions)
        sql_items = self._db.count_compendium_entries("items", edition=edition, language=target_lang, expansions=expansions)

        # Conteo SQLite de entidades unificadas
        sql_clases = self._db.count_compendium_entries("entities", categories=self.COMPENDIUM_CATEGORY_TYPES["clases"], edition=edition, language=target_lang, expansions=expansions)
        sql_especies = self._db.count_compendium_entries("entities", categories=self.COMPENDIUM_CATEGORY_TYPES["especies_y_linajes"], edition=edition, language=target_lang, expansions=expansions)
        sql_trasfondos = self._db.count_compendium_entries("entities", categories=self.COMPENDIUM_CATEGORY_TYPES["trasfondos"], edition=edition, language=target_lang, expansions=expansions)
        sql_dotes = self._db.count_compendium_entries("entities", categories=self.COMPENDIUM_CATEGORY_TYPES["dotes"], edition=edition, language=target_lang, expansions=expansions)
        sql_reglas = self._db.count_compendium_entries("entities", categories=self.COMPENDIUM_CATEGORY_TYPES["reglas_y_mecanicas"], edition=edition, language=target_lang, expansions=expansions)

        # Fallback a OKF solo si compendium_entities aún no ha sido poblado en SQLite
        cnt_clases = sql_clases if sql_clases > 0 else self._okf.count_entities(self.COMPENDIUM_CATEGORY_TYPES["clases"], lang=target_lang)
        cnt_especies = sql_especies if sql_especies > 0 else self._okf.count_entities(self.COMPENDIUM_CATEGORY_TYPES["especies_y_linajes"], lang=target_lang)
        cnt_trasfondos = sql_trasfondos if sql_trasfondos > 0 else self._okf.count_entities("trasfondo", lang=target_lang)
        cnt_dotes = sql_dotes if sql_dotes > 0 else self._okf.count_entities("dote", lang=target_lang)
        cnt_reglas = sql_reglas if sql_reglas > 0 else self._okf.count_entities("regla", lang=target_lang)

        if target_lang == "en":
            return [
                {"id": "clases", "label": "Classes & Subclasses", "count": cnt_clases},
                {"id": "especies_y_linajes", "label": "Species & Lineages", "count": cnt_especies},
                {"id": "conjuros", "label": "Spell Grimoire", "count": sql_spells},
                {"id": "monstruos", "label": "Monsters & Bestiary", "count": sql_monsters},
                {"id": "trasfondos", "label": "Backgrounds", "count": cnt_trasfondos},
                {"id": "dotes", "label": "Character Feats", "count": cnt_dotes},
                {"id": "equipo_y_armamento", "label": "Equipment & Weapons", "count": sql_items},
                {"id": "reglas_y_mecanicas", "label": "Rules & Mechanics", "count": cnt_reglas},
            ]
        return [
            {"id": "clases", "label": "Clases y Subclases", "count": cnt_clases},
            {"id": "especies_y_linajes", "label": "Especies y Linajes", "count": cnt_especies},
            {"id": "conjuros", "label": "Grimorio de Conjuros", "count": sql_spells},
            {"id": "monstruos", "label": "Monstruos y Bestiario", "count": sql_monsters},
            {"id": "trasfondos", "label": "Trasfondos", "count": cnt_trasfondos},
            {"id": "dotes", "label": "Dotes de Personaje", "count": cnt_dotes},
            {"id": "equipo_y_armamento", "label": "Equipo y Armamento", "count": sql_items},
            {"id": "reglas_y_mecanicas", "label": "Reglas y Mecánicas", "count": cnt_reglas},
        ]

    def _format_monster_entry(self, m: Dict[str, Any], entry_name: str) -> Dict[str, Any]:
        """Formatea un registro de monstruo de SQLite en una entrada estructurada de compendio con markdown."""
        cr_str = m.get("cr_text", "0")
        md_content = f"### {m.get('name')}\n\n*{m.get('size', '')} {m.get('monster_type', '')}, {m.get('alignment', '')}*\n\n"
        md_content += f"- **Clase de Armadura:** {m.get('ac')}\n"
        md_content += f"- **Puntos de Golpe:** {m.get('hp_avg')} ({m.get('hp_formula', '')})\n"
        md_content += f"- **Velocidad:** {m.get('speed')}\n"
        md_content += f"- **Desafío (CR):** {cr_str}\n"
        details = m.get("details", {})
        if isinstance(details, dict):
            if "str" in details or "fuerza" in details:
                md_content += f"\n| FUE | DES | CON | INT | SAB | CAR |\n| :---: | :---: | :---: | :---: | :---: | :---: |\n"
                md_content += f"| {details.get('str', 10)} | {details.get('dex', 10)} | {details.get('con', 10)} | {details.get('int', 10)} | {details.get('wis', 10)} | {details.get('cha', 10)} |\n\n"
            traits = details.get("trait") or details.get("special_abilities") or []
            if traits:
                md_content += "#### Rasgos\n"
                for t in traits:
                    if isinstance(t, dict):
                        md_content += f"**{t.get('name')}:** {t.get('desc', t.get('entries', ''))}\n\n"
            actions = details.get("action") or details.get("actions") or []
            if actions:
                md_content += "#### Acciones\n"
                for a in actions:
                    if isinstance(a, dict):
                        md_content += f"**{a.get('name')}:** {a.get('desc', a.get('entries', ''))}\n\n"
        return {
            "id": m.get("entity_id", ""),
            "name": m.get("name", entry_name),
            "category": "monstruos",
            "content": md_content,
            "metadata": m,
        }

    def _format_spell_entry(self, s: Dict[str, Any], entry_name: str) -> Dict[str, Any]:
        """Formatea un conjuro de SQLite en una entrada estructurada de compendio con markdown."""
        md_content = f"### {s.get('name')}\n\n*{s.get('school')} • Nivel {s.get('level')}*\n\n"
        md_content += f"- **Tiempo de Lanzamiento:** {s.get('casting_time')}\n"
        md_content += f"- **Alcance / Área:** {s.get('range_area')}\n"
        md_content += f"- **Componentes:** {s.get('components')}\n"
        md_content += f"- **Duración:** {s.get('duration')}\n\n"
        md_content += s.get("description", "")
        return {
            "id": s.get("entity_id", ""),
            "name": s.get("name", entry_name),
            "category": "conjuros",
            "content": md_content,
            "metadata": s,
        }

    def _format_item_entry(self, it: Dict[str, Any], entry_name: str) -> Dict[str, Any]:
        """Formatea un objeto/arma/armadura de SQLite en una entrada estructurada de compendio con markdown."""
        md_content = f"### {it.get('name')}\n\n*{it.get('item_type')} • {it.get('rarity')}*\n\n"
        if it.get("weapon_mastery"):
            md_content += f"- **Weapon Mastery (2024):** {it.get('weapon_mastery')}\n"
        if it.get("damage"):
            md_content += f"- **Daño:** {it.get('damage')} ({it.get('damage_type', '')})\n"
        if it.get("cost"):
            md_content += f"- **Precio:** {it.get('cost')}\n"
        if it.get("weight"):
            md_content += f"- **Peso:** {it.get('weight')}\n\n"
        md_content += it.get("description", "")
        return {
            "id": it.get("entity_id", ""),
            "name": it.get("name", entry_name),
            "category": "equipo_y_armamento",
            "content": md_content,
            "metadata": it,
        }

    def search_compendium(self, query: str = "", category: Optional[str] = None, lang: str = "es", edition: Optional[str] = None, expansions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Búsqueda de texto o listado por categoría en el compendio SQLite con soporte de edición y expansiones."""
        query_clean = (query or "").strip()
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"

        # Categoría Monstruos (SQLite)
        if category == "monstruos":
            monsters = self._db.search_compendium_monsters(query=query_clean, edition=edition, language=target_lang, expansions=expansions, limit=150)
            return [
                {
                    "id": m.get("entity_id", ""),
                    "name": m.get("name", ""),
                    "category": "monstruos",
                    "snippet": f"{m.get('size', '')} {m.get('monster_type', '')} • CR {m.get('cr_text', '0')} • CA {m.get('ac', 10)} • PG {m.get('hp_avg', 10)}",
                    "path": "sqlite:compendium_monsters",
                }
                for m in monsters
            ]

        # Categoría Conjuros (SQLite)
        if category == "conjuros":
            spells = self._db.search_compendium_spells(query=query_clean, edition=edition, language=target_lang, expansions=expansions, limit=150)
            lvl_lbl = "Level" if target_lang == "en" else "Nivel"
            return [
                {
                    "id": s.get("entity_id", ""),
                    "name": s.get("name", ""),
                    "category": "conjuros",
                    "snippet": f"{lvl_lbl} {s.get('level', 0)} • {s.get('school', '')} • {s.get('casting_time', '')}",
                    "path": "sqlite:compendium_spells",
                }
                for s in spells
            ]

        # Categoría Equipo y Armamento (SQLite)
        if category in ("equipo_y_armamento", "equipo", "items"):
            items = self._db.search_compendium_items(query=query_clean, edition=edition, language=target_lang, expansions=expansions, limit=150)
            return [
                {
                    "id": it.get("entity_id", ""),
                    "name": it.get("name", ""),
                    "category": "equipo_y_armamento",
                    "snippet": f"{it.get('item_type', '')} • {it.get('rarity', '')}" + (f" • {it.get('weapon_mastery')}" if it.get("weapon_mastery") else ""),
                    "path": "sqlite:compendium_items",
                }
                for it in items
            ]

        # Categorías en SQLite compendium_entities (clases, especies_y_linajes, trasfondos, dotes, reglas_y_mecanicas)
        if category in self.COMPENDIUM_CATEGORY_TYPES:
            types = self.COMPENDIUM_CATEGORY_TYPES[category]
            sql_entities = self._db.search_compendium_entities(
                query=query_clean,
                categories=types,
                language=target_lang,
                edition=edition,
                expansions=expansions,
                limit=150
            )
            if sql_entities:
                return [
                    {
                        "id": item.get("entity_id", ""),
                        "name": item.get("name", ""),
                        "category": item.get("category", category),
                        "snippet": item.get("snippet", ""),
                        "path": f"sqlite:compendium_entities:{item.get('entity_id')}",
                    }
                    for item in sql_entities
                ]

        # Fallback para búsqueda general o si compendium_entities aún no está poblada
        category_type_map = self.COMPENDIUM_CATEGORY_TYPES
        tipo_filter = category_type_map.get(category) if category else [
            "clase", "subclase", "especie", "linaje", "especie_linaje", "trasfondo", "dote", "regla"
        ]
        entities = self._okf.search_entities(query=query_clean, tipo=tipo_filter, limit=150, lang=target_lang)

        results = []
        for item in entities:
            item_tipo = item.get("tipo", "")
            snippet_parts = [item.get("fuente", "PHB 2024")]
            if "nivel" in item and item["nivel"] is not None:
                snippet_parts.append(f"Level {item['nivel']}" if target_lang == "en" else f"Nivel {item['nivel']}")
            if "escuela" in item and item["escuela"]:
                snippet_parts.append(str(item["escuela"]))
            if "dado_golpe" in item and item["dado_golpe"]:
                snippet_parts.append(f"HD: {item['dado_golpe']}" if target_lang == "en" else f"DG: {item['dado_golpe']}")
            if "dote_concedida" in item and item["dote_concedida"]:
                snippet_parts.append(f"Feat: {item['dote_concedida']}" if target_lang == "en" else f"Dote: {item['dote_concedida']}")
            if "caracteristicas_clave" in item and item["caracteristicas_clave"]:
                snippet_parts.append(f"{item['caracteristicas_clave']}")

            results.append({
                "id": item.get("id", ""),
                "name": item.get("nombre", item.get("id", "")),
                "category": item_tipo,
                "snippet": " • ".join(snippet_parts),
                "path": item.get("path", ""),
            })

        # Búsqueda global agregada (sin categoría): sumar muestras de SQLite
        if not category and query_clean:
            monsters = self._db.search_compendium_monsters(query=query_clean, edition=edition, language=target_lang, limit=20)
            for m in monsters:
                results.append({
                    "id": m.get("entity_id", ""),
                    "name": m.get("name", ""),
                    "category": "monstruos",
                    "snippet": f"{m.get('size', '')} {m.get('monster_type', '')} • CR {m.get('cr_text', '0')} • CA {m.get('ac', 10)} • PG {m.get('hp_avg', 10)}",
                    "path": "sqlite:compendium_monsters",
                })
            spells = self._db.search_compendium_spells(query=query_clean, edition=edition, language=target_lang, limit=20)
            lvl_lbl = "Level" if target_lang == "en" else "Nivel"
            for s in spells:
                results.append({
                    "id": s.get("entity_id", ""),
                    "name": s.get("name", ""),
                    "category": "conjuros",
                    "snippet": f"{lvl_lbl} {s.get('level', 0)} • {s.get('school', '')} • {s.get('casting_time', '')}",
                    "path": "sqlite:compendium_spells",
                })
            items = self._db.search_compendium_items(query=query_clean, edition=edition, language=target_lang, limit=20)
            for it in items:
                results.append({
                    "id": it.get("entity_id", ""),
                    "name": it.get("name", ""),
                    "category": "equipo_y_armamento",
                    "snippet": f"{it.get('item_type', '')} • {it.get('rarity', '')}" + (f" • {it.get('weapon_mastery')}" if it.get("weapon_mastery") else ""),
                    "path": "sqlite:compendium_items",
                })

        return results

    def get_compendium_entry(self, category: str, entry_name: str, lang: str = "es") -> Optional[Dict[str, Any]]:
        """Obtiene una entrada completa del compendio desde SQLite (monstruos, conjuros, equipo, clases, etc.) u OKF con formato markdown."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        query_id = entry_name.strip()

        # Rutas canónicas directas para tablas SQLite
        if category == "monstruos":
            m = self._db.get_compendium_monster_by_id(query_id)
            if m:
                return self._format_monster_entry(m, entry_name)
            return None

        if category == "conjuros":
            s = self._db.get_compendium_spell_by_id(query_id)
            if s:
                return self._format_spell_entry(s, entry_name)
            return None

        if category in ("equipo_y_armamento", "equipo", "items"):
            it = self._db.get_compendium_item_by_id(query_id)
            if it:
                return self._format_item_entry(it, entry_name)
            return None

        # Consultar compendium_entities en SQLite (clases, trasfondos, dotes, especies, reglas)
        ent = self._db.get_compendium_entity_by_id(query_id)
        if ent:
            return {
                "id": ent.get("entity_id", ""),
                "name": ent.get("name", entry_name),
                "category": ent.get("category", category),
                "content": ent.get("content_markdown", ""),
                "metadata": ent.get("details", {}),
            }

        # Fallback a OKF solo si no se encuentra en SQLite
        clean = query_id.lower()
        clean_slug = clean.replace(" ", "_")
        clean_en = f"{clean_slug}_en"
        clean_base = clean_slug.replace("_en", "")

        matched = next(
            (
                item for item in self._okf._index
                if item.get("idioma", "es") == target_lang
                and (
                    item.get("id", "").lower() in (clean_slug, clean_en, clean_base)
                    or item.get("original_id", "").lower() in (clean_slug, clean_en, clean_base)
                    or item.get("nombre", "").lower() == clean
                    or item.get("nombre_ingles", "").lower() == clean
                    or item.get("nombre_espanol", "").lower() == clean
                )
            ),
            None
        )
        if not matched:
            results = self._okf.search_entities(query=query_id, lang=target_lang, limit=1)
            if results:
                matched = results[0]

        if not matched:
            matched = next(
                (item for item in self._okf._index if item.get("id") == query_id or item.get("nombre", "").lower() == clean),
                None
            )

        if not matched:
            m = self._db.get_compendium_monster_by_id(query_id)
            if m:
                return self._format_monster_entry(m, entry_name)
            s = self._db.get_compendium_spell_by_id(query_id)
            if s:
                return self._format_spell_entry(s, entry_name)
            it = self._db.get_compendium_item_by_id(query_id)
            if it:
                return self._format_item_entry(it, entry_name)
            return None

        if not matched:
            # Fallback de seguridad cruzado a compendio SQLite
            m = self._db.get_compendium_monster_by_id(query_id)
            if m:
                return self._format_monster_entry(m, entry_name)
            s = self._db.get_compendium_spell_by_id(query_id)
            if s:
                return self._format_spell_entry(s, entry_name)
            it = self._db.get_compendium_item_by_id(query_id)
            if it:
                return self._format_item_entry(it, entry_name)
            return None

        rel_path = matched.get("path")
        content = ""
        full_meta = dict(matched)
        if rel_path:
            full_data = self._okf.read_entity_file(rel_path)
            if full_data:
                full_meta.update(full_data)
                content = full_data.get("body_markdown") or full_data.get("descripcion", "")

        if not content:
            content = matched.get("descripcion", "")

        return {
            "id": matched.get("id", ""),
            "name": matched.get("nombre", entry_name),
            "category": matched.get("tipo", category),
            "content": content,
            "metadata": full_meta,
        }

    # =========================================================================
    # REGLAS 5E & DESCANSO
    # =========================================================================

    def validate_point_buy(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Valida si los atributos respetan el presupuesto de 27 puntos de 5e."""
        clean_scores = {k: int(v) for k, v in scores.items()}
        spent = PointBuyCalculator.calculate_used_points(clean_scores)
        remaining = PointBuyCalculator.get_remaining_points(clean_scores)
        valid = remaining >= 0 and all(MIN_SCORE <= v <= MAX_SCORE for v in clean_scores.values())
        error = None
        if remaining < 0:
            error = f"Presupuesto excedido por {abs(remaining)} puntos."
        elif any(v < MIN_SCORE or v > MAX_SCORE for v in clean_scores.values()):
            error = f"Atributos fuera del rango legal ({MIN_SCORE}-{MAX_SCORE})."

        can_inc = {k: PointBuyCalculator.can_increment(clean_scores, k) for k in clean_scores}
        can_dec = {k: PointBuyCalculator.can_decrement(clean_scores, k) for k in clean_scores}

        return {
            "valid": valid,
            "points_spent": spent,
            "points_remaining": remaining,
            "can_increment": can_inc,
            "can_decrement": can_dec,
            "error": error,
            "standard_array": STANDARD_ARRAY,
            "min_score": MIN_SCORE,
            "max_score": MAX_SCORE,
        }

    def get_quick_build_options(self) -> Dict[str, Any]:
        """Retorna las listas de clases, especies y presets de creación rápida."""
        return {
            "classes": CLASSES_LIST,
            "species": SPECIES_LIST,
            "alignments": ALIGNMENTS_LIST,
            "presets": CLASS_QUICK_PRESETS,
        }

    def generate_quick_character(self, char_class: str, species: str, name: str) -> Dict[str, Any]:
        """Genera un personaje en 60 segundos usando los presets y Standard Array de Quick Build."""
        char_name = name.strip() or f"Héroe {char_class}"
        raw_scores, final_scores, bg, plus2, plus1 = QuickBuildEngine.generate_quick_stats(char_class, species)
        preset = QuickBuildEngine.get_preset_for_class(char_class)

        calc_mod = lambda score: (score - 10) // 2
        con_mod = calc_mod(final_scores.get("CON", 10))
        des_mod = calc_mod(final_scores.get("DES", 10))

        hd_map = {
            "Bárbaro": 12, "Guerrero": 10, "Paladín": 10, "Explorador": 10,
            "Bardo": 8, "Clérigo": 8, "Druida": 8, "Monje": 8, "Pícaro": 8, "Brujo": 8,
            "Hechicero": 6, "Mago": 6
        }
        hd_face = hd_map.get(char_class, 8)
        hp = max(1, hd_face + con_mod)

        abilities: Dict[str, Any] = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = final_scores.get(stat, 10)
            mod = calc_mod(base)
            abilities[stat] = {
                "base": base,
                "override": 0,
                "bonus": mod,
                "proficient": False,
                "save_bonus": mod,
            }

        weapons = []
        for w_name, w_dmg, w_notes in preset.get("weapons", []):
            weapons.append({
                "name": w_name,
                "type": "Cuerpo a cuerpo" if "Arco" not in w_name and "Ballesta" not in w_name else "A distancia",
                "range_val": "5 pies" if "Arco" not in w_name and "Ballesta" not in w_name else "80/320",
                "hit_dc": f"+{2 + max(calc_mod(final_scores['FUE']), calc_mod(final_scores['DES']))}",
                "damage_dice": w_dmg.split(" ")[0],
                "damage_type": w_dmg.split(" ")[1] if len(w_dmg.split(" ")) > 1 else "cortante",
                "notes": w_notes,
                "proficient": True,
            })

        spells = []
        for c_name in preset.get("cantrips", []):
            spells.append({
                "name": c_name,
                "level": 0,
                "school": "Evocación",
                "cast_time": "1 acción",
                "range_area": "60 pies",
                "components": "V, S",
                "duration": "Instantáneo",
                "prepared": True,
                "notes": "Truco sugerido por Quick Build.",
            })
        for s_name in preset.get("spells_known", []):
            spells.append({
                "name": s_name,
                "level": 1,
                "school": "Abjuración",
                "cast_time": "1 acción",
                "range_area": "30 pies",
                "components": "V, S",
                "duration": "1 minuto",
                "prepared": True,
                "notes": "Conjuro de Nivel 1 asignado por Quick Build.",
            })

        return {
            "name": char_name,
            "char_class": char_class,
            "subclass": "",
            "level": 1,
            "race": species,
            "background": bg,
            "alignment": "Neutral Bueno",
            "xp": 0,
            "inspiration": False,
            "proficiency_bonus": 2,
            "ac": 10 + des_mod,
            "speed": 30,
            "initiative": des_mod,
            "hp_current": hp,
            "hp_max": hp,
            "hp_temp": 0,
            "hit_dice_total": f"1d{hd_face}",
            "hit_dice_current": f"1d{hd_face}",
            "death_save_successes": 0,
            "death_save_failures": 0,
            "abilities": abilities,
            "skills": {s: {"proficient": True, "bonus": 2, "expertise": False} for s in preset.get("skills", [])},
            "spells": spells,
            "spell_slots_total": {"1": 2} if spells else {},
            "spell_slots_used": {},
            "weapon_actions": weapons,
            "features": [
                {"name": f"Competencias de {char_class}", "source": char_class, "description": f"Entrenado en el repertorio de combate de {char_class}."},
                {"name": f"Trasfondo {bg}", "source": bg, "description": f"Beneficio inicial concedido por la vida de {bg}."},
            ],
            "sessions": [],
            "network_nodes": [],
            "network_edges": [],
        }

    def generate_random_character(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Genera un personaje procedural completo con tiradas 4d6 descartando el menor."""
        opts = options or {}
        f_class = opts.get("forced_class")
        f_species = opts.get("forced_species")
        f_level = int(opts.get("forced_level", 1))

        raw = RandomCharacterGenerator.generate_random_character(
            forced_class=f_class,
            forced_species=f_species,
            forced_level=f_level
        )

        char_class = raw["char_class"]
        species = raw["species"]
        level = raw["level"]
        final_scores = raw["final_abilities"]

        calc_mod = lambda score: (score - 10) // 2
        con_mod = calc_mod(final_scores.get("CON", 10))
        des_mod = calc_mod(final_scores.get("DES", 10))
        hd_face = raw["hit_dice_faces"]

        abilities: Dict[str, Any] = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = final_scores.get(stat, 10)
            mod = calc_mod(base)
            abilities[stat] = {
                "base": base,
                "override": 0,
                "bonus": mod,
                "proficient": False,
                "save_bonus": mod,
            }

        preset = raw["preset"]
        weapons = []
        for w_name, w_dmg, w_notes in preset.get("weapons", []):
            weapons.append({
                "name": w_name,
                "type": "Cuerpo a cuerpo" if "Arco" not in w_name and "Ballesta" not in w_name else "A distancia",
                "range_val": "5 pies" if "Arco" not in w_name and "Ballesta" not in w_name else "80/320",
                "hit_dc": f"+{raw['proficiency_bonus'] + max(calc_mod(final_scores['FUE']), calc_mod(final_scores['DES']))}",
                "damage_dice": w_dmg.split(" ")[0],
                "damage_type": w_dmg.split(" ")[1] if len(w_dmg.split(" ")) > 1 else "cortante",
                "notes": w_notes,
                "proficient": True,
            })

        return {
            "name": raw["name"],
            "char_class": char_class,
            "subclass": "",
            "level": level,
            "race": species,
            "background": raw["background"],
            "alignment": raw["alignment"],
            "xp": 0,
            "inspiration": False,
            "proficiency_bonus": raw["proficiency_bonus"],
            "ac": raw["armor_class"],
            "speed": 30,
            "initiative": raw["initiative_bonus"],
            "hp_current": raw["hp_current"],
            "hp_max": raw["hp_max"],
            "hp_temp": 0,
            "hit_dice_total": f"{level}d{hd_face}",
            "hit_dice_current": f"{level}d{hd_face}",
            "death_save_successes": 0,
            "death_save_failures": 0,
            "abilities": abilities,
            "skills": {s: {"proficient": True, "bonus": raw["proficiency_bonus"], "expertise": False} for s in preset.get("skills", [])},
            "spells": [],
            "spell_slots_total": {},
            "spell_slots_used": {},
            "weapon_actions": weapons,
            "features": [
                {"name": "Personalidad", "source": "Trasfondo", "description": raw["personality_trait"]},
                {"name": "Ideal", "source": "Alineamiento", "description": raw["ideal"]},
                {"name": "Vínculo", "source": "Historia", "description": raw["bond"]},
                {"name": "Defecto", "source": "Historia", "description": raw["flaw"]},
            ],
            "sessions": [],
            "network_nodes": [],
            "network_edges": [],
        }

    def perform_rest(self, char_id: int, rest_type: str, hit_dice_spent: int = 0) -> Dict[str, Any]:
        """Aplica descanso corto o descanso largo y actualiza la base de datos."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        if rest_type == "long":
            char, message = perform_long_rest(char)
        else:
            char, message = perform_short_rest(char, hit_dice_spent=int(hit_dice_spent))

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {
            "success": True,
            "message": message,
            "character": self._serialize_character(char),
        }

    # =========================================================================
    # AJUSTES & TEMAS
    # =========================================================================

    def get_settings(self) -> Dict[str, Any]:
        """Retorna todos los ajustes configurados."""
        return {
            "theme": self._db.get_setting("theme", "dark-obsidian"),
            "dnd_edition": self._db.get_setting("dnd_edition", "5.5e"),
            "language": self._db.get_setting("language", "es"),
            "talespire_mode": self._db.get_setting("talespire_mode", "dm"),
            "talespire_enabled": self._db.get_setting("talespire_enabled", "true") == "true",
            "talespire_auto_throw": self._db.get_setting("talespire_auto_throw", "true") == "true",
            "okf_path": self._db.get_setting("okf_path", os.path.join(self._base_dir, "okf_dnd5e")),
            "custom_themes_dir": os.path.join(self._base_dir, "themes"),
            "last_seen_version": self._db.get_setting("last_seen_version", ""),
            "has_completed_onboarding": self._db.get_setting("has_completed_onboarding", "false").lower() == "true",
        }

    def set_setting(self, key: str, value: Any) -> bool:
        """Guarda un ajuste en la base de datos."""
        self._db.set_setting(key, str(value))
        return True

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Retorna temas base y temas personalizados en themes/ sin duplicar IDs."""
        themes_map: Dict[str, Dict[str, Any]] = {
            "dark-obsidian": {"id": "dark-obsidian", "name": "Obsidian & Steel (Oscuro)", "is_dark": True},
            "light-obsidian": {"id": "light-obsidian", "name": "Obsidian & Steel (Claro)", "is_dark": False},
            "dark-parchment": {"id": "dark-parchment", "name": "Illuminated Parchment (Oscuro)", "is_dark": True},
            "light-parchment": {"id": "light-parchment", "name": "Illuminated Parchment (Claro)", "is_dark": False},
            "dark-amethyst": {"id": "dark-amethyst", "name": "Arcane Amethyst (Oscuro)", "is_dark": True},
            "light-amethyst": {"id": "light-amethyst", "name": "Arcane Amethyst (Claro)", "is_dark": False},
            "dark-mithril": {"id": "dark-mithril", "name": "Mithril Scribe (Oscuro)", "is_dark": True},
            "light-mithril": {"id": "light-mithril", "name": "Mithril Scribe (Claro)", "is_dark": False},
        }
        themes_dir = os.path.join(self._base_dir, "themes")
        if os.path.exists(themes_dir):
            for entry in sorted(os.listdir(themes_dir)):
                theme_path = os.path.join(themes_dir, entry)
                if os.path.isdir(theme_path):
                    json_path = os.path.join(theme_path, "theme.json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            tid = meta.get("id", entry)
                            if tid not in themes_map:
                                themes_map[tid] = {
                                    "id": tid,
                                    "name": meta.get("name", entry),
                                    "is_dark": bool(meta.get("is_dark", True)),
                                }
                        except Exception:
                            pass
        return list(themes_map.values())
