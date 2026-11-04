import os
import sqlite3
import tempfile
import pytest
from core.db import DatabaseManager
from core.compendium_importer import (
    CompendiumImporter,
    parse_cr_to_float,
    normalize_monster,
    normalize_spell,
    normalize_item,
)


def test_migration_user_version_2_and_backup():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # 1. Simular base de datos existente en user_version = 1
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE characters (id INTEGER PRIMARY KEY, name TEXT);")
    cur.execute("PRAGMA user_version = 1;")
    conn.commit()
    conn.close()

    # 2. Inicializar DatabaseManager y disparar migración a user_version = 2
    db = DatabaseManager(db_path=path)

    # 3. Comprobar creación de backup .bak_v1
    backup_path = f"{path}.bak_v1"
    assert os.path.exists(backup_path), "No se creó el respaldo .bak_v1 antes de migrar a v2"

    # 4. Comprobar que user_version es >= 3
    with db._get_connection() as c:
        cursor = c.cursor()
        cursor.execute("PRAGMA user_version;")
        assert cursor.fetchone()[0] >= 3

        # 5. Comprobar existencia de las tablas relacionales del compendio
        for tbl in ("compendium_monsters", "compendium_spells", "compendium_items", "compendium_entities"):
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}';")
            assert cursor.fetchone() is not None, f"Falta la tabla {tbl}"


def test_cr_parsing():
    assert parse_cr_to_float("0") == (0.0, "0")
    assert parse_cr_to_float("1/8") == (0.125, "1/8")
    assert parse_cr_to_float("1/4") == (0.25, "1/4")
    assert parse_cr_to_float("1/2") == (0.5, "1/2")
    assert parse_cr_to_float("1") == (1.0, "1")
    assert parse_cr_to_float(5) == (5.0, "5")
    assert parse_cr_to_float("20") == (20.0, "20")


def test_monster_normalization_and_search():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    importer = CompendiumImporter(db)

    sample_monsters = [
        {
            "name": "Goblin",
            "source": "XPHB",
            "size": ["S"],
            "type": "Humanoid",
            "cr": "1/4",
            "ac": [15],
            "hp": {"average": 7, "formula": "2d6"},
            "speed": {"walk": 30},
            "alignment": ["N", "E"],
        },
        {
            "name": "Adult Red Dragon",
            "source": "XPHB",
            "size": ["H"],
            "type": "Dragon",
            "cr": "17",
            "ac": [19],
            "hp": {"average": 256, "formula": "19d12 + 133"},
            "speed": {"walk": 40, "fly": 80},
            "alignment": ["C", "E"],
        },
    ]

    count = importer.ingest_monsters(sample_monsters, edition="5.5e", lang="en")
    assert count == 2

    # Filtrar por CR
    low_cr = db.search_compendium_monsters(max_cr=1.0)
    assert len(low_cr) == 1
    assert low_cr[0]["name"] == "Goblin"
    assert low_cr[0]["cr"] == 0.25

    # Filtrar por tipo
    dragons = db.search_compendium_monsters(monster_type="Dragon")
    assert len(dragons) == 1
    assert dragons[0]["name"] == "Adult Red Dragon"
    assert dragons[0]["cr"] == 17.0

    # Obtener con detalles completos
    dragon_detail = db.get_compendium_monster_by_id(dragons[0]["entity_id"])
    assert dragon_detail is not None
    assert dragon_detail["details"]["ac"] == [19]


def test_spells_normalization_and_search():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    importer = CompendiumImporter(db)

    sample_spells = [
        {
            "name": "Fireball",
            "source": "XPHB",
            "level": 3,
            "school": "V",
            "time": [{"number": 1, "unit": "action"}],
            "range": {"type": "point", "distance": {"type": "feet", "amount": 150}},
            "components": {"v": True, "s": True, "m": "a tiny ball of bat guano"},
            "duration": [{"type": "instant"}],
            "entries": ["A bright streak flashes from your pointing finger to a point you choose..."],
            "classes": {"fromClassList": [{"name": "Sorcerer"}, {"name": "Wizard"}]},
        },
        {
            "name": "Bless",
            "source": "XPHB",
            "level": 1,
            "school": "E",
            "time": [{"number": 1, "unit": "action"}],
            "range": {"type": "point", "distance": {"type": "feet", "amount": 30}},
            "duration": [{"type": "timed", "duration": {"type": "minute", "amount": 1}, "concentration": True}],
            "entries": ["You bless up to three creatures of your choice..."],
            "classes": {"fromClassList": [{"name": "Cleric"}, {"name": "Paladin"}]},
        },
    ]

    count = importer.ingest_spells(sample_spells, edition="5.5e", lang="en")
    assert count == 2

    # Filtrar por nivel
    lvl1 = db.search_compendium_spells(level=1)
    assert len(lvl1) == 1
    assert lvl1[0]["name"] == "Bless"
    assert lvl1[0]["is_concentration"] == 1

    # Filtrar por escuela
    evoc = db.search_compendium_spells(school="Evocation")
    assert len(evoc) == 1
    assert evoc[0]["name"] == "Fireball"

    # Filtrar por clase
    wizards = db.search_compendium_spells(class_name="Wizard")
    assert len(wizards) == 1
    assert wizards[0]["name"] == "Fireball"


