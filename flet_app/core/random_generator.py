"""
Motor de Generación Procedural y Aleatoria (Randomize) para D&D 5e (PHB 2024).
Genera personajes coherentes y jugables en cualquier nivel (1-20):
- Tirada 4d6 descartando el menor para cada característica.
- Asignación inteligente por jerarquía de clase para evitar combinaciones inviables.
- Cálculo de Puntos de Golpe escalados por nivel y modificador de Constitución.
- Selección aleatoria de Nombres por especie, Trasfondo, Alineamiento y Dotes.
- Soporte para filtros configurables (fijar clase, especie o nivel) y botón re-roll.
"""
import random
from typing import Dict, List, Tuple, Optional, Any
from .quick_build import CLASS_ABILITY_PRIORITIES, CLASS_QUICK_PRESETS
from .rules import calc_modifier

CLASSES_LIST = [
    "Bárbaro", "Bardo", "Clérigo", "Druida", "Guerrero",
    "Monje", "Paladín", "Explorador", "Pícaro", "Hechicero", "Brujo", "Mago"
]

SPECIES_LIST = [
    "Humano", "Elfo", "Enano", "Mediano", "Dracónido",
    "Gnomo", "Tiefling", "Goliat", "Orco", "Aasimar"
]

ALIGNMENTS_LIST = [
    "Legal Bueno", "Neutral Bueno", "Caótico Bueno",
    "Legal Neutral", "Neutral Auténtico", "Caótico Neutral",
    "Legal Maligno", "Neutral Maligno", "Caótico Maligno"
]

NAMES_BY_SPECIES: Dict[str, List[str]] = {
    "Humano": ["Alden", "Baelen", "Cedric", "Doran", "Elena", "Fiona", "Gareth", "Isolda", "Kael", "Lyra", "Rowan", "Theron"],
    "Elfo": ["Aelion", "Caelynn", "Faelar", "Ilphukiir", "Lia", "Mirieth", "Naeris", "Sariel", "Thalion", "Valanthe", "Xanaphia"],
    "Enano": ["Balin", "Dain", "Durin", "Eldeth", "Gimli", "Helga", "Kragthor", "Morgran", "Rorik", "Thorgar", "Vondal"],
    "Mediano": ["Alton", "Bree", "Cade", "Corrin", "Eldon", "Finnan", "Jilly", "Merric", "Osborn", "Perrin", "Rosie", "Wellby"],
    "Dracónido": ["Arjhan", "Balasar", "Donaar", "Ghesh", "Heskan", "Kriv", "Medrash", "Nadarr", "Patrin", "Rhogar", "Torinn"],
    "Gnomo": ["Boddynock", "Dimble", "Fonkin", "Gimble", "Glin", "Kellen", "Namfoodle", "Orryn", "Roondar", "Seebo", "Zook"],
    "Tiefling": ["Akmenos", "Ammon", "Barakas", "Damakos", "Ekemon", "Iados", "Kairon", "Leucis", "Mephistopheles", "Mordai", "Pelaios"],
    "Goliat": ["Aukan", "Egil", "Gauthak", "Ilik", "Keothi", "Kuori", "Lo-Kag", "Manneo", "Thotham", "Vaunea", "Vimak"],
    "Orco": ["Dench", "Feng", "Gell", "Henk", "Holg", "Imsh", "Keth", "Krag", "Mhurren", "Ront", "Shump", "Thokk"],
    "Aasimar": ["Ariel", "Celestia", "Gabriel", "Harriel", "Ithuriel", "Mikael", "Raphael", "Seraphina", "Uriel", "Zariel"]
}

BACKGROUNDS_LIST = [
    "Acólito", "Animador", "Artesano", "Charlatán", "Criminal",
    "Soldado", "Vagabundo", "Sabio", "Noble", "Guardia", "Guía"
]

PERSONALITY_TRAITS = [
    "Siempre tengo un plan para cuando las cosas salen mal.",
    "Nunca rechazo una apuesta o un desafío amistoso.",
    "Hablo con una calma imperturbable incluso en medio del combate.",
    "Colecciono baratijas extrañas de cada lugar que visito.",
    "Prefiero escuchar y observar antes de desenfundar mi arma.",
    "Tengo un sentido del humor mordaz en los momentos más inoportunos."
]

IDEALS_LIST = [
    "Libertad: Nadie debería vivir bajo las cadenas de la tiranía.",
    "Honor: Mi palabra es tan firme como el acero de mi espada.",
    "Conocimiento: El secreto de la victoria reside en comprender lo desconocido.",
    "Lealtad: Protegeré a mis compañeros de armas sin importar el coste.",
    "Gloria: Forjaré un nombre que perdurará en las canciones durante eras."
]

BONDS_LIST = [
    "Porto una reliquia familiar que debo devolver a mi hogar ancestral.",
    "Busco a un mentor desaparecido que me enseñó todo lo que sé.",
    "Una deuda de honor me une a la causa de mis aliados.",
    "Un misterioso adversario juró destruir a todos los que amo."
]

FLAWS_LIST = [
    "Me cuesta confiar plenamente en quienes no han probado su valía en batalla.",
    "A veces mi orgullo me impide pedir ayuda cuando la necesito desesperadamente.",
    "No puedo resistir investigar una pista misteriosa aunque sea una trampa.",
    "Tiendo a subestimar el poder del enemigo por exceso de confianza."
]


