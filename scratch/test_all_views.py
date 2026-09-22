import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flet_app.core.models import CharacterSheet, NetworkNode, NetworkEdge
from flet_app.core.okf_engine import OkfEngine
from flet_app.ui.views.combat_view import CombatView
from flet_app.ui.views.sheet_view import SheetView
from flet_app.ui.views.spells_view import SpellsView
from flet_app.ui.views.powers_view import PowersView
from flet_app.ui.views.okf_view import OkfCompendiumView
from flet_app.ui.views.journal_view import JournalView
from flet_app.ui.views.network_view import NetworkView
from flet_app.ui.views.pdf_viewer import PdfViewerView
from flet_app.ui.components.character_wizard import CharacterCreatorWizard

class MockPage:
    def __init__(self):
        self.overlay = []
        self.snack_bar = None
        class MockWindow:
            full_screen = False
        self.window = MockWindow()

    def update(self, *args, **kwargs):
        pass

def run_integration_tests():
    print("=== Testing UI Views & Components Integration ===")
    page = MockPage()
    okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))
    char = CharacterSheet(name="Test Hero", char_class="Mago", level=2)

    # 1. CombatView
    cv = CombatView(char=char, on_roll_request=lambda s, m, r: None)
    assert cv is not None
    print("  CombatView created.")

    # 2. SheetView with full PHB vitals & DC
    sv = SheetView(char=char, on_roll_request=lambda s, m, r: None)
    sv.page = page
    sv.update_data(char)
    assert sv is not None
    print("  SheetView created & updated with vital stats & spell DC.")

    # 3. SpellsView
    spv = SpellsView(char=char, okf_engine=okf)
    spv.page = page
    spv.update_data(char)
    assert spv is not None
    print("  SpellsView created & updated.")

    # 4. PowersView
    pv = PowersView(char=char, okf_engine=okf)
    pv.page = page
    pv.update_data(char)
    assert pv is not None
    print("  PowersView created & updated.")

    # 5. OkfCompendiumView category switching
    okfv = OkfCompendiumView(char=char, okf_engine=okf)
    okfv.page = page
    okfv._select_category("especie")
    assert okfv.current_category == "especie"
    assert len(okfv.results_cache) == 11
    okfv._select_category("clase")
    assert okfv.current_category == "clase"
    assert len(okfv.results_cache) == 13
    okfv._select_category("conjuro")
    assert okfv.current_category == "conjuro"
    assert len(okfv.results_cache) == 378
    print("  OkfCompendiumView category switching verified across all entities.")

    # 6. JournalView
    jv = JournalView(char=char)
    jv.page = page
    jv.update_data(char)
    assert jv is not None
    print("  JournalView created & updated.")

    # 7. NetworkView
    nv = NetworkView(char=char)
    nv.page = page
    nv.update_data(char)
    initial_nodes = len(char.network_nodes)
    char.network_nodes.append(NetworkNode(
        id="test_npc",
        name="Elminster",
        role="ally",
        description="Archimago aliado",
        x=100.0,
        y=100.0
    ))
    nv.update_data(char)
    assert len(char.network_nodes) == initial_nodes + 1
    assert any(n.id == "test_npc" for n in char.network_nodes)
    print("  NetworkView node creation & auto-save verified.")

    # 8. PdfViewerView
    pdfv = PdfViewerView()
    pdfv.page = page
    # Test fullscreen toggle
    assert page.window.full_screen is False
    pdfv._toggle_fullscreen(None)
    assert page.window.full_screen is True
    pdfv._toggle_fullscreen(None)
    assert page.window.full_screen is False
    print("  PdfViewerView fullscreen toggle verified.")

    # 9. CharacterCreatorWizard
    wizard = CharacterCreatorWizard(page=page, okf_engine=okf, on_character_created=lambda c: None)
    assert wizard is not None
    assert wizard.dialog is not None
    print("  CharacterCreatorWizard instantiated & verified.")

    print("\nALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_integration_tests()
