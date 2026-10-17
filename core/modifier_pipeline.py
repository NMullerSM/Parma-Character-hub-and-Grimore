"""
Motor Determinista de Modificadores (Modifier Pipeline) para D&D 5e.
Inspirado en la arquitectura backend desacoplada de D&D Beyond:
En lugar de almacenar valores derivados rígidos, almacena la intención de cada regla
como un modificador atómico y calcula el estado final mediante un orden estricto de evaluación:
1. Base Value
2. Reglas 'Set' (fuerzan un valor mínimo absoluto)
3. Modificadores 'Bonus' (Raza + Trasfondo + Clase + Dotes + Magia)
4. Modificadores de Competencia (Proficiency, Expertise, Half-Proficiency)
5. Sentidos y estadísticas derivadas en tiempo real.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from .rules import calc_modifier, calc_proficiency_bonus

class ModifierType(str, Enum):
    BONUS = "bonus"
    SET = "set"
    PROFICIENCY = "proficiency"
    EXPERTISE = "expertise"
    HALF_PROFICIENCY = "half-proficiency"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"
    SENSE = "sense"


class CharacterModifier:
    def __init__(
        self,
        id: str,
        mod_type: ModifierType,
        target_stat: str,
        value: Optional[int] = None,
        source: str = "regla",
        description: str = ""
    ):
        self.id = id
        self.type = mod_type
        self.target_stat = target_stat  # Ej: 'FUE-score', 'armor-class', 'Percepción', 'darkvision'
        self.value = value
        self.source = source
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ModifierType) else str(self.type),
            "target_stat": self.target_stat,
            "value": self.value,
            "source": self.source,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterModifier":
        raw_type = data.get("type", "bonus")
        try:
            m_type = ModifierType(raw_type)
        except ValueError:
            m_type = ModifierType.BONUS
        return cls(
            id=data.get("id", ""),
            mod_type=m_type,
            target_stat=data.get("target_stat", ""),
            value=data.get("value"),
            source=data.get("source", "regla"),
            description=data.get("description", "")
        )


class ModifierPipeline:
    """Motor de cálculo y evaluación de modificadores deterministas."""

    @staticmethod
    def evaluate_ability_score(
        ability_name: str,
        base_score: int,
        modifiers: List[CharacterModifier]
    ) -> int:
        """
        Calcula el valor total de una característica (FUE, DES, CON, INT, SAB, CAR)
        siguiendo el orden: Base -> Set -> Bonos.
        """
        target_tag = f"{ability_name}-score"
        relevant = [m for m in modifiers if m.target_stat == target_tag]

        # 1. Reglas 'Set' (ej. Diadema de Intelecto = 19)
        sets = [m.value for m in relevant if m.type == ModifierType.SET and m.value is not None]
        current = base_score
        if sets:
            highest_set = max(sets)
            if highest_set > current:
                current = highest_set

        # 2. Sumar todos los modificadores 'Bonus'
        bonuses = sum(m.value for m in relevant if m.type == ModifierType.BONUS and m.value is not None)
        return current + bonuses

    @staticmethod
    def evaluate_skill_modifier(
        skill_name: str,
        governing_ability_score: int,
        total_level: int,
        modifiers: List[CharacterModifier]
    ) -> int:
        """Calcula el bono total de una habilidad considerando competencia, pericia o media competencia."""
        ability_mod = calc_modifier(governing_ability_score)
        pb = calc_proficiency_bonus(total_level)

        skill_mods = [m for m in modifiers if m.target_stat == skill_name]

        if any(m.type == ModifierType.EXPERTISE for m in skill_mods):
            return ability_mod + (2 * pb)
        elif any(m.type == ModifierType.PROFICIENCY for m in skill_mods):
            return ability_mod + pb
        elif any(m.target_stat == "all-skills" and m.type == ModifierType.HALF_PROFICIENCY for m in modifiers):
            return ability_mod + (pb // 2)

        return ability_mod

    @staticmethod
    def evaluate_armor_class(
        des_score: int,
        armor_base_ac: int,
        has_shield: bool,
        modifiers: List[CharacterModifier]
    ) -> int:
        """Calcula la Clase de Armadura total sumando bonos mágicos y escudo."""
        ac = armor_base_ac
        if has_shield:
            ac += 2
        # Sumar bonos específicos a AC
        ac_bonuses = sum(
            m.value for m in modifiers
            if m.target_stat == "armor-class" and m.type == ModifierType.BONUS and m.value is not None
        )
        return ac + ac_bonuses

    @staticmethod
    def evaluate_spell_dc(
        casting_stat_score: int,
        total_level: int,
        modifiers: List[CharacterModifier]
    ) -> int:
        """Calcula la Clase de Dificultad (CD) mágica: 8 + PB + Modificador Clave + Bonos."""
        pb = calc_proficiency_bonus(total_level)
        mod = calc_modifier(casting_stat_score)
        bonuses = sum(
            m.value for m in modifiers
            if m.target_stat == "spell-save-dc" and m.type == ModifierType.BONUS and m.value is not None
        )
        return 8 + pb + mod + bonuses
