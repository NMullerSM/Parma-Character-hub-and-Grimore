"""
Puente PyWebView (RPC / IPC) para D&D Sanctum.
Conecta la interfaz de usuario React 18 con los motores de negocio en Python:
SQLite (db.py), OKF Compendium (okf_engine.py), TaleSpire Bridge, PDF Engine y Reglas 5e.
"""
import os
import sys
import json
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from core.models import CharacterSheet
from core.db import DatabaseManager
from core.okf_engine import OkfEngine
from core.pdf_engine import UniversalAcroFormHandler
from core.talespire_bridge import TaleSpireBridge
from core.point_buy import PointBuyCalculator, TOTAL_BUDGET, MIN_SCORE, MAX_SCORE
from core.rules import perform_short_rest, perform_long_rest
from core.session_ledger import SessionRollLedger, RollEntry


class DesktopBridge:
    """
    Clase expuesta a JavaScript en 'window.pywebview.api'.
    Todos los métodos retornan tipos serializables a JSON (dict, list, str, int, bool).
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.db = DatabaseManager()
        self.okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))
        self.ts = TaleSpireBridge()
        self.window = None

        # Migrar autosave_character.json si la base de datos está vacía
        autosave = os.path.join(base_dir, "autosave_character.json")
        chars = self.db.list_characters()
        if not chars and os.path.exists(autosave):
            self.db.migrate_from_json(autosave)

    def set_window(self, window):
        self.window = window

    # =========================================================================
    # GESTIÓN DE PERSONAJES
    # =========================================================================

    def list_characters(self) -> List[Dict[str, Any]]:
        """Lista resumen de todos los personajes guardados."""
        return self.db.list_characters()

    def get_active_character(self) -> Optional[Dict[str, Any]]:
        """Obtiene el personaje activo actual en formato diccionario."""
        char = self.db.get_active_character()
        return char.to_dict() if char else None

    def get_character_by_id(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Carga un personaje por ID."""
        char = self.db.get_character_by_id(char_id)
        return char.to_dict() if char else None

    def set_active_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Establece el personaje activo por ID y lo retorna."""
        char = self.db.set_active_character_by_id(char_id)
        return char.to_dict() if char else None

    def save_character(self, character_dict: Dict[str, Any], set_active: bool = True) -> Dict[str, Any]:
        """Guarda o actualiza un personaje en SQLite."""
        try:
            char = CharacterSheet.from_dict(character_dict)
            char_id = self.db.save_character(char, set_active=set_active)
            return {"success": True, "id": char_id, "error": None}
        except Exception as e:
            return {"success": False, "id": None, "error": str(e)}

    def delete_character(self, char_id: int) -> bool:
        """Elimina un personaje."""
        return self.db.delete_character(char_id)

    # =========================================================================
    # TALESPIRE BRIDGE & BANDEJA DE DADOS
    # =========================================================================

    def get_talespire_status(self) -> Dict[str, Any]:
        """Estado actual de TaleSpire en el equipo."""
        return {
            "is_installed": self.ts.is_installed,
            "is_running": self.ts.is_process_running(),
            "is_connected": self.ts.is_session_connected(),
            "state_label": self.ts.state.value,
        }

    def connect_talespire(self) -> Dict[str, Any]:
        """Conecta manualmente la sesión con TaleSpire."""
        success, message = self.ts.connect()
        return {"success": success, "message": message}

    def disconnect_talespire(self) -> Dict[str, Any]:
        """Desconecta de TaleSpire y vuelve a modo local."""
        self.ts.disconnect()
        return {"success": True, "message": "Sesión desconectada de TaleSpire."}

    def roll_dice(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una tirada de dados combinada.
        request: {
          'dice': { '20': 1, '6': 2 },
          'modifier': 3,
          'label': 'Ataque con Espada',
          'send_to_talespire': True
        }
        """
        pool_raw = request.get("dice", {"20": 1})
        modifier = int(request.get("modifier", 0))
        label = str(request.get("label", "Tirada")).strip() or "Tirada"
        send_ts = bool(request.get("send_to_talespire", True))

        pool = {int(k): int(v) for k, v in pool_raw.items() if int(v) > 0}
        if not pool:
            pool = {20: 1}

        rolls = []
        total = modifier
        for sides, count in pool.items():
            for _ in range(count):
                val = random.randint(1, sides)
                rolls.append({"sides": sides, "roll": val})
                total += val

        ts_sent = False
        if send_ts and self.ts.is_session_connected():
            try:
                url = self.ts.build_pool_url(pool, modifier=modifier, label=label)
                ts_sent = self.ts.send_roll(url)
                # Ejecutar micro-gesto físico
                ts_mode = self.db.get_setting("talespire_mode", "dm")
                self.ts.execute_throw_gesture(ts_mode=ts_mode)
            except Exception as e:
                print(f"[DesktopBridge] Error enviando a TaleSpire: {e}")

        # Registrar en Ledger de sesión
        active_char = self.db.get_active_character()
        char_name = active_char.name if active_char else "Héroe"
        dice_repr = " + ".join([f"{count}d{sides}" for sides, count in pool.items()])
        mod_repr = f" + {modifier}" if modifier > 0 else (f" - {abs(modifier)}" if modifier < 0 else "")
        formula_str = f"{dice_repr}{mod_repr}" if mod_repr else dice_repr
        detail_str = f"Dados: [{', '.join(str(r['roll']) for r in rolls)}]"
        is_crit = any(r["sides"] == 20 and r["roll"] == 20 for r in rolls)
        is_fumble = any(r["sides"] == 20 and r["roll"] == 1 for r in rolls)
        channel_str = "TaleSpire 3D" if ts_sent else "Motor Local"

        SessionRollLedger.get_current().record_roll(
            character_name=char_name,
            reason=label,
            formula=formula_str,
            detail=detail_str,
            total=total,
            is_crit=is_crit,
            is_fumble=is_fumble,
            channel=channel_str,
        )

        return {
            "total": total,
            "dice_rolls": rolls,
            "modifier": modifier,
            "label": label,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "talespire_sent": ts_sent,
        }

    def trigger_talespire_gesture(self) -> bool:
        """Simula manualmente el gesto de lanzamiento en TaleSpire."""
        ts_mode = self.db.get_setting("talespire_mode", "dm")
        return self.ts.execute_throw_gesture(ts_mode=ts_mode)

    # =========================================================================
    # COMPENDIO OKF (MARKDOWN & REGLAS)
    # =========================================================================

    def get_compendium_categories(self) -> List[Dict[str, Any]]:
        """Lista las categorías disponibles en el compendio OKF con su conteo."""
        categories = [
            {"id": "clases", "label": "Clases y Subclases", "count": len(self.okf.get_classes())},
            {"id": "especies_y_linajes", "label": "Especies y Linajes", "count": len(self.okf.get_races())},
            {"id": "conjuros", "label": "Grimorio de Conjuros", "count": len(self.okf.get_spells())},
            {"id": "trasfondos", "label": "Trasfondos", "count": len(self.okf.get_backgrounds())},
            {"id": "dotes", "label": "Dotes de Personaje", "count": len(self.okf.get_feats())},
            {"id": "equipo_y_armamento", "label": "Equipo y Armamento", "count": len(self.okf.get_equipment())},
            {"id": "reglas_y_mecanicas", "label": "Reglas y Mecánicas", "count": len(self.okf.get_rules())},
        ]
        return categories

    def search_compendium(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Búsqueda de texto completo en el compendio OKF."""
        query_clean = query.strip().lower()
        if not query_clean:
            return []

        results = []
        entries = self.okf.search_all(query_clean)
        for item in entries:
            if category and item.get("category") != category:
                continue
            results.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "category": item.get("category", ""),
                "snippet": item.get("snippet", ""),
                "path": item.get("path", ""),
            })
            if len(results) >= 50:
                break
        return results

    def get_compendium_entry(self, category: str, entry_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene una entrada completa del compendio OKF con su markdown."""
        return self.okf.get_entry(category, entry_name)

    # =========================================================================
    # REGLAS 5E & DESCANSO
    # =========================================================================

    def validate_point_buy(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Valida si los atributos respetan el presupuesto de 27 puntos de 5e."""
        spent = PointBuyCalculator.calculate_used_points(scores)
        remaining = PointBuyCalculator.get_remaining_points(scores)
        valid = remaining >= 0 and all(MIN_SCORE <= v <= MAX_SCORE for v in scores.values())
        error = None
        if remaining < 0:
            error = f"Presupuesto excedido por {abs(remaining)} puntos."
        elif any(v < MIN_SCORE or v > MAX_SCORE for v in scores.values()):
            error = f"Atributos fuera del rango legal ({MIN_SCORE}-{MAX_SCORE})."

        return {
            "valid": valid,
            "points_spent": spent,
            "points_remaining": remaining,
            "error": error,
            "standard_array": [15, 14, 13, 12, 10, 8],
            "min_score": MIN_SCORE,
            "max_score": MAX_SCORE,
        }

    def perform_rest(self, char_id: int, rest_type: str, hit_dice_spent: int = 0) -> Dict[str, Any]:
        """Aplica descanso corto o descanso largo y actualiza la base de datos."""
        char = self.db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        if rest_type == "long":
            perform_long_rest(char)
        else:
            perform_short_rest(char, hit_dice_spent=hit_dice_spent)

        self.db.save_character(char, set_active=(char.id == getattr(self.db.get_active_character(), "id", None)))
        return {"success": True, "character": char.to_dict()}

    # =========================================================================
    # MOTOR DE PDFS (ACROFORMS OFICIALES)
    # =========================================================================

    def export_character_pdf(self, char_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Exporta el personaje activo a una hoja PDF oficial rellena con AcroForms."""
        char = self.db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        template_pdf = os.path.join(self.base_dir, "data", "characters", "Artanis LVL 4.pdf")
        if not os.path.exists(template_pdf):
            template_pdf = os.path.join(self.base_dir, "Artanis LVL 4.pdf")

        if not target_path:
            clean_name = "".join(c for c in char.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            target_path = os.path.join(self.base_dir, "data", "characters", f"{clean_name}_Sheet.pdf")

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            handler = UniversalAcroFormHandler(template_pdf)
            handler.fill_from_character(char, target_path)
            return {"success": True, "path": target_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # AJUSTES & TEMAS
    # =========================================================================

    def get_settings(self) -> Dict[str, Any]:
        """Retorna todos los ajustes configurados."""
        return {
            "theme": self.db.get_setting("theme", "dark-obsidian"),
            "talespire_mode": self.db.get_setting("talespire_mode", "dm"),
            "talespire_enabled": self.db.get_setting("talespire_enabled", "true") == "true",
            "okf_path": self.db.get_setting("okf_path", os.path.join(self.base_dir, "okf_dnd5e")),
            "custom_themes_dir": os.path.join(self.base_dir, "themes"),
        }

    def set_setting(self, key: str, value: Any) -> bool:
        """Guarda un ajuste en la base de datos."""
        self.db.set_setting(key, str(value))
        return True

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Retorna temas base y temas personalizados en themes/."""
        themes = [
            {"id": "dark-obsidian", "name": "Obsidian Sanctum (Oscuro)", "is_dark": True},
            {"id": "light-parchment", "name": "Illuminated Grimoire (Claro)", "is_dark": False},
        ]
        themes_dir = os.path.join(self.base_dir, "themes")
        if os.path.exists(themes_dir):
            for entry in os.listdir(themes_dir):
                theme_path = os.path.join(themes_dir, entry)
                if os.path.isdir(theme_path):
                    json_path = os.path.join(theme_path, "theme.json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            themes.append({
                                "id": entry,
                                "name": meta.get("name", entry),
                                "is_dark": meta.get("is_dark", True),
                            })
                        except Exception:
                            pass
        return themes

    # =========================================================================
    # DIÁLOGOS NATIVOS DE ARCHIVO (PyWebView)
    # =========================================================================

    def open_image_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar imagen de retrato."""
        if not self.window:
            return None
        file_types = ("Archivos de Imagen (*.png;*.jpg;*.jpeg;*.webp)", "Todos los Archivos (*.*)")
        result = self.window.create_file_dialog(pywebview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None

    def open_pdf_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar un PDF de personaje."""
        if not self.window:
            return None
        file_types = ("Archivos PDF (*.pdf)", "Todos los Archivos (*.*)")
        result = self.window.create_file_dialog(pywebview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None
