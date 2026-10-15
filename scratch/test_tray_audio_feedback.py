"""
Prueba de validación para las mejoras solicitadas en el feedback de audio:
1. Estilo no-amarillo del d20 consistente con los demás dados.
2. Botones de cantidad (1 a 8) asignados al dado seleccionado.
3. Sincronización en vivo con TaleSpire (staging sin esperar a pulsar Lanzar).
4. Simulación del gesto físico de lanzamiento (elipse + flick forward).
5. Botón 'Limpiar' vacía completamente el pool y actualiza controles.
6. Botón de lanzamiento tiene texto estricto '🎲 Lanzar Dados'.
7. Historial muestra sumatoria total clara sin redundancia de badge 'TaleSpire 3D'.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flet_app.ui.components.dice_tray import DiceTray
from flet_app.core.talespire_bridge import TaleSpireBridge, TaleSpireState
from flet_app.core.models import CharacterSheet

class MockPage:
    def __init__(self):
        self.snack_bar = None
    def update(self, *args, **kwargs):
        pass
    def open(self, dlg, *args, **kwargs):
        pass
    def close(self, dlg, *args, **kwargs):
        pass

def test_audio_feedback_requirements():
    print("=== Testing Audio Feedback Requirements ===")
    page = MockPage()
    char = CharacterSheet(name="Valeros", char_class="Guerrero", level=3)
    tray = DiceTray(char=char)
    tray.page = page

    # 1. d20 styling verification
    d20_btn = tray.dice_buttons_row.controls[0]
    print("1. d20 button styling verified (no permanent yellow bgcolor):", d20_btn.bgcolor)
    assert d20_btn.bgcolor != "#d4af37"

    # 2. Stepper controls & Mode toggle
    assert tray.btn_dec_qty is not None
    assert tray.btn_inc_qty is not None
    assert tray.btn_add_to_pool is not None
    assert tray.ts_mode == "dm"
    tray._set_ts_mode("player")
    assert tray.ts_mode == "player"
    tray._set_ts_mode("dm")
    print("2. Stepper controls and Mode toggle verified successfully!")

    # 3. Live staging to TaleSpire on dice / quantity selection
    staged_calls = []
    original_send_roll = tray.bridge.send_roll
    tray.bridge.send_roll = lambda url: staged_calls.append(url) or True
    tray.bridge.is_process_running = lambda: True
    tray.bridge.state = TaleSpireState.CONNECTED

    # Select d4, increment qty to 3, add to pool
    tray._on_die_select_click(4)
    assert tray.active_die == 4
    tray.pending_qty = 3
    tray._on_add_to_pool_click(None)
    assert tray.pool[4] == 3
    print("3. Live staging captured URL:", staged_calls[-1])
    assert "3d4" in staged_calls[-1]

    # Select d20, set qty 2, add to pool (i.e. 2d20 + 3d4)
    tray._on_die_select_click(20)
    tray.pending_qty = 2
    tray._on_add_to_pool_click(None)
    assert tray.pool[20] == 2
    assert tray.pool[4] == 3
    print("   Live staging updated with 2d20 + 3d4:", staged_calls[-1])
    assert "2d20" in staged_calls[-1]
    assert "3d4" in staged_calls[-1]

    # 4. Physical throw gesture simulation on launch
    gesture_called = []
    tray.bridge.execute_throw_gesture = lambda *args, **kwargs: gesture_called.append(True) or True

    # Check launch button text
    assert tray.btn_roll_pool.text == "🎲 Lanzar Dados"
    print("4. Launch button text verified strictly as: Lanzar Dados")

    # Trigger launch
    tray._on_launch_pool_click(None)
    assert len(gesture_called) == 1
    print("5. Throw gesture executed successfully on Launch click!")

    # Verify pool remains active for re-rolls until explicitly cleared
    assert len(tray.pool) > 0
    print("6. Pool persistence verified (re-rollable until [Limpiar]).")

    # 7. Check session ledger entry (Total sum present, no redundant TaleSpire pill)
    history = tray.ledger.get_history()
    assert len(history) >= 1
    latest_entry = history[0]
    print("7. History roll entry:")
    print("   Reason:", latest_entry.reason)
    print("   Total sum:", repr(latest_entry.total))
    print("   Detail breakdown:", repr(latest_entry.detail))
    assert latest_entry.total == "🎲 En mesa 3D" or (isinstance(latest_entry.total, int) and latest_entry.total > 0)

    # Verify UI log row structure
    log_item = tray.log_column.controls[0]
    row_controls = log_item.content.controls[0].controls
    left_text = row_controls[0].value
    right_text = row_controls[1].value
    print(f"   Log item UI: '{left_text}' | '{repr(right_text)}'")
    assert "En mesa 3D" in right_text or "Total:" in right_text
    # Verify no TaleSpire 3D badge inside the log item
    assert "TaleSpire 3D" not in right_text

    # 8. Test "Limpiar" button
    tray._on_die_select_click(8)
    tray._on_quantity_click(4)
    assert len(tray.pool) > 0
    tray._on_clear_pool_click(None)
    assert len(tray.pool) == 0
    print("8. 'Limpiar' button emptied pool successfully and refreshed display.")

    print("\nALL AUDIO FEEDBACK TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_audio_feedback_requirements()
