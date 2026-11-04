#!/usr/bin/env python3
"""
CLI Script de Ingesta del Compendio D&D 5.5e (2024 PHB / SRD) para Parma Character Hub.
Permite ingestar archivos JSON de monstruos, conjuros y objetos (5etools o Foundry)
directamente en la base de datos relacional SQLite de la aplicación.
"""
import os
import sys
import argparse
from pathlib import Path

# Añadir raíz del proyecto al sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from core.paths import get_default_db_path
from core.db import DatabaseManager
from core.compendium_importer import CompendiumImporter


def main():
    parser = argparse.ArgumentParser(description="Ingesta de compendio D&D 5.5e a SQLite relacional.")
    parser.add_argument("--db", default=None, help="Ruta a characters.db (por defecto usa la del sistema)")
    parser.add_argument("--monsters", help="Ruta al archivo JSON de monstruos/bestiario (bestiary-xphb.json)")
    parser.add_argument("--spells", help="Ruta al archivo JSON de conjuros (spells-xphb.json)")
    parser.add_argument("--items", help="Ruta al archivo JSON de equipo/armas (items.json)")
    parser.add_argument("--edition", default="5.5e", help="Edición (5.5e o 5e)")
    parser.add_argument("--lang", default="en", help="Idioma (en o es)")

    args = parser.parse_args()

    db_path = args.db or get_default_db_path()
    print(f"[Compendium Ingest] Conectando a SQLite: {db_path}")
    db = DatabaseManager(db_path=db_path)
    importer = CompendiumImporter(db)

    total_ingested = 0

    if args.monsters:
        print(f"[Compendium Ingest] Ingestando monstruos desde {args.monsters}...")
        cnt = importer.ingest_from_json_file(args.monsters, category="monsters", edition=args.edition, lang=args.lang)
        print(f"[Compendium Ingest] ✓ {cnt} monstruos ingestados/actualizados.")
        total_ingested += cnt

    if args.spells:
        print(f"[Compendium Ingest] Ingestando conjuros desde {args.spells}...")
        cnt = importer.ingest_from_json_file(args.spells, category="spells", edition=args.edition, lang=args.lang)
        print(f"[Compendium Ingest] ✓ {cnt} conjuros ingestados/actualizados.")
        total_ingested += cnt

    if args.items:
        print(f"[Compendium Ingest] Ingestando equipo/armas desde {args.items}...")
        cnt = importer.ingest_from_json_file(args.items, category="items", edition=args.edition, lang=args.lang)
        print(f"[Compendium Ingest] ✓ {cnt} ítems/armas ingestados/actualizados.")
        total_ingested += cnt

    print(f"\n[Compendium Ingest] Operación finalizada. Total registros procesados: {total_ingested}")


if __name__ == "__main__":
    main()
