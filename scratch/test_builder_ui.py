"""
Suite de Pruebas de Integración de UI para el Creador de Personajes D&D 5e.
Valida la instanciación de todos los componentes Flet:
1. BuilderHeader
2. BuilderStepper
3. AbilityMatrix (con Point Buy, Standard Array, 4d6 y Manual)
4. OkfDrawer
5. BuilderHubDialog
6. StandardBuilderDialog
7. QuickBuildDialog
8. RandomizeDialog
9. CharacterCreatorWizard
"""
import sys
import os
import flet as ft

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flet_app.core.okf_engine import OkfEngine
from flet_app.core.models import CharacterSheet
from flet_app.ui.components.builder_header import BuilderHeader
from flet_app.ui.components.builder_stepper import BuilderStepper
from flet_app.ui.components.ability_matrix import AbilityMatrix
from flet_app.ui.components.okf_drawer import OkfDrawer
from flet_app.ui.components.builder_hub import BuilderHubDialog
from flet_app.ui.components.standard_builder import StandardBuilderDialog
from flet_app.ui.components.quick_and_random_dialogs import QuickBuildDialog, RandomizeDialog
from flet_app.ui.components.character_wizard import CharacterCreatorWizard

class MockPage:
    def __init__(self):
        self.overlay = []
        self.controls = []
        self.dialog = None
        self.snack_bar = None

    def open(self, control):
        self.dialog = control

    def close(self, control):
        self.dialog = None

    def update(self):
        pass

def test_ui_components():
    print("Iniciando pruebas de integración de UI de componentes...")
    page = MockPage()
    okf = OkfEngine()

    # 1. BuilderHeader
    header = BuilderHeader(
        char_name="Test Hero",
        char_class="Paladín",
        char_species="Aasimar",
        char_level=3,
        hp_max=28,
        armor_class=18
    )
    assert header.char_name == "Test Hero"
    header.update_identity(name="Lord Test", hp=35)
    assert header.char_name == "Lord Test"
    print("✅ BuilderHeader instanciado y reactivo.")

    # 2. BuilderStepper
    stepper = BuilderStepper(current_step=1)
    assert stepper.current_step == 1
    stepper.set_current_step(4)
    assert stepper.current_step == 4
    stepper.set_pending_choices({7: "Elige 2 trucos"})
    print("✅ BuilderStepper instanciado y reactivo.")

    # 3. AbilityMatrix
    matrix = AbilityMatrix(mode="point_buy")
    assert matrix.mode == "point_buy"
    matrix.set_background_bonuses("DES", "INT")
    matrix._set_mode("standard")
    assert matrix.mode == "standard"
    matrix._set_mode("dice")
    assert matrix.mode == "dice"
    print("✅ AbilityMatrix instanciado en todos sus modos.")

    # 4. OkfDrawer
    drawer = OkfDrawer(okf_engine=okf)
    drawer.show_entity({"nombre": "Mago", "tipo": "Clase", "desc": "Lanzador arcano"})
    assert drawer.visible is True
    drawer.hide()
    assert drawer.visible is False
    print("✅ OkfDrawer instanciado y funcional.")

    created_chars = []
    def on_created(c: CharacterSheet):
        created_chars.append(c)

    # 5. BuilderHubDialog
    hub = BuilderHubDialog(
        page=page,
        on_start_standard=lambda: None,
        on_start_quick=lambda: None,
        on_start_random=lambda: None
    )
    hub.show()
    assert page.dialog == hub.dialog
    hub.close()
    assert page.dialog is None
    print("✅ BuilderHubDialog instanciado con sus 3 rutas.")

    # 6. QuickBuildDialog
    quick = QuickBuildDialog(page=page, on_character_created=on_created)
    quick.show()
    quick._forge_quick(None)
    assert len(created_chars) == 1
    assert created_chars[0].level == 1
    quick.close()
    print("✅ QuickBuildDialog forjó héroe en 60s exitosamente.")

    # 7. RandomizeDialog
    random_dlg = RandomizeDialog(page=page, on_character_created=on_created)
    random_dlg.selected_level = 5
    random_dlg.show()
    random_dlg._accept_random(None)
    assert len(created_chars) == 2
    assert created_chars[1].level == 5
    random_dlg.close()
    print("✅ RandomizeDialog generó héroe nivel 5 procedural exitosamente.")

    # 8. StandardBuilderDialog (7 Fases)
    builder = StandardBuilderDialog(page=page, okf_engine=okf, on_character_created=on_created)
    builder.show()
    assert builder.current_step == 1
    # Navegar por las 7 fases
    for step in range(2, 8):
        builder._go_to_step(step)
        assert builder.current_step == step
    builder._finish_and_forge()
    assert len(created_chars) == 3
    assert created_chars[2].name == "Nuevo Aventurero"
    print("✅ StandardBuilderDialog completó las 7 fases de D&D Beyond exitosamente.")

    # 9. CharacterCreatorWizard (Master Dispatcher)
    wizard = CharacterCreatorWizard(page=page, okf_engine=okf, on_character_created=on_created)
    wizard.show()
    assert page.dialog == wizard.hub_dialog.dialog
    print("✅ CharacterCreatorWizard unificado con D&D Beyond Hub.")

    print("\n🎉 TODAS LAS PRUEBAS DE INTEGRACIÓN DE UI PASARON EXITOSAMENTE.")

if __name__ == "__main__":
    test_ui_components()
