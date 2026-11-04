#!/usr/bin/env python3
"""
CLI Script de Ingesta del Compendio D&D (2024 PHB / SRD 5.2 y 2014 SRD 5.1) para Parma Character Hub.
Permite ingestar archivos JSON (5etools) y paquetes YAML oficiales de Foundry VTT SRD dnd5e
directamente en la base de datos relacional SQLite de la aplicación.
Soporte bilingüe completo (ES + EN) y etiquetado por edición.
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
    parser = argparse.ArgumentParser(description="Ingesta de compendio D&D a SQLite relacional.")
    parser.add_argument("--db", default=None, help="Ruta a characters.db (por defecto usa la del sistema)")
    parser.add_argument("--foundry-packs", default=None, help="Ruta a la carpeta packs/_source del repositorio foundryvtt/dnd5e")
    parser.add_argument("--okf-entities", action="store_true", help="Ingestar entidades OKF (clases, especies, etc.) a compendium_entities")
    parser.add_argument("--monsters", help="Ruta al archivo JSON de monstruos/bestiario (5etools/plano)")
    parser.add_argument("--spells", help="Ruta al archivo JSON de conjuros (5etools/plano)")
    parser.add_argument("--items", help="Ruta al archivo JSON de equipo/armas (5etools/plano)")
    parser.add_argument("--edition", default="5.5e", help="Edición (5.5e o 5e)")
    parser.add_argument("--lang", default="en", help="Idioma (en o es)")
    parser.add_argument("--no-bilingual", action="store_true", help="Desactivar generación bilingüe automática en paquetes Foundry")

    args = parser.parse_args()

    db_path = args.db or get_default_db_path()
    print(f"[Compendium Ingest] Conectando a SQLite: {db_path}")
    db = DatabaseManager(db_path=db_path)
    importer = CompendiumImporter(db)

    total_ingested = 0

    if args.foundry_packs:
        print(f"[Compendium Ingest] Ingestando paquetes Foundry VTT desde: {args.foundry_packs}")
        bilingue = not args.no_bilingual
        results = importer.ingest_all_foundry_packs(args.foundry_packs, bilingue=bilingue)
        for k, v in results.items():
            print(f"[Compendium Ingest] ✓ {k}: {v} filas generadas.")
            total_ingested += v

    if args.okf_entities and not args.foundry_packs:
        print(f"[Compendium Ingest] Ingestando entidades OKF (clases, especies, trasfondos, dotes, reglas)...")
        cnt = importer.ingest_okf_entities()
        print(f"[Compendium Ingest] ✓ {cnt} entidades OKF ingestadas.")
        total_ingested += cnt

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
    print(f"[Compendium Ingest] Conteos actuales en BD:")
    print(f"  - Monstruos: {db.count_compendium_entries('monsters')}")
    print(f"  - Conjuros:  {db.count_compendium_entries('spells')}")
    print(f"  - Equipo:    {db.count_compendium_entries('items')}")
    print(f"  - Entidades: {db.count_compendium_entries('entities')}")


if __name__ == "__main__":
    main()
