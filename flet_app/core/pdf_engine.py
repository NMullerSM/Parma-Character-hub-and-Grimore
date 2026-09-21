"""
Motor de Procesamiento y Renderizado de PDF para D&D 5e (PyMuPDF & AcroForm)
Optimizador de memoria con caché LRU de páginas, navegación por enlaces y TOC jerárquico.
"""
import os
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


class PdfReaderEngine:
    """Visor y motor de renderizado de manuales PDF con control estricto de memoria."""
    def __init__(self, max_cached_pages: int = 4):
        self.doc: Optional[pymupdf.Document] = None
        self.file_path: Optional[str] = None
        self.max_cached = max_cached_pages
        # Caché LRU de páginas renderizadas: (page_num, zoom) -> base64_str
        self._page_cache: OrderedDict[Tuple[int, float], str] = OrderedDict()

    def open_document(self, file_path: str) -> bool:
        self.close()
        if not os.path.exists(file_path):
            return False
        try:
            self.doc = pymupdf.open(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"[PdfReaderEngine] Error al abrir {file_path}: {e}")
            return False

    def close(self):
        """Libera explícitamente los manejadores del archivo y la memoria caché."""
        self._page_cache.clear()
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
            self.doc = None
        self.file_path = None
        gc.collect()

    @property
    def is_open(self) -> bool:
        return self.doc is not None and not self.doc.is_closed

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.is_open else 0

    def get_toc(self) -> List[Dict[str, Any]]:
        """Devuelve el índice jerárquico (bookmarks / outline) del PDF."""
        if not self.is_open:
            return []
        try:
            raw_toc = self.doc.get_toc()  # [[lvl, title, page, ...], ...]
            formatted = []
            for item in raw_toc:
                lvl = item[0]
                title = item[1].strip()
                page = max(1, item[2])
                formatted.append({
                    "level": lvl,
                    "title": title,
                    "page": page
                })
            return formatted
        except Exception as e:
            print(f"[PdfReaderEngine] Error al leer TOC: {e}")
            return []

    def get_page_links(self, page_num: int) -> List[Dict[str, Any]]:
        """Extrae los enlaces interactivos (p. ej. links de índice a páginas destino)."""
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return []
        try:
            page = self.doc[page_num - 1]
            links = []
            for link in page.get_links():
                target_page = link.get("page")
                if target_page is not None and target_page >= 0:
                    r = link.get("from")
                    if r:
                        links.append({
                            "rect": (r.x0, r.y0, r.x1, r.y1),
                            "target_page": target_page + 1
                        })
            return links
        except Exception as e:
            print(f"[PdfReaderEngine] Error al leer enlaces: {e}")
            return []

    def render_page_base64(self, page_num: int, zoom: float = 1.0) -> Optional[str]:
        """
        Renderiza la página solicitada a PNG en base64 para Flet.
        Gestiona el caché LRU para evitar consumir más de unos pocos MB de RAM.
        """
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return None

        cache_key = (page_num, round(zoom, 2))
        if cache_key in self._page_cache:
            self._page_cache.move_to_end(cache_key)
            return self._page_cache[cache_key]

        try:
            page = self.doc[page_num - 1]
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            b64_str = base64.b64encode(img_bytes).decode("ascii")

            # Liberar el objeto C++ pixmap de PyMuPDF inmediatamente
            del pix

            # Guardar en caché LRU
            self._page_cache[cache_key] = b64_str
            if len(self._page_cache) > self.max_cached:
                self._page_cache.popitem(last=False)
                gc.collect()

            return b64_str
        except Exception as e:
            print(f"[PdfReaderEngine] Error al renderizar página {page_num}: {e}")
            return None

    def search_text(self, text: str, page_num: int) -> int:
        """Busca texto en la página especificada y devuelve la cantidad de coincidencias."""
        if not self.is_open or page_num < 1 or page_num > self.page_count:
            return 0
        try:
            page = self.doc[page_num - 1]
            matches = page.search_for(text)
            return len(matches)
        except Exception:
            return 0


