"""
Motor de Conocimiento Atómico OKF (Open Knowledge Format) para D&D 5e
Lectura y búsqueda eficiente de alta velocidad con caché LRU y bajo consumo de RAM.
"""
import os
import sys
import json
import yaml
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union
from .models import SpellItem


class OkfEngine:
    def __init__(self, okf_root_path: Optional[str] = None):
        if okf_root_path is None:
            # Detectar automáticamente relativo al repo o bundle congelado
            if getattr(sys, "frozen", False):
                base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.okf_dir = os.path.join(base_dir, "okf_dnd5e")
        else:
            self.okf_dir = okf_root_path

        self._index: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        """Carga el índice precalculado JSON en memoria para búsquedas instantáneas."""
        idx_path = os.path.join(self.okf_dir, "index_metadata.json")
        if os.path.exists(idx_path):
            try:
                with open(idx_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "entities" in data:
                        self._index = data["entities"]
                    elif isinstance(data, list):
                        self._index = data
                    else:
                        self._index = []
            except Exception as e:
                print(f"[OkfEngine] Error al cargar índice: {e}")
                self._index = []
        else:
            self._index = []

    def search_entities(
        self,
        query: str = "",
        tipo: Optional[Union[str, List[str]]] = None,
        nivel: Optional[int] = None,
        clase: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Búsqueda ultrarrápida en memoria sobre el índice precalculado."""
        q = query.lower().strip()
        results = []

        for item in self._index:
            if tipo:
                item_tipo = item.get("tipo")
                if isinstance(tipo, list):
                    if item_tipo not in tipo:
                        continue
                elif item_tipo != tipo:
                    continue

            if nivel is not None:
                item_lvl = item.get("nivel")
                if item_lvl is None or int(item_lvl) != nivel:
                    continue

            if clase and clase != "all":
                item_classes = item.get("clases", [])
                if not any(clase.lower() == str(c).lower() for c in item_classes):
                    continue

            if q:
                nombre = item.get("nombre", "").lower()
                nombre_en = item.get("nombre_ingles", "").lower()
                escuela = item.get("escuela", "").lower()
                tags = [t.lower() for t in item.get("tags", [])]

                match = (
                    q in nombre
                    or q in nombre_en
                    or q in escuela
                    or any(q in t for t in tags)
                )
                if not match:
                    continue

            results.append(item)
            if len(results) >= limit:
                break

        return results

    @lru_cache(maxsize=128)
    def read_entity_file(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """Lee y parsea bajo demanda un archivo atómico Markdown con frontmatter YAML."""
        full_path = os.path.join(self.okf_dir, rel_path)
        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    markdown_body = parts[2].strip()
                    frontmatter["body_markdown"] = markdown_body
                    return frontmatter

            return {"body_markdown": content}
        except Exception as e:
            print(f"[OkfEngine] Error al leer {rel_path}: {e}")
            return None

    def get_spell_item(self, entity_id: str) -> Optional[SpellItem]:
        """Transforma una entidad de conjuro OKF en un objeto SpellItem listo para la ficha."""
        entity_meta = next((e for e in self._index if e.get("id") == entity_id), None)
        if not entity_meta:
            return None

        file_path = entity_meta.get("path")
        full_data = self.read_entity_file(file_path) if file_path else None
        data = full_data or entity_meta

        return SpellItem(
            id=data.get("id", entity_id),
            name=data.get("nombre", entity_meta.get("nombre", "")),
            name_en=data.get("nombre_ingles", entity_meta.get("nombre_ingles", "")),
            level=int(data.get("nivel", entity_meta.get("nivel", 0))),
            school=data.get("escuela", entity_meta.get("escuela", "Evocación")),
            casting_time=data.get("tiempo_lanzamiento", "1 acción"),
            range=data.get("alcance", "18 m"),
            components=data.get("componentes", "V, S"),
            duration=data.get("duracion", "Instantáneo"),
            concentration=bool(data.get("concentracion", False)),
            ritual=bool(data.get("ritual", False)),
            description=data.get("descripcion", data.get("body_markdown", "")),
            higher_levels=data.get("niveles_superiores", ""),
            source=data.get("fuente", entity_meta.get("fuente", "PHB 2024")),
            classes=data.get("clases", entity_meta.get("clases", []))
        )
