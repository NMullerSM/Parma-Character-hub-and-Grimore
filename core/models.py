"""
Modelos de Datos para Visualizador & Editor D&D 5e (Flet Edition)
Arquitectura modular, fuertemente tipada y con serialización JSON completa.
"""
from dataclasses import dataclass, field, fields, asdict
from typing import List, Dict, Optional, Any


@dataclass
class AbilityScore:
    name: str
    score: int = 10

    @property
    def modifier(self) -> int:
        return (self.score - 10) // 2

    @property
    def modifier_str(self) -> str:
        mod = self.modifier
        return f"+{mod}" if mod >= 0 else str(mod)


@dataclass
class SkillEntry:
    name: str
    stat: str
    prof_type: str = "none"  # "none", "proficient", "expertise"
    bonus: int = 0


@dataclass
class WeaponAction:
    name: str
    attack_bonus: str = "+0"
    damage: str = "1d4"
    damage_type: str = "contundente"
    notes: str = ""


@dataclass
class SpellItem:
    id: str = ""
    name: str = ""
    name_en: str = ""
    level: int = 0
    school: str = "Evocación"
    casting_time: str = "1 acción"
    range: str = "18 m"
    components: str = "V, S"
    duration: str = "Instantáneo"
    concentration: bool = False
    ritual: bool = False
    description: str = ""
    higher_levels: str = ""
    source: str = "PHB 2024"
    classes: List[str] = field(default_factory=list)


@dataclass
class SpellSlotTier:
    level: int
    total: int = 0
    current: int = 0


@dataclass
class CharacterFeature:
    id: str = ""
    name: str = ""
    source: str = "Clase"  # Clase, Raza, Dote, etc.
    description: str = ""
    uses_max: int = 0
    uses_current: int = 0
    recharge: str = "Largo"  # Corto, Largo, Especial


@dataclass
class SessionLog:
    id: str = ""
    date: str = ""
    title: str = ""
    summary: str = ""
    loot: str = ""
    xp_gained: int = 0


@dataclass
class NetworkNode:
    id: str
    name: str
    role: str = "ally"  # ally, villain, contact, companion, enigma, neutral
    description: str = ""
    avatar_base64: str = ""
    x: float = 0.0
    y: float = 0.0


@dataclass
class NetworkEdge:
    source_id: str
    target_id: str
    relation: str = "Aliado"


