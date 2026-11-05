import pytest
from core.db import DatabaseManager
from core.models import CharacterSheet, WeaponAction, EquipmentItem
from core.rules import get_class_progression_limits, PROGRESSION_TABLES_2024
from desktop_api.bridge import DesktopBridge


@pytest.fixture
def test_bridge(tmp_path):
    db_file = str(tmp_path / "test_char.db")
    db = DatabaseManager(db_file)
    bridge = DesktopBridge()
    bridge._db = db
    return bridge


def test_card_parma_19_progression_tables_and_limits():
    """Verifica que las tablas de progresión 2024 cubren niveles 1-20 y alias en inglés."""
    for c in ["Bardo", "Clérigo", "Druida", "Mago", "Hechicero", "Brujo", "Paladín", "Explorador"]:
        assert c in PROGRESSION_TABLES_2024
        assert len(PROGRESSION_TABLES_2024[c]) == 20

    # Test alias en inglés
    wizard_limits = get_class_progression_limits("wizard", 5, edition="5.5e")
    assert wizard_limits["cantrips_limit"] == 4
    assert wizard_limits["spells_limit"] == 9
    assert wizard_limits["max_spell_level"] == 3

    paladin_limits = get_class_progression_limits("paladin", 1, edition="5.5e")
    assert paladin_limits["cantrips_limit"] == 0
    assert paladin_limits["spells_limit"] == 2


def test_card_parma_19_add_equipment_and_spells_enforcement(test_bridge):
    """Verifica el flujo completo de agregar equipo y el bloqueo al superar límite de conjuros."""
    char = CharacterSheet(name="Aventurero Test", char_class="Bardo", level=1)
    char_id = test_bridge._db.save_character(char)

    # 1. Agregar arma desde compendio
    res_wpn = test_bridge.add_item_to_character(char_id, {
        "name": "Daga de Acero",
        "name_en": "Steel Dagger",
        "item_type": "Arma Simple CaC",
        "damage": "1d4",
        "damage_type": "Perforante",
        "notes": "Sutil, Arrojadiza",
        "weapon_mastery": "Nick"
    })
    assert res_wpn["success"] is True
    char_data = res_wpn["character"]
    assert any(w["name"] == "Daga de Acero" for w in char_data["weapon_actions"])
    assert any(eq["name"] == "Daga de Acero" for eq in char_data["equipment"])

    # 2. Agregar armadura
    res_arm = test_bridge.add_item_to_character(char_id, {
        "name": "Armadura de Cuero",
        "name_en": "Leather Armor",
        "item_type": "Armadura Ligera",
        "ac_bonus": 11,
        "cost": "10 po"
    })
    assert res_arm["success"] is True
    char_data = res_arm["character"]
    assert any(eq["name"] == "Armadura de Cuero" for eq in char_data["equipment"])

    # 3. Límite de trucos (Bardo nivel 1 -> 2 trucos permitidos)
    assert test_bridge.add_spell_to_character(char_id, {"name": "Truco 1", "level": 0})["success"] is True
    assert test_bridge.add_spell_to_character(char_id, {"name": "Truco 2", "level": 0})["success"] is True
    
    # El tercer truco debe fallar con error descriptivo
    res_fail_cantrip = test_bridge.add_spell_to_character(char_id, {"name": "Truco 3", "level": 0})
    assert res_fail_cantrip["success"] is False
    assert "Límite de trucos alcanzado" in res_fail_cantrip["error"]

    # 4. Límite de preparados (Bardo nivel 1 -> 4 preparados permitidos)
    for i in range(1, 5):
        assert test_bridge.add_spell_to_character(char_id, {"name": f"Conjuro Lvl1 #{i}", "level": 1})["success"] is True

    # El quinto preparado debe fallar con error descriptivo
    res_fail_prep = test_bridge.add_spell_to_character(char_id, {"name": "Conjuro Excedente", "level": 1})
    assert res_fail_prep["success"] is False
    assert "Límite de conjuros preparados alcanzado" in res_fail_prep["error"]

    # 5. Eliminar equipo
    res_del = test_bridge.remove_item_from_character(char_id, "Daga de Acero", category="all")
    assert res_del["success"] is True
    char_data_after = res_del["character"]
    assert not any(w["name"] == "Daga de Acero" for w in char_data_after["weapon_actions"])
    assert not any(eq["name"] == "Daga de Acero" for eq in char_data_after["equipment"])
