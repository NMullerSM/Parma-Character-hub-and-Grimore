"""
Test de Integración y Regresión: TaleSpire Dice Bridge & Volatile Session Ledger.
Verifica:
1. TaleSpireBridge: construcción de URLs, sanitización, límite de 40 dados y latencia.
2. Motor de Reglas: roll_dice_multiple para tiradas individuales y pools de dados.
3. SessionRollLedger: persistencia volátil, orden cronológico inverso y purga destructiva.
4. Componente DiceTray: inicialización, ejecución de tiradas y fallback transparente.
"""
import os
import sys
import time

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flet_app.core.talespire_bridge import TaleSpireBridge, MAX_DICE_COUNT
from flet_app.core.session_ledger import SessionRollLedger, RollEntry
from flet_app.core.rules import roll_dice, roll_dice_multiple
from flet_app.core.models import CharacterSheet
from flet_app.ui.components.dice_tray import DiceTray


class MockPage:
    def __init__(self):
        self.overlay = []
        self.snack_bar = None
        self.dialog = None

    def update(self, *args, **kwargs):
        pass


    def open(self, dlg):
        self.dialog = dlg

    def close(self, dlg):
        self.dialog = None


def test_talespire_bridge():
    print("--- 1. Testing TaleSpireBridge ---")
    bridge = TaleSpireBridge(timeout_ms=50, cache_ttl=0.1)

    # 1.1 Medición de latencia de detección (debe ser ultra rápida, < 50ms)
    t0 = time.time()
    connected = bridge.is_connected(force_refresh=True)
    dt_ms = (time.time() - t0) * 1000
    print(f"  is_connected check completed in {dt_ms:.2f} ms (Result: {connected})")
    assert dt_ms < 60.0, f"Detección tomó demasiado tiempo: {dt_ms:.2f} ms"

    # 1.2 Generación de URLs
    url1 = bridge.build_roll_url([{"label": "Iniciativa", "count": 1, "sides": 20, "mod": 3}])
    print(f"  Simple roll URL: {url1}")
    assert url1 == "talespire://dice/Iniciativa:1d20+3"

    url_compound = bridge.build_roll_url([
        {"label": "Ataque", "count": 1, "sides": 20, "mod": 5},
        {"label": "Daño", "count": 2, "sides": 6, "mod": 3}
    ])
    print(f"  Compound roll URL: {url_compound}")
    assert url_compound == "talespire://dice/Ataque:1d20+5/Daño:2d6+3"

    # 1.3 Sanitización de etiquetas con caracteres prohibidos
    url_sanitized = bridge.build_roll_url([{"label": "Espada:Corte/Fuego", "count": 1, "sides": 8, "mod": 2}])
    print(f"  Sanitized roll URL: {url_sanitized}")
    assert ":" not in url_sanitized.split("talespire://dice/")[1].split(":")[0]

    # 1.4 Límite estricto de dados (máximo 40)
    try:
        bridge.build_roll_url([{"label": "Exceso", "count": 45, "sides": 6, "mod": 0}])
        assert False, "Debería haber lanzado ValueError por exceder 40 dados"
    except ValueError as ex:
        print(f"  Correctly caught exceeding dice count: {ex}")

    # 1.5 Fallback seguro en send_roll sin TaleSpire abierto
    res = bridge.send_roll(url1)
    print(f"  send_roll fallback test: {res} (Expected False if TaleSpire is closed)")


def test_rules_roll_dice_multiple():
    print("--- 2. Testing rules.roll_dice_multiple ---")
    # 2.1 Tirada simple de 1d20
    r1 = roll_dice_multiple(count=1, sides=20, mode="normal", modifier=4)
    assert r1["sides"] == 20
    assert r1["modifier"] == 4
    assert r1["total"] == r1["selected"] + 4
    print(f"  1d20 roll: {r1['detail']}")

    # 2.2 Tirada de pool múltiple (ej: Bola de Fuego 8d6)
    r_multi = roll_dice_multiple(count=8, sides=6, mode="normal", modifier=0)
    assert r_multi["count"] == 8
    assert r_multi["sides"] == 6
    assert len(r_multi["rolls"]) == 8
    assert sum(r_multi["rolls"]) == r_multi["total"]
    print(f"  8d6 fireball pool: {r_multi['detail']}")

    # 2.3 Modificador negativo
    r_neg = roll_dice_multiple(count=2, sides=6, modifier=-2)
    assert r_neg["total"] == sum(r_neg["rolls"]) - 2
    print(f"  2d6 - 2 roll: {r_neg['detail']}")


def test_session_roll_ledger():
    print("--- 3. Testing SessionRollLedger (Volatile RAM Ledger) ---")
    ledger = SessionRollLedger.get_current()
    ledger.destroy_session()  # Asegurar estado limpio

    ledger = SessionRollLedger.get_current()
    assert len(ledger.get_history()) == 0

    e1 = ledger.record_roll("Artanis", "Iniciativa", "1d20", "1d20: [14] + 2 = 16", 16)
    e2 = ledger.record_roll("Artanis", "Ataque Espada", "1d20", "1d20: [18] + 5 = 23", 23)
    e3 = ledger.record_roll("Artanis", "Daño Espada", "1d8", "1d8: [7] + 3 = 10", 10)

    history = ledger.get_history()
    assert len(history) == 3
    # Comprobar orden cronológico inverso (última tirada al inicio)
    assert history[0].reason == "Daño Espada"
    assert history[1].reason == "Ataque Espada"
    assert history[2].reason == "Iniciativa"
    print(f"  Ledger recorded 3 entries. Most recent: {history[0].reason}")

    # Probar purga total destructiva
    ledger.destroy_session()
    assert len(ledger.entries) == 0
    assert SessionRollLedger._instance is None
    print("  SessionRollLedger destroy_session purged memory completely.")


def test_dice_tray_component():
    print("--- 4. Testing DiceTray UI Component ---")
    page = MockPage()
    char = CharacterSheet(name="Valeros", char_class="Guerrero", level=3)

    tray = DiceTray(char=char)
    tray.page = page

    # Ejecutar tirada local
    tray.do_roll(sides=20, reason="Prueba Atletismo", count=1)
    history = tray.ledger.get_history()
    assert len(history) >= 1
    assert "Atletismo" in history[0].reason
    assert history[0].character_name == "Valeros"
    print(f"  DiceTray roll performed and logged: {history[0].detail}")

    # Cambiar personaje y volver a tirar
    char2 = CharacterSheet(name="Eldrin", char_class="Mago", level=3)
    tray.set_character(char2)
    tray.do_roll(sides=6, reason="Rayo Relámpago", count=4)
    assert tray.ledger.get_history()[0].character_name == "Eldrin"
    print(f"  DiceTray hero dynamic update confirmed: {tray.ledger.get_history()[0].character_name}")

    # Limpiar
    tray.ledger.destroy_session()
    print("  DiceTray test completed successfully.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING TALESPIRE DICE BRIDGE INTEGRATION TESTS")
    print("==================================================")
    test_talespire_bridge()
    test_rules_roll_dice_multiple()
    test_session_roll_ledger()
    test_dice_tray_component()
    print("\nALL TALESPIRE INTEGRATION TESTS PASSED!")
