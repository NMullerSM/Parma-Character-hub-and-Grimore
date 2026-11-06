"""
CARD-PARMA-26 — Sembrado del compendio desde la base de referencia empaquetada.

Una instalación nueva (o una instalación v1.0.5 afectada) arranca con las tablas
compendium_* vacías porque el instalador nunca siembra dnd_database.db. El fix
copia el compendio desde data/dnd_database.db del bundle de solo lectura, pero
SIN pisar nunca los personajes que el usuario ya haya creado en su base.

Estas pruebas usan un bundle falso pequeño generado en tmp_path, así que no
dependen del compendio real de foundryvtt/dnd5e ni de data/dnd_database.db.
"""
import sqlite3

import pytest

import core.db as core_db
from core.db import DatabaseManager
from core.models import CharacterSheet


def _user_db(tmp_path, name: str) -> str:
    """Ruta de base de usuario con su carpeta padre creada (como hace get_user_data_dir en la app)."""
    folder = tmp_path / name
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / "dnd_database.db")


def _build_fake_bundle(bundle_root, monkeypatch) -> str:
    """Crea <bundle_root>/data/dnd_database.db con unas pocas filas de compendio."""
    data_dir = bundle_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    bundle_db = str(data_dir / "dnd_database.db")
    # Construir el bundle sin sembrarse desde el bundle real del entorno (data/ del repo en dev).
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(bundle_root / "_no_bundle_here"))
    dm = DatabaseManager(bundle_db)
    dm.upsert_compendium_monster({"name": "Goblin de Prueba", "name_en": "Test Goblin", "cr": 0.25})
    dm.upsert_compendium_monster({"name": "Ogro de Prueba", "name_en": "Test Ogre", "cr": 2})
    dm.upsert_compendium_spell({"name": "Conjuro de Prueba", "name_en": "Test Spell", "level": 1})
    dm.upsert_compendium_item({"name": "Espada de Prueba", "name_en": "Test Sword"})
    dm.upsert_compendium_entity({"name": "Entidad de Prueba", "name_en": "Test Entity", "category": "regla"})
    return bundle_db


def _count(db_path: str, table: str) -> int:
    con = sqlite3.connect(db_path)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        con.close()


@pytest.fixture
def fake_bundle_root(tmp_path, monkeypatch):
    """Devuelve la raíz de un bundle falso poblado (data/dnd_database.db con compendio)."""
    root = tmp_path / "bundle"
    _build_fake_bundle(root, monkeypatch)
    return root


@pytest.fixture
def empty_bundle_root(tmp_path):
    """Raíz de bundle sin data/dnd_database.db: simula una instalación sin base de referencia."""
    root = tmp_path / "no_bundle"
    root.mkdir()
    return root


def test_user_character_survives_reseed_on_next_start(tmp_path, monkeypatch, empty_bundle_root, fake_bundle_root):
    """
    No pérdida de datos: un personaje creado en una base con compendio vacío
    debe seguir existiendo tras el reseeding del siguiente arranque.
    """
    user_db = _user_db(tmp_path, "user")

    # 1. Primer arranque sin base de referencia disponible: esquema nuevo, compendio vacío.
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(empty_bundle_root))
    db = DatabaseManager(user_db)
    assert _count(user_db, "compendium_monsters") == 0
    char_id = db.save_character(CharacterSheet(name="Sobreviviente CARD-26", char_class="Mago", level=3))
    assert char_id > 0

    # 2. Siguiente arranque, ahora con la base de referencia poblada disponible.
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(fake_bundle_root))
    db2 = DatabaseManager(user_db)

    # (a) El personaje sigue ahí, con sus datos intactos.
    recovered = db2.get_character_by_id(char_id)
    assert recovered is not None
    assert recovered.name == "Sobreviviente CARD-26"
    assert recovered.char_class == "Mago"
    assert recovered.level == 3

    # (b) El compendio ahora tiene filas.
    assert _count(user_db, "compendium_monsters") == 2
    assert _count(user_db, "compendium_spells") == 1
    assert _count(user_db, "compendium_items") == 1
    assert _count(user_db, "compendium_entities") == 1


def test_fresh_install_gets_compendium_from_bundle(tmp_path, monkeypatch, fake_bundle_root):
    """Instalación nueva: no existe la base de usuario y debe quedar sembrada."""
    user_db = _user_db(tmp_path, "fresh")
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(fake_bundle_root))

    DatabaseManager(user_db)

    assert _count(user_db, "compendium_monsters") == 2
    assert _count(user_db, "compendium_spells") == 1


def test_populated_compendium_is_not_touched(tmp_path, monkeypatch, empty_bundle_root, fake_bundle_root):
    """Si la base de usuario ya tiene compendio, no se reemplaza ni se duplica nada."""
    user_db = _user_db(tmp_path, "populated")
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(empty_bundle_root))
    db = DatabaseManager(user_db)
    db.upsert_compendium_monster({"name": "Monstruo Propio del Usuario", "cr": 5})

    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(fake_bundle_root))
    DatabaseManager(user_db)

    assert _count(user_db, "compendium_monsters") == 1
    assert _count(user_db, "compendium_spells") == 0


def test_bundle_same_file_as_user_db_is_noop(tmp_path, monkeypatch):
    """
    En modo desarrollo la base del bundle ES la base del usuario
    (data/dnd_database.db). No debe intentar copiarse sobre sí misma ni perder filas.
    """
    bundle_root = tmp_path / "devrepo"
    same_db = _build_fake_bundle(bundle_root, monkeypatch)
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(bundle_root))

    db = DatabaseManager(same_db)
    db.save_character(CharacterSheet(name="Personaje Dev", char_class="Bardo", level=1))

    DatabaseManager(same_db)

    assert _count(same_db, "compendium_monsters") == 2
    assert _count(same_db, "characters") == 1


def test_empty_bundle_does_not_seed(tmp_path, monkeypatch):
    """Un bundle sin compendio (0 monstruos) no debe sembrar nada."""
    bundle_root = tmp_path / "emptybundle"
    (bundle_root / "data").mkdir(parents=True)
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(bundle_root / "_no_bundle_here"))
    DatabaseManager(str(bundle_root / "data" / "dnd_database.db"))  # esquema sin filas
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(bundle_root))

    user_db = _user_db(tmp_path, "user2")
    DatabaseManager(user_db)

    assert _count(user_db, "compendium_monsters") == 0
