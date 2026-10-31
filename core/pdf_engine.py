"""
Motor de Procesamiento y Renderizado de PDF para D&D 5e (PyMuPDF & AcroForm)
Optimizador de memoria con caché LRU de páginas, navegación por enlaces y TOC jerárquico.
"""
import os
import sys
import re
import gc
import base64
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict

try:
    import fitz as pymupdf
except ImportError:
    import pymupdf

from .models import (
    CharacterSheet,
    WeaponAction,
    SpellItem,
    SpellSlotTier,
    CharacterFeature
)
from .rules import calc_modifier, calc_proficiency_bonus


class PdfReaderEngine:
    """Visor y motor de renderizado de manuales PDF con control estricto de memoria."""
    def __init__(self, max_cached_pages: int = 4):
        self.doc: Optional[pymupdf.Document] = None
        self.file_path: Optional[str] = None
        self.max_cached = max_cached_pages
        self.trim_margin: float = 6.0
        self.has_scanner_borders: bool = False
        # Caché LRU de páginas renderizadas: (page_num, zoom, trim) -> base64_str
        self._page_cache: OrderedDict[Tuple[int, float, bool], str] = OrderedDict()

    def open_document(self, file_path: str) -> bool:
        self.close()
        if not os.path.exists(file_path):
            return False
        try:
            self.doc = pymupdf.open(file_path)
            self.file_path = file_path
            # Detección heurística de manuales escaneados con marco de registro (Tasha/Xanathar)
            lower_name = os.path.basename(file_path).lower()
            self.has_scanner_borders = "xanathar" in lower_name or "tasha" in lower_name
            return True
        except Exception as e:
            print(f"[PdfReader] Error al abrir documento {file_path}: {e}")
            return False

    def close(self):
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
            self.doc = None
        self.file_path = None
        self._page_cache.clear()
        gc.collect()

    def get_info(self) -> Dict[str, Any]:
        if not self.doc:
            return {"success": False, "error": "No hay documento abierto"}
        toc = []
        try:
            raw_toc = self.doc.get_toc()
            toc = [{"level": item[0], "title": item[1], "page": item[2]} for item in raw_toc]
        except Exception as e:
            print(f"[PdfReader] Advertencia al extraer TOC: {e}")

        return {
            "success": True,
            "path": self.file_path,
            "filename": os.path.basename(self.file_path or ""),
            "page_count": len(self.doc),
            "total_pages": len(self.doc),
            "toc": toc,
        }

    def render_page(self, page_num: int, zoom: float = 1.0, trim_margins: bool = False) -> Dict[str, Any]:
        if not self.doc or page_num < 1 or page_num > len(self.doc):
            return {"success": False, "error": "Página inválida o documento no cargado"}

        cache_key = (page_num, round(zoom, 2), trim_margins)
        if cache_key in self._page_cache:
            self._page_cache.move_to_end(cache_key)
            return {"success": True, "page_num": page_num, "image_base64": self._page_cache[cache_key]}

        try:
            page = self.doc.load_page(page_num - 1)
            rect = page.rect

            # Opcional: recortar márgenes negros de escaneo
            clip = None
            if trim_margins and self.has_scanner_borders:
                margin = self.trim_margin
                clip = pymupdf.Rect(rect.x0 + margin, rect.y0 + margin, rect.x1 - margin, rect.y1 - margin)

            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
            img_bytes = pix.tobytes("jpeg")
            b64_str = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('ascii')}"

            # Extraer hipervínculos internos de la página
            links = []
            for link in page.get_links():
                target_page = link.get("page", -1)
                r = link.get("from")
                if r:
                    links.append({
                        "rect": [r.x0, r.y0, r.x1, r.y1],
                        "target_page": target_page + 1 if target_page >= 0 else None,
                        "uri": link.get("uri")
                    })

            # Control LRU
            if len(self._page_cache) >= self.max_cached:
                self._page_cache.popitem(last=False)
            self._page_cache[cache_key] = b64_str

            return {
                "success": True,
                "page_num": page_num,
                "image_base64": b64_str,
                "links": links,
                "width": pix.width,
                "height": pix.height
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class UniversalAcroFormHandler:
    """Importador y exportador universal para PDFs de ficha oficiales D&D 5e con campos AcroForm."""

    # Mapeo universal de nombres de campos AcroForm (WotC 2014 & 2024, ES & EN)
    FIELD_MAP = {
        "character_name": ["CharacterName", "NombrePersonaje", "CharacterName_2", "CharacterName_3"],
        "class_level": ["ClassLevel", "ClaseNivel", "Class", "Clase"],
        "background": ["Background", "Trasfondo"],
        "player_name": ["PlayerName", "NombreJugador"],
        "race": ["Race", "Raza", "Especie"],
        "alignment": ["Alignment", "Alineamiento"],
        "xp": ["ExperiencePoints", "PuntosExperiencia", "XP"],
        "ac": ["AC", "CA", "ArmorClass", "ClaseArmadura"],
        "initiative": ["Initiative", "Iniciativa"],
        "speed": ["Speed", "Velocidad"],
        "hp_max": ["HPMax", "PGMax", "MaxHP"],
        "hp_current": ["HPCurrent", "PGActual", "CurrentHP"],
        "hp_temp": ["HPTemp", "PGTemp", "TempHP"],
        "hit_dice_total": ["HDTotal", "DadosGolpeTotal", "TotalHD"],
        "hit_dice": ["HD", "DadosGolpe"],
        "str": ["STR", "FUE", "STRmod", "FUEmod"],
        "dex": ["DEX", "DES", "DEXmod", "DESmod"],
        "con": ["CON", "CONmod"],
        "int": ["INT", "INTmod"],
        "wis": ["WIS", "SAB", "WISmod", "SABmod"],
        "cha": ["CHA", "CAR", "CHAmod", "CARmod"],
        "proficiency_bonus": ["ProfBonus", "BonoCompetencia", "PB"],
        "passive_perception": ["PassivePerception", "PercepcionPasiva", "Passive"],
    }

    @classmethod
    def load_character_from_pdf(cls, pdf_path: str) -> CharacterSheet:
        """Extrae los valores de los campos AcroForm de un PDF y construye un CharacterSheet."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        raw_fields: Dict[str, Any] = {}

        for page in doc:
            for widget in page.widgets():
                if widget.field_name:
                    val = widget.field_value
                    raw_fields[widget.field_name] = str(val).strip() if val is not None else ""

        doc.close()

        def get_val(keys: List[str], default: str = "") -> str:
            for k in keys:
                for f_name, f_val in raw_fields.items():
                    if k.lower() == f_name.lower():
                        return f_val
            return default

        name = get_val(cls.FIELD_MAP["character_name"], "Héroe sin Nombre")
        class_level = get_val(cls.FIELD_MAP["class_level"], "Aventurero 1")
        parts = class_level.rsplit(" ", 1)
        char_class = parts[0] if len(parts) > 0 else "Aventurero"
        try:
            level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        except Exception:
            level = 1

        race = get_val(cls.FIELD_MAP["race"], "Humano")
        background = get_val(cls.FIELD_MAP["background"], "Soldado")
        alignment = get_val(cls.FIELD_MAP["alignment"], "Neutral")

        try:
            hp_max = int(get_val(cls.FIELD_MAP["hp_max"], "10") or 10)
        except ValueError:
            hp_max = 10

        try:
            hp_current = int(get_val(cls.FIELD_MAP["hp_current"], str(hp_max)) or hp_max)
        except ValueError:
            hp_current = hp_max

        try:
            ac = int(get_val(cls.FIELD_MAP["ac"], "10") or 10)
        except ValueError:
            ac = 10

        def parse_stat(keys: List[str]) -> int:
            raw = get_val(keys, "10")
            try:
                # Si viene un modificador tipo "+3", derivar puntuación base aprox
                if raw.startswith("+") or (raw.startswith("-") and len(raw) <= 3):
                    mod = int(raw)
                    return 10 + (mod * 2)
                return int(raw)
            except ValueError:
                return 10

        abilities = {
            "FUE": parse_stat(cls.FIELD_MAP["str"]),
            "DES": parse_stat(cls.FIELD_MAP["dex"]),
            "CON": parse_stat(cls.FIELD_MAP["con"]),
            "INT": parse_stat(cls.FIELD_MAP["int"]),
            "SAB": parse_stat(cls.FIELD_MAP["wis"]),
            "CAR": parse_stat(cls.FIELD_MAP["cha"]),
        }

        # Armas básicas desde texto
        weapons: List[WeaponAction] = []
        for i in range(1, 4):
            w_name = raw_fields.get(f"Wpn Name {i}") or raw_fields.get(f"NombreArma{i}") or ""
            w_atk = raw_fields.get(f"Wpn1 AtkBonus {i}") or raw_fields.get(f"BonoAtaque{i}") or "+0"
            w_dmg = raw_fields.get(f"Wpn1 Damage {i}") or raw_fields.get(f"DanoArma{i}") or "1d6"
            if w_name:
                weapons.append(WeaponAction(
                    name=w_name,
                    attack_bonus=w_atk,
                    damage=w_dmg,
                    damage_type="Físico"
                ))

        # Rasgos y características
        features: List[CharacterFeature] = []
        feat_text = raw_fields.get("Features and Traits") or raw_fields.get("RasgosYAtributos") or ""
        if feat_text:
            features.append(CharacterFeature(
                name="Rasgos de Personaje",
                source="Manual",
                description=feat_text[:500]
            ))

        return CharacterSheet(
            name=name,
            char_class=char_class,
            level=level,
            race=race,
            background=background,
            alignment=alignment,
            armor_class=ac,
            hp_current=hp_current,
            hp_max=hp_max,
            abilities=abilities,
            weapon_actions=weapons,
            features=features
        )

    @classmethod
    def export_character_to_pdf(cls, char: CharacterSheet, template_pdf_path: str, output_path: str) -> str:
        """Escribe los valores de una ficha CharacterSheet dentro de un PDF editable con AcroForms."""
        if not os.path.exists(template_pdf_path):
            raise FileNotFoundError(f"Plantilla PDF no encontrada: {template_pdf_path}")

        doc = pymupdf.open(template_pdf_path)

        data_to_write = {
            "CharacterName": char.name,
            "NombrePersonaje": char.name,
            "ClassLevel": f"{char.char_class} {char.level}",
            "ClaseNivel": f"{char.char_class} {char.level}",
            "Race": char.race,
            "Raza": char.race,
            "Background": char.background,
            "Trasfondo": char.background,
            "Alignment": char.alignment,
            "Alineamiento": char.alignment,
            "AC": str(char.armor_class),
            "CA": str(char.armor_class),
            "HPMax": str(char.hp_max),
            "PGMax": str(char.hp_max),
            "HPCurrent": str(char.hp_current),
            "PGActual": str(char.hp_current),
            "STR": str(char.abilities.get("FUE", 10)),
            "DEX": str(char.abilities.get("DES", 10)),
            "CON": str(char.abilities.get("CON", 10)),
            "INT": str(char.abilities.get("INT", 10)),
            "WIS": str(char.abilities.get("SAB", 10)),
            "CHA": str(char.abilities.get("CAR", 10)),
            "STRmod": f"{calc_modifier(char.abilities.get('FUE', 10)):+d}",
            "DEXmod": f"{calc_modifier(char.abilities.get('DES', 10)):+d}",
            "CONmod": f"{calc_modifier(char.abilities.get('CON', 10)):+d}",
            "INTmod": f"{calc_modifier(char.abilities.get('INT', 10)):+d}",
            "WISmod": f"{calc_modifier(char.abilities.get('SAB', 10)):+d}",
            "CHAmod": f"{calc_modifier(char.abilities.get('CAR', 10)):+d}",
            "ProfBonus": f"+{calc_proficiency_bonus(char.level)}",
            "Speed": str(char.speed),
            "Initiative": f"{char.initiative_bonus:+d}",
        }

        # Escribir en widgets de todas las páginas
        for page in doc:
            for widget in page.widgets():
                fn = widget.field_name
                if fn in data_to_write:
                    widget.field_value = data_to_write[fn]
                    widget.update()

        doc.save(output_path, incremental=False, deflate=True)
        doc.close()
        return output_path
