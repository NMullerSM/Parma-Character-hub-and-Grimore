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
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

    def count_entities(self, tipo: Optional[Union[str, List[str]]] = None) -> int:
        """Devuelve el conteo rápido de entidades según el tipo o lista de tipos."""
        if not tipo:
            return len(self._index)
        if isinstance(tipo, list):
            return sum(1 for item in self._index if item.get("tipo") in tipo)
        return sum(1 for item in self._index if item.get("tipo") == tipo)

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

    # ==========================================
    # MÉTODOS REACTIVOS PARA CONSTRUCTOR DE PJ
    # ==========================================

    @staticmethod
    def _normalize_source_key(source_str: Optional[str]) -> str:
        """Normaliza cadenas de fuentes a identificadores canónicos para filtrado."""
        if not source_str:
            return ""
        s = source_str.lower().strip()
        if "2024" in s:
            return "phb2024"
        if "2014" in s or "legacy" in s:
            return "phb2014"
        if "tasha" in s or "tce" in s or "caldero" in s:
            return "tasha"
        if "xanathar" in s or "xge" in s or "guia" in s or "guía" in s:
            return "xanathar"
        return s

    def _source_matches(
        self,
        entity_fuente: Optional[str],
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> bool:
        """Verifica si la fuente de una entidad está permitida según la configuración activa."""
        if not allowed_sources:
            return True

        normalized_allowed = {self._normalize_source_key(src) for src in allowed_sources if src}
        # Si la lista contiene "all" o está vacía tras filtrar, permitir todo
        if "all" in normalized_allowed or not normalized_allowed:
            return True

        canonical_entity = self._normalize_source_key(entity_fuente)
        return canonical_entity in normalized_allowed

    def get_species(
        self,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve la lista reactiva de especies oficiales disponibles en OKF."""
        species_list = []
        for item in self._index:
            if item.get("tipo") == "especie":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue
                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                traits_raw = data.get("rasgos_principales", [])
                if isinstance(traits_raw, list):
                    traits_str = ", ".join(traits_raw)
                else:
                    traits_str = str(traits_raw)

                species_list.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "tipo_criatura": data.get("tipo_criatura", "humanoide"),
                    "tamano": data.get("tamano", "Mediano"),
                    "velocidad": data.get("velocidad", "9 m"),
                    "sentidos": data.get("sentidos", "Normal"),
                    "darkvision": "oscuridad" in str(data.get("sentidos", "")).lower(),
                    "rasgos_principales": traits_str,
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "pagina": data.get("pagina", item.get("pagina")),
                    "path": rel_path,
                    "body_markdown": data.get("body_markdown", "")
                })

        # Ordenar alfabéticamente por nombre
        species_list.sort(key=lambda s: s["nombre"])
        return species_list

    def get_lineages(
        self,
        species_name_or_id: Optional[str] = None,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve los linajes/subrazas filtrados por especie padre y fuentes permitidas."""
        lineages = []
        sp_filter = (species_name_or_id or "").lower().strip()

        for item in self._index:
            if item.get("tipo") == "linaje":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                tags = [str(t).lower() for t in item.get("tags", [])]
                item_path = item.get("path", "").lower()

                if sp_filter:
                    # Coincidencia por tag de especie o ruta de carpeta (ej. especies_y_linajes/elfo/)
                    match_species = (
                        sp_filter in tags
                        or f"especies_y_linajes/{sp_filter}" in item_path
                        or sp_filter in item.get("nombre", "").lower()
                    )
                    if not match_species:
                        continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                lineages.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "nombre_ingles": data.get("nombre_ingles", item.get("nombre_ingles", "")),
                    "velocidad": data.get("velocidad", "9 m"),
                    "tamano": data.get("tamano", "Mediano"),
                    "vision_oscuridad": data.get("vision_oscuridad", "18 m"),
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "tags": item.get("tags", []),
                    "body_markdown": data.get("body_markdown", "")
                })

        lineages.sort(key=lambda l: l["nombre"])
        return lineages

    def get_classes(
        self,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve las 12 clases heroicas oficiales con sus estadísticas base y salvaciones."""
        classes = []
        # Mapa de perfiles de equipo y competencias para complementar el markdown
        class_prof_defaults = {
            "Bárbaro": {"armor": "Ligeras, medias, escudos", "weapons": "Marciales, sencillas"},
            "Bardo": {"armor": "Ligeras", "weapons": "Sencillas, estoque, arco corto"},
            "Clérigo": {"armor": "Ligeras, medias, escudos", "weapons": "Sencillas"},
            "Druida": {"armor": "Ligeras, medias, escudos", "weapons": "Sencillas"},
            "Guerrero": {"armor": "Todas las armaduras, escudos", "weapons": "Sencillas, marciales"},
            "Monje": {"armor": "Ninguna", "weapons": "Sencillas, armas de monje"},
            "Paladín": {"armor": "Todas las armaduras, escudos", "weapons": "Sencillas, marciales"},
            "Explorador": {"armor": "Ligeras, medias, escudos", "weapons": "Sencillas, marciales"},
            "Pícaro": {"armor": "Ligeras", "weapons": "Sencillas, sutiles"},
            "Hechicero": {"armor": "Ninguna", "weapons": "Dagas, dardos, hondas"},
            "Brujo": {"armor": "Ligeras", "weapons": "Sencillas"},
            "Mago": {"armor": "Ninguna", "weapons": "Dagas, dardos, hondas, bastones"}
        }

        for item in self._index:
            if item.get("tipo") == "clase":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                c_name = data.get("nombre", item.get("nombre"))
                hit_dice_str = str(data.get("dado_golpe", "1d8"))
                # Parsear valor entero de caras del dado de golpe (ej. "1d10" -> 10)
                try:
                    hit_dice_val = int(hit_dice_str.lower().split("d")[-1])
                except Exception:
                    hit_dice_val = 8

                saves = data.get("salvaciones_competentes", ["CON", "FUE"])
                profs = class_prof_defaults.get(c_name, {"armor": "Ligeras", "weapons": "Sencillas"})

                classes.append({
                    "id": item.get("id"),
                    "nombre": c_name,
                    "caracteristica_principal": data.get("caracteristica_principal", "FUE"),
                    "dado_golpe_str": hit_dice_str,
                    "hit_dice": hit_dice_val,
                    "saves": saves,
                    "armor": profs["armor"],
                    "weapons": profs["weapons"],
                    "subclass_level": 3,  # Regla unificada PHB 2024
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "body_markdown": data.get("body_markdown", "")
                })

        classes.sort(key=lambda c: c["nombre"])
        return classes

    def get_subclasses(
        self,
        class_name: Optional[str] = None,
        allowed_sources: Optional[Union[List[str], set]] = None,
        max_level: int = 20
    ) -> List[Dict[str, Any]]:
        """Devuelve las subclases atómicas oficiales de OKF para la clase y fuentes dadas."""
        subclasses = []
        target_class = (class_name or "").lower().strip()

        for item in self._index:
            if item.get("tipo") == "subclase":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                item_class = str(item.get("clase") or "").lower().strip()
                item_tags = [str(t).lower() for t in item.get("tags", [])]
                item_path = item.get("path", "").lower()

                if target_class:
                    matches = (
                        item_class == target_class
                        or target_class in item_tags
                        or f"clases/{target_class}/subclases" in item_path
                    )
                    if not matches:
                        continue

                raw_lvl = item.get("nivel")
                item_lvl = int(raw_lvl) if raw_lvl is not None and str(raw_lvl).isdigit() else 3
                if item_lvl > max_level:
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                subclasses.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "nombre_ingles": data.get("nombre_ingles", item.get("nombre_ingles", "")),
                    "clase": item.get("clase", class_name or "Desconocida"),
                    "nivel": item_lvl,
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "tags": item.get("tags", []),
                    "body_markdown": data.get("body_markdown", "")
                })

        subclasses.sort(key=lambda s: s["nombre"])
        return subclasses

    def get_backgrounds(
        self,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve los trasfondos oficiales de OKF con sus dotes de origen y bonos de atributos."""
        backgrounds = []
        for item in self._index:
            if item.get("tipo") == "trasfondo":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                backgrounds.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "dote_concedida": data.get("dote_concedida", "Dote de Origen"),
                    "caracteristicas_clave": data.get("caracteristicas_clave", "Fuerza, Destreza, Constitución"),
                    "habilidades_competentes": data.get("habilidades_competentes", "Atletismo, Percepción"),
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "body_markdown": data.get("body_markdown", "")
                })

        backgrounds.sort(key=lambda b: b["nombre"])
        return backgrounds

    def get_origin_feats(
        self,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve las dotes de origen oficiales de OKF."""
        feats = []
        for item in self._index:
            if item.get("tipo") == "dote":
                tags = [str(t).lower() for t in item.get("tags", [])]
                is_origin = (
                    "origen" in tags
                    or str(item.get("categoria", "")).lower() == "origen"
                    or "dotes/origen/" in item.get("path", "")
                )
                if not is_origin:
                    continue

                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                feats.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "categoria": "Origen",
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "body_markdown": data.get("body_markdown", "")
                })

        feats.sort(key=lambda f: f["nombre"])
        return feats

    def get_spells_for_class(
        self,
        class_name: str,
        max_spell_level: int = 9,
        min_spell_level: int = 0,
        allowed_sources: Optional[Union[List[str], set]] = None
    ) -> List[Dict[str, Any]]:
        """Devuelve la lista de conjuros disponibles para una clase en un rango de niveles."""
        spells = []
        c_target = class_name.lower().strip()

        for item in self._index:
            if item.get("tipo") == "conjuro":
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                raw_lvl = item.get("nivel")
                lvl = int(raw_lvl) if raw_lvl is not None and str(raw_lvl).isdigit() else 0
                if lvl < min_spell_level or lvl > max_spell_level:
                    continue

                item_classes = [str(c).lower() for c in item.get("clases", [])]
                if not any(c_target == c for c in item_classes):
                    continue

                spells.append(item)

        spells.sort(key=lambda s: (s.get("nivel", 0), s.get("nombre", "")))
        return spells

    @staticmethod
    def _format_components(comp: Any) -> str:
        """Formatea componentes de conjuro garantizando siempre un string seguro."""
        if not comp:
            return "V, S"
        if isinstance(comp, str):
            return comp.strip() or "V, S"
        if isinstance(comp, dict):
            parts = []
            if comp.get("verbal") or comp.get("v"):
                parts.append("V")
            if comp.get("somatico") or comp.get("s"):
                parts.append("S")
            if comp.get("material") or comp.get("m"):
                desc = comp.get("material_desc") or comp.get("descripcion_material") or comp.get("desc") or ""
                if desc:
                    parts.append(f"M ({str(desc).strip()})")
                else:
                    parts.append("M")
            return ", ".join(parts) if parts else "V, S"
        if isinstance(comp, list):
            return ", ".join(str(c) for c in comp)
        return str(comp)

    @staticmethod
    def _format_range_with_tiles(range_val: Any) -> str:
        """Formatea el alcance en metros añadiendo su equivalente exacto en casillas (tiles)."""
        import re
        if not range_val:
            return "18 m (12 casillas)"
        r_str = str(range_val).strip()
        if "casilla" in r_str.lower() or "tile" in r_str.lower():
            return r_str
        if r_str.lower() == "toque":
            return "Toque (1 casilla)"

        def _sub_m(m):
            num_str = m.group(1).replace(",", ".")
            try:
                meters = float(num_str)
                tiles = max(1, round(meters / 1.5))
                t_label = "casilla" if tiles == 1 else "casillas"
                return f"{meters:g} m ({tiles} {t_label})"
            except Exception:
                return m.group(0)

        res = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:m|metros|metro)\b', _sub_m, r_str, flags=re.IGNORECASE)
        return res

    @staticmethod
    def _format_duration_with_turns(dur_val: Any) -> str:
        """Formatea la duración indicando el número de turnos/asaltos cuando aplique."""
        import re
        if not dur_val:
            return "Instantáneo"
        d_str = str(dur_val).strip()
        if re.search(r'\(\d+\s*(?:turno|asalt|round)', d_str, re.IGNORECASE):
            return d_str

        res = d_str
        if re.search(r'\b1\s*(?:minuto|min)\b', res, re.IGNORECASE):
            res = re.sub(r'\b1\s*(?:minuto|min)\b', '1 minuto (10 turnos)', res, flags=re.IGNORECASE)
        elif re.search(r'\b10\s*(?:minutos|mins)\b', res, re.IGNORECASE):
            res = re.sub(r'\b10\s*(?:minutos|mins)\b', '10 minutos (100 turnos)', res, flags=re.IGNORECASE)
        elif re.search(r'\b1\s*(?:hora|hr)\b', res, re.IGNORECASE):
            res = re.sub(r'\b1\s*(?:hora|hr)\b', '1 hora (600 turnos)', res, flags=re.IGNORECASE)
        elif re.search(r'\b8\s*(?:horas|hrs)\b', res, re.IGNORECASE):
            res = re.sub(r'\b8\s*(?:horas|hrs)\b', '8 horas (4800 turnos)', res, flags=re.IGNORECASE)
        elif re.search(r'\b24\s*(?:horas|hrs)\b', res, re.IGNORECASE):
            res = re.sub(r'\b24\s*(?:horas|hrs)\b', '24 horas (14400 turnos)', res, flags=re.IGNORECASE)
        elif re.search(r'\b1\s*(?:asalto|round)\b', res, re.IGNORECASE) and "turno" not in res.lower():
            res = re.sub(r'\b1\s*(?:asalto|round)\b', '1 asalto (1 turno)', res, flags=re.IGNORECASE)

        return res

    def search_available_spells(
        self,
        query: str = "",
        class_name: Optional[str] = None,
        level: Optional[int] = None,
        max_level: Optional[int] = None,
        school: Optional[str] = None,
        limit: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda enriquecida de conjuros en el compendio OKF con filtros combinados
        de clase, nivel, escuela y texto libre. Devuelve objetos listos para el grimorio.
        """
        q = (query or "").lower().strip()
        c_filter = (class_name or "").lower().strip()
        if c_filter == "all" or c_filter == "cualquiera" or c_filter == "todos":
            c_filter = ""
        s_filter = (school or "").lower().strip()
        if s_filter == "all" or s_filter == "todas":
            s_filter = ""

        results = []
        for item in self._index:
            if item.get("tipo") != "conjuro":
                continue

            lvl = int(item.get("nivel", 0)) if item.get("nivel") is not None else 0
            if level is not None and lvl != level:
                continue
            if max_level is not None and lvl > max_level:
                continue

            if c_filter:
                item_classes = [str(c).lower() for c in item.get("clases", [])]
                if not any(c_filter in c for c in item_classes):
                    continue

            if s_filter:
                item_school = str(item.get("escuela", "")).lower()
                if s_filter not in item_school:
                    continue

            if q:
                nombre = str(item.get("nombre", "")).lower()
                nombre_en = str(item.get("nombre_ingles", "")).lower()
                tags = [str(t).lower() for t in item.get("tags", [])]
                if not (q in nombre or q in nombre_en or any(q in t for t in tags)):
                    continue

            # Enriquecer con los metadatos completos del archivo
            rel_path = item.get("path")
            full_data = self.read_entity_file(rel_path) if rel_path else None
            data = full_data or item

            body_md = data.get("body_markdown", data.get("descripcion", ""))
            if not isinstance(body_md, str):
                body_md = str(body_md or "")
            snippet = body_md[:200] + "..." if len(body_md) > 200 else body_md

            raw_range = data.get("alcance", item.get("alcance", "18 m"))
            formatted_range = self._format_range_with_tiles(raw_range)

            raw_dur = data.get("duracion", item.get("duracion", "Instantáneo"))
            formatted_dur = self._format_duration_with_turns(raw_dur)

            raw_comp = data.get("componentes", item.get("componentes", "V, S"))
            formatted_comp = self._format_components(raw_comp)

            hl = data.get("niveles_superiores", "")
            if isinstance(hl, list):
                hl = "\n".join(str(x) for x in hl)
            elif isinstance(hl, dict):
                hl = "\n".join(f"{k}: {v}" for k, v in hl.items())
            else:
                hl = str(hl or "")

            results.append({
                "id": item.get("id"),
                "name": data.get("nombre", item.get("nombre")),
                "name_en": data.get("nombre_ingles", item.get("nombre_ingles", "")),
                "level": lvl,
                "school": data.get("escuela", item.get("escuela", "Evocación")),
                "cast_time": data.get("tiempo_lanzamiento", "1 acción"),
                "casting_time": data.get("tiempo_lanzamiento", "1 acción"),
                "range_area": formatted_range,
                "range": formatted_range,
                "components": formatted_comp,
                "duration": formatted_dur,
                "concentration": bool(data.get("concentracion", False)),
                "ritual": bool(data.get("ritual", False)),
                "classes": data.get("clases", item.get("clases", [])),
                "prepared": True,
                "notes": body_md,
                "description": body_md,
                "snippet": snippet,
                "higher_levels": hl,
                "source": data.get("fuente", item.get("fuente", "PHB 2024")),
                "path": rel_path
            })

            if len(results) >= limit:
                break

        results.sort(key=lambda s: (s["level"], s["name"]))
        return results

