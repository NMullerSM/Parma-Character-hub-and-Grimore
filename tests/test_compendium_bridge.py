"""
Pruebas automatizadas para CompendiumBridgeMixin y su integración en DesktopBridge.
Verifica búsqueda, filtrado, detalle y paginación sobre las tablas SQLite compendium_*.
"""
import os
import json
import tempfile
import pytest
from core.db import DatabaseManager
from desktop_api.bridge import DesktopBridge
from desktop_api.bridges import CompendiumBridgeMixin


class DummyCompendiumBridge(CompendiumBridgeMixin):
    """Bridge de prueba para aislar el mixin con base de datos temporal."""
    def __init__(self, db: DatabaseManager):
        self._db = db


@pytest.fixture
def compendium_fixture():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)

    # Insertar criaturas de prueba
    db.upsert_compendium_monster({
        "entity_id": "goblin",
        "name": "Goblin",
        "name_en": "Goblin",
        "cr": 0.25,
        "cr_text": "1/4",
        "size": "Small",
        "monster_type": "humanoid",
        "alignment": "Neutral Evil",
        "ac": 15,
        "hp_avg": 7,
        "hp_formula": "2d6",
        "speed": "30 ft.",
        "edition": "5.5e",
        "language": "en",
        "data_json": json.dumps({"dex": 14, "skills": {"stealth": 6}})
    })
    db.upsert_compendium_monster({
        "entity_id": "ancient_red_dragon",
        "name": "Ancient Red Dragon",
        "name_en": "Ancient Red Dragon",
        "cr": 24.0,
        "cr_text": "24",
        "size": "Gargantuan",
        "monster_type": "dragon",
        "alignment": "Chaotic Evil",
        "ac": 22,
        "hp_avg": 546,
        "hp_formula": "28d20 + 252",
        "speed": "40 ft., fly 80 ft.",
        "edition": "5.5e",
        "language": "en",
        "data_json": json.dumps({"str": 30, "legendary_actions": True})
    })

    # Insertar conjuros de prueba
    db.upsert_compendium_spell({
        "entity_id": "fireball",
        "name": "Fireball",
        "name_en": "Fireball",
        "level": 3,
        "school": "Evocation",
        "casting_time": "1 action",
        "range_area": "150 feet",
        "components": "V, S, M",
        "duration": "Instantaneous",
        "is_concentration": False,
        "is_ritual": False,
        "classes": ["Sorcerer", "Wizard"],
        "edition": "5.5e",
        "language": "en",
        "description": "A bright streak flashes from your pointing finger to a point you choose...",
        "data_json": json.dumps({"damage": "8d6 fire"})
    })
    db.upsert_compendium_spell({
        "entity_id": "guidance",
        "name": "Guidance",
        "name_en": "Guidance",
        "level": 0,
        "school": "Divination",
        "casting_time": "1 action",
        "range_area": "Touch",
        "components": "V, S",
        "duration": "Concentration, up to 1 minute",
        "is_concentration": True,
        "is_ritual": False,
        "classes": ["Cleric", "Druid"],
        "edition": "5.5e",
        "language": "en",
        "description": "You touch one willing creature. Once before the spell ends...",
        "data_json": json.dumps({"bonus": "1d4"})
    })

    # Insertar ítems de prueba
    db.upsert_compendium_item({
        "entity_id": "dagger",
        "name": "Dagger",
        "name_en": "Dagger",
        "item_type": "weapon",
        "rarity": "common",
        "cost": "2 gp",
        "weight": "1 lb.",
        "weapon_mastery": "Nick",
        "damage": "1d4",
        "damage_type": "piercing",
        "ac_bonus": 0,
        "edition": "5.5e",
        "language": "en",
        "description": "Simple melee weapon with finesse, light, thrown properties.",
        "data_json": json.dumps({"properties": ["finesse", "light", "thrown"]})
    })
    db.upsert_compendium_item({
        "entity_id": "longsword",
        "name": "Longsword",
        "name_en": "Longsword",
        "item_type": "weapon",
        "rarity": "common",
        "cost": "15 gp",
        "weight": "3 lb.",
        "weapon_mastery": "Sap",
        "damage": "1d8 / 1d10",
        "damage_type": "slashing",
        "ac_bonus": 0,
        "edition": "5.5e",
        "language": "en",
        "description": "Versatile martial weapon with Sap mastery.",
        "data_json": json.dumps({"properties": ["versatile"]})
    })

    bridge = DummyCompendiumBridge(db)
    yield bridge, db

    try:
        os.remove(path)
    except Exception:
        pass


