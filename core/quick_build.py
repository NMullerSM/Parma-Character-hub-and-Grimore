"""
Motor de Creación Rápida (Quick Build) para D&D 5e (PHB 2024 / 2014).
Permite forjar un héroe completo y legal en 60 segundos seleccionando únicamente:
- Nombre del Personaje
- Especie / Linaje
- Clase Heroica
Asigna el Standard Array [15, 14, 13, 12, 10, 8] según la jerarquía óptima de cada clase,
junto con trasfondos sinérgicos, competencias recomendadas, equipo y conjuros base.
"""
from typing import Dict, List, Tuple, Any

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# Prioridad de asignación de características por clase (de más a menos importante)
CLASS_ABILITY_PRIORITIES: Dict[str, List[str]] = {
    "Bárbaro": ["FUE", "CON", "DES", "SAB", "CAR", "INT"],
    "Bardo": ["CAR", "DES", "CON", "SAB", "INT", "FUE"],
    "Clérigo": ["SAB", "CON", "FUE", "DES", "CAR", "INT"],
    "Druida": ["SAB", "CON", "DES", "INT", "CAR", "FUE"],
    "Guerrero": ["FUE", "CON", "DES", "SAB", "INT", "CAR"],
    "Monje": ["DES", "SAB", "CON", "FUE", "INT", "CAR"],
    "Paladín": ["FUE", "CAR", "CON", "SAB", "INT", "DES"],
    "Explorador": ["DES", "SAB", "CON", "FUE", "INT", "CAR"],
    "Pícaro": ["DES", "CON", "INT", "SAB", "CAR", "FUE"],
    "Hechicero": ["CAR", "CON", "DES", "SAB", "INT", "FUE"],
    "Brujo": ["CAR", "CON", "DES", "SAB", "INT", "FUE"],
    "Mago": ["INT", "CON", "DES", "SAB", "CAR", "FUE"]
}

# Arquetipos recomendados de trasfondo (+2 y +1) para Quick Build
CLASS_QUICK_PRESETS: Dict[str, Dict[str, Any]] = {
    "Bárbaro": {
        "background": "Soldado",
        "bg_plus2": "FUE",
        "bg_plus1": "CON",
        "skills": ["Atletismo", "Supervivencia"],
        "weapons": [("Gran Hacha", "1d12 cortante", "A dos manos, pesada"), ("Jabalina", "1d6 perforante", "Arrojadiza (9/36m)")],
        "spells_known": [],
        "cantrips": []
    },
    "Bardo": {
        "background": "Animador",
        "bg_plus2": "CAR",
        "bg_plus1": "DES",
        "skills": ["Interpretación", "Persuasión", "Engaño"],
        "weapons": [("Estoque", "1d8 perforante", "Sutil"), ("Daga", "1d4 perforante", "Sutil, Ligera")],
        "cantrips": ["Burla Cruel", "Luces Danzantes"],
        "spells_known": ["Palabra de Curación", "Onda Atronadora", "Hechizar Persona", "Detección de Magia"]
    },
    "Clérigo": {
        "background": "Acólito",
        "bg_plus2": "SAB",
        "bg_plus1": "CON",
        "skills": ["Perspicacia", "Religión"],
        "weapons": [("Maza", "1d6 contundente", ""), ("Ballesta Ligera", "1d8 perforante", "Munición (24/96m)")],
        "cantrips": ["Llama Sagrada", "Piedad con los Moribundos", "Guía"],
        "spells_known": ["Curar Heridas", "Bendición", "Escudo de la Fe"]
    },
    "Druida": {
        "background": "Guía",
        "bg_plus2": "SAB",
        "bg_plus1": "CON",
        "skills": ["Naturaleza", "Percepción"],
        "weapons": [("Cimitarra", "1d6 cortante", "Sutil, Ligera"), ("Honda", "1d4 contundente", "Munición (9/36m)")],
        "cantrips": ["Báculo Flotante", "Producir Llama"],
        "spells_known": ["Enredo", "Hablar con Animales", "Curar Heridas"]
    },
    "Guerrero": {
        "background": "Soldado",
        "bg_plus2": "FUE",
        "bg_plus1": "CON",
        "skills": ["Atletismo", "Intimidación"],
        "weapons": [("Espada Larga", "1d8/1d10 cortante", "Versátil"), ("Arco Largo", "1d8 perforante", "Pesada, dos manos (45/180m)")],
        "spells_known": [],
        "cantrips": []
    },
    "Monje": {
        "background": "Sabio",
        "bg_plus2": "DES",
        "bg_plus1": "SAB",
        "skills": ["Acrobacias", "Sigilo"],
        "weapons": [("Espada Corta", "1d6 perforante", "Sutil, Ligera"), ("Dardo", "1d4 perforante", "Sutil (6/18m)")],
        "spells_known": [],
        "cantrips": []
    },
    "Paladín": {
        "background": "Noble",
        "bg_plus2": "FUE",
        "bg_plus1": "CAR",
        "skills": ["Atletismo", "Persuasión"],
        "weapons": [("Espada Larga", "1d8/1d10 cortante", "Versátil"), ("Escudo", "+2 CA", "Protección")],
        "spells_known": ["Castigo Abrasador", "Heroísmo"],
        "cantrips": []
    },
    "Explorador": {
        "background": "Guía",
        "bg_plus2": "DES",
        "bg_plus1": "SAB",
        "skills": ["Supervivencia", "Percepción", "Sigilo"],
        "weapons": [("Arco Largo", "1d8 perforante", "Munición (45/180m)"), ("Dos Espadas Cortas", "1d6 perforante", "Sutil, Ligera")],
        "spells_known": ["Marca del Cazador", "Zancada Prodigiosa"],
        "cantrips": []
    },
    "Pícaro": {
        "background": "Criminal",
        "bg_plus2": "DES",
        "bg_plus1": "CON",
        "skills": ["Sigilo", "Juego de Manos", "Engaño", "Percepción"],
        "weapons": [("Estoque", "1d8 perforante", "Sutil"), ("Ballesta de Mano", "1d6 perforante", "Ligera (9/36m)")],
        "spells_known": [],
        "cantrips": []
    },
    "Hechicero": {
        "background": "Charlatán",
        "bg_plus2": "CAR",
        "bg_plus1": "CON",
        "skills": ["Engaño", "Arcanos"],
        "weapons": [("Daga", "1d4 perforante", "Sutil, Ligera"), ("Ballesta Ligera", "1d8 perforante", "Munición (24/96m)")],
        "cantrips": ["Descarga de Fuego", "Rayo de Escarcha", "Ilusión Menor", "Prestidigitación"],
        "spells_known": ["Manos Ardientes", "Escudo"]
    },
    "Brujo": {
        "background": "Charlatán",
        "bg_plus2": "CAR",
        "bg_plus1": "CON",
        "skills": ["Arcanos", "Investigación"],
        "weapons": [("Daga", "1d4 perforante", "Sutil"), ("Ballesta Ligera", "1d8 perforante", "Munición (24/96m)")],
        "cantrips": ["Descarga Sobrenatural", "Toque Helado"],
        "spells_known": ["Armadura de Agathys", "Reprensión Infernal"]
    },
    "Mago": {
        "background": "Sabio",
        "bg_plus2": "INT",
        "bg_plus1": "CON",
        "skills": ["Arcanos", "Historia"],
        "weapons": [("Bastón", "1d6/1d8 contundente", "Versátil, foco arcano"), ("Daga", "1d4 perforante", "Sutil, Ligera")],
        "cantrips": ["Rayo de Fuego", "Mano de Mago", "Luces Danzantes"],
        "spells_known": ["Armadura de Mago", "Proyectil Mágico", "Manos Ardientes", "Dormir", "Escudo", "Detectar Magia"]
    }
}


