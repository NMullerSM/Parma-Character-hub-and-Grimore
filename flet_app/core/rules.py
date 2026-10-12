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


CLASS_CASTING_ABILITY = {
    "Bardo": "CAR",
    "Brujo": "CAR",
    "Hechicero": "CAR",
    "Paladín": "CAR",
    "Clérigo": "SAB",
    "Druida": "SAB",
    "Explorador": "SAB",
    "Mago": "INT",
    "Artífice": "INT",
}


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


def get_character_spell_stats(char: CharacterSheet) -> Dict[str, Any]:
    ability = CLASS_CASTING_ABILITY.get(char.char_class, "CAR")
    return get_spell_stats(char, casting_ability=ability)


CLASS_HIT_DICE = {
    "Bárbaro": 12,
    "Guerrero": 10,
    "Paladín": 10,
    "Explorador": 10,
    "Bardo": 8,
    "Clérigo": 8,
    "Druida": 8,
    "Monje": 8,
    "Pícaro": 8,
    "Brujo": 8,
    "Hechicero": 6,
    "Mago": 6,
    "Artífice": 8,
}

DND_CONDITIONS = [
    {
        "name": "Concentración",
        "icon": "auto_awesome",
        "color": "#a855f7",
        "description": "Mantienes un conjuro activo. Si recibes daño, debes superar una salvación de CON (CD 10 o la mitad del daño)."
    },
    {
        "name": "Envenenado",
        "icon": "coronavirus",
        "color": "#22c55e",
        "description": "Tienes desventaja en tiradas de ataque y pruebas de característica."
    },
    {
        "name": "Asustado",
        "icon": "sentiment_very_dissatisfied",
        "color": "#ef4444",
        "description": "Desventaja en pruebas y ataques mientras la fuente del miedo esté a la vista. No puedes acercarte voluntariamente."
    },
    {
        "name": "Derribado",
        "icon": "airline_seat_flat",
        "color": "#f59e0b",
        "description": "Tus ataques tienen desventaja. Ataques a 1.5m contra ti tienen ventaja. Levantarse cuesta la mitad de tu movimiento."
    },
    {
        "name": "Cegado",
        "icon": "visibility_off",
        "color": "#64748b",
        "description": "Fallas automáticamente pruebas de visión. Ataques contra ti tienen ventaja; tus ataques tienen desventaja."
    },
    {
        "name": "Ensordecido",
        "icon": "hearing_disabled",
        "color": "#64748b",
        "description": "Fallas automáticamente pruebas de audición."
    },
    {
        "name": "Paralizado",
        "icon": "lock",
        "color": "#dc2626",
        "description": "Incapacitado (sin acciones ni reacciones). Fallas salvaciones FUE/DES. Ataques a 1.5m son críticos automáticos."
    },
    {
        "name": "Incapacitado",
        "icon": "pan_tool",
        "color": "#e11d48",
        "description": "No puedes realizar acciones ni reacciones. Tu concentración se interrumpe de inmediato."
    },
    {
        "name": "Invisible",
        "icon": "blur_on",
        "color": "#38bdf8",
        "description": "Imposible de ver sin magia o sentidos especiales. Tienes ventaja en ataques; ataques contra ti tienen desventaja."
    },
]


def perform_short_rest(char: CharacterSheet, hit_dice_spent: int = 1) -> Tuple[CharacterSheet, str]:
    """Aplica descanso corto: consume dados de golpe según la clase y recupera recursos de descanso corto."""
    curr_dice = getattr(char, "hit_dice_current", char.level)
    actual_spent = max(0, min(curr_dice, hit_dice_spent))
    char.hit_dice_current = max(0, curr_dice - actual_spent)

    con_mod = calc_modifier(char.abilities.get("CON", 10))
    healed = 0
    rolls = []
    faces = getattr(char, "hit_dice_faces", 8) or 8

    for _ in range(actual_spent):
        roll = random.randint(1, faces)
        tot = max(1, roll + con_mod)
        healed += tot
        rolls.append(f"1d{faces}({roll}) + {con_mod} = {tot}")

    old_hp = char.hp_current
    char.hp_current = min(char.hp_max, char.hp_current + healed)
    recovered = char.hp_current - old_hp

    # Recuperar poderes de descanso corto
    features_recovered = []
    for f in char.features:
        if f.recharge in ("Corto", "Corto o Largo"):
            f.uses_current = f.uses_max
            features_recovered.append(f.name)

    hd_max = getattr(char, "hit_dice_max", char.level) or max(1, char.level)
    if actual_spent > 0:
        msg = f"Descanso Corto ({actual_spent}d{faces} gastados): Se recuperaron {recovered} PG ({', '.join(rolls)}). Dados de golpe restantes: {char.hit_dice_current}/{hd_max}."
    else:
        msg = f"Descanso Corto (sin gastar dados): Dados de golpe restantes: {char.hit_dice_current}/{hd_max}."

    if features_recovered:
        msg += f" Usos recargados: {', '.join(features_recovered)}."
    return char, msg


def perform_long_rest(char: CharacterSheet) -> Tuple[CharacterSheet, str]:
    """Aplica descanso largo: restaura PG al máximo, la mitad de dados de golpe gastados, espacios de conjuro y poderes."""
    char.hp_current = char.hp_max
    char.hp_temp = 0
    char.death_saves_success = 0
    char.death_saves_failure = 0

    # Restaurar dados de golpe (al menos la mitad de los dados máximos, mín 1)
    hd_max = getattr(char, "hit_dice_max", char.level) or max(1, char.level)
    char.hit_dice_max = hd_max
    hd_curr = getattr(char, "hit_dice_current", hd_max)
    recovered_hd = max(1, hd_max // 2)
    new_hd = min(hd_max, hd_curr + recovered_hd)
    diff_hd = new_hd - hd_curr
    char.hit_dice_current = new_hd

    # Restaurar todos los espacios de conjuros
    for tier in char.spell_slots.values():
        tier.current = tier.total

    # Restaurar todos los usos de rasgos
    for f in char.features:
        f.uses_current = f.uses_max

    hd_msg = f"+{diff_hd} Dados de Golpe ({char.hit_dice_current}/{char.hit_dice_max})" if diff_hd > 0 else f"Dados de Golpe al máximo ({char.hit_dice_current}/{char.hit_dice_max})"
    return char, f"Descanso Largo: PG al 100%, {hd_msg}, espacios de conjuro y poderes recargados."


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