def test_bridge_inheritance():
    assert issubclass(DesktopBridge, CompendiumBridgeMixin)
    for method in (
        "search_monsters", "get_monster_by_id",
        "search_spells", "get_spell_by_id",
        "search_items", "get_item_by_id",
        "get_compendium_counts"
    ):
        assert hasattr(DesktopBridge, method)
        assert callable(getattr(DesktopBridge, method))


def test_search_monsters_and_pagination(compendium_fixture):
    bridge, db = compendium_fixture

    # Búsqueda general
    res = bridge.search_monsters()
    assert res["total"] == 2
    assert len(res["items"]) == 2
    assert res["page"] == 1
    assert not res["has_more"]

    # Filtro por texto
    res_gob = bridge.search_monsters(query="Goblin")
    assert len(res_gob["items"]) == 1
    assert res_gob["items"][0]["entity_id"] == "goblin"

    # Filtro por CR
    res_cr = bridge.search_monsters(cr_min=1.0, cr_max=30.0)
    assert len(res_cr["items"]) == 1
    assert res_cr["items"][0]["entity_id"] == "ancient_red_dragon"

    # Detalle con deserialización
    detail = bridge.get_monster_by_id("goblin")
    assert detail is not None
    assert detail["name"] == "Goblin"
    assert detail["details"]["skills"]["stealth"] == 6

    # Registro inexistente
    assert bridge.get_monster_by_id("beholder_nonexistent") is None


def test_search_spells_and_filters(compendium_fixture):
    bridge, db = compendium_fixture

    # Todos los conjuros
    res = bridge.search_spells()
    assert res["total"] == 2
    assert len(res["items"]) == 2

    # Filtro por nivel
    res_cantrip = bridge.search_spells(level=0)
    assert len(res_cantrip["items"]) == 1
    assert res_cantrip["items"][0]["entity_id"] == "guidance"

    # Filtro por escuela
    res_evo = bridge.search_spells(school="Evocation")
    assert len(res_evo["items"]) == 1
    assert res_evo["items"][0]["entity_id"] == "fireball"

    # Filtro por concentración
    res_conc = bridge.search_spells(is_concentration=True)
    assert len(res_conc["items"]) == 1
    assert res_conc["items"][0]["entity_id"] == "guidance"

    # Detalle
    spell = bridge.get_spell_by_id("fireball")
    assert spell is not None
    assert spell["name"] == "Fireball"
    assert spell["details"]["damage"] == "8d6 fire"

    assert bridge.get_spell_by_id("wish_nonexistent") is None


def test_search_items_and_weapon_mastery(compendium_fixture):
    bridge, db = compendium_fixture

    # Búsqueda general
    res = bridge.search_items()
    assert res["total"] == 2
    assert len(res["items"]) == 2

    # Filtrar por Weapon Mastery (2024 D&D 5.5e)
    res_nick = bridge.search_items(weapon_mastery="Nick")
    assert len(res_nick["items"]) == 1
    assert res_nick["items"][0]["entity_id"] == "dagger"

    res_sap = bridge.search_items(weapon_mastery="Sap")
    assert len(res_sap["items"]) == 1
    assert res_sap["items"][0]["entity_id"] == "longsword"

    # Detalle
    item = bridge.get_item_by_id("dagger")
    assert item is not None
    assert item["weapon_mastery"] == "Nick"
    assert "finesse" in item["details"]["properties"]

    assert bridge.get_item_by_id("excalibur_nonexistent") is None


def test_get_compendium_counts(compendium_fixture):
    bridge, db = compendium_fixture
    counts = bridge.get_compendium_counts()
    assert counts == {
        "monsters": 2,
        "spells": 2,
        "items": 2
    }


def test_character_bridge_compendium_integration(compendium_fixture):
    _, db = compendium_fixture
    desktop_bridge = DesktopBridge()
    desktop_bridge._db = db

    # 1. Categorías incluyen monstruos
    cats = desktop_bridge.get_compendium_categories("en")
    cat_ids = [c["id"] for c in cats]
    assert "monstruos" in cat_ids
    monster_cat = next(c for c in cats if c["id"] == "monstruos")
    assert monster_cat["count"] == 2

    # 2. search_compendium con category="monstruos"
    res_m = desktop_bridge.search_compendium(query="dragon", category="monstruos", lang="en")
    assert len(res_m) == 1
    assert res_m[0]["id"] == "ancient_red_dragon"
    assert res_m[0]["category"] == "monstruos"

    # 3. get_compendium_entry para monstruo
    entry = desktop_bridge.get_compendium_entry(category="monstruos", entry_name="goblin", lang="en")
    assert entry is not None
    assert entry["name"] == "Goblin"
    assert "Clase de Armadura" in entry["content"] or "Armadura" in entry["content"]

