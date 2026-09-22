import os
import sys
import json

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flet_app.core.models import CharacterSheet, WeaponAction, SpellSlotTier, CharacterFeature
from flet_app.core.okf_engine import OkfEngine
from flet_app.core.rules import (
    get_character_spell_stats,
    CLASS_CASTING_ABILITY,
    calc_modifier
)
from flet_app.ui.components.character_wizard import (
    STANDARD_ARRAY,
    CLASS_DEFAULTS,
    SPECIES_DEFAULTS,
    BACKGROUND_FEATS
)

def run_tests():
    print("=== TEST 1: OKF Engine Category Retrieval ===")
    okf_path = os.path.join(base_dir, "okf_dnd5e")
    okf = OkfEngine(okf_path)
    
    categories = {
        "conjuro": "conjuro",
        "dote": "dote",
        "especies": ["especie", "linaje"],
        "clases": ["clase", "subclase"],
        "trasfondo": "trasfondo",
        "reglas": "regla"
    }
    
    for cat_name, cat_type in categories.items():
        results = okf.search_entities(tipo=cat_type, limit=500)
        print(f"  Category '{cat_name}' (type={cat_type}): {len(results)} items found.")
        assert len(results) > 0, f"Error: Category {cat_name} returned 0 items!"

    print("\n=== TEST 2: PHB 2024 Wizard Data Integrity ===")
    assert len(STANDARD_ARRAY) == 6
    assert sum(STANDARD_ARRAY) == 72
    assert "Guerrero" in CLASS_DEFAULTS
    assert "Elfo" in SPECIES_DEFAULTS
    assert "Acólito" in BACKGROUND_FEATS
    print(f"  Standard Array verified: {STANDARD_ARRAY}")
    print(f"  Classes covered in Wizard: {len(CLASS_DEFAULTS)}")
    print(f"  Species covered in Wizard: {len(SPECIES_DEFAULTS)}")
    print(f"  Backgrounds covered in Wizard: {len(BACKGROUND_FEATS)}")

    print("\n=== TEST 3: Character Generation & Stat Derivations ===")
    # Simulate wizard character generation
    char = CharacterSheet(
        name="Theron",
        char_class="Mago",
        subclass="Evocación",
        level=1,
        race="Elfo",
        background="Sabio",
        alignment="Neutral Bueno",
        xp=0,
        armor_class=12, # 10 + DEX mod (+2)
        initiative_bonus=2,
        speed="9 m",
        hp_max=8, # 6 (Mago d6) + CON mod (+2)
        hp_current=8,
        hp_temp=0,
        proficiency_bonus=2,
        death_saves_success=0,
        death_saves_failure=0,
        abilities={
            "FUE": 8,
            "DES": 14,
            "CON": 14,
            "INT": 17, # 15 base + 2 background sabio
            "SAB": 13, # 12 base + 1 background sabio
            "CAR": 10
        },
        saving_throw_profs=CLASS_DEFAULTS["Mago"]["saves"],
        features=[
            CharacterFeature(name="Iniciado en la Magia", source="Trasfondo", description="Dote de origen"),
            CharacterFeature(name="Linaje Élfico", source="Especie", description="Visión en la oscuridad")
        ]
    )

    spell_stats = get_character_spell_stats(char)
    print(f"  Mago Level 1 Spell Stats:")
    print(f"    Ability: {spell_stats['ability']}")
    print(f"    Modifier: +{spell_stats['modifier']}")
    print(f"    Spell Save DC: {spell_stats['save_dc']}")
    print(f"    Spell Attack Bonus: {spell_stats['attack_bonus']}")
    
    # INT 17 has mod +3. DC = 8 + 2 (prof) + 3 (INT) = 13. Attack = 2 + 3 = +5.
    assert spell_stats['ability'] == "INT"
    assert spell_stats['modifier'] == 3
    assert spell_stats['save_dc'] == 13
    assert spell_stats['attack_bonus'] == "+5"
    print("  Spell DC and Attack formulas verified!")

    print("\n=== TEST 4: Autosave Serialization ===")
    char_dict = char.to_dict()
    char_json = json.dumps(char_dict)
    char_restored = CharacterSheet.from_dict(json.loads(char_json))
    assert char_restored.name == "Theron"
    assert char_restored.char_class == "Mago"
    assert char_restored.abilities["INT"] == 17
    assert char_restored.hp_max == 8
    print("  CharacterSheet serialization / deserialization roundtrip verified!")

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
