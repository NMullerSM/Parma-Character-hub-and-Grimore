"""
Módulo de Ingestión y Normalización de Datos SRD 5e (Open Knowledge Format - OKF).
Descarga y transforma entidades desde el repositorio oficial 5e-bits/5e-srd-api (2024 & 2014)
y AideDD en tarjetas Markdown atómicas (~1KB) con YAML Frontmatter.
"""
import os
import sys
import json
import re
import urllib.request
from typing import Dict, List, Any, Optional
from pathlib import Path


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OKF_DIR = os.path.join(BASE_DIR, "okf_dnd5e")
INDEX_PATH = os.path.join(OKF_DIR, "index_metadata.json")

# URLs del repositorio 5e-bits monorepo (GitHub raw)
RAW_GITHUB_BASE = "https://raw.githubusercontent.com/5e-bits/5e-srd-api/main/packages/5e-database/src"

TRADUCCION_ESCUELAS = {
    "abjuration": "Abjuración",
    "conjuration": "Conjuración",
    "divination": "Adivinación",
    "enchantment": "Encantamiento",
    "evocation": "Evocación",
    "illusion": "Ilusionismo",
    "necromancy": "Nigromancia",
    "transmutation": "Transmutación",
}

TRADUCCION_CLASES = {
    "barbarian": "Bárbaro",
    "bard": "Bardo",
    "cleric": "Clérigo",
    "druid": "Druida",
    "fighter": "Guerrero",
    "monk": "Monje",
    "paladin": "Paladín",
    "ranger": "Explorador",
    "rogue": "Pícaro",
    "sorcerer": "Hechicero",
    "warlock": "Brujo",
    "wizard": "Mago",
    "artificer": "Artífice",
}


