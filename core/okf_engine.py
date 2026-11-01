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


CLASS_NAME_ALIASES: Dict[str, List[str]] = {
    "bardo": ["bardo", "bard"],
    "clérigo": ["clérigo", "clerigo", "cleric"],
    "druida": ["druida", "druid"],
    "hechicero": ["hechicero", "sorcerer"],
    "mago": ["mago", "wizard"],
    "paladín": ["paladín", "paladin"],
    "explorador": ["explorador", "ranger"],
    "brujo": ["brujo", "warlock"],
    "bárbaro": ["bárbaro", "barbaro", "barbarian"],
    "guerrero": ["guerrero", "fighter"],
    "monje": ["monje", "monk"],
    "pícaro": ["pícaro", "picaro", "rogue"],
    "artífice": ["artífice", "artifice", "artificer"],
    "bard": ["bardo", "bard"],
    "cleric": ["clérigo", "clerigo", "cleric"],
    "druid": ["druida", "druid"],
    "sorcerer": ["hechicero", "sorcerer"],
    "wizard": ["mago", "wizard"],
    "paladin": ["paladín", "paladin"],
    "ranger": ["explorador", "ranger"],
    "warlock": ["brujo", "warlock"],
    "barbarian": ["bárbaro", "barbaro", "barbarian"],
    "fighter": ["guerrero", "fighter"],
    "monk": ["monje", "monk"],
    "rogue": ["pícaro", "picaro", "rogue"],
    "artificer": ["artífice", "artifice", "artificer"],
}

