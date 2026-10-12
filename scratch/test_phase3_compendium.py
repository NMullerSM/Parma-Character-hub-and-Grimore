"""
Test suite de validación para Fase 3:
Expansión del Compendio OKF (Equipamiento, Armamento, Condiciones y Acciones)
"""
import sys
import os

# Ajustar path al root del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flet_app.core.models import CharacterSheet
from flet_app.core.okf_engine import OkfEngine
from flet_app.ui.views.okf_view import OkfCompendiumView

def test_phase3_compendium():
    print("=== TEST FASE 3: Compendio OKF (Equipamiento & Reglas) ===")
    okf = OkfEngine()
    assert len(okf._index) == 513, f"Esperados 513 items en el índice, obtenidos {len(okf._index)}"
    print(f"  [Pass] Índice maestro contiene {len(okf._index)} entidades OKF.")

    # 1. Contadores dinámicos
    conjuros_cnt = okf.count_entities("conjuro")
    dotes_cnt = okf.count_entities("dote")
    especies_cnt = okf.count_entities(["especie", "linaje"])
    trasfondos_cnt = okf.count_entities("trasfondo")
    clases_cnt = okf.count_entities(["clase", "subclase"])
    equipo_cnt = okf.count_entities(["equipo", "arma", "armadura"])
    reglas_cnt = okf.count_entities("regla")

    assert conjuros_cnt == 378, f"Esperados 378 conjuros, obtenidos {conjuros_cnt}"
    assert dotes_cnt == 74, f"Esperados 74 dotes, obtenidos {dotes_cnt}"
    assert especies_cnt == 23, f"Esperadas 23 especies/linajes, obtenidas {especies_cnt}"
    assert trasfondos_cnt == 17, f"Esperados 17 trasfondos, obtenidos {trasfondos_cnt}"
    assert clases_cnt == 13, f"Esperadas 13 clases/subclases, obtenidas {clases_cnt}"
    assert equipo_cnt == 4, f"Esperados 4 grupos de equipo, obtenidos {equipo_cnt}"
    assert reglas_cnt == 4, f"Esperados 4 documentos de reglas, obtenidos {reglas_cnt}"
    print(f"  [Pass] Conteo dinámico verificado por taxonomía:")
    print(f"         Conjuros: {conjuros_cnt} | Dotes: {dotes_cnt} | Especies: {especies_cnt}")
    print(f"         Trasfondos: {trasfondos_cnt} | Clases: {clases_cnt} | Equipo: {equipo_cnt} | Reglas: {reglas_cnt}")

    # 2. Lectura atómica de archivos Markdown con Frontmatter
    files_to_test = [
        "equipo_y_armamento/armas_simples.md",
        "equipo_y_armamento/armas_marciales.md",
        "equipo_y_armamento/armaduras_y_escudos.md",
        "equipo_y_armamento/equipo_de_aventuras.md",
        "reglas_y_mecanicas/condiciones_de_estado.md",
        "reglas_y_mecanicas/acciones_en_combate.md"
    ]

    for rel_path in files_to_test:
        parsed = okf.read_entity_file(rel_path)
        assert parsed is not None, f"Fallo al leer {rel_path}"
        assert "body_markdown" in parsed and len(parsed["body_markdown"]) > 50, f"Markdown body vacío en {rel_path}"
        assert "nombre" in parsed or "id" in parsed, f"Falta 'nombre' o 'id' en frontmatter de {rel_path}"
        print(f"  [Pass] Archivo atómico verificado: {rel_path} ({len(parsed['body_markdown'])} chars)")

    # 3. Búsquedas específicas por texto
    res_espada = okf.search_entities(query="marcial", tipo=["equipo", "arma", "armadura"])
    assert len(res_espada) > 0, "No se encontró arma marcial con búsqueda 'marcial'"
    print(f"  [Pass] Búsqueda de equipo por término 'marcial' retornó: {[r['nombre'] for r in res_espada]}")

    res_cond = okf.search_entities(query="condiciones", tipo="regla")
    assert len(res_cond) > 0, "No se encontró 'condiciones' en reglas"
    print(f"  [Pass] Búsqueda de reglas por término 'condiciones' retornó: {[r['nombre'] for r in res_cond]}")

    # 4. Integración con OkfCompendiumView
    char = CharacterSheet(name="Valeros", char_class="Guerrero", level=3)
    view = OkfCompendiumView(char=char, okf_engine=okf)

    # Validar que los botones de categorías tienen los textos dinámicos
    equipo_btn = view.cat_buttons.get("equipo")
    assert equipo_btn is not None, "Botón de categoría 'equipo' no encontrado"
    assert "Equipo & Armamento (4)" in equipo_btn.text, f"Texto inesperado en botón equipo: {equipo_btn.text}"

    regla_btn = view.cat_buttons.get("regla")
    assert regla_btn is not None, "Botón de categoría 'regla' no encontrado"
    assert "Reglas & Mecánicas (4)" in regla_btn.text, f"Texto inesperado en botón regla: {regla_btn.text}"

    # Simular selección de 'equipo' y 'regla'
    view._select_category("equipo")
    assert len(view.results_cache) == 4, f"Esperados 4 items en vista de equipo, obtenidos {len(view.results_cache)}"
    assert view.selected_item is not None
    assert view.detail_container.content is not None

    view._select_category("regla")
    assert len(view.results_cache) == 4, f"Esperados 4 items en vista de regla, obtenidos {len(view.results_cache)}"
    assert view.selected_item is not None
    assert view.detail_container.content is not None

    print("  [Pass] Integración con UI OkfCompendiumView verificada (chips, selección y detalle).")
    print("\nTODOS LOS TESTS DE LA FASE 3 PASARON SATISFACTORIAMENTE!\n")

if __name__ == "__main__":
    test_phase3_compendium()