class SrdImporter:
    """Importador y generador de tarjetas atómicas OKF de ~1KB."""

    def __init__(self, okf_root: Optional[str] = None):
        self.okf_root = okf_root or OKF_DIR
        os.makedirs(self.okf_root, exist_ok=True)

    def fetch_json_from_github(self, relative_path: str) -> Optional[List[Dict[str, Any]]]:
        """Descarga un fichero JSON desde GitHub de 5e-database."""
        url = f"{RAW_GITHUB_BASE}/{relative_path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "D&D Sanctum Importer"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, list) else data.get("results", [])
        except Exception as e:
            print(f"[SrdImporter] Error al descargar {url}: {e}")
            return None

    def generate_spell_card(self, spell_data: Dict[str, Any], edition: str = "PHB 2024") -> Dict[str, Any]:
        """Convierte una entidad de conjuro de 5e-srd-api en una tarjeta atómica OKF ~1KB."""
        index_key = spell_data.get("index", "")
        name_en = spell_data.get("name", "")
        level = int(spell_data.get("level", 0))

        school_data = spell_data.get("school")
        school_name = school_data.get("name", "Evocation") if isinstance(school_data, dict) else str(school_data)
        school_es = TRADUCCION_ESCUELAS.get(school_name.lower(), school_name)

        classes_list = []
        for c in spell_data.get("classes", []):
            c_name = c.get("name", "") if isinstance(c, dict) else str(c)
            classes_list.append(TRADUCCION_CLASES.get(c_name.lower(), c_name))

        casting_time = spell_data.get("casting_time", "1 action")
        casting_time_es = (
            casting_time.replace("1 bonus action", "1 acción adicional")
            .replace("1 action", "1 acción")
            .replace("1 reaction", "1 reacción")
        )

        range_val = spell_data.get("range", "60 feet")
        range_es = (
            range_val.replace("Self", "Personal")
            .replace("Touch", "Toque")
            .replace("feet", "pies")
            .replace("foot", "pies")
        )

        components_arr = spell_data.get("components", ["V", "S"])
        comp_str = ", ".join(components_arr)
        if spell_data.get("material"):
            comp_str += f" ({spell_data.get('material')})"

        duration = spell_data.get("duration", "Instantaneous")
        concentration = bool(spell_data.get("concentration", False))
        ritual = bool(spell_data.get("ritual", False))

        desc_list = spell_data.get("desc", [])
        body_text = "\n\n".join(desc_list) if isinstance(desc_list, list) else str(desc_list)

        higher_list = spell_data.get("higher_level", [])
        higher_text = "\n\n".join(higher_list) if isinstance(higher_list, list) else str(higher_list)

        slug = index_key.replace("-", "_").lower()
        if level == 0:
            target_dir = os.path.join(self.okf_root, "conjuros", "nivel_0_trucos")
            rel_path = f"conjuros/nivel_0_trucos/{slug}.md"
        else:
            target_dir = os.path.join(self.okf_root, "conjuros", f"nivel_{level}")
            rel_path = f"conjuros/nivel_{level}/{slug}.md"

        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(self.okf_root, rel_path)

        tags = [
            school_es.lower(),
            f"nivel_{level}",
            *[c.lower() for c in classes_list],
        ]
        if concentration:
            tags.append("concentracion")
        if ritual:
            tags.append("ritual")

        frontmatter = {
            "id": slug,
            "nombre": name_en,
            "nombre_ingles": name_en,
            "nivel": level,
            "escuela": school_es,
            "clases": classes_list,
            "tiempo_lanzamiento": casting_time_es,
            "alcance": range_es,
            "componentes": comp_str,
            "duracion": duration,
            "concentracion": concentration,
            "ritual": ritual,
            "fuente": edition,
            "tags": tags,
        }

        # Generar contenido Markdown (~1KB)
        md_lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                md_lines.append(f"{k}:")
                for item in v:
                    md_lines.append(f"  - \"{item}\"")
            elif isinstance(v, bool):
                md_lines.append(f"{k}: {'true' if v else 'false'}")
            elif isinstance(v, int):
                md_lines.append(f"{k}: {v}")
            else:
                clean_v = str(v).replace('"', '\\"')
                md_lines.append(f'{k}: "{clean_v}"')
        md_lines.append("---\n")
        md_lines.append(f"# {name_en}\n")
        md_lines.append(body_text)
        if higher_text:
            md_lines.append(f"\n\n### En Niveles Superiores\n{higher_text}")

        content = "\n".join(md_lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "id": slug,
            "nombre": name_en,
            "nombre_ingles": name_en,
            "tipo": "conjuro",
            "nivel": level,
            "escuela": school_es,
            "clases": classes_list,
            "fuente": edition,
            "tags": tags,
            "path": rel_path,
        }

    def rebuild_master_index(self) -> int:
        """Escanea todos los archivos Markdown de okf_dnd5e y reconstruye index_metadata.json."""
        entities = []
        for root, _, files in os.walk(self.okf_root):
            for file in files:
                if not file.endswith(".md") or file.upper() == "README.MD":
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.okf_root).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml
                            meta = yaml.safe_load(parts[1])
                            # Determinar tipo canónico de entidad OKF
                            tipo = meta.get("tipo")
                            if not tipo:
                                if "conjuros" in rel_path:
                                    tipo = "conjuro"
                                elif "dotes" in rel_path:
                                    tipo = "dote"
                                elif "subclases" in rel_path:
                                    tipo = "subclase"
                                elif "clases" in rel_path:
                                    tipo = "clase"
                                elif "especies" in rel_path:
                                    tipo = "especie"
                                elif "linajes" in rel_path:
                                    tipo = "linaje"
                                elif "trasfondos" in rel_path:
                                    tipo = "trasfondo"
                                elif "equipo" in rel_path:
                                    tipo = "equipo"
                                else:
                                    tipo = "regla"

                            entry = {
                                "id": meta.get("id", Path(file).stem),
                                "nombre": meta.get("nombre", Path(file).stem.replace("_", " ").title()),
                                "nombre_ingles": meta.get("nombre_ingles", meta.get("nombre", "")),
                                "tipo": tipo,
                                "nivel": meta.get("nivel"),
                                "escuela": meta.get("escuela"),
                                "clases": meta.get("clases", []),
                                "fuente": meta.get("fuente", "PHB 2024"),
                                "tags": meta.get("tags", []),
                                "path": rel_path,
                            }
                            if "dote_concedida" in meta:
                                entry["dote_concedida"] = meta["dote_concedida"]
                            if "caracteristicas_clave" in meta:
                                entry["caracteristicas_clave"] = meta["caracteristicas_clave"]
                            if "habilidades_competentes" in meta:
                                entry["habilidades_competentes"] = meta["habilidades_competentes"]
                            if "dado_golpe" in meta:
                                entry["dado_golpe"] = meta["dado_golpe"]
                            if "tiempo_lanzamiento" in meta:
                                entry["tiempo_lanzamiento"] = meta["tiempo_lanzamiento"]
                            if "alcance" in meta:
                                entry["alcance"] = meta["alcance"]
                            if "duracion" in meta:
                                entry["duracion"] = meta["duracion"]
                            if "concentracion" in meta:
                                entry["concentracion"] = meta["concentracion"]
                            if "ritual" in meta:
                                entry["ritual"] = meta["ritual"]

                            entities.append(entry)
                except Exception as e:
                    print(f"[SrdImporter] Error al procesar {rel_path}: {e}")

        # Guardar en index_metadata.json
        index_data = {
            "version": "2.0.0",
            "total_entities": len(entities),
            "entities": entities,
        }
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"[SrdImporter] Índice reconstruido con {len(entities)} entidades.")
        return len(entities)


if __name__ == "__main__":
    importer = SrdImporter()
    count = importer.rebuild_master_index()
    print(f"Indexación finalizada: {count} entidades.")
