import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flet_app.core.models import CharacterSheet
from flet_app.core.rules import perform_short_rest, perform_long_rest, DND_CONDITIONS
from flet_app.ui.views.combat_view import CombatView

def test_phase2_mechanics():
    print("=== TEST PHASE 2: Hit Dice, Rests & Conditions ===")

    # 1. Test Barbarian (d12 hit dice)
    barb = CharacterSheet(
        name="Conan",
        char_class="Bárbaro",
        level=4,
        hp_current=15,
        hp_max=45,
        hit_dice_max=4,
        hit_dice_current=4,
        hit_dice_faces=12,
        abilities={"CON": 16}  # mod +3
    )

    # Perform short rest spending 2 dice
    barb, msg = perform_short_rest(barb, hit_dice_spent=2)
    assert barb.hit_dice_current == 2, f"Expected 2 hit dice left, got {barb.hit_dice_current}"
    assert barb.hp_current > 15, "Expected HP to increase after spending hit dice"
    assert "2d12" in msg, "Expected d12 in message"
    print("  [Pass] Barbarian short rest with 2d12 verified:", msg)

    # Spend remaining 2 dice
    barb, msg = perform_short_rest(barb, hit_dice_spent=2)
    assert barb.hit_dice_current == 0
    print("  [Pass] Expended all hit dice successfully.")

    # Try spending when 0 dice remaining
    barb, msg = perform_short_rest(barb, hit_dice_spent=1)
    assert barb.hit_dice_current == 0
    assert "sin gastar dados" in msg
    print("  [Pass] Handled 0 dice remaining gracefully.")

    # Perform long rest
    barb.hp_current = 20
    barb, msg = perform_long_rest(barb)
    assert barb.hp_current == barb.hp_max, "Expected full HP on long rest"
    # Long rest should restore at least half max dice (4 // 2 = 2)
    assert barb.hit_dice_current == 2, f"Expected 2 restored hit dice, got {barb.hit_dice_current}"
    assert "+2 Dados de Golpe" in msg
    print("  [Pass] Long rest restored 100% HP and half max hit dice:", msg)

    # 2. Test Wizard (d6 hit dice) serialization
    char_dict = barb.to_dict()
    restored = CharacterSheet.from_dict(char_dict)
    assert restored.hit_dice_faces == 12
    assert restored.hit_dice_max == 4
    assert restored.hit_dice_current == 2
    print("  [Pass] Serialization roundtrip for hit dice verified.")

    # 3. Test Conditions in CombatView
    cv = CombatView(char=barb)
    assert len(barb.conditions) == 0
    cv._toggle_condition("Envenenado")
    assert "Envenenado" in barb.conditions
    cv._toggle_condition("Concentración")
    assert "Concentración" in barb.conditions
    cv._toggle_condition("Envenenado")
    assert "Envenenado" not in barb.conditions
    assert "Concentración" in barb.conditions
    print("  [Pass] Combat conditions toggle verified.")

    print("\nALL PHASE 2 TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_phase2_mechanics()
