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
                char.weapons = [WeaponAction(**w) if isinstance(w, dict) else w for w in v]
            elif k == "spell_slots":
                char.spell_slots = {
                    lvl: SpellSlotTier(**tier) if isinstance(tier, dict) else tier
                    for lvl, tier in v.items()
                }
            elif k == "spells":
                spell_fields = {f.name for f in fields(SpellItem)}
                char.spells = [
                    SpellItem(**{sk: sv for sk, sv in s.items() if sk in spell_fields})
                    if isinstance(s, dict) else s
                    for s in v
                ]
            elif k == "features":
                char.features = [CharacterFeature(**f) if isinstance(f, dict) else f for f in v]
            elif k == "sessions":
                char.sessions = [SessionLog(**sess) if isinstance(sess, dict) else sess for sess in v]
            elif k == "network_nodes":
                char.network_nodes = [NetworkNode(**n) if isinstance(n, dict) else n for n in v]
            elif k == "network_edges":
                char.network_edges = [NetworkEdge(**e) if isinstance(e, dict) else e for e in v]
            elif hasattr(char, k):
                setattr(char, k, v)

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
