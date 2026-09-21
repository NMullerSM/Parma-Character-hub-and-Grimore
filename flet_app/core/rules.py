"""
Motor de Reglas D&D 5e (SRD 5.1 & 2024 Compatible)
Lógica pura, desacoplada de la interfaz gráfica y 100% testeable.
"""
import random
from typing import Dict, Tuple, List, Any
from .models import CharacterSheet


SKILLS_MAP = {
    "Acrobacias": "DES",
    "Trato con Animales": "SAB",
    "Arcanos": "INT",
    "Atletismo": "FUE",
    "Engaño": "CAR",
    "Historia": "INT",
    "Perspicacia": "SAB",
    "Intimidación": "CAR",
    "Investigación": "INT",
    "Medicina": "SAB",
    "Naturaleza": "INT",
    "Percepción": "SAB",
    "Interpretación": "CAR",
    "Persuasión": "CAR",
    "Religión": "INT",
    "Juego de Manos": "DES",
    "Sigilo": "DES",
    "Supervivencia": "SAB"
}


def calc_modifier(score: int) -> int:
    return (score - 10) // 2


def calc_proficiency_bonus(level: int) -> int:
    return max(2, (level - 1) // 4 + 2)


def get_skill_modifier(char: CharacterSheet, skill_name: str) -> int:
    stat = SKILLS_MAP.get(skill_name, "CAR")
    base_mod = calc_modifier(char.abilities.get(stat, 10))
    prof_bonus = calc_proficiency_bonus(char.level)
    prof_type = char.skills.get(skill_name, "none")

    if prof_type == "expertise":
        return base_mod + (prof_bonus * 2)
    elif prof_type == "proficient":
        return base_mod + prof_bonus
    return base_mod


def get_saving_throw_modifier(char: CharacterSheet, stat_name: str) -> int:
    base_mod = calc_modifier(char.abilities.get(stat_name, 10))
    prof_bonus = calc_proficiency_bonus(char.level)
    if stat_name in char.saving_throw_profs:
        return base_mod + prof_bonus
    return base_mod


def get_spell_stats(char: CharacterSheet, casting_ability: str = "CAR") -> Dict[str, Any]:
    prof = calc_proficiency_bonus(char.level)
    mod = calc_modifier(char.abilities.get(casting_ability, 10))
    return {
        "ability": casting_ability,
        "modifier": mod,
        "save_dc": 8 + prof + mod,
        "attack_bonus": f"+{prof + mod}" if (prof + mod) >= 0 else str(prof + mod),
        "prof_bonus": prof
    }


def perform_short_rest(char: CharacterSheet, hit_dice_spent: int = 1) -> Tuple[CharacterSheet, str]:
    """Aplica descanso corto: consume dados de golpe y recupera recursos de descanso corto."""
    con_mod = calc_modifier(char.abilities.get("CON", 10))
    healed = 0
    rolls = []
    for _ in range(hit_dice_spent):
        roll = random.randint(1, 8)
        tot = max(1, roll + con_mod)
        healed += tot
        rolls.append(f"1d8({roll}) + {con_mod} = {tot}")

    old_hp = char.hp_current
    char.hp_current = min(char.hp_max, char.hp_current + healed)
    recovered = char.hp_current - old_hp

    # Recuperar poderes de descanso corto
    features_recovered = []
    for f in char.features:
        if f.recharge in ("Corto", "Corto o Largo"):
            f.uses_current = f.uses_max
            features_recovered.append(f.name)

    msg = f"Descanso Corto: Se recuperaron {recovered} PG ({', '.join(rolls)})."
    if features_recovered:
        msg += f" Usos recargados: {', '.join(features_recovered)}."
    return char, msg


def perform_long_rest(char: CharacterSheet) -> Tuple[CharacterSheet, str]:
    """Aplica descanso largo: restaura PG al máximo, todos los espacios de conjuro y poderes."""
    char.hp_current = char.hp_max
    char.hp_temp = 0
    char.death_saves_success = 0
    char.death_saves_failure = 0

    # Restaurar todos los espacios de conjuros
    for tier in char.spell_slots.values():
        tier.current = tier.total

    # Restaurar todos los usos de rasgos
    for f in char.features:
        f.uses_current = f.uses_max

    return char, "Descanso Largo: PG restaurados al 100%, espacios de conjuro y poderes recargados."


def roll_dice(sides: int, mode: str = "normal", modifier: int = 0) -> Dict[str, Any]:
    """Tirada de dados con soporte de Ventaja, Desventaja y Modificadores."""
    r1 = random.randint(1, sides)
    r2 = random.randint(1, sides)

    if sides == 20:
        if mode == "advantage":
            selected = max(r1, r2)
            breakdown = f"[{r1}, {r2}] -> max: {selected}"
        elif mode == "disadvantage":
            selected = min(r1, r2)
            breakdown = f"[{r1}, {r2}] -> min: {selected}"
        else:
            selected = r1
            breakdown = f"{selected}"
    else:
        selected = r1
        breakdown = f"{selected}"

    total = selected + modifier
    mod_str = f" + {modifier}" if modifier > 0 else (f" - {abs(modifier)}" if modifier < 0 else "")

    return {
        "sides": sides,
        "mode": mode,
        "modifier": modifier,
        "rolls": [r1, r2] if sides == 20 and mode != "normal" else [r1],
        "selected": selected,
        "total": total,
        "is_crit": (sides == 20 and selected == 20),
        "is_fumble": (sides == 20 and selected == 1),
        "detail": f"d{sides}: {breakdown}{mod_str} = {total}"
    }