class RandomCharacterGenerator:
    """Generador procedural de aventureros para D&D 5e."""

    @staticmethod
    def roll_4d6_drop_lowest() -> int:
        """Tira 4d6, descarta el dado más bajo y suma los 3 mayores."""
        dice = [random.randint(1, 6) for _ in range(4)]
        dice.sort()
        return sum(dice[1:])

    @classmethod
    def roll_ability_pool(cls) -> List[int]:
        """Genera 6 puntuaciones usando 4d6 drop lowest ordenadas de mayor a menor."""
        pool = [cls.roll_4d6_drop_lowest() for _ in range(6)]
        pool.sort(reverse=True)
        return pool

    @classmethod
    def assign_to_class_priorities(cls, char_class: str, rolled_scores: List[int]) -> Dict[str, int]:
        """Asigna las puntuaciones tiradas a las características en el orden óptimo de la clase."""
        priorities = CLASS_ABILITY_PRIORITIES.get(char_class, CLASS_ABILITY_PRIORITIES["Guerrero"])
        sorted_scores = sorted(rolled_scores, reverse=True)
        assigned: Dict[str, int] = {}
        for i, stat in enumerate(priorities):
            assigned[stat] = sorted_scores[i]
        return assigned

    @classmethod
    def generate_random_character(
        cls,
        forced_class: Optional[str] = None,
        forced_species: Optional[str] = None,
        forced_level: int = 1,
        forced_alignment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un personaje completo con todos sus datos mecánicos y narrativos.
        Permite parametrizar filtros o dejarlo 100% aleatorio.
        """
        char_class = forced_class if forced_class in CLASSES_LIST else random.choice(CLASSES_LIST)
        species = forced_species if forced_species in SPECIES_LIST else random.choice(SPECIES_LIST)
        level = max(1, min(20, forced_level))
        alignment = forced_alignment if forced_alignment in ALIGNMENTS_LIST else random.choice(ALIGNMENTS_LIST)

        # Nombre temático por especie
        name_pool = NAMES_BY_SPECIES.get(species, NAMES_BY_SPECIES["Humano"])
        name = f"{random.choice(name_pool)} de las Tierras Sombrías"

        # Tirada de características y asignación por clase
        pool = cls.roll_ability_pool()
        raw_scores = cls.assign_to_class_priorities(char_class, pool)

        # Trasfondo y asignación de bonos +2/+1
        preset = CLASS_QUICK_PRESETS.get(char_class, CLASS_QUICK_PRESETS["Guerrero"])
        background = random.choice(BACKGROUNDS_LIST)
        plus2_stat = preset["bg_plus2"]
        plus1_stat = preset["bg_plus1"]

        final_abilities = dict(raw_scores)
        final_abilities[plus2_stat] = final_abilities.get(plus2_stat, 10) + 2
        final_abilities[plus1_stat] = final_abilities.get(plus1_stat, 10) + 1

        # Dados de golpe y PG por nivel
        hd_faces_map = {
            "Bárbaro": 12, "Guerrero": 10, "Paladín": 10, "Explorador": 10,
            "Bardo": 8, "Clérigo": 8, "Druida": 8, "Monje": 8, "Pícaro": 8, "Brujo": 8,
            "Hechicero": 6, "Mago": 6
        }
        hd_faces = hd_faces_map.get(char_class, 8)
        con_mod = calc_modifier(final_abilities["CON"])

        # Nivel 1 = dado max + CON; niveles posteriores = promedio redondeado hacia arriba
        avg_gain = (hd_faces // 2) + 1 + con_mod
        max_hp = max(1, hd_faces + con_mod) + (max(0, level - 1) * max(1, avg_gain))

        # Bono de competencia por nivel
        prof_bonus = ((level - 1) // 4) + 2

        # Clase de armadura básica
        des_mod = calc_modifier(final_abilities["DES"])
        if char_class == "Bárbaro":
            ca = 10 + des_mod + con_mod  # Defensa sin armadura bárbaro
        elif char_class == "Monje":
            wis_mod = calc_modifier(final_abilities["SAB"])
            ca = 10 + des_mod + wis_mod  # Defensa sin armadura monje
        else:
            ca = 10 + des_mod

        return {
            "name": name,
            "char_class": char_class,
            "species": species,
            "level": level,
            "alignment": alignment,
            "background": background,
            "raw_scores": raw_scores,
            "final_abilities": final_abilities,
            "bg_plus2": plus2_stat,
            "bg_plus1": plus1_stat,
            "hp_max": max_hp,
            "hp_current": max_hp,
            "hit_dice_max": level,
            "hit_dice_current": level,
            "hit_dice_faces": hd_faces,
            "armor_class": ca,
            "initiative_bonus": des_mod,
            "proficiency_bonus": prof_bonus,
            "personality_trait": random.choice(PERSONALITY_TRAITS),
            "ideal": random.choice(IDEALS_LIST),
            "bond": random.choice(BONDS_LIST),
            "flaw": random.choice(FLAWS_LIST),
            "preset": preset
        }