@dataclass
class CharacterSheet:
    id: Optional[int] = None
    # Identidad Básica
    name: str = "Nuevo Aventurero"
    char_class: str = "Bardo"
    subclass: str = "Colegio de Susurros"
    level: int = 4
    race: str = "Elfo (Drow)"
    background: str = "Vagabundo"
    alignment: str = "Caótico Bueno"
    xp: int = 2700

    # Combate y Salud
    hp_current: int = 27
    hp_max: int = 27
    hp_temp: int = 0
    hit_dice_max: int = 4
    hit_dice_current: int = 4
    hit_dice_faces: int = 8
    conditions: List[str] = field(default_factory=list)
    armor_class: int = 15
    initiative_bonus: int = 3
    speed: str = "9 m"
    proficiency_bonus: int = 2
    inspiration: bool = False

    # Salvaciones contra la muerte
    death_saves_success: int = 0
    death_saves_failure: int = 0

    # Atributos principales
    abilities: Dict[str, int] = field(default_factory=lambda: {
        "FUE": 8,
        "DES": 16,
        "CON": 12,
        "INT": 13,
        "SAB": 10,
        "CAR": 17
    })

    # Competencia en salvaciones
    saving_throw_profs: List[str] = field(default_factory=lambda: ["DES", "CAR"])

    # Habilidades
    skills: Dict[str, str] = field(default_factory=lambda: {
        "Acrobacias": "proficient",
        "Engaño": "expertise",
        "Interpretación": "expertise",
        "Juego de Manos": "proficient",
        "Percepción": "proficient",
        "Sigilo": "proficient",
    })

    # Armas / Acciones
    weapons: List[WeaponAction] = field(default_factory=lambda: [
        WeaponAction(name="Estoque", attack_bonus="+5", damage="1d8+3", damage_type="Perforante", notes="Sutil"),
        WeaponAction(name="Daga", attack_bonus="+5", damage="1d4+3", damage_type="Perforante", notes="Arrojadiza 6/18m"),
        WeaponAction(name="Ballesta de Mano", attack_bonus="+5", damage="1d6+3", damage_type="Perforante", notes="Rango 9/36m"),
    ])

    # Espacios de Conjuros (Niveles 1 a 9)
    spell_slots: Dict[str, SpellSlotTier] = field(default_factory=lambda: {
        "1": SpellSlotTier(level=1, total=4, current=4),
        "2": SpellSlotTier(level=2, total=3, current=3),
        "3": SpellSlotTier(level=3, total=0, current=0),
        "4": SpellSlotTier(level=4, total=0, current=0),
        "5": SpellSlotTier(level=5, total=0, current=0),
        "6": SpellSlotTier(level=6, total=0, current=0),
        "7": SpellSlotTier(level=7, total=0, current=0),
        "8": SpellSlotTier(level=8, total=0, current=0),
        "9": SpellSlotTier(level=9, total=0, current=0),
    })

    # Conjuros
    spells: List[SpellItem] = field(default_factory=list)

    # Rasgos y Poderes
    features: List[CharacterFeature] = field(default_factory=list)

    # Biografía y Retrato
    portrait_path: str = ""
    portrait_base64: str = ""
    appearance: str = ""
    history: str = ""
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""
    languages: str = "Común, Élfico, Inframundo"
    senses: str = "Visión en la Oscuridad Superior (36 m)"
    proficiencies_extra: str = "Instrumentos: Laúd, Flauta dulce, Violín. Armaduras: Ligeras. Armas: Simples, Ballesta de mano, Espada corta, Estoque."

    # Diario de Campaña
    sessions: List[SessionLog] = field(default_factory=list)

    # Red de Personajes (Campaña)
    network_nodes: List[NetworkNode] = field(default_factory=list)
    network_edges: List[NetworkEdge] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterSheet":
        char = cls()
        for k, v in data.items():
            if k == "weapons":
                char.weapons = [
                    WeaponAction(
                        name=w.get("name", "Arma"),
                        attack_bonus=str(w.get("attack_bonus") or w.get("hit_dc", "+0")),
                        damage=str(w.get("damage") or w.get("damage_dice", "1d4")),
                        damage_type=str(w.get("damage_type", "")),
                        notes=str(w.get("notes", "")),
                    )
                    if isinstance(w, dict) else w
                    for w in v
                ]
            elif k == "weapon_actions" and "weapons" not in data:
                char.weapons = [
                    WeaponAction(
                        name=w.get("name", "Arma"),
                        attack_bonus=str(w.get("hit_dc") or w.get("attack_bonus", "+0")),
                        damage=str(w.get("damage_dice") or w.get("damage", "1d4")),
                        damage_type=str(w.get("damage_type", "")),
                        notes=str(w.get("notes", "")),
                    )
                    if isinstance(w, dict) else w
                    for w in v
                ]
            elif k == "spell_slots":
                char.spell_slots = {
                    str(lvl): SpellSlotTier(**tier) if isinstance(tier, dict) else tier
                    for lvl, tier in v.items()
                }
            elif k == "spells":
                spell_fields = {f.name for f in fields(SpellItem)}
                parsed_spells = []
                for s in v:
                    if isinstance(s, dict):
                        s_norm = dict(s)
                        if "cast_time" in s_norm and "casting_time" not in s_norm:
                            s_norm["casting_time"] = s_norm["cast_time"]
                        if "range_area" in s_norm and "range" not in s_norm:
                            s_norm["range"] = s_norm["range_area"]
                        if "notes" in s_norm and not s_norm.get("description"):
                            s_norm["description"] = s_norm["notes"]
                        parsed_spells.append(SpellItem(**{sk: sv for sk, sv in s_norm.items() if sk in spell_fields}))
                    else:
                        parsed_spells.append(s)
                char.spells = parsed_spells
            elif k == "features":
                feat_fields = {f.name for f in fields(CharacterFeature)}
                char.features = [
                    CharacterFeature(**{fk: fv for fk, fv in f.items() if fk in feat_fields})
                    if isinstance(f, dict) else f
                    for f in v
                ]
            elif k == "sessions":
                sess_fields = {f.name for f in fields(SessionLog)}
                char.sessions = [
                    SessionLog(**{sk: sv for sk, sv in sess.items() if sk in sess_fields})
                    if isinstance(sess, dict) else sess
                    for sess in v
                ]
            elif k == "network_nodes":
                node_fields = {f.name for f in fields(NetworkNode)}
                char.network_nodes = [
                    NetworkNode(**{nk: nv for nk, nv in n.items() if nk in node_fields})
                    if isinstance(n, dict) else n
                    for n in v
                ]
            elif k == "network_edges":
                edge_fields = {f.name for f in fields(NetworkEdge)}
                char.network_edges = [
                    NetworkEdge(**{ek: ev for ek, ev in e.items() if ek in edge_fields})
                    if isinstance(e, dict) else e
                    for e in v
                ]
            elif k == "abilities" and isinstance(v, dict):
                norm_abilities: Dict[str, int] = {}
                profs_from_abilities: List[str] = list(data.get("saving_throw_profs", []))
                has_dict_ability = False
                for stat_k, stat_v in v.items():
                    if isinstance(stat_v, dict):
                        has_dict_ability = True
                        override_val = int(stat_v.get("override", 0) or 0)
                        base_val = int(stat_v.get("base", 10) or 10)
                        norm_abilities[stat_k] = override_val if override_val > 0 else base_val
                        if stat_v.get("proficient") and stat_k not in profs_from_abilities:
                            profs_from_abilities.append(stat_k)
                    else:
                        try:
                            norm_abilities[stat_k] = int(stat_v)
                        except (ValueError, TypeError):
                            norm_abilities[stat_k] = 10
                char.abilities = norm_abilities
                if has_dict_ability and "saving_throw_profs" not in data:
                    char.saving_throw_profs = profs_from_abilities
            elif k == "skills" and isinstance(v, dict):
                norm_skills: Dict[str, str] = {}
                for sk_k, sk_v in v.items():
                    if isinstance(sk_v, dict):
                        if sk_v.get("expertise"):
                            norm_skills[sk_k] = "expertise"
                        elif sk_v.get("proficient"):
                            norm_skills[sk_k] = "proficient"
                        else:
                            norm_skills[sk_k] = "none"
                    else:
                        norm_skills[sk_k] = str(sk_v)
                char.skills = norm_skills
            elif k == "ac" and "armor_class" not in data:
                char.armor_class = int(v)
            elif k == "initiative" and "initiative_bonus" not in data:
                char.initiative_bonus = int(v)
            elif k == "death_save_successes" and "death_saves_success" not in data:
                char.death_saves_success = int(v)
            elif k == "death_save_failures" and "death_saves_failure" not in data:
                char.death_saves_failure = int(v)
            elif k == "speed":
                char.speed = f"{v} pies" if isinstance(v, (int, float)) else str(v)
            elif k == "hit_dice_current":
                if isinstance(v, str) and "d" in v.lower():
                    try:
                        char.hit_dice_current = int(v.lower().split("d")[0].strip())
                    except ValueError:
                        char.hit_dice_current = char.level
                else:
                    try:
                        char.hit_dice_current = int(v)
                    except (ValueError, TypeError):
                        char.hit_dice_current = char.level
            elif hasattr(char, k):
                setattr(char, k, v)

        # Soportar spell_slots_total y spell_slots_used provenientes del frontend React
        if "spell_slots_total" in data and isinstance(data["spell_slots_total"], dict):
            used_map = data.get("spell_slots_used", {}) if isinstance(data.get("spell_slots_used"), dict) else {}
            for lvl_str, tot_val in data["spell_slots_total"].items():
                lvl_key = str(lvl_str)
                tot_int = int(tot_val or 0)
                used_int = int(used_map.get(lvl_key, 0) or 0)
                char.spell_slots[lvl_key] = SpellSlotTier(
                    level=int(lvl_key) if lvl_key.isdigit() else 1,
                    total=tot_int,
                    current=max(0, tot_int - used_int)
                )

        # Soportar hit_dice_total (ej. "4d10") si viene desde el frontend
        if "hit_dice_total" in data and isinstance(data["hit_dice_total"], str) and "d" in data["hit_dice_total"].lower():
            parts = data["hit_dice_total"].lower().split("d", 1)
            if "hit_dice_max" not in data:
                try:
                    char.hit_dice_max = int(parts[0].strip())
                except ValueError:
                    pass
            if "hit_dice_faces" not in data:
                try:
                    char.hit_dice_faces = int(parts[1].strip())
                except ValueError:
                    pass

        # Asegurar coherencia en dados de golpe y condiciones si faltan en guardados anteriores
        if "hit_dice_max" not in data or char.hit_dice_max <= 0:
            char.hit_dice_max = max(1, char.level)
        if "hit_dice_current" not in data:
            char.hit_dice_current = char.hit_dice_max
        if "hit_dice_faces" not in data or char.hit_dice_faces <= 0:
            hd_map = {
                "bárbaro": 12, "barbaro": 12,
                "guerrero": 10, "paladín": 10, "paladin": 10, "explorador": 10,
                "bardo": 8, "clérigo": 8, "clerigo": 8, "druida": 8, "monje": 8, "pícaro": 8, "picaro": 8, "brujo": 8,
                "mago": 6, "hechicero": 6
            }
            char.hit_dice_faces = hd_map.get(char.char_class.lower(), 8)
        if not isinstance(char.conditions, list):
            char.conditions = []

        return char
