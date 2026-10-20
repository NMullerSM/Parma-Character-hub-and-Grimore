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


def roll_dice_multiple(count: int = 1, sides: int = 20, mode: str = "normal", modifier: int = 0) -> Dict[str, Any]:
    """
    Tirada de uno o múltiples dados con soporte de Ventaja/Desventaja (para d20)
    y acumulador de pools de dados con modificadores.
    """
    count = max(1, count)
    if count == 1:
        res = roll_dice(sides=sides, mode=mode, modifier=modifier)
        res["count"] = 1
        return res

    # Múltiples dados
    rolls = [random.randint(1, sides) for _ in range(count)]
    subtotal = sum(rolls)
    total = subtotal + modifier
    mod_str = f" + {modifier}" if modifier > 0 else (f" - {abs(modifier)}" if modifier < 0 else "")
    rolls_str = ", ".join(str(r) for r in rolls)

    is_crit = False
    is_fumble = False
    if sides == 20:
        is_crit = (20 in rolls)
        is_fumble = (1 in rolls and not is_crit)

    return {
        "count": count,
        "sides": sides,
        "mode": mode,
        "modifier": modifier,
        "rolls": rolls,
        "selected": subtotal,
        "total": total,
        "is_crit": is_crit,
        "is_fumble": is_fumble,
        "detail": f"{count}d{sides}: [{rolls_str}]{mod_str} = {total}"
    }


def roll_dice_pool(pool: Dict[Any, int], modifier: int = 0, mode: str = "normal") -> Dict[str, Any]:
    """
    Resuelve una tirada compuesta de múltiples tipos de dados (ej. 1d20 + 2d6 + 1d8 + 3).
    Soporta claves de dados enteras (20, 6) o textuales ('d20', 'd6').
    """
    clean_pool: Dict[int, int] = {}
    for k, v in pool.items():
        if v <= 0:
            continue
        try:
            face = int(str(k).lower().replace("d", ""))
            clean_pool[face] = clean_pool.get(face, 0) + int(v)
        except ValueError:
            continue

    if not clean_pool:
        # Default a 1d20 si el pool está vacío
        clean_pool = {20: 1}

    # Ordenar con d20 primero, luego d100, d12, d10, d8, d6, d4
    sorted_faces = sorted(clean_pool.keys(), key=lambda f: (0 if f == 20 else 1, -f))

    parts = []
    formula_parts = []
    subtotal = 0
    is_crit = False
    is_fumble = False
    d20_rolled = False

    for sides in sorted_faces:
        count = clean_pool[sides]
        if sides == 20 and count == 1 and mode in ("advantage", "disadvantage"):
            d20_rolled = True
            r1 = random.randint(1, 20)
            r2 = random.randint(1, 20)
            sel = max(r1, r2) if mode == "advantage" else min(r1, r2)
            subtotal += sel
            if sel == 20:
                is_crit = True
            elif sel == 1:
                is_fumble = True
            tag = "ventaja" if mode == "advantage" else "desventaja"
            parts.append(f"1d20[{r1}, {r2} -> {sel}]({tag})")
            formula_parts.append(f"1d20({tag})")
        else:
            rolls = [random.randint(1, sides) for _ in range(count)]
            s = sum(rolls)
            subtotal += s
            if sides == 20:
                d20_rolled = True
                if 20 in rolls:
                    is_crit = True
                elif 1 in rolls and not is_crit:
                    is_fumble = True
            rolls_repr = ", ".join(str(r) for r in rolls)
            parts.append(f"{count}d{sides}({rolls_repr})")
            formula_parts.append(f"{count}d{sides}")

    if not d20_rolled:
        is_crit = False
        is_fumble = False

    total = subtotal + modifier
    mod_str = f" + {modifier}" if modifier > 0 else (f" - {abs(modifier)}" if modifier < 0 else "")
    mod_formula = f"+{modifier}" if modifier > 0 else (f"{modifier}" if modifier < 0 else "")

    detail = f"{' + '.join(parts)}{mod_str} = {total}"
    formula = f"{' + '.join(formula_parts)}{mod_formula}"

    return {
        "pool": clean_pool,
        "modifier": modifier,
        "mode": mode,
        "subtotal": subtotal,
        "total": total,
        "is_crit": is_crit,
        "is_fumble": is_fumble,
        "detail": detail,
        "formula": formula
    }