SCHOOL_NAME_ALIASES: Dict[str, List[str]] = {
    "abjuración": ["abjuración", "abjuracion", "abjuration"],
    "conjuración": ["conjuración", "conjuracion", "conjuration"],
    "adivinación": ["adivinación", "adivinacion", "divination"],
    "encantamiento": ["encantamiento", "enchantment"],
    "evocación": ["evocación", "evocacion", "evocation"],
    "ilusión": ["ilusión", "ilusion", "ilusionismo", "illusion", "illusionism"],
    "ilusionismo": ["ilusión", "ilusion", "ilusionismo", "illusion", "illusionism"],
    "nigromancia": ["nigromancia", "necromancy"],
    "transmutación": ["transmutación", "transmutacion", "transmutation"],
    "abjuration": ["abjuración", "abjuracion", "abjuration"],
    "conjuration": ["conjuración", "conjuracion", "conjuration"],
    "divination": ["adivinación", "adivinacion", "divination"],
    "enchantment": ["encantamiento", "enchantment"],
    "evocation": ["evocación", "evocacion", "evocation"],
    "illusion": ["ilusión", "ilusion", "ilusionismo", "illusion", "illusionism"],
    "necromancy": ["nigromancia", "necromancy"],
    "transmutation": ["transmutación", "transmutacion", "transmutation"],
}


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
        limit: int = 500,
        lang: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Búsqueda ultrarrápida en memoria sobre el índice precalculado con filtro opcional de idioma."""
        q = query.lower().strip()
        target_lang = ("en" if lang.lower().startswith("en") else "es") if lang else None
        results = []

        for item in self._index:
            if target_lang:
                item_lang = item.get("idioma", "es")
                if item_lang != target_lang:
                    continue

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
                nombre = str(item.get("nombre") or "").lower()
                nombre_en = str(item.get("nombre_ingles") or "").lower()
                nombre_orig = str(item.get("nombre_original") or "").lower()
                escuela = str(item.get("escuela") or "").lower()
                tags = [str(t).lower() for t in (item.get("tags") or [])]

                match = (
                    q in nombre
                    or q in nombre_en
                    or q in nombre_orig
                    or q in escuela
                    or any(q in t for t in tags)
                )
                if not match:
                    continue

            results.append(item)
            if len(results) >= limit:
                break

        return results

    def count_entities(self, tipo: Optional[Union[str, List[str]]] = None, lang: str = "es") -> int:
        """Devuelve el conteo rápido de entidades según el tipo y el idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        items = [i for i in self._index if i.get("idioma", "es") == target_lang]
        if not tipo:
            return len(items)
        if isinstance(tipo, list):
            return sum(1 for item in items if item.get("tipo") in tipo)
        return sum(1 for item in items if item.get("tipo") == tipo)

    @lru_cache(maxsize=128)
    def read_entity_file(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """Lee y parsea bajo demanda un archivo atómico Markdown con frontmatter YAML."""
        normalized_rel = os.path.normpath(rel_path)
        candidates = [
            os.path.join(self.okf_dir, normalized_rel),
            os.path.join(self.okf_dir, rel_path),
            os.path.join(os.path.dirname(self.okf_dir), "okf_dnd5e", normalized_rel),
            os.path.join(os.path.dirname(self.okf_dir), normalized_rel),
        ]
        full_path = next((p for p in candidates if os.path.exists(p)), None)
        if not full_path:
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




    def get_spell_item(self, entity_id: str, lang: str = "es") -> Optional[SpellItem]:
        """Transforma una entidad de conjuro OKF en un objeto SpellItem listo para la ficha."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        clean = (entity_id or "").strip().lower()
        if not clean:
            return None

        clean_slug = clean.replace(" ", "_")
        clean_en = f"{clean_slug}_en"
        clean_base = clean_slug.replace("_en", "")

        entity_meta = next(
            (
                e for e in self._index
                if e.get("tipo") == "conjuro"
                and e.get("idioma", "es") == target_lang
                and (
                    e.get("id", "").lower() in (clean_slug, clean_en, clean_base)
                    or e.get("original_id", "").lower() in (clean_slug, clean_en, clean_base)
                    or e.get("nombre", "").lower() == clean
                    or e.get("nombre_ingles", "").lower() == clean
                    or e.get("nombre_espanol", "").lower() == clean
                )
            ),
            None
        )
        if not entity_meta:
            entity_meta = next(
                (
                    e for e in self._index
                    if e.get("tipo") == "conjuro"
                    and (
                        e.get("id", "").lower() in (clean_slug, clean_en, clean_base)
                        or e.get("original_id", "").lower() in (clean_slug, clean_en, clean_base)
                        or e.get("nombre", "").lower() == clean
                        or e.get("nombre_ingles", "").lower() == clean
                        or e.get("nombre_espanol", "").lower() == clean
                    )
                ),
                None
            )
        if not entity_meta:
            return None

        file_path = entity_meta.get("path")
        full_data = self.read_entity_file(file_path) if file_path else None
        data = full_data or entity_meta

        body_desc = data.get("body_markdown") or data.get("descripcion", entity_meta.get("descripcion", ""))

        return SpellItem(
            id=data.get("id", entity_meta.get("id", entity_id)),
            name=data.get("nombre", entity_meta.get("nombre", "")),
            name_en=data.get("nombre_ingles", entity_meta.get("nombre_ingles", "")),
            level=int(data.get("nivel", entity_meta.get("nivel", 0))),
            school=data.get("escuela", entity_meta.get("escuela", "Evocación")),
            casting_time=data.get("tiempo_lanzamiento", "1 action" if target_lang == "en" else "1 acción"),
            range=data.get("alcance", "60 ft (12 tiles)" if target_lang == "en" else "18 m"),
            components=data.get("componentes", "V, S"),
            duration=data.get("duracion", "Instantaneous" if target_lang == "en" else "Instantáneo"),
            concentration=bool(data.get("concentracion", False)),
            ritual=bool(data.get("ritual", False)),
            description=body_desc,
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
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve la lista reactiva de especies oficiales disponibles en OKF según el idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        species_list = []
        for item in self._index:
            if item.get("tipo") == "especie":
                if item.get("idioma", "es") != target_lang:
                    continue
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
                    "tipo_criatura": data.get("tipo_criatura", "humanoid" if target_lang == "en" else "humanoide"),
                    "tamano": data.get("tamano", "Medium" if target_lang == "en" else "Mediano"),
                    "velocidad": data.get("velocidad", "30 ft (6 tiles)" if target_lang == "en" else "9 m"),
                    "sentidos": data.get("sentidos", "Normal"),
                    "darkvision": "oscuridad" in str(data.get("sentidos", "")).lower() or "darkvision" in str(data.get("sentidos", "")).lower(),
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
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve los linajes/subrazas filtrados por especie padre, fuentes e idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        lineages = []
        sp_filter = (species_name_or_id or "").lower().strip()

        for item in self._index:
            if item.get("tipo") == "linaje":
                if item.get("idioma", "es") != target_lang:
                    continue
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
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve las 12 clases heroicas oficiales con sus estadísticas base y salvaciones según el idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        classes = []
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
            "Mago": {"armor": "Ninguna", "weapons": "Dagas, dardos, hondas, bastones"},
            "Barbarian": {"armor": "Light, medium, shields", "weapons": "Simple, martial"},
            "Bard": {"armor": "Light", "weapons": "Simple, hand crossbow, longsword, rapier, shortsword"},
            "Cleric": {"armor": "Light, medium, shields", "weapons": "Simple"},
            "Druid": {"armor": "Light, medium, shields", "weapons": "Clubs, daggers, darts, javelins, maces, scimitars, sickles, slings, spears"},
            "Fighter": {"armor": "All armor, shields", "weapons": "Simple, martial"},
            "Monk": {"armor": "None", "weapons": "Simple, monk weapons"},
            "Paladin": {"armor": "All armor, shields", "weapons": "Simple, martial"},
            "Ranger": {"armor": "Light, medium, shields", "weapons": "Simple, martial"},
            "Rogue": {"armor": "Light", "weapons": "Simple, hand crossbow, longsword, rapier, shortsword"},
            "Sorcerer": {"armor": "None", "weapons": "Daggers, darts, slings, quarterstaffs, light crossbows"},
            "Warlock": {"armor": "Light", "weapons": "Simple"},
            "Wizard": {"armor": "None", "weapons": "Daggers, darts, slings, quarterstaffs, light crossbows"}
        }

        for item in self._index:
            if item.get("tipo") == "clase":
                if item.get("idioma", "es") != target_lang:
                    continue
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                c_name = data.get("nombre", item.get("nombre"))
                hit_dice_str = str(data.get("dado_golpe", "1d8"))
                try:
                    hit_dice_val = int(hit_dice_str.lower().split("d")[-1])
                except Exception:
                    hit_dice_val = 8

                saves = data.get("salvaciones_competentes", ["CON", "STR" if target_lang == "en" else "FUE"])
                profs = class_prof_defaults.get(c_name, {"armor": "Light" if target_lang == "en" else "Ligeras", "weapons": "Simple" if target_lang == "en" else "Sencillas"})

                classes.append({
                    "id": item.get("id"),
                    "nombre": c_name,
                    "caracteristica_principal": data.get("caracteristica_principal", "STR" if target_lang == "en" else "FUE"),
                    "dado_golpe_str": hit_dice_str,
                    "hit_dice": hit_dice_val,
                    "saves": saves,
                    "armor": profs["armor"],
                    "weapons": profs["weapons"],
                    "subclass_level": 3,
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
        max_level: int = 20,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve las subclases atómicas oficiales de OKF para la clase, fuentes e idioma dados."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        subclasses = []
        target_class = (class_name or "").lower().strip()

        for item in self._index:
            if item.get("tipo") == "subclase":
                if item.get("idioma", "es") != target_lang:
                    continue
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                item_class = str(item.get("clase") or item.get("clase_padre") or "").lower().strip()
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
                    "clase": item.get("clase", class_name or ("Unknown" if target_lang == "en" else "Desconocida")),
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
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve los trasfondos oficiales de OKF según el idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        backgrounds = []
        for item in self._index:
            if item.get("tipo") == "trasfondo":
                if item.get("idioma", "es") != target_lang:
                    continue
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                rel_path = item.get("path")
                full_data = self.read_entity_file(rel_path) if rel_path else None
                data = full_data or item

                backgrounds.append({
                    "id": item.get("id"),
                    "nombre": data.get("nombre", item.get("nombre")),
                    "dote_concedida": data.get("dote_concedida", "Origin Feat" if target_lang == "en" else "Dote de Origen"),
                    "caracteristicas_clave": data.get("caracteristicas_clave", "Strength, Dexterity, Constitution" if target_lang == "en" else "Fuerza, Destreza, Constitución"),
                    "habilidades_competentes": data.get("habilidades_competentes", "Athletics, Perception" if target_lang == "en" else "Atletismo, Percepción"),
                    "fuente": data.get("fuente", item.get("fuente", "PHB 2024")),
                    "path": rel_path,
                    "body_markdown": data.get("body_markdown", "")
                })

        backgrounds.sort(key=lambda b: b["nombre"])
        return backgrounds

    def get_origin_feats(
        self,
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve las dotes de origen oficiales de OKF según el idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        feats = []
        for item in self._index:
            if item.get("tipo") == "dote":
                if item.get("idioma", "es") != target_lang:
                    continue
                tags = [str(t).lower() for t in item.get("tags", [])]
                is_origin = (
                    "origen" in tags
                    or "origin" in tags
                    or str(item.get("categoria", "")).lower() in ("origen", "origin")
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
                    "categoria": "Origin" if target_lang == "en" else "Origen",
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
        allowed_sources: Optional[Union[List[str], set]] = None,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Devuelve la lista de conjuros disponibles para una clase en un rango de niveles e idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        spells = []
        c_target = class_name.lower().strip()
        allowed_classes = CLASS_NAME_ALIASES.get(c_target, [c_target])

        for item in self._index:
            if item.get("tipo") == "conjuro":
                if item.get("idioma", "es") != target_lang:
                    continue
                if not self._source_matches(item.get("fuente"), allowed_sources):
                    continue

                raw_lvl = item.get("nivel")
                lvl = int(raw_lvl) if raw_lvl is not None and str(raw_lvl).isdigit() else 0
                if lvl < min_spell_level or lvl > max_spell_level:
                    continue

                item_classes = [str(c).lower() for c in item.get("clases", [])]
                if not any(c in allowed_classes or any(ac in c for ac in allowed_classes) for c in item_classes):
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
    def _format_range_with_tiles(range_val: Any, lang: str = "es") -> str:
        """Formatea el alcance en metros o pies añadiendo su equivalente exacto en casillas (tiles)."""
        import re
        is_en = (lang or "").lower().startswith("en")
        if not range_val:
            return "60 ft (12 tiles)" if is_en else "18 m (12 casillas)"
        r_str = str(range_val).strip()
        if "casilla" in r_str.lower() or "tile" in r_str.lower():
            return r_str
        if r_str.lower() in ("toque", "touch"):
            return "Touch (1 tile)" if is_en else "Toque (1 casilla)"
        if r_str.lower() in ("personal", "self"):
            return "Self" if is_en else "Personal"

        # Formato pies (ft)
        def _sub_ft(m):
            num_str = m.group(1).replace(",", ".")
            try:
                feet = float(num_str)
                tiles = max(1, round(feet / 5))
                t_label = "tile" if tiles == 1 else "tiles"
                return f"{feet:g} ft ({tiles} {t_label})"
            except Exception:
                return m.group(0)

        if re.search(r'\b\d+(?:[.,]\d+)?\s*(?:ft|feet|foot)\b', r_str, re.IGNORECASE):
            return re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:ft|feet|foot)\b', _sub_ft, r_str, flags=re.IGNORECASE)

        # Formato metros (m)
        def _sub_m(m):
            num_str = m.group(1).replace(",", ".")
            try:
                meters = float(num_str)
                tiles = max(1, round(meters / 1.5))
                if is_en:
                    feet = round(meters / 0.3)
                    t_label = "tile" if tiles == 1 else "tiles"
                    return f"{feet} ft ({tiles} {t_label})"
                t_label = "casilla" if tiles == 1 else "casillas"
                return f"{meters:g} m ({tiles} {t_label})"
            except Exception:
                return m.group(0)

        res = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:m|metros|metro)\b', _sub_m, r_str, flags=re.IGNORECASE)
        return res

    @staticmethod
    def _format_duration_with_turns(dur_val: Any, lang: str = "es") -> str:
        """Formatea la duración indicando el número de turnos/asaltos cuando aplique según el idioma."""
        import re
        is_en = (lang or "").lower().startswith("en")
        if not dur_val:
            return "Instantaneous" if is_en else "Instantáneo"
        d_str = str(dur_val).strip()
        if re.search(r'\(\d+\s*(?:turno|asalt|round)', d_str, re.IGNORECASE):
            return d_str

        res = d_str
        if is_en:
            if re.search(r'\b1\s*(?:minute|minuto|min)\b', res, re.IGNORECASE):
                res = re.sub(r'\b1\s*(?:minute|minuto|min)\b', '1 minute (10 rounds)', res, flags=re.IGNORECASE)
            elif re.search(r'\b10\s*(?:minutes|minutos|mins)\b', res, re.IGNORECASE):
                res = re.sub(r'\b10\s*(?:minutes|minutos|mins)\b', '10 minutes (100 rounds)', res, flags=re.IGNORECASE)
            elif re.search(r'\b1\s*(?:hour|hora|hr)\b', res, re.IGNORECASE):
                res = re.sub(r'\b1\s*(?:hour|hora|hr)\b', '1 hour (600 rounds)', res, flags=re.IGNORECASE)
            elif re.search(r'\b8\s*(?:hours|horas|hrs)\b', res, re.IGNORECASE):
                res = re.sub(r'\b8\s*(?:hours|horas|hrs)\b', '8 hours (4800 rounds)', res, flags=re.IGNORECASE)
            elif re.search(r'\b24\s*(?:hours|horas|hrs)\b', res, re.IGNORECASE):
                res = re.sub(r'\b24\s*(?:hours|horas|hrs)\b', '24 hours (14400 rounds)', res, flags=re.IGNORECASE)
            elif re.search(r'\b1\s*(?:round|asalto)\b', res, re.IGNORECASE):
                res = re.sub(r'\b1\s*(?:round|asalto)\b', '1 round (1 turn)', res, flags=re.IGNORECASE)
        else:
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
        limit: int = 150,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda enriquecida de conjuros en el compendio OKF con filtros combinados
        de clase, nivel, escuela, idioma y texto libre. Devuelve objetos listos para el grimorio.
        """
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
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
            if item.get("idioma", "es") != target_lang:
                continue

            lvl = int(item.get("nivel", 0)) if item.get("nivel") is not None else 0
            if level is not None and lvl != level:
                continue
            if max_level is not None and lvl > max_level:
                continue

            if c_filter:
                allowed_classes = CLASS_NAME_ALIASES.get(c_filter, [c_filter])
                item_classes = [str(c).lower() for c in item.get("clases", [])]
                if not any(c in allowed_classes or any(ac in c for ac in allowed_classes) for c in item_classes):
                    continue

            if s_filter:
                allowed_schools = SCHOOL_NAME_ALIASES.get(s_filter, [s_filter])
                item_school = str(item.get("escuela", "")).lower()
                if not any(s in item_school or item_school in s for s in allowed_schools):
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
            formatted_range = self._format_range_with_tiles(raw_range, lang=target_lang)

            raw_dur = data.get("duracion", item.get("duracion", "Instantáneo"))
            formatted_dur = self._format_duration_with_turns(raw_dur, lang=target_lang)

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
