"""
Test suite de validación automatizada para Fase 4:
Flujos de Importación/Exportación (JSON individual & AcroForm PDF Oficial)
"""
import sys
import os
import json

# Asegurar path al root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flet_app.core.models import CharacterSheet, WeaponAction, SpellItem, CharacterFeature
from flet_app.core.db import DatabaseManager
from flet_app.core.pdf_engine import UniversalAcroFormHandler

def test_phase4_export_import():
    print("=== TEST FASE 4: Importación / Exportación JSON & PDF Oficial ===")
    
    # 1. Crear personaje de prueba complejo
    char = CharacterSheet(
        name="Elminster de Shadowdale",
        char_class="Mago",
        subclass="Evocador",
        level=5,
        race="Humano",
        background="Sabio",
        alignment="Caótico Bueno",
        senses="Visión Normal (Luz de Antorcha)",
        hp_current=32,
        hp_max=32,
        hp_temp=5,
        hit_dice_max=5,
        hit_dice_current=4,
        hit_dice_faces=6,
        armor_class=15,
        speed="9 m",
        proficiency_bonus=3,
        abilities={"FUE": 10, "DES": 14, "CON": 14, "INT": 18, "SAB": 14, "CAR": 12},
        saving_throw_profs=["INT", "SAB"],
        skills={"Arcanos": "expert", "Historia": "proficient", "Investigación": "proficient"},
        weapons=[
            WeaponAction(name="Bastón Arcano", attack_bonus="+3", damage="1d6", damage_type="Contundente", notes="Foco arcano")
        ],
        spells=[
            SpellItem(id="bola_fuego", name="Bola de Fuego", level=3, school="Evocación", casting_time="1 acción", range="45 m", description="Explosión de 8d6 fuego.")
        ],
        features=[
            CharacterFeature(name="Recuperación Arcana", source="Mago", uses_max=1, uses_current=1, recharge="Largo", description="Recupera espacios de conjuro en descanso corto.")
        ],
        conditions=["Concentración"]
    )

    # 2. Test Exportación JSON
    export_json_path = "data/characters/test_elminster_export.json"
    with open(export_json_path, "w", encoding="utf-8") as f:
        json.dump(char.to_dict(), f, indent=2, ensure_ascii=False)
    
    assert os.path.exists(export_json_path), "Fallo al crear archivo JSON exportado"
    print(f"  [Pass] Archivo JSON exportado exitosamente ({os.path.getsize(export_json_path)} bytes).")

    # 3. Test Importación JSON
    with open(export_json_path, "r", encoding="utf-8") as f:
        imported_data = json.load(f)
    
    imported_char = CharacterSheet.from_dict(imported_data)
    assert imported_char.name == "Elminster de Shadowdale"
    assert imported_char.char_class == "Mago"
    assert imported_char.level == 5
    assert imported_char.abilities["INT"] == 18
    assert imported_char.hit_dice_faces == 6
    assert imported_char.hit_dice_current == 4
    assert "Concentración" in imported_char.conditions
    assert len(imported_char.spells) == 1
    assert imported_char.spells[0].name == "Bola de Fuego"
    print("  [Pass] Integridad de datos JSON importados 100% verificada.")

    # 4. Test Persistencia en SQLite
    db = DatabaseManager()
    cid = db.save_character(imported_char, set_active=False)
    assert cid > 0, "Fallo al guardar personaje importado en base de datos"
    
    saved_char = db.get_character_by_id(cid)
    assert saved_char is not None, f"No se pudo recuperar personaje con id {cid}"
    assert saved_char.name == "Elminster de Shadowdale"
    assert saved_char.abilities["INT"] == 18
    print(f"  [Pass] Personaje persistido en SQLite y recuperado con get_character_by_id (ID: {cid}).")

    # Limpiar personaje de prueba de la BD
    db.delete_character(cid)
    assert db.get_character_by_id(cid) is None
    print("  [Pass] Limpieza de registro de prueba en SQLite confirmada.")

    # Limpiar archivo JSON de prueba
    if os.path.exists(export_json_path):
        os.remove(export_json_path)

    # 5. Test Exportación AcroForm PDF Oficial
    template_pdf = "data/characters/Artanis LVL 4.pdf"
    export_pdf_path = "data/characters/test_elminster_export.pdf"
    
    assert os.path.exists(template_pdf), f"No existe la plantilla de prueba {template_pdf}"
    generated_pdf = UniversalAcroFormHandler.export_character_to_pdf(
        char=char,
        template_pdf_path=template_pdf,
        output_path=export_pdf_path
    )
    assert os.path.exists(generated_pdf), "El PDF exportado no fue generado en disco"
    assert os.path.getsize(generated_pdf) > 10000, "El PDF exportado parece estar corrupto o vacío"
    print(f"  [Pass] PDF Oficial generado exitosamente ({os.path.getsize(generated_pdf)} bytes).")

    # 6. Test Lectura de Formulario del PDF Generado
    loaded_from_pdf = UniversalAcroFormHandler.load_character_from_pdf(generated_pdf)
    assert "Elminster" in loaded_from_pdf.name, f"Nombre inesperado en PDF: {loaded_from_pdf.name}"
    assert loaded_from_pdf.char_class == "Mago"
    assert loaded_from_pdf.level == 5
    assert loaded_from_pdf.armor_class == 15
    assert loaded_from_pdf.hp_max == 32
    assert loaded_from_pdf.abilities["INT"] == 18
    assert loaded_from_pdf.abilities["DES"] == 14
    print(f"  [Pass] Lectura inversa del PDF generado verificada: {loaded_from_pdf.name}, {loaded_from_pdf.char_class} {loaded_from_pdf.level}, INT: {loaded_from_pdf.abilities['INT']}.")

    # Limpiar archivo PDF de prueba
    if os.path.exists(export_pdf_path):
        os.remove(export_pdf_path)

    print("\nTODOS LOS TESTS DE LA FASE 4 PASARON SATISFACTORIAMENTE!\n")

if __name__ == "__main__":
    test_phase4_export_import()
