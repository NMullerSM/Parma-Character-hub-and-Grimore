"""
Suite de Pruebas Unitarias para los Motores de Negocio del Creador de Personajes.
Valida:
1. PointBuyCalculator (Presupuesto 27, costes no lineales, incrementos y decrementos válidos).
2. QuickBuildEngine (Priority Arrays de las 12 clases y presets de inicio).
3. RandomCharacterGenerator (Tiradas 4d6, coherencia procedural y escalado de niveles 1 a 20).
4. ModifierPipeline (Base -> Set -> Bonus, habilidades con competencia/pericia, CD mágica).
"""
import sys
import os

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flet_app.core.point_buy import PointBuyCalculator
from flet_app.core.quick_build import QuickBuildEngine, CLASS_ABILITY_PRIORITIES
from flet_app.core.random_generator import RandomCharacterGenerator
from flet_app.core.modifier_pipeline import ModifierPipeline, CharacterModifier, ModifierType

def test_point_buy():
    print("Testing PointBuyCalculator...")
    scores = PointBuyCalculator.get_initial_scores()
    assert PointBuyCalculator.get_remaining_points(scores) == 27, "El presupuesto inicial debe ser 27"
    assert PointBuyCalculator.can_decrement(scores, "FUE") is False, "No se puede decrementar por debajo de 8"
    assert PointBuyCalculator.can_increment(scores, "FUE") is True, "Se debe poder subir de 8 a 9"

    # Subir FUE a 15 (cuesta 9 pts)
    for _ in range(7):
        assert PointBuyCalculator.increment(scores, "FUE") is True
    assert scores["FUE"] == 15
    assert PointBuyCalculator.can_increment(scores, "FUE") is False, "No se puede superar 15 en Point Buy"
    assert PointBuyCalculator.get_remaining_points(scores) == 18

    # Probar compra estándar balanceada: 15, 14, 13, 12, 10, 8 (total = 9 + 7 + 5 + 4 + 2 + 0 = 27)
    std_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}
    assert PointBuyCalculator.calculate_used_points(std_scores) == 27
    assert PointBuyCalculator.get_remaining_points(std_scores) == 0
    assert PointBuyCalculator.can_increment(std_scores, "CAR") is False
    print("✅ PointBuyCalculator passed!")

def test_quick_build():
    print("Testing QuickBuildEngine...")
    for cls_name in CLASS_ABILITY_PRIORITIES:
        assigned = QuickBuildEngine.get_assigned_standard_array(cls_name)
        assert len(assigned) == 6
        assert sorted(list(assigned.values())) == [8, 10, 12, 13, 14, 15]

    # Validar Mago (INT debe ser 15)
    wizard_scores = QuickBuildEngine.get_assigned_standard_array("Mago")
    assert wizard_scores["INT"] == 15
    assert wizard_scores["CON"] == 14

    # Validar Bárbaro (FUE debe ser 15)
    barb_scores = QuickBuildEngine.get_assigned_standard_array("Bárbaro")
    assert barb_scores["FUE"] == 15
    assert barb_scores["CON"] == 14

    raw, final, bg, p2, p1 = QuickBuildEngine.generate_quick_stats("Pícaro", "Mediano")
    assert raw["DES"] == 15
    assert final["DES"] == 17  # 15 + 2 del trasfondo
    print("✅ QuickBuildEngine passed!")

def test_random_generator():
    print("Testing RandomCharacterGenerator...")
    for _ in range(50):
        val = RandomCharacterGenerator.roll_4d6_drop_lowest()
        assert 3 <= val <= 18

    char_lvl1 = RandomCharacterGenerator.generate_random_character(forced_class="Paladín", forced_level=1)
    assert char_lvl1["char_class"] == "Paladín"
    assert char_lvl1["level"] == 1
    assert char_lvl1["hit_dice_faces"] == 10
    assert char_lvl1["hp_max"] > 0

    char_lvl5 = RandomCharacterGenerator.generate_random_character(forced_class="Mago", forced_level=5)
    assert char_lvl5["level"] == 5
    assert char_lvl5["proficiency_bonus"] == 3
    assert char_lvl5["hp_max"] > char_lvl1["hp_max"]
    print("✅ RandomCharacterGenerator passed!")

def test_modifier_pipeline():
    print("Testing ModifierPipeline...")
    mods = [
        CharacterModifier("m1", ModifierType.BONUS, "FUE-score", value=2, source="especie"),
        CharacterModifier("m2", ModifierType.BONUS, "FUE-score", value=1, source="dote"),
        CharacterModifier("m3", ModifierType.SET, "INT-score", value=19, source="objeto"),
        CharacterModifier("m4", ModifierType.PROFICIENCY, "Sigilo", source="clase"),
        CharacterModifier("m5", ModifierType.EXPERTISE, "Percepción", source="pícaro"),
    ]

    total_str = ModifierPipeline.evaluate_ability_score("FUE", 14, mods)
    assert total_str == 17  # 14 + 2 + 1

    total_int = ModifierPipeline.evaluate_ability_score("INT", 10, mods)
    assert total_int == 19  # Set en 19

    # Nivel 1 (PB = 2)
    # Sigilo con DES 14 (mod +2) + PB 2 = +4
    stealth_mod = ModifierPipeline.evaluate_skill_modifier("Sigilo", 14, 1, mods)
    assert stealth_mod == 4

    # Percepción con SAB 12 (mod +1) + 2*PB (4) = +5
    perc_mod = ModifierPipeline.evaluate_skill_modifier("Percepción", 12, 1, mods)
    assert perc_mod == 5

    # CD mágica para Nivel 5 (PB = 3) con INT 19 (mod +4) = 8 + 3 + 4 = 15
    dc = ModifierPipeline.evaluate_spell_dc(19, 5, mods)
    assert dc == 15
    print("✅ ModifierPipeline passed!")

def test_ai_optimizer():
    print("Testing AiBuildOptimizerEngine...")
    from flet_app.core.ai_optimizer_interface import AiBuildOptimizerEngine, BuildOptimizationRequest
    engine = AiBuildOptimizerEngine()

    req = BuildOptimizationRequest(
        target_class="Mago",
        target_role="Controlador",
        target_level=3,
        allowed_sources=["PHB 2024", "TCE", "XGE"]
    )

    # 1. Empaquetador de contexto OKF
    payload = engine.build_okf_context_payload(req)
    assert "legal_rules_corpus" in payload
    assert len(payload["legal_rules_corpus"]["available_subclasses"]) >= 4

    # 2. Recomendación heurística sinérgica
    rec = engine.generate_optimized_build_rulebased(req)
    assert rec.recommended_species != ""
    assert rec.recommended_background != ""
    assert rec.legal_validation is True
    assert rec.recommended_subclass is not None

    # 3. Validación de legalidad
    val = engine.validate_build_legality({
        "ability_scores": rec.recommended_ability_scores,
        "background_bonuses": rec.background_bonuses
    })
    assert val["is_legal"] is True
    assert val["cost_used"] == 27
    print("✅ AiBuildOptimizerEngine passed!")

if __name__ == "__main__":
    test_point_buy()
    test_quick_build()
    test_random_generator()
    test_modifier_pipeline()
    test_ai_optimizer()
    print("\n🎉 TODOS LOS TESTS DE MOTORES DE NEGOCIO PASARON EXITOSAMENTE.")
