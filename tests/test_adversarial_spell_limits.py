"""
Tests adversariales de límites de conjuros (hallazgo A3, grupo 4).

Invariantes:
- I4-b: el backend (autoridad) no permite agregar un conjuro de nivel>0 a un lanzador
  con 0 preparados modelados.
- I4-c: un dict de límites sin `is_caster` se trata como no lanzador (sin tope duro).
- I4-d (compat): un no lanzador (Guerrero) puede agregar conjuros.
- Expuesto al frontend: `spell_limits.is_caster` booleano en el payload serializado.

Categorías: compatibilidad, límite, input malformado.
"""
import pytest

from core.db import DatabaseManager
from core.models import CharacterSheet
from desktop_api.bridge import DesktopBridge

BRIDGE_LIMITS = "desktop_api.bridges.character_bridge.get_class_progression_limits"


@pytest.fixture
def test_bridge(tmp_path):
    db = DatabaseManager(str(tmp_path / "test_spell_limits.db"))
    bridge = DesktopBridge()
    bridge._db = db
    return bridge


def _new_char(bridge, char_class: str, level: int = 1) -> int:
    char = CharacterSheet(name=f"Test {char_class}", char_class=char_class, level=level)
    return bridge._db.save_character(char)


def test_spell_limits_is_caster_flag_for_real_classes(test_bridge):
    """Compat/exposición: Mago nivel 1 es lanzador, Guerrero nivel 1 no lo es.
    Categoría: compatibilidad. Hallazgo A3."""
    mago_id = _new_char(test_bridge, "Mago")
    guerrero_id = _new_char(test_bridge, "Guerrero")

    mago_limits = test_bridge.get_character_by_id(mago_id)["spell_limits"]
    guerrero_limits = test_bridge.get_character_by_id(guerrero_id)["spell_limits"]

    assert mago_limits["is_caster"] is True
    assert guerrero_limits["is_caster"] is False
    # Los demás campos no cambian con el nuevo flag.
    assert mago_limits["cantrips_max"] == 3
    assert mago_limits["spells_prepared_max"] == 4
    assert mago_limits["cantrips_current"] == 0
    assert mago_limits["spells_prepared_current"] == 0
    assert guerrero_limits["cantrips_max"] == 0
    assert guerrero_limits["spells_prepared_max"] == 0


def test_no_caster_can_still_add_spells(test_bridge):
    """I4-d (compat): Guerrero (no lanzador, tope 0) puede agregar un conjuro de nivel 1
    porque sus rasgos/dotes no están modelados. Categoría: compatibilidad. Hallazgo A3."""
    guerrero_id = _new_char(test_bridge, "Guerrero")
    res = test_bridge.add_spell_to_character(guerrero_id, {"name": "Conjuro Dote", "level": 1})
    assert res["success"] is True


def test_caster_with_zero_prepared_cannot_add_prepared_spell(test_bridge, monkeypatch):
    """I4-b: un lanzador con 0 preparados modelados no puede agregar nivel>0 desde el backend.
    Categoría: límite. Hallazgo A3 (la UI bloquea, pero la autoridad debe bloquear también)."""
    def fake_limits(*_args, **_kwargs):
        return {"is_caster": True, "cantrips_limit": 2, "spells_limit": 0}

    monkeypatch.setattr(BRIDGE_LIMITS, fake_limits)
    char_id = _new_char(test_bridge, "Mago")

    res = test_bridge.add_spell_to_character(char_id, {"name": "Conjuro Bloqueado", "level": 1})
    assert res["success"] is False
    assert "preparados" in res["error"]


def test_caster_with_zero_cantrips_can_add_cantrip(test_bridge, monkeypatch):
    """Decisión de dominio (default del plan): trucos=0 en un lanzador NO bloquea trucos,
    porque la dote/estilo que da trucos no está modelada. Categoría: compatibilidad."""
    def fake_limits(*_args, **_kwargs):
        return {"is_caster": True, "cantrips_limit": 0, "spells_limit": 2}

    monkeypatch.setattr(BRIDGE_LIMITS, fake_limits)
    char_id = _new_char(test_bridge, "Paladín")

    res = test_bridge.add_spell_to_character(char_id, {"name": "Truco Dote", "level": 0})
    assert res["success"] is True


def test_missing_is_caster_key_is_treated_as_non_caster(test_bridge, monkeypatch):
    """Input malformado / versión vieja: sin la clave `is_caster` el flag queda False y
    un tope de 0 no bloquea. Categoría: input malformado. Hallazgo A3."""
    def fake_limits(*_args, **_kwargs):
        return {"cantrips_limit": 0, "spells_limit": 0}

    monkeypatch.setattr(BRIDGE_LIMITS, fake_limits)
    char_id = _new_char(test_bridge, "Mago")

    limits = test_bridge.get_character_by_id(char_id)["spell_limits"]
    assert limits["is_caster"] is False

    res = test_bridge.add_spell_to_character(char_id, {"name": "Conjuro Viejo", "level": 1})
    assert res["success"] is True
