"""
Interfaz y Empaquetador de Contexto para Optimización de Builds mediante IA / API.
Proporciona contratos fuertemente tipados, serialización de conocimiento atómico OKF
y un motor de validación de legalidad para recomendar progresiones de personajes D&D 5e.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json

from .okf_engine import OkfEngine
from .point_buy import PointBuyCalculator
from .quick_build import QuickBuildEngine


@dataclass
class BuildOptimizationRequest:
    target_class: str
    target_role: str = "Equilibrado"  # "Tanque", "Daño (DPS)", "Soporte/Curación", "Controlador", "Infiltrador"
    target_level: int = 1
    preferred_species: Optional[str] = None
    allowed_sources: List[str] = field(default_factory=lambda: ["PHB 2024", "TCE", "XGE"])
    stat_generation_method: str = "point_buy"  # "point_buy" o "standard_array"
    concept_theme: Optional[str] = None


@dataclass
class BuildRecommendation:
    character_name_suggestion: str
    recommended_species: str
    recommended_lineage: Optional[str]
    recommended_background: str
    recommended_origin_feat: str
    recommended_ability_scores: Dict[str, int]
    background_bonuses: Dict[str, int]  # ej: {"FUE": 2, "CON": 1}
    recommended_subclass: Optional[str]
    recommended_spells: List[str]
    progression_advice: str
    legal_validation: bool
    sourcebooks_used: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AiBuildOptimizerEngine:
    def __init__(self, okf_engine: Optional[OkfEngine] = None):
        self.okf = okf_engine or OkfEngine()

    def build_okf_context_payload(self, request: BuildOptimizationRequest) -> Dict[str, Any]:
        """
        Empaqueta un payload estructurado y compacto con todas las opciones legales de OKF
        para que un modelo de IA (ej. Gemini) pueda evaluar y recomendar la build óptima.
        """
        # 1. Clases y subclases legales
        subclasses = self.okf.get_subclasses(
            class_name=request.target_class,
            allowed_sources=request.allowed_sources,
            max_level=request.target_level
        )
        subclass_summaries = [
            {"id": s["id"], "nombre": s["nombre"], "fuente": s["fuente"]}
            for s in subclasses
        ]

        # 2. Especies y linajes
        species = self.okf.get_species(allowed_sources=request.allowed_sources)
        species_summaries = [
            {"nombre": sp["nombre"], "velocidad": sp["velocidad"], "rasgos": sp.get("rasgos_principales", "")[:120]}
            for sp in species
        ]

        # 3. Trasfondos oficiales
        backgrounds = self.okf.get_backgrounds(allowed_sources=request.allowed_sources)
        bg_summaries = [
            {
                "nombre": bg["nombre"],
                "dote": bg["dote_concedida"],
                "atributos": bg["caracteristicas_clave"]
            }
            for bg in backgrounds
        ]

        # 4. Conjuros disponibles si es lanzador
        spells_okf = self.okf.get_spells_for_class(
            class_name=request.target_class,
            max_spell_level=min(9, max(1, (request.target_level + 1) // 2)),
            min_spell_level=0,
            allowed_sources=request.allowed_sources
        )
        spell_names = [s.get("nombre") for s in spells_okf[:30]]

        return {
            "system_instruction": (
                "Eres un optimizador de personajes de D&D 5e (Reglas 2024 y suplementos oficiales). "
                "Genera una recomendación de build legal que maximice la efectividad del personaje "
                "según la clase, rol y fuentes especificadas."
            ),
            "request": {
                "target_class": request.target_class,
                "target_role": request.target_role,
                "target_level": request.target_level,
                "preferred_species": request.preferred_species,
                "concept_theme": request.concept_theme,
                "allowed_sources": request.allowed_sources
            },
            "legal_rules_corpus": {
                "available_subclasses": subclass_summaries,
                "available_species": species_summaries,
                "available_backgrounds": bg_summaries,
                "available_spells_sample": spell_names,
                "point_buy_budget": 27,
                "min_stat": 8,
                "max_base_stat": 15
            }
        }

    def generate_optimized_build_rulebased(self, request: BuildOptimizationRequest) -> BuildRecommendation:
        """
        Generador heurístico de optimización basado en las matrices de prioridad de D&D 5e.
        Funciona como motor nativo de alta velocidad cuando no se invoca una API externa.
        """
        # 1. Obtener matriz de atributos optimizada para la clase
        ability_scores = QuickBuildEngine.get_assigned_standard_array(request.target_class)
        preset = QuickBuildEngine.get_preset_for_class(request.target_class)
        primary_stat = preset.get("bg_plus2", "FUE")
        secondary_stat = preset.get("bg_plus1", "CON")

        # 2. Seleccionar trasfondo sinérgico
        target_stat = primary_stat
        backgrounds = self.okf.get_backgrounds(allowed_sources=request.allowed_sources)

        best_bg = None
        for bg in backgrounds:
            attrs = bg.get("caracteristicas_clave", "").lower()
            if target_stat.lower() in attrs:
                best_bg = bg
                break
        if not best_bg and backgrounds:
            best_bg = backgrounds[0]

        bg_name = best_bg["nombre"] if best_bg else preset.get("background", "Soldado")
        bg_feat = best_bg.get("dote_concedida", "Dote de Origen") if best_bg else "Dote de Origen"

        # 3. Asignar bonos de trasfondo (+2 a primaria, +1 a secundaria)
        bg_bonuses = {
            primary_stat: 2,
            secondary_stat: 1
        }

        # 4. Especie recomendada
        species_name = request.preferred_species or "Humano"
        lineages = self.okf.get_lineages(species_name, allowed_sources=request.allowed_sources)
        lineage_name = lineages[0]["nombre"] if lineages else None

        # 5. Subclase óptima
        subclasses = self.okf.get_subclasses(
            class_name=request.target_class,
            allowed_sources=request.allowed_sources,
            max_level=request.target_level
        )
        chosen_subclass = subclasses[0]["nombre"] if subclasses and request.target_level >= 3 else None

        # 6. Conjuros recomendados
        spells_okf = self.okf.get_spells_for_class(
            class_name=request.target_class,
            max_spell_level=1,
            min_spell_level=0,
            allowed_sources=request.allowed_sources
        )
        recommended_spells = [s.get("nombre") for s in spells_okf[:4]]

        advice = (
            f"Build optimizada para {request.target_role}. "
            f"Prioriza {primary_stat} para CD y efectividad ofensiva, "
            f"seguido de {secondary_stat} para supervivencia en combate."
        )

        return BuildRecommendation(
            character_name_suggestion=f"{request.target_class} {request.target_role}",
            recommended_species=species_name,
            recommended_lineage=lineage_name,
            recommended_background=bg_name,
            recommended_origin_feat=bg_feat,
            recommended_ability_scores=ability_scores,
            background_bonuses=bg_bonuses,
            recommended_subclass=chosen_subclass,
            recommended_spells=recommended_spells,
            progression_advice=advice,
            legal_validation=True,
            sourcebooks_used=list(request.allowed_sources)
        )

    def validate_build_legality(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que una build propuesta cumpla con las reglas oficiales:
        - Presupuesto de Point Buy (máximo 27 puntos)
        - Valores entre 8 y 15 antes de bonos
        - Bonos de trasfondo válidos (+2 y +1 a atributos distintos)
        """
        scores = build_data.get("ability_scores", {})
        errors = []

        # Validar rango
        for stat, val in scores.items():
            if val < 8 or val > 15:
                errors.append(f"Atributo {stat} ({val}) fuera del rango legal de Point Buy [8-15].")

        # Validar presupuesto de 27 pts
        cost = PointBuyCalculator.calculate_used_points(scores)
        if cost > 27:
            errors.append(f"Costo de compra por puntos ({cost} pts) excede el presupuesto de 27 pts.")

        # Validar bonos de trasfondo
        bonuses = build_data.get("background_bonuses", {})
        if len(bonuses) == 2:
            vals = list(bonuses.values())
            if sorted(vals) != [1, 2]:
                errors.append(f"Los bonos de trasfondo deben ser exactamente +2 y +1. Recibido: {bonuses}")
        elif len(bonuses) == 3:
            vals = list(bonuses.values())
            if vals != [1, 1, 1]:
                errors.append(f"Los bonos alternativos de trasfondo deben ser +1, +1, +1. Recibido: {bonuses}")

        return {
            "is_legal": len(errors) == 0,
            "cost_used": cost,
            "budget": 27,
            "errors": errors
        }