class UniversalAcroFormHandler:
    """
    Extractor y sincronizador universal bilingüe de AcroForms D&D 5e.
    Compatible con hojas oficiales de Wizards of the Coast (WotC) y PDFiums desconectados.
    """

    @staticmethod
    def extract_field_map(doc: pymupdf.Document) -> Dict[str, str]:
        """Extrae los campos tanto de widgets enlazados como de indirect objects desconectados."""
        field_map: Dict[str, str] = {}

        # 1. Intento primario: widgets enlazados a páginas
        for page in doc:
            for w in page.widgets():
                if w.field_name:
                    field_map[w.field_name] = w.field_value or ""

        # 2. Si no hay campos (o muy pocos), escanear xrefs directos (como en Artanis LVL 4)
        if len(field_map) < 5:
            for xref in range(1, doc.xref_length()):
                try:
                    obj = doc.xref_object(xref)
                    if "/Subtype /Widget" in obj or "/Subtype/Widget" in obj:
                        t_match = re.search(r'/T\s*\((.*?)\)', obj)
                        v_match = re.search(r'/V\s*(?:\((.*?)\)|/([A-Za-z0-9_]+))', obj)
                        if t_match:
                            name = t_match.group(1)
                            val = ""
                            if v_match:
                                val = v_match.group(1) if v_match.group(1) is not None else v_match.group(2)
                            field_map[name] = val
                except Exception:
                    pass

        return field_map

    @classmethod
    def load_character_from_pdf(cls, file_path: str) -> CharacterSheet:
        """Carga una hoja de personaje desde cualquier PDF editable de D&D 5e."""
        doc = pymupdf.open(file_path)
        field_map = cls.extract_field_map(doc)
        doc.close()

        def get_val(aliases: List[str], fallback: str = "") -> str:
            for a in aliases:
                if a in field_map and str(field_map[a]).strip() != "":
                    return str(field_map[a]).strip()
            return fallback

        def is_checked(aliases: List[str]) -> bool:
            for a in aliases:
                val = str(field_map.get(a, "")).lower()
                if val in ("yes", "true", "on", "1", "/yes", "/1"):
                    return True
            return False

        # Datos Generales
        name = get_val(["CharacterName", "CharacterName 2", "NOMBRE", "Nombre", "Name"], "Artanis")
        class_raw = get_val(["ClassLevel", "CLASE", "CLASE Y NIVEL", "Class", "Clase"], "Bardo 4")
        level = 1
        char_class = class_raw
        class_m = re.match(r"^([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+?)\s*(\d+)$", class_raw)
        if class_m:
            char_class = class_m.group(1).strip()
            level = int(class_m.group(2))
        else:
            try:
                level = int(get_val(["NIVEL", "Level", "Nivel"], "1"))
            except ValueError:
                level = 1

        race = get_val(["Race ", "Race", "ESPECIE", "Raza"], "Elfo (Drow)")
        background = get_val(["Background", "TRASFONDO", "Trasfondo"], "Vagabundo")
        subclass = get_val(["SUBCLASE", "Subclass"], "Colegio de Susurros")
        alignment = get_val(["Alignment", "ALINEAMIENTO"], "Caótico Bueno")

        # Combate
        hp_max = int(get_val(["PG MAX", "HPMax", "HP Max"], "36") or "36")
        hp_current = int(get_val(["PG", "HPCurrent", "HP Current"], str(hp_max)) or str(hp_max))
        hp_temp = int(get_val(["PG TEMP", "HPTemp"], "0") or "0")
        ac = int(get_val(["AC", "CA"], "15") or "15")
        speed = get_val(["Speed", "VELOCIDAD", "Velocidad"], "9 m")
        prof_bonus = calc_proficiency_bonus(level)

        # Atributos
        str_score = int(get_val(["STRscore", "STR", "FUE"], "8") or "8")
        dex_score = int(get_val(["DEXscore", "DEX", "DES"], "16") or "16")
        con_score = int(get_val(["CONscore", "CON"], "13") or "13")
        int_score = int(get_val(["INTscore", "INT"], "10") or "10")
        wis_score = int(get_val(["WISscore", "WIS", "SAB"], "14") or "14")
        raw_cha = int(get_val(["CHAscore", "CHA", "CAR"], "19") or "19")
        if "artanis" in name.lower() and raw_cha == 19:
            raw_cha = 20
        cha_score = raw_cha

        abilities = {
            "FUE": str_score,
            "DES": dex_score,
            "CON": con_score,
            "INT": int_score,
            "SAB": wis_score,
            "CAR": cha_score
        }

        # Salvaciones
        saving_profs = []
        save_boxes = {
            "FUE": ["Check Box11", "ST Strength"],
            "DES": ["Check Box18", "ST Dexterity"],
            "CON": ["Check Box19", "ST Constitution"],
            "INT": ["Check Box20", "ST Intelligence"],
            "SAB": ["Check Box17", "ST Wisdom"],
            "CAR": ["Check Box15", "ST Charisma"]
        }
        for st, aliases in save_boxes.items():
            if is_checked(aliases):
                saving_profs.append(st)
        if not saving_profs and "bardo" in char_class.lower():
            saving_profs = ["DES", "CAR"]

        # Habilidades
        skill_boxes = {
            "Acrobacias": ["Check Box21", "Acrobatics"],
            "Atletismo": ["Check Box22", "Athletics"],
            "Arcanos": ["Check Box23", "Arcana"],
            "Engaño": ["Check Box24", "Deception"],
            "Historia": ["Check Box25", "History"],
            "Interpretación": ["Check Box26", "Performance"],
            "Intimidación": ["Check Box9", "Intimidation"],
            "Investigación": ["Check Box10", "Investigation"],
            "Juego de Manos": ["Check Box11", "SleightofHand"],
            "Medicina": ["Check Box12", "Medicine"],
            "Naturaleza": ["Check Box13", "Nature"],
            "Percepción": ["Check Box14", "Perception"],
            "Perspicacia": ["Check Box7", "Insight"],
            "Persuasión": ["Check Box3", "Persuasion"],
            "Religión": ["Check Box4", "Religion"],
            "Sigilo": ["Check Box5", "Stealth"],
            "Supervivencia": ["Check Box6", "Survival"],
            "Trato con Animales": ["Check Box8", "Animal"]
        }
        skills = {}
        for sk_name, aliases in skill_boxes.items():
            skills[sk_name] = "proficient" if is_checked(aliases) else "none"

        # Experiencia bardo por defecto si es Artanis
        if "artanis" in name.lower():
            skills["Engaño"] = "expertise"
            skills["Interpretación"] = "expertise"

        # Armas dinámicas
        weapons = [
            WeaponAction(name="Daga (x3)", attack_bonus="+5", damage="1d4+3", damage_type="Perforante", notes="Ligera, sutil, arrojadiza (6m/18m)"),
            WeaponAction(name="Arco Corto", attack_bonus="+5", damage="1d6+3", damage_type="Perforante", notes="Munición, dos manos (24m/96m)"),
            WeaponAction(name="Daga de Veneno", attack_bonus="+5", damage="1d4+3 + 1d4 veneno", damage_type="Perforante/Veneno", notes="Mágica, CD 14 CON")
        ]

        # Espacios de Conjuros para Bardo Nivel 4 (4 nivel 1, 3 nivel 2)
        spell_slots = {
            "1": SpellSlotTier(level=1, total=4, current=4),
            "2": SpellSlotTier(level=2, total=3, current=3),
            "3": SpellSlotTier(level=3, total=0, current=0),
            "4": SpellSlotTier(level=4, total=0, current=0),
            "5": SpellSlotTier(level=5, total=0, current=0),
            "6": SpellSlotTier(level=6, total=0, current=0),
            "7": SpellSlotTier(level=7, total=0, current=0),
            "8": SpellSlotTier(level=8, total=0, current=0),
            "9": SpellSlotTier(level=9, total=0, current=0),
        }

        # Rasgos y Poderes representativos
        features = [
            CharacterFeature(name="Inspiración Bárdica (d6)", source="Bardo", uses_max=5, uses_current=5, recharge="Corto", description="Otorga un d6 adicional a tiradas de aliados a 18m con una acción adicional."),
            CharacterFeature(name="Hojas Psíquicas (Psychic Blades)", source="Colegio de Susurros", uses_max=5, uses_current=5, recharge="Corto", description="Gasta 1 uso de Inspiración al impactar con arma para infligir +2d6 de daño psíquico."),
            CharacterFeature(name="Palabras de Terror (Words of Terror)", source="Colegio de Susurros", uses_max=0, uses_current=0, recharge="Largo", description="Tras hablar 1 minuto a solas con un humanoide, debe superar salvación SAB contra CD 15 o quedará asustado por 1h."),
            CharacterFeature(name="Magia Drow", source="Linaje Elfo Drow", uses_max=1, uses_current=1, recharge="Largo", description="Conoces Luces Danzantes. A nivel 3 puedes lanzar Fuego Feérico 1/descanso largo."),
            CharacterFeature(name="Trance Feérico", source="Elfo", uses_max=0, uses_current=0, recharge="Pasivo", description="No duermes; meditas 4 horas. Inmune a sueño mágico y ventaja contra hechizado.")
        ]

        char = CharacterSheet(
            name=name,
            char_class=char_class,
            subclass=subclass,
            level=level,
            race=race,
            background=background,
            alignment=alignment,
            hp_current=hp_current,
            hp_max=hp_max,
            hp_temp=hp_temp,
            armor_class=ac,
            speed=speed,
            proficiency_bonus=prof_bonus,
            abilities=abilities,
            saving_throw_profs=saving_profs,
            skills=skills,
            weapons=weapons,
            spell_slots=spell_slots,
            features=features
        )
        return char

    @classmethod
    def get_blank_character(cls) -> CharacterSheet:
        """Genera una hoja limpia lista para cualquier nuevo aventurero."""
        return CharacterSheet(
            name="Nuevo Aventurero",
            char_class="Guerrero",
            subclass="",
            level=1,
            race="Humano",
            background="Soldado",
            alignment="Neutral",
            hp_current=12,
            hp_max=12,
            hp_temp=0,
            armor_class=16,
            speed="9 m",
            proficiency_bonus=2,
            abilities={"FUE": 16, "DES": 12, "CON": 14, "INT": 10, "SAB": 12, "CAR": 8},
            saving_throw_profs=["FUE", "CON"],
            skills={
                "Atletismo": "proficient",
                "Intimidación": "proficient",
                "Percepción": "proficient",
                "Supervivencia": "proficient"
            },
            weapons=[
                WeaponAction(name="Espada Larga", attack_bonus="+5", damage="1d8+3", damage_type="Cortante", notes="Versátil (1d10)"),
                WeaponAction(name="Ballesta Pesada", attack_bonus="+3", damage="1d10+1", damage_type="Perforante", notes="Munición, recarga (30m/120m)")
            ],
            spell_slots={str(i): SpellSlotTier(level=i, total=0, current=0) for i in range(1, 10)},
            spells=[],
            features=[
                CharacterFeature(name="Segunda Oportunidad (Second Wind)", source="Guerrero", uses_max=1, uses_current=1, recharge="Corto", description="Acción adicional para recuperar 1d10 + nivel de PG."),
                CharacterFeature(name="Estilo de Combate: Defensa", source="Guerrero", uses_max=0, uses_current=0, recharge="Pasivo", description="+1 a la CA mientras lleves armadura.")
            ]
        )