def compute_dynamic_features(char: CharacterSheet) -> List[Any]:
    """
    Calcula y actualiza dinámicamente los rasgos, dotes y habilidades especiales
    del personaje de acuerdo a las reglas oficiales de D&D 5e / 2024 (usos por nivel,
    dados escalados, recarga en descansos y CDs de salvación).
    """
    from .models import CharacterFeature

    car_mod = calc_modifier(char.abilities.get("CAR", 10))
    des_mod = calc_modifier(char.abilities.get("DES", 10))
    fue_mod = calc_modifier(char.abilities.get("FUE", 10))
    int_mod = calc_modifier(char.abilities.get("INT", 10))
    sab_mod = calc_modifier(char.abilities.get("SAB", 10))
    prof = calc_proficiency_bonus(char.level)

    features = list(char.features or [])
    feat_names = {f.name.lower(): f for f in features}

    # 1. Inspiración Bárdica (Bardo)
    if "bardo" in (char.char_class or "").lower() or any("inspiración" in k for k in feat_names):
        bard_die = "d6" if char.level < 5 else ("d8" if char.level < 10 else ("d10" if char.level < 15 else "d12"))
        max_uses = max(1, car_mod)
        recharge = "Corto" if char.level >= 5 else "Largo"
        insp_name = f"Inspiración Bárdica ({bard_die})"

        # Buscar si ya existe
        existing = next((f for f in features if "inspiración" in f.name.lower() or "bárdica" in f.name.lower()), None)
        if existing:
            existing.name = insp_name
            existing.uses_max = max_uses
            if existing.uses_current is None or existing.uses_current > max_uses:
                existing.uses_current = max_uses
            existing.recharge = recharge
            existing.description = (
                f"Con una acción adicional, inspiras a una criatura a 18 m. Añade 1{bard_die} a una tirada de "
                f"d20 durante los próximos 10 minutos. Usos máximos: {max_uses} (+{car_mod} CAR). "
                f"Recarga con Descanso {recharge}."
            )
        else:
            features.insert(
                0,
                CharacterFeature(
                    id="feat_bardic_insp",
                    name=insp_name,
                    source="Bardo",
                    uses_max=max_uses,
                    uses_current=max_uses,
                    recharge=recharge,
                    description=f"Con una acción adicional, inspiras a una criatura a 18 m (1{bard_die}). Recarga con Descanso {recharge}."
                )
            )

    # 2. Hojas Psíquicas (Psychic Blades - Colegio de Susurros)
    if "susurro" in (char.subclass or "").lower() or any("hojas psíquicas" in k or "psychic blades" in k for k in feat_names):
        pb_die = "2d6" if char.level < 5 else ("3d6" if char.level < 10 else ("5d6" if char.level < 15 else "8d6"))
        recharge = "Corto" if char.level >= 5 else "Largo"
        existing = next((f for f in features if "hojas psíquicas" in f.name.lower() or "psychic blades" in f.name.lower()), None)
        desc = (
            f"Al impactar con un arma sutil o a distancia, puedes gastar 1 uso de Inspiración Bárdica para infligir "
            f"+{pb_die} de daño psíquico a la criatura (1 vez por turno). Recarga con Descanso {recharge}."
        )
        if existing:
            existing.name = f"Hojas Psíquicas ({pb_die})"
            existing.description = desc
            existing.recharge = recharge
            existing.uses_max = max(1, car_mod)
        else:
            features.append(
                CharacterFeature(
                    id="feat_psychic_blades",
                    name=f"Hojas Psíquicas ({pb_die})",
                    source="Colegio de Susurros",
                    uses_max=max(1, car_mod),
                    uses_current=max(1, car_mod),
                    recharge=recharge,
                    description=desc,
                )
            )

    # 3. Palabras de Terror (Words of Terror - Colegio de Susurros)
    if "susurro" in (char.subclass or "").lower() or any("palabras de terror" in k or "words of terror" in k for k in feat_names):
        cd_val = 8 + prof + car_mod
        desc = (
            f"Tras hablar 1 minuto a solas con un humanoide, debe superar una tirada de salvación de SAB "
            f"contra CD {cd_val} o quedará asustado de ti (o de quien elijas) durante 1 hora. Recarga con Descanso Corto o Largo."
        )
        existing = next((f for f in features if "palabras de terror" in f.name.lower() or "words of terror" in f.name.lower()), None)
        if existing:
            existing.description = desc
            existing.recharge = "Corto"
            existing.uses_max = 1
        else:
            features.append(
                CharacterFeature(
                    id="feat_words_of_terror",
                    name=f"Palabras de Terror (CD {cd_val})",
                    source="Colegio de Susurros",
                    uses_max=1,
                    uses_current=1,
                    recharge="Corto",
                    description=desc,
                )
            )

    # 4. Magia Drow (Especie / Linaje Drow)
    if "drow" in (char.race or "").lower() or any("magia drow" in k for k in feat_names):
        existing = next((f for f in features if "magia drow" in f.name.lower()), None)
        desc = (
            "Conoces el truco Luces Danzantes (a voluntad). "
            + ("A partir de nivel 3 puedes lanzar Fuego Feérico 1 vez por descanso largo sin gastar ranura. " if char.level >= 3 else "")
            + ("A nivel 5 puedes lanzar Oscuridad 1 vez por descanso largo. " if char.level >= 5 else "")
            + f"Tu aptitud mágica es Carisma (CD {8 + prof + car_mod})."
        )
        if existing:
            existing.description = desc
            existing.uses_max = 1
            existing.recharge = "Largo"
        else:
            features.append(
                CharacterFeature(
                    id="feat_drow_magic",
                    name="Magia Drow",
                    source="Linaje Drow",
                    uses_max=1,
                    uses_current=1,
                    recharge="Largo",
                    description=desc,
                )
            )

    # 5. Dote Afortunado (Lucky)
    if any("afortunado" in k or "lucky" in k for k in feat_names):
        lucky_feat = next((f for f in features if "afortunado" in f.name.lower() or "lucky" in f.name.lower()), None)
        if lucky_feat:
            lucky_feat.uses_max = prof
            if lucky_feat.uses_current is None or lucky_feat.uses_current > prof:
                lucky_feat.uses_current = prof
            lucky_feat.recharge = "Largo"
            lucky_feat.description = (
                f"Tienes {prof} puntos de suerte. Puedes gastar 1 punto para tirar un d20 adicional en tiradas de ataque, "
                f"pruebas o salvaciones y elegir qué dado usar. Recarga con Descanso Largo."
            )

    # 6. Ataque Furtivo (Pícaro)
    if "pícaro" in (char.char_class or "").lower() or "picaro" in (char.char_class or "").lower():
        sneak_dice = f"{(char.level + 1) // 2}d6"
        existing = next((f for f in features if "ataque furtivo" in f.name.lower() or "sneak attack" in f.name.lower()), None)
        desc = f"1 vez por turno, infliges +{sneak_dice} de daño adicional si tienes ventaja o un aliado a 1.5 m del objetivo."
        if existing:
            existing.name = f"Ataque Furtivo ({sneak_dice})"
            existing.description = desc
        else:
            features.append(
                CharacterFeature(
                    id="feat_sneak_attack",
                    name=f"Ataque Furtivo ({sneak_dice})",
                    source="Pícaro",
                    uses_max=0,
                    uses_current=0,
                    recharge="Pasivo",
                    description=desc,
                )
            )

    return features