class QuickBuildEngine:
    """Generador de asignación rápida para héroes de 60 segundos."""

    @classmethod
    def get_assigned_standard_array(cls, char_class: str) -> Dict[str, int]:
        """Asigna los 6 números del Standard Array [15, 14, 13, 12, 10, 8] en orden óptimo."""
        priorities = CLASS_ABILITY_PRIORITIES.get(char_class, CLASS_ABILITY_PRIORITIES["Guerrero"])
        scores: Dict[str, int] = {}
        for i, stat in enumerate(priorities):
            scores[stat] = STANDARD_ARRAY[i]
        return scores

    @classmethod
    def get_preset_for_class(cls, char_class: str) -> Dict[str, Any]:
        """Retorna el paquete preconfigurado de trasfondo, bonos y equipo sugerido."""
        return CLASS_QUICK_PRESETS.get(char_class, CLASS_QUICK_PRESETS["Guerrero"])

    @classmethod
    def generate_quick_stats(
        cls,
        char_class: str,
        species: str,
        custom_bg_plus2: str = "",
        custom_bg_plus1: str = ""
    ) -> Tuple[Dict[str, int], Dict[str, int], str, str, str]:
        """
        Retorna:
        - raw_scores: Dict con los 6 valores base [15, 14, 13, 12, 10, 8]
        - final_scores: Dict con los valores tras sumar el trasfondo (+2 y +1)
        - background: Nombre del trasfondo sugerido
        - plus2_stat: Característica que recibe el +2
        - plus1_stat: Característica que recibe el +1
        """
        preset = cls.get_preset_for_class(char_class)
        raw_scores = cls.get_assigned_standard_array(char_class)

        plus2 = custom_bg_plus2 or preset["bg_plus2"]
        plus1 = custom_bg_plus1 or preset["bg_plus1"]
        bg = preset["background"]

        final_scores = dict(raw_scores)
        final_scores[plus2] = final_scores.get(plus2, 10) + 2
        final_scores[plus1] = final_scores.get(plus1, 10) + 1

        return raw_scores, final_scores, bg, plus2, plus1