def test_item_weapon_mastery_55e():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    importer = CompendiumImporter(db)

    sample_items = [
        {
            "name": "Dagger",
            "source": "XPHB",
            "type": "M",
            "weaponCategory": "simple",
            "dmg1": "1d4",
            "dmgType": "P",
            "mastery": "nick",
            "value": 200,
            "weight": 1,
        },
        {
            "name": "Greatsword",
            "source": "XPHB",
            "type": "M",
            "weaponCategory": "martial",
            "dmg1": "2d6",
            "dmgType": "S",
            "mastery": "graze",
            "value": 5000,
            "weight": 6,
        },
    ]

    count = importer.ingest_items(sample_items, edition="5.5e", lang="en")
    assert count == 2

    # Filtrar por Weapon Mastery (Regla 5.5e)
    nick_weapons = db.search_compendium_items(weapon_mastery="nick")
    assert len(nick_weapons) == 1
    assert nick_weapons[0]["name"] == "Dagger"
    assert nick_weapons[0]["weapon_mastery"] == "nick"

    graze_weapons = db.search_compendium_items(weapon_mastery="graze")
    assert len(graze_weapons) == 1
    assert graze_weapons[0]["name"] == "Greatsword"
    assert graze_weapons[0]["weapon_mastery"] == "graze"


def test_clean_foundry_syntax():
    from core.compendium_importer import clean_foundry_syntax

    raw_text = "<p>The [[lookup @name lowercase]]{monster} uses [[/attack]] [[/r 1d20+5]]. On hit, [[/damage]] &Reference[poisoned].</p>"
    cleaned = clean_foundry_syntax(
        raw_text,
        name_en="Barbed Devil",
        name_es="Barbed Devil",
        it_data={"system": {"damage": {"base": {"number": 2, "denomination": 6, "types": ["fire"]}}}},
        raw_data={},
        lang="es"
    )
    assert "[[" not in cleaned
    assert "]]" not in cleaned
    assert "barbed devil" in cleaned
    assert "envenenado" in cleaned
    assert "Impacto:" in cleaned


def test_item_damage_filtering_non_weapons():
    from core.compendium_importer import normalize_foundry_item

    # Ítem no arma (poción)
    potion_raw = {
        "name": "Potion of Healing",
        "type": "consumable",
        "system": {
            "type": {"value": "potion"},
            "damage": {"base": {}},
            "price": {"value": 50, "denomination": "gp"},
        }
    }
    norm_potion = normalize_foundry_item(potion_raw, edition="5.5e", lang="es")
    assert norm_potion["damage"] == ""

    # Ítem arma
    weapon_raw = {
        "name": "Longsword",
        "type": "weapon",
        "system": {
            "type": {"value": "martialM"},
            "damage": {"base": {"number": 1, "denomination": 8, "types": ["slashing"]}},
            "price": {"value": 15, "denomination": "gp"},
            "mastery": "sap",
        }
    }
    norm_weapon = normalize_foundry_item(weapon_raw, edition="5.5e", lang="es")
    assert "1d8" in norm_weapon["damage"]
    assert "Sap" in norm_weapon["weapon_mastery"]


def test_compendium_entities_crud():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)

    entity = {
        "entity_id": "paladin_55e_es",
        "name": "Paladín",
        "name_en": "Paladin",
        "category": "clase",
        "edition": "5.5e",
        "language": "es",
        "snippet": "Un guerrero santo unido por un juramento sagrado.",
        "content_markdown": "# Paladín\n\nEl paladín es...",
        "data_json": {"hit_die": "d10", "primary_ability": "FUE, CAR"},
    }
    db.upsert_compendium_entity(entity)

    # Búsqueda
    results = db.search_compendium_entities("paladin", category="clase", language="es", edition="5.5e")
    assert len(results) == 1
    assert results[0]["name"] == "Paladín"
    assert results[0]["entity_id"] == "paladin_55e_es"

    # Obtención directa por ID o nombre
    got = db.get_compendium_entity_by_id("paladin_55e_es")
    assert got is not None
    assert got["category"] == "clase"
    assert got["details"].get("hit_die") == "d10"

    # Conteo
    assert db.count_compendium_entries("clase") == 1
    assert db.count_compendium_entries("entities") == 1
    assert db.count_compendium_entries("dotes") == 0