# Tablas canónicas de Progresión D&D 5.5e (2024) y 5e (2014)
# Mapeo: nivel (1-20) -> (cantrips, prepared_spells, slots_dict, max_spell_level)
PROGRESSION_TABLES_2024: Dict[str, Dict[int, Dict[str, Any]]] = {
    "Bardo": {
        1: {"cantrips": 2, "prepared": 4, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 2, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        3: {"cantrips": 2, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
        4: {"cantrips": 3, "prepared": 7, "slots": {"1": 4, "2": 3}, "max_lvl": 2},
        5: {"cantrips": 3, "prepared": 9, "slots": {"1": 4, "2": 3, "3": 2}, "max_lvl": 3},
        6: {"cantrips": 3, "prepared": 10, "slots": {"1": 4, "2": 3, "3": 3}, "max_lvl": 3},
        7: {"cantrips": 3, "prepared": 11, "slots": {"1": 4, "2": 3, "3": 3, "4": 1}, "max_lvl": 4},
        8: {"cantrips": 3, "prepared": 12, "slots": {"1": 4, "2": 3, "3": 3, "4": 2}, "max_lvl": 4},
        9: {"cantrips": 3, "prepared": 14, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1}, "max_lvl": 5},
        10: {"cantrips": 4, "prepared": 15, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2}, "max_lvl": 5},
        11: {"cantrips": 4, "prepared": 16, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1}, "max_lvl": 6},
        12: {"cantrips": 4, "prepared": 16, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1}, "max_lvl": 6},
        13: {"cantrips": 4, "prepared": 17, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1}, "max_lvl": 7},
        14: {"cantrips": 4, "prepared": 17, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1}, "max_lvl": 7},
        15: {"cantrips": 4, "prepared": 18, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1}, "max_lvl": 8},
        16: {"cantrips": 4, "prepared": 18, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1}, "max_lvl": 8},
        17: {"cantrips": 4, "prepared": 19, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1}, "max_lvl": 9},
        18: {"cantrips": 4, "prepared": 20, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1}, "max_lvl": 9},
        19: {"cantrips": 4, "prepared": 21, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1}, "max_lvl": 9},
        20: {"cantrips": 4, "prepared": 22, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1}, "max_lvl": 9},
    },
    "Clérigo": {
        1: {"cantrips": 3, "prepared": 4, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 3, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        3: {"cantrips": 3, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
        4: {"cantrips": 4, "prepared": 7, "slots": {"1": 4, "2": 3}, "max_lvl": 2},
        5: {"cantrips": 4, "prepared": 9, "slots": {"1": 4, "2": 3, "3": 2}, "max_lvl": 3},
        6: {"cantrips": 4, "prepared": 10, "slots": {"1": 4, "2": 3, "3": 3}, "max_lvl": 3},
        7: {"cantrips": 4, "prepared": 11, "slots": {"1": 4, "2": 3, "3": 3, "4": 1}, "max_lvl": 4},
        8: {"cantrips": 4, "prepared": 12, "slots": {"1": 4, "2": 3, "3": 3, "4": 2}, "max_lvl": 4},
        9: {"cantrips": 4, "prepared": 14, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1}, "max_lvl": 5},
        10: {"cantrips": 5, "prepared": 15, "slots": {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2}, "max_lvl": 5},
    },
    "Druida": {
        1: {"cantrips": 2, "prepared": 4, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 2, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        3: {"cantrips": 2, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
        4: {"cantrips": 3, "prepared": 7, "slots": {"1": 4, "2": 3}, "max_lvl": 2},
        5: {"cantrips": 3, "prepared": 9, "slots": {"1": 4, "2": 3, "3": 2}, "max_lvl": 3},
    },
    "Mago": {
        1: {"cantrips": 3, "prepared": 4, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 3, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        3: {"cantrips": 3, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
        4: {"cantrips": 4, "prepared": 7, "slots": {"1": 4, "2": 3}, "max_lvl": 2},
        5: {"cantrips": 4, "prepared": 9, "slots": {"1": 4, "2": 3, "3": 2}, "max_lvl": 3},
    },
    "Hechicero": {
        1: {"cantrips": 4, "prepared": 2, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 4, "prepared": 4, "slots": {"1": 3}, "max_lvl": 1},
        3: {"cantrips": 4, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
        4: {"cantrips": 5, "prepared": 7, "slots": {"1": 4, "2": 3}, "max_lvl": 2},
        5: {"cantrips": 5, "prepared": 9, "slots": {"1": 4, "2": 3, "3": 2}, "max_lvl": 3},
    },
    "Brujo": {
        1: {"cantrips": 2, "prepared": 2, "slots": {"1": 1}, "max_lvl": 1},
        2: {"cantrips": 2, "prepared": 3, "slots": {"1": 2}, "max_lvl": 1},
        3: {"cantrips": 2, "prepared": 4, "slots": {"2": 2}, "max_lvl": 2},
        4: {"cantrips": 3, "prepared": 5, "slots": {"2": 2}, "max_lvl": 2},
        5: {"cantrips": 3, "prepared": 6, "slots": {"3": 2}, "max_lvl": 3},
    },
    "Paladín": {
        1: {"cantrips": 0, "prepared": 2, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 0, "prepared": 3, "slots": {"1": 2}, "max_lvl": 1},
        3: {"cantrips": 0, "prepared": 4, "slots": {"1": 3}, "max_lvl": 1},
        4: {"cantrips": 0, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        5: {"cantrips": 0, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
    },
    "Explorador": {
        1: {"cantrips": 0, "prepared": 2, "slots": {"1": 2}, "max_lvl": 1},
        2: {"cantrips": 0, "prepared": 3, "slots": {"1": 2}, "max_lvl": 1},
        3: {"cantrips": 0, "prepared": 4, "slots": {"1": 3}, "max_lvl": 1},
        4: {"cantrips": 0, "prepared": 5, "slots": {"1": 3}, "max_lvl": 1},
        5: {"cantrips": 0, "prepared": 6, "slots": {"1": 4, "2": 2}, "max_lvl": 2},
    },
}

# Límites de Dominio de Armas (Weapon Mastery) en 2024
WEAPON_MASTERY_2024 = {
    "Bárbaro": {1: 2, 4: 3, 10: 4},
    "Guerrero": {1: 3, 4: 4, 10: 5, 16: 6},
    "Paladín": {1: 2, 4: 2},
    "Explorador": {1: 2, 4: 2},
    "Pícaro": {1: 2, 4: 2},
}


def get_class_progression_limits(
    class_name: str,
    level: int,
    edition: str = "5.5e",
    ability_mod: int = 0,
    has_magic_initiate: bool = False
) -> Dict[str, Any]:
    """
    Devuelve los límites canónicos exactos de conjuros conocidos/preparados,
    ranuras mágicas, y maestrías de armas para la clase y nivel especificados.
    """
    c_clean = class_name.capitalize().strip()
    lvl = max(1, min(20, level))
    is_2024 = "5.5" in edition or "2024" in edition

    # Fallback canónico estándar si la clase no es lanzadora pura
    default_res = {
        "is_caster": False,
        "edition": "5.5e (2024)" if is_2024 else "5e (2014)",
        "cantrips_limit": 2 if has_magic_initiate else 0,
        "spells_limit": 1 if has_magic_initiate else 0,
        "max_spell_level": 1 if has_magic_initiate else 0,
        "spell_slots": {},
        "weapon_mastery_slots": 0,
        "casting_ability": CLASS_CASTING_ABILITY.get(c_clean, "INT")
    }

    # Asignar dominio de armas si es 2024
    if is_2024 and c_clean in WEAPON_MASTERY_2024:
        table = WEAPON_MASTERY_2024[c_clean]
        mastery_cnt = 2
        for min_lvl, cnt in sorted(table.items()):
            if lvl >= min_lvl:
                mastery_cnt = cnt
        default_res["weapon_mastery_slots"] = mastery_cnt

    # Si es lanzador en 2024
    if is_2024 and c_clean in PROGRESSION_TABLES_2024:
        c_table = PROGRESSION_TABLES_2024[c_clean]
        row = c_table.get(lvl) or c_table.get(max(c_table.keys()))
        cantrips = row["cantrips"] + (2 if has_magic_initiate else 0)
        spells_prep = row["prepared"] + (1 if has_magic_initiate else 0)
        return {
            "is_caster": True,
            "edition": "5.5e (2024)",
            "cantrips_limit": cantrips,
            "spells_limit": spells_prep,
            "max_spell_level": row["max_lvl"],
            "spell_slots": dict(row["slots"]),
            "weapon_mastery_slots": default_res["weapon_mastery_slots"],
            "casting_ability": CLASS_CASTING_ABILITY.get(c_clean, "CAR")
        }

    # Si es 5e (2014 Clásico)
    if not is_2024:
        if c_clean in ("Clérigo", "Druida", "Mago"):
            # Preparados = Nivel + Modificador de Atributo Clave (mín 1)
            prep_cnt = max(1, lvl + ability_mod)
            cantrips = 3 if c_clean in ("Clérigo", "Mago") else 2
            if lvl >= 4:
                cantrips += 1
            if has_magic_initiate:
                cantrips += 2
                prep_cnt += 1
            slots = {"1": 2} if lvl == 1 else ({"1": 3} if lvl == 2 else ({"1": 4, "2": 2} if lvl == 3 else {"1": 4, "2": 3}))
            return {
                "is_caster": True,
                "edition": "5e (2014)",
                "cantrips_limit": cantrips,
                "spells_limit": prep_cnt,
                "max_spell_level": 1 if lvl < 3 else 2,
                "spell_slots": slots,
                "weapon_mastery_slots": 0,
                "casting_ability": CLASS_CASTING_ABILITY.get(c_clean, "INT")
            }
        elif c_clean == "Bardo":
            # 2014: 4 conjuros conocidos a Nvl 1, 5 a Nvl 2, 6 a Nvl 3, 7 a Nvl 4
            known_spells = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}.get(lvl, 4 + lvl)
            cantrips = 2 if lvl < 4 else 3
            if has_magic_initiate:
                cantrips += 2
                known_spells += 1
            slots = {"1": 2} if lvl == 1 else ({"1": 3} if lvl == 2 else ({"1": 4, "2": 2} if lvl == 3 else {"1": 4, "2": 3}))
            return {
                "is_caster": True,
                "edition": "5e (2014)",
                "cantrips_limit": cantrips,
                "spells_limit": known_spells,
                "max_spell_level": 1 if lvl < 3 else 2,
                "spell_slots": slots,
                "weapon_mastery_slots": 0,
                "casting_ability": "CAR"
            }

    return default_res




