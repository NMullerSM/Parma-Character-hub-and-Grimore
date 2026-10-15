"""
Suite de Pruebas: TaleSpire Dice Bridge (Revisión Final) & Multi-Dice Pool Builder.
Prueba:
1. Máquina de estados TaleSpireState (NOT_INSTALLED, INSTALLED_CLOSED, RUNNING_IDLE, CONNECTED).
2. Detección de instalación y manejo amigable cuando el juego está cerrado.
3. Motor de reglas roll_dice_pool para tiradas compuestas (1d20 + 2d6 + 1d8 + 3).
4. Multi-Dice Pool Builder en DiceTray: acumulación, visor de chips, ejecución y limpieza.
5. Retrocompatibilidad total con tiradas directas de armas y habilidades.
6. Ciclo de vida y purga del SessionRollLedger.
"""
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flet_app.core.talespire_bridge import TaleSpireBridge, TaleSpireState, MAX_DICE_COUNT
from flet_app.core.rules import roll_dice_pool, roll_dice_multiple
from flet_app.core.session_ledger import SessionRollLedger
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


def test_talespire_state_machine():
    print("--- 1. Testing TaleSpireState & State Transitions ---")
    bridge = TaleSpireBridge()
    print(f"  Estado inicial detectado: {bridge.state.value} (is_installed: {bridge.is_installed})")

    # Si TaleSpire.exe no está corriendo, connect() debe retornar False con mensaje claro
    if not bridge.is_process_running():
        success, msg = bridge.connect()
        assert not success
        assert "no está abierto" in msg or "no está instalado" in msg
        assert bridge.state in (TaleSpireState.INSTALLED_CLOSED, TaleSpireState.NOT_INSTALLED)
        print(f"  connect() cuando el juego está inactivo: {msg}")

    # Simulación de sesión conectada para probar persistencia
    bridge.state = TaleSpireState.CONNECTED
    # Mock is_process_running para test
    orig_is_running = bridge.is_process_running
    bridge.is_process_running = lambda: True

    assert bridge.is_session_connected() is True
    print("  Sesión en estado CONNECTED se mantiene persistente.")

    # Desconectar manual
    bridge.disconnect()
    assert bridge.state in (TaleSpireState.RUNNING_IDLE, TaleSpireState.INSTALLED_CLOSED)
    assert bridge.is_session_connected() is False
    print("  disconnect() manual vuelve a modo local con éxito.")

    # Restaurar
    bridge.is_process_running = orig_is_running


def test_pool_url_builder():
    print("--- 2. Testing build_pool_url for Combined Dice Pools ---")
    bridge = TaleSpireBridge()

    # Pool complejo: 1d20 + 2d6 + 1d8 con modificador +3
    pool = {20: 1, 6: 2, 8: 1}
    url = bridge.build_pool_url(pool, modifier=3, label="Ataque y Daño")
    print(f"  Combined Pool URL: {url}")
    assert "talespire://dice/" in url
    assert "1d20" in url
    assert "1d8" in url
    assert "2d6+3" in url


    # Límite de 40 dados
    try:
        bridge.build_pool_url({6: 50}, modifier=0)
        assert False, "Debería haber lanzado ValueError al superar 40 dados"
    except ValueError as ex:
        print(f"  Límite de 40 dados validado correctamente: {ex}")


def test_rules_roll_dice_pool():
    print("--- 3. Testing rules.roll_dice_pool ---")
    # Pool: 1d20 + 2d6 + 1d8 + 3
    pool = {20: 1, 6: 2, 8: 1}
    res = roll_dice_pool(pool, modifier=3, mode="normal")

    assert res["modifier"] == 3
    assert res["total"] == res["subtotal"] + 3
    assert "1d20" in res["detail"]
    assert "2d6" in res["detail"]
    assert "1d8" in res["detail"]
    print(f"  Pool Roll Result: {res['detail']}")

    # Ventaja en d20 con dados adicionales
    res_adv = roll_dice_pool({20: 1, 6: 1}, modifier=2, mode="advantage")
    assert "ventaja" in res_adv["detail"]
    print(f"  Advantage Pool Roll: {res_adv['detail']}")


def test_dice_tray_multi_pool_builder():
    print("--- 4. Testing DiceTray Multi-Dice Pool Builder & UI Interaction ---")
    page = MockPage()
    char = CharacterSheet(name="Theron", char_class="Paladín", level=5)
    tray = DiceTray(char=char)
    tray.page = page

    # Acumular dados en el pool: 1d20 + 2d6 + 1d8
    tray._add_die_to_pool(20)
    tray._add_die_to_pool(6)
    tray._add_die_to_pool(6)
    tray._add_die_to_pool(8)

    assert tray.pool[20] == 1
    assert tray.pool[6] == 2
    assert tray.pool[8] == 1
    formula = tray._format_pool_formula()
    print(f"  Pool acumulado en tray: {formula}")
    assert "1d20" in formula
    assert "2d6" in formula
    assert "1d8" in formula

    # Retirar un dado del pool
    tray._remove_die_from_pool(6)
    assert tray.pool[6] == 1
    print(f"  Tras retirar 1d6: {tray._format_pool_formula()}")

    # Lanzar pool
    tray.execute_pool_roll(tray.pool, reason="Golpe Divino")
    history = tray.ledger.get_history()
    assert len(history) >= 1
    assert history[0].reason == "Golpe Divino"
    assert history[0].character_name == "Theron"
    print(f"  Tirada de pool ejecutada y registrada: {history[0].detail}")

    # Probar tirada directa retrocompatible (ej: arma desde CombatView)
    tray.do_roll(sides=8, custom_mod=4, reason="Espada Larga", count=1)
    history2 = tray.ledger.get_history()
    assert history2[0].reason == "Espada Larga"
    print(f"  Tirada directa retrocompatible exitosa: {history2[0].detail}")

    # Limpieza total de sesión
    tray.ledger.destroy_session()
    assert len(tray.ledger.get_history()) == 0
    print("  Sesión purgada en memoria exitosamente.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING TALESPIRE REVISION FINAL TESTS")
    print("==================================================")
    test_talespire_state_machine()
    test_pool_url_builder()
    test_rules_roll_dice_pool()
    test_dice_tray_multi_pool_builder()
    print("\nALL REVISION FINAL TESTS PASSED SUCCESSFULLY!")
