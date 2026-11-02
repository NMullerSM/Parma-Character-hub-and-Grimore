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
    import pymupdf
except ImportError:
    import fitz as pymupdf

from .models import (
    CharacterSheet,
    WeaponAction,
    SpellItem,
    SpellSlotTier,
    CharacterFeature
)
from .rules import calc_modifier, calc_proficiency_bonus
from .paths import get_bundle_dir, get_user_data_dir


class PdfReaderEngine:
    """Visor y motor de renderizado de manuales PDF con control estricto de memoria."""

    def __init__(self, max_cache_entries: int = 12):
        self._doc: Optional[Any] = None
        self._current_path: Optional[str] = None
        self._page_cache: OrderedDict[Tuple[int, float, bool], str] = OrderedDict()
        self._max_cache = max_cache_entries

    @property
    def is_open(self) -> bool:
        return self._doc is not None and not self._doc.is_closed

    @property
    def page_count(self) -> int:
        return len(self._doc) if self.is_open else 0

    @property
    def current_path(self) -> Optional[str]:
        return self._current_path

    def open_document(self, path: str) -> bool:
        """Abre un archivo PDF liberando el anterior y reiniciando la caché."""
        self.close()
        if not os.path.exists(path):
            return False
        try:
            self._doc = pymupdf.open(path)
            self._current_path = path
            return True
        except Exception as e:
            print(f"[PdfReaderEngine] Error al abrir {path}: {e}")
            self._doc = None
            self._current_path = None
            return False

    def close(self):
        """Cierra el documento y libera memoria inmediatamente."""
        if self._doc is not None:
            try:
                if not self._doc.is_closed:
                    self._doc.close()
            except Exception:
                pass
            self._doc = None
        self._current_path = None
        self._page_cache.clear()
        gc.collect()

    def get_toc(self) -> List[Dict[str, Any]]:
        """Retorna la tabla de contenidos jerárquica del PDF."""
        if not self.is_open:
            return []
        try:
            raw_toc = self._doc.get_toc()
            return [
                {"level": item[0], "title": item[1], "page": item[2]}
                for item in raw_toc
                if len(item) >= 3 and item[2] > 0
            ]
        except Exception:
            return []

    def _should_trim(self, trim_margins: Optional[bool]) -> bool:
        if trim_margins is not None:
            return trim_margins
        p = (self._current_path or "").lower()
        # En el PHB 2024 de D&D, recortar el encabezado/pie decorativo permite mejor lectura táctica
        return "phb" in p or "player" in p or "2024" in p or "manual" in p

    def get_page_dimensions(self, page_num: int, trim_margins: Optional[bool] = None) -> Tuple[float, float]:
        """Dimensiones de la página (o del recorte) para calcular proporciones en UI."""
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return (0.0, 0.0)
        try:
            page = self._doc[page_num - 1]
            rect = page.rect
            if self._should_trim(trim_margins):
                t_top = rect.height * 0.045
                t_bottom = rect.height * 0.045
                t_left = rect.width * 0.04
                t_right = rect.width * 0.04
                return (rect.width - t_left - t_right, rect.height - t_top - t_bottom)
            return (rect.width, rect.height)
        except Exception:
            return (0.0, 0.0)

    def render_page_base64(self, page_num: int, zoom: float = 1.0, trim_margins: Optional[bool] = None) -> Optional[str]:
        """Renderiza una página a imagen PNG en base64 con caché LRU."""
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return None

        trim = self._should_trim(trim_margins)
        cache_key = (page_num, round(zoom, 2), trim)
        if cache_key in self._page_cache:
            self._page_cache.move_to_end(cache_key)
            return self._page_cache[cache_key]

        try:
            page = self._doc[page_num - 1]
            mat = pymupdf.Matrix(zoom, zoom)

            clip_rect = None
            if trim:
                rect = page.rect
                t_top = rect.height * 0.045
                t_bottom = rect.height * 0.045
                t_left = rect.width * 0.04
                t_right = rect.width * 0.04
                clip_rect = pymupdf.Rect(
                    rect.x0 + t_left,
                    rect.y0 + t_top,
                    rect.x1 - t_right,
                    rect.y1 - t_bottom
                )

            pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
            img_bytes = pix.tobytes("png")
            b64_str = base64.b64encode(img_bytes).decode("ascii")

            del pix
            del img_bytes

            self._page_cache[cache_key] = b64_str
            if len(self._page_cache) > self._max_cache:
                self._page_cache.popitem(last=False)

            return b64_str
        except Exception as e:
            print(f"[PdfReaderEngine] Error renderizando página {page_num}: {e}")
            return None

    def get_page_links(self, page_num: int, trim_margins: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Extrae enlaces internos o hipervínculos para navegación interactiva."""
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return []
        try:
            page = self._doc[page_num - 1]
            links = page.get_links()
            rect = page.rect
            pw, ph = rect.width, rect.height

            trim = self._should_trim(trim_margins)
            t_left = pw * 0.04 if trim else 0.0
            t_top = ph * 0.045 if trim else 0.0
            eff_w = pw * 0.92 if trim else pw
            eff_h = ph * 0.91 if trim else ph

            result = []
            for l in links:
                from_rect = l.get("from")
                if not from_rect:
                    continue

                if trim:
                    rx0 = max(0.0, (from_rect.x0 - t_left) / eff_w)
                    ry0 = max(0.0, (from_rect.y0 - t_top) / eff_h)
                    rw = (from_rect.x1 - from_rect.x0) / eff_w
                    rh = (from_rect.y1 - from_rect.y0) / eff_h
                else:
                    rx0 = from_rect.x0 / pw
                    ry0 = from_rect.y0 / ph
                    rw = (from_rect.x1 - from_rect.x0) / pw
                    rh = (from_rect.y1 - from_rect.y0) / ph

                item = {
                    "kind": l.get("kind"),
                    "page": l.get("page", 0) + 1 if "page" in l and l["page"] is not None else None,
                    "uri": l.get("uri"),
                    "rect": [rx0, ry0, rw, rh],
                }
                if item["page"] or item["uri"]:
                    result.append(item)
            return result
        except Exception:
            return []


class UniversalAcroFormHandler:
    """
    Controlador Universal de Formularios PDF AcroForm para D&D 5e / 2024.
    Mapea campos tanto en inglés como en español para importar y exportar fichas.
    """

    # Diccionario bilingüe de campos estándar AcroForm (Wizards / D&D Beyond / Roll20 / Parma)
    FIELD_MAP = {
        # Identidad
        "name": ["CharacterName", "NombrePersonaje", "CharacterName_2", "Name", "Nombre"],
        "class_level": ["ClassLevel", "ClaseNivel", "Class", "Clase"],
        "background": ["Background", "Trasfondo"],
        "player_name": ["PlayerName", "NombreJugador"],
        "race": ["Race", "Raza", "Especie"],
        "alignment": ["Alignment", "Alineamiento"],
        "xp": ["ExperiencePoints", "PuntosExperiencia", "XP"],

        # Estadísticas Principales
        "str": ["STR", "FUE", "Fuerza", "Strength"],
        "str_mod": ["STRmod", "FUEmod", "ModFuerza"],
        "dex": ["DEX", "DES", "Destreza", "Dexterity"],
        "dex_mod": ["DEXmod", "DESmod", "ModDestreza"],
        "con": ["CON", "Constitucion", "Constitution"],
        "con_mod": ["CONmod", "ModConstitucion"],
        "int": ["INT", "Inteligencia", "Intelligence"],
        "int_mod": ["INTmod", "ModInteligencia"],
        "wis": ["WIS", "SAB", "Sabiduria", "Wisdom"],
        "wis_mod": ["WISmod", "SABmod", "ModSabiduria"],
        "cha": ["CHA", "CAR", "Carisma", "Charisma"],
        "cha_mod": ["CHAmod", "CARmod", "ModCarisma"],

        # Combate
        "ac": ["AC", "CA", "ClaseArmadura", "ArmorClass"],
        "initiative": ["Initiative", "Iniciativa"],
        "speed": ["Speed", "Velocidad"],
        "hp_max": ["HPMax", "PGMax", "MaxHP"],
        "hp_current": ["HPCurrent", "PGActual", "CurrentHP"],
        "hp_temp": ["HPTemp", "PGTemp", "TempHP"],
        "hit_dice": ["HDTotal", "DGTotales", "HitDice"],
        "hit_dice_current": ["HD", "DG"],
        "prof_bonus": ["ProfBonus", "BonoCompetencia", "PB"],

        # Salvaciones
        "save_str": ["ST Strength", "Salvacion Fuerza"],
        "save_dex": ["ST Dexterity", "Salvacion Destreza"],
        "save_con": ["ST Constitution", "Salvacion Constitucion"],
        "save_int": ["ST Intelligence", "Salvacion Inteligencia"],
        "save_wis": ["ST Wisdom", "Salvacion Sabiduria"],
        "save_cha": ["ST Charisma", "Salvacion Carisma"],

        # Habilidades
        "skill_acrobatics": ["Acrobatics", "Acrobacias"],
        "skill_animal_handling": ["Animal", "Animal Handling", "Trato con Animales"],
        "skill_arcana": ["Arcana", "Conocimiento Arcano"],
        "skill_athletics": ["Athletics", "Atletismo"],
        "skill_deception": ["Deception", "Engaño"],
        "skill_history": ["History", "Historia"],
        "skill_insight": ["Insight", "Perspicacia"],
        "skill_intimidation": ["Intimidation", "Intimidación"],
        "skill_investigation": ["Investigation", "Investigación"],
        "skill_medicine": ["Medicine", "Medicina"],
        "skill_nature": ["Nature", "Naturaleza"],
        "skill_perception": ["Perception", "Percepción"],
        "skill_performance": ["Performance", "Interpretación"],
        "skill_persuasion": ["Persuasion", "Persuasión"],
        "skill_religion": ["Religion", "Religión"],
        "skill_sleight_of_hand": ["SleightofHand", "Juego de Manos"],
        "skill_stealth": ["Stealth", "Sigilo"],
        "skill_survival": ["Survival", "Supervivencia"],

        # Textos Largos
        "features": ["Features and Traits", "Rasgos y Atributos", "FeaturesTraits"],
        "proficiencies": ["ProficienciesLang", "Otras Competencias e Idiomas", "Proficiencies"],
        "equipment": ["Equipment", "Equipo", "Inventario"],
        "personality": ["PersonalityTraits", "RasgosPersonalidad"],
        "ideals": ["Ideals", "Ideales"],
        "bonds": ["Bonds", "Vinculos"],
        "flaws": ["Flaws", "Defectos"],
    }

    @classmethod
    def load_character_from_pdf(cls, pdf_path: str) -> CharacterSheet:
        """Extrae los campos de un AcroForm y construye un CharacterSheet."""
        doc = pymupdf.open(pdf_path)
        form_data: Dict[str, str] = {}

        for page in doc:
            for widget in page.widgets():
                if widget.field_name:
                    val = widget.field_value or ""
                    form_data[widget.field_name.strip()] = str(val).strip()

        doc.close()

        def get_val(key_canonical: str, default: str = "") -> str:
            candidates = cls.FIELD_MAP.get(key_canonical, [key_canonical])
            for c in candidates:
                if c in form_data and form_data[c]:
                    return form_data[c]
                # Búsqueda insensible a mayúsculas
                for k, v in form_data.items():
                    if k.lower() == c.lower() and v:
                        return v
            return default

        def parse_int(key_canonical: str, default: int = 10) -> int:
            raw = get_val(key_canonical, str(default))
            raw = raw.replace("+", "").strip()
            try:
                return int(raw)
            except ValueError:
                return default

        # Descomponer clase y nivel (ej: "Paladín 4" o "Mago 1 / Clérigo 1")
        class_level_raw = get_val("class_level", "Aventurero 1")
        char_class = "Aventurero"
        level = 1
        m = re.search(r"([A-Za-zÀ-ÿ\s]+?)\s*(\d+)", class_level_raw)
        if m:
            char_class = m.group(1).strip()
            level = int(m.group(2))
        elif class_level_raw:
            char_class = class_level_raw

        abilities = {
            "FUE": parse_int("str", 10),
            "DES": parse_int("dex", 10),
            "CON": parse_int("con", 10),
            "INT": parse_int("int", 10),
            "SAB": parse_int("wis", 10),
            "CAR": parse_int("cha", 10),
        }

        # Armas y ataques (buscar patrones en campos Wpn Name / AtkBonus / Damage)
        weapons: List[WeaponAction] = []
        for i in range(1, 4):
            w_name = form_data.get(f"Wpn Name {i}") or form_data.get(f"Wpn{i} Name") or form_data.get(f"Arma {i}")
            if w_name:
                w_atk = form_data.get(f"Wpn{i} AtkBonus") or form_data.get(f"Wpn AtkBonus {i}") or "+0"
                w_dmg = form_data.get(f"Wpn{i} Damage") or form_data.get(f"Wpn Damage {i}") or "1d6"
                weapons.append(WeaponAction(
                    name=w_name.strip(),
                    attack_bonus=w_atk.strip(),
                    damage=w_dmg.strip(),
                    damage_type="Físico",
                    notes="Importado de AcroForm"
                ))

        features_text = get_val("features", "")
        features_list = []
        if features_text:
            for line in features_text.split("\n"):
                if line.strip():
                    features_list.append(CharacterFeature(
                        name=line.strip()[:60],
                        source=char_class,
                        description=line.strip()
                    ))

        return CharacterSheet(
            name=get_val("name", "Héroe sin Nombre"),
            char_class=char_class,
            level=level,
            race=get_val("race", "Humano"),
            background=get_val("background", "Personalizado"),
            alignment=get_val("alignment", "Neutral"),
            xp=parse_int("xp", 0),
            hp_current=parse_int("hp_current", 10),
            hp_max=parse_int("hp_max", 10),
            hp_temp=parse_int("hp_temp", 0),
            armor_class=parse_int("ac", 10),
            initiative_bonus=parse_int("initiative", 0),
            speed=get_val("speed", "9 m"),
            proficiency_bonus=parse_int("prof_bonus", calc_proficiency_bonus(level)),
            abilities=abilities,
            weapons=weapons,
            features=features_list,
            proficiencies_extra=get_val("proficiencies", ""),
            personality_traits=get_val("personality", ""),
            ideals=get_val("ideals", ""),
            bonds=get_val("bonds", ""),
            flaws=get_val("flaws", ""),
        )

    @classmethod
    def export_character_to_pdf(cls, char: CharacterSheet, template_pdf_path: str, output_path: str) -> str:
        """Rellena una plantilla AcroForm oficial con los datos del CharacterSheet."""
        if not os.path.exists(template_pdf_path):
            raise FileNotFoundError(f"Plantilla PDF no encontrada en {template_pdf_path}")

        doc = pymupdf.open(template_pdf_path)

        prof = calc_proficiency_bonus(char.level)
        fmt_mod = lambda m: f"+{m}" if m >= 0 else str(m)

        str_mod = calc_modifier(char.abilities.get("FUE", 10))
        dex_mod = calc_modifier(char.abilities.get("DES", 10))
        con_mod = calc_modifier(char.abilities.get("CON", 10))
        int_mod = calc_modifier(char.abilities.get("INT", 10))
        wis_mod = calc_modifier(char.abilities.get("SAB", 10))
        cha_mod = calc_modifier(char.abilities.get("CAR", 10))

        # Construir valores a exportar
        fill_dict: Dict[str, str] = {
            "CharacterName": char.name,
            "NombrePersonaje": char.name,
            "ClassLevel": f"{char.char_class} {char.level}",
            "ClaseNivel": f"{char.char_class} {char.level}",
            "Background": char.background,
            "Trasfondo": char.background,
            "Race": char.race,
            "Raza": char.race,
            "Alignment": char.alignment,
            "Alineamiento": char.alignment,
            "ExperiencePoints": str(char.xp),
            "XP": str(char.xp),
            "ProfBonus": fmt_mod(prof),
            "BonoCompetencia": fmt_mod(prof),
            "AC": str(char.armor_class),
            "CA": str(char.armor_class),
            "Initiative": fmt_mod(char.initiative_bonus),
            "Iniciativa": fmt_mod(char.initiative_bonus),
            "Speed": str(char.speed),
            "Velocidad": str(char.speed),
            "HPMax": str(char.hp_max),
            "PGMax": str(char.hp_max),
            "HPCurrent": str(char.hp_current),
            "PGActual": str(char.hp_current),
            "HPTemp": str(char.hp_temp) if char.hp_temp else "",
            "HDTotal": f"{char.hit_dice_max}d{char.hit_dice_faces}",
            "HD": str(char.hit_dice_current),

            # Atributos y Modificadores
            "STR": str(char.abilities.get("FUE", 10)),
            "FUE": str(char.abilities.get("FUE", 10)),
            "STRmod": fmt_mod(str_mod),
            "FUEmod": fmt_mod(str_mod),
            "DEX": str(char.abilities.get("DES", 10)),
            "DES": str(char.abilities.get("DES", 10)),
            "DEXmod": fmt_mod(dex_mod),
            "DESmod": fmt_mod(dex_mod),
            "CON": str(char.abilities.get("CON", 10)),
            "CONmod": fmt_mod(con_mod),
            "INT": str(char.abilities.get("INT", 10)),
            "INTmod": fmt_mod(int_mod),
            "WIS": str(char.abilities.get("SAB", 10)),
            "SAB": str(char.abilities.get("SAB", 10)),
            "WISmod": fmt_mod(wis_mod),
            "SABmod": fmt_mod(wis_mod),
            "CHA": str(char.abilities.get("CAR", 10)),
            "CAR": str(char.abilities.get("CAR", 10)),
            "CHAmod": fmt_mod(cha_mod),
            "CARmod": fmt_mod(cha_mod),

            # Textos
            "PersonalityTraits": char.personality_traits,
            "Ideals": char.ideals,
            "Bonds": char.bonds,
            "Flaws": char.flaws,
            "ProficienciesLang": f"Idiomas: {char.languages}\nSentidos: {char.senses}\n{char.proficiencies_extra}",
            "FeaturesTraits": "\n".join([f"• {f.name}: {f.description}" for f in char.features]),
        }

        # Armas (hasta 3 slots habituales de AcroForm)
        for i, w in enumerate(char.weapons[:3], 1):
            fill_dict[f"Wpn Name {i}"] = w.name
            fill_dict[f"Wpn{i} Name"] = w.name
            fill_dict[f"Wpn{i} AtkBonus"] = str(w.attack_bonus)
            fill_dict[f"Wpn AtkBonus {i}"] = str(w.attack_bonus)
            fill_dict[f"Wpn{i} Damage"] = f"{w.damage} {w.damage_type}"
            fill_dict[f"Wpn Damage {i}"] = f"{w.damage} {w.damage_type}"

        # Llenar widgets
        for page in doc:
            for widget in page.widgets():
                fn = widget.field_name
                if fn and fn in fill_dict:
                    widget.field_value = fill_dict[fn]
                    widget.update()
                elif fn:
                    # Coincidencia parcial insensible a mayúsculas
                    for k, val in fill_dict.items():
                        if fn.lower() == k.lower():
                            widget.field_value = val
                            widget.update()
                            break

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.save(output_path)
        doc.close()
        return output_path
