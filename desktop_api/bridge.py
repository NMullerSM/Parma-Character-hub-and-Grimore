"""
Puente PyWebView (RPC / IPC) para D&D Sanctum.
Conecta la interfaz de usuario React con los motores de negocio en Python:
SQLite (db.py), OKF Compendium (okf_engine.py), TaleSpire Bridge, PDF Engine,
Point Buy, Quick Build, Random Generator y Reglas 5e.
"""
import os
import sys
import json
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import webview

from core.models import (
    CharacterSheet,
    WeaponAction,
    SpellItem,
    SpellSlotTier,
    CharacterFeature,
    SessionLog,
    NetworkNode,
    NetworkEdge,
)
from core.db import DatabaseManager
from core.okf_engine import OkfEngine
from core.pdf_engine import UniversalAcroFormHandler, PdfReaderEngine
from core.talespire_bridge import TaleSpireBridge
from core.point_buy import PointBuyCalculator, TOTAL_BUDGET, MIN_SCORE, MAX_SCORE
from core.quick_build import QuickBuildEngine, CLASS_QUICK_PRESETS, STANDARD_ARRAY
from core.random_generator import (
    RandomCharacterGenerator,
    CLASSES_LIST,
    SPECIES_LIST,
    ALIGNMENTS_LIST,
)
from core.rules import (
    SKILLS_MAP,
    CLASS_HIT_DICE,
    CLASS_CASTING_ABILITY,
    DND_CONDITIONS,
    calc_modifier,
    calc_proficiency_bonus,
    get_skill_modifier,
    get_saving_throw_modifier,
    get_character_spell_stats,
    perform_short_rest,
    perform_long_rest,
    roll_dice_pool,
    compute_dynamic_features,
    get_class_progression_limits,
)
from core.session_ledger import SessionRollLedger
from core.srd_importer import SrdImporter
from .tunnel_manager import CloudflareTunnelManager
from .session_server import DmSessionServer


# Tabla de ranuras de conjuro para lanzadores completos (Nvl 1-20)
FULL_CASTER_SLOTS: Dict[int, Dict[str, int]] = {
    1: {"1": 2},
    2: {"1": 3},
    3: {"1": 4, "2": 2},
    4: {"1": 4, "2": 3},
    5: {"1": 4, "2": 3, "3": 2},
    6: {"1": 4, "2": 3, "3": 3},
    7: {"1": 4, "2": 3, "3": 3, "4": 1},
    8: {"1": 4, "2": 3, "3": 3, "4": 2},
    9: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    10: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    11: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    12: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    13: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    16: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1},
}


def _compute_spell_slots_for_class(char_class: str, level: int) -> Dict[str, SpellSlotTier]:
    """Calcula las ranuras de conjuro oficiales según la clase y nivel."""
    tiers = {str(i): SpellSlotTier(level=i, total=0, current=0) for i in range(1, 10)}
    c_norm = char_class.strip()
    full_casters = {"Bardo", "Clérigo", "Druida", "Hechicero", "Mago"}
    half_casters = {"Paladín", "Explorador", "Artífice"}

    if c_norm in full_casters:
        slot_map = FULL_CASTER_SLOTS.get(max(1, min(20, level)), {})
        for lvl_str, count in slot_map.items():
            tiers[lvl_str] = SpellSlotTier(level=int(lvl_str), total=count, current=count)
    elif c_norm in half_casters:
        eff_level = max(1, (level + 1) // 2)
        slot_map = FULL_CASTER_SLOTS.get(min(10, eff_level), {})
        for lvl_str, count in slot_map.items():
            tiers[lvl_str] = SpellSlotTier(level=int(lvl_str), total=count, current=count)
    elif c_norm == "Brujo":
        pact_lvl = min(5, (level + 1) // 2)
        pact_slots = 1 if level == 1 else (2 if level < 11 else (3 if level < 17 else 4))
        tiers[str(pact_lvl)] = SpellSlotTier(level=pact_lvl, total=pact_slots, current=pact_slots)

    return tiers


class DesktopBridge:
    """
    Clase expuesta a JavaScript en 'window.pywebview.api'.
    Todos los métodos retornan tipos serializables a JSON (dict, list, str, int, bool).
    """

    def __init__(self, base_dir: Optional[str] = None):
        if not base_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._base_dir = base_dir
        self._db = DatabaseManager()
        self._okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))
        self._ts = TaleSpireBridge()
        self._pdf_reader = PdfReaderEngine()
        self._tunnel_mgr = CloudflareTunnelManager(base_dir)
        self._session_server = DmSessionServer(self._db, base_dir)
        self._window = None

        # Migrar autosave_character.json si la base de datos está vacía
        autosave = os.path.join(base_dir, "autosave_character.json")
        chars = self._db.list_characters()
        if not chars and os.path.exists(autosave):
            self._db.migrate_from_json(autosave)

    def set_window(self, window):
        self._window = window

    def _is_active_character_id(self, char_id: int) -> bool:
        active = self._db.get_active_character()
        return bool(active and active.id == char_id)

    @staticmethod
    def _parse_speed_feet(speed_val: Any) -> int:
        if isinstance(speed_val, (int, float)):
            return int(speed_val)
        s = str(speed_val or "30").lower()
        if "7.5" in s or "7,5" in s or "25" in s:
            return 25
        if "10.5" in s or "10,5" in s or "35" in s:
            return 35
        return 30

    @staticmethod
    def _serialize_character(char: Optional[CharacterSheet]) -> Optional[Dict[str, Any]]:
        """Serializa CharacterSheet a dict compatible con TypeScript."""
        if not char:
            return None
        data = char.to_dict()
        data["spell_stats"] = get_character_spell_stats(char)
        data["features"] = compute_dynamic_features(char)
        return data

    # =========================================================================
    # GESTIÓN DE PERSONAJES
    # =========================================================================

    def list_characters(self) -> List[Dict[str, Any]]:
        """Lista resumen de todos los personajes guardados."""
        return self._db.list_characters()

    def get_active_character(self) -> Optional[Dict[str, Any]]:
        """Devuelve el personaje activo con estadísticas calculadas."""
        char = self._db.get_active_character()
        return self._serialize_character(char)

    def get_character_by_id(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve un personaje por su ID."""
        char = self._db.get_character_by_id(char_id)
        return self._serialize_character(char)

    def set_active_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Establece el personaje activo por ID."""
        self._db.set_active_character(char_id)
        return self.get_active_character()

    def save_character(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda o actualiza un personaje en SQLite."""
        try:
            char = CharacterSheet.from_dict(char_data)
            is_active = self._is_active_character_id(char.id) if char.id else True
            char_id = self._db.save_character(char, set_active=is_active)
            saved = self._db.get_character_by_id(char_id)
            return {"success": True, "id": char_id, "character": self._serialize_character(saved)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_character(self, char_id: int) -> bool:
        """Elimina un personaje y sus datos vinculados."""
        return self._db.delete_character(char_id)

    def upload_character_portrait(self, char_id: int) -> Dict[str, Any]:
        """Abre un selector nativo de imagen, guarda una copia local y actualiza SQLite."""
        if not self._window:
            return {"success": False, "error": "Ventana no disponible."}

        file_types = ("Archivos de Imagen (*.png;*.jpg;*.jpeg;*.webp)", "Todos los Archivos (*.*)")
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if not result or len(result) == 0:
            return {"success": False, "error": "Selección cancelada."}

        source_path = result[0]
        try:
            dest_dir = os.path.join(self._base_dir, "data", "characters", "portraits")
            os.makedirs(dest_dir, exist_ok=True)
            ext = os.path.splitext(source_path)[1]
            dest_file = f"portrait_char_{char_id}{ext}"
            dest_path = os.path.join(dest_dir, dest_file)
            shutil.copy2(source_path, dest_path)

            with open(dest_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png" if ext.lower() == ".png" else ("image/webp" if ext.lower() == ".webp" else "image/jpeg")
            b64_url = f"data:{mime};base64,{b64_data}"

            char = self._db.get_character_by_id(char_id)
            if char:
                char.portrait_path = dest_path
                char.portrait_base64 = b64_url
                self._db.save_character(char, set_active=self._is_active_character_id(char_id))
                return {
                    "success": True,
                    "portrait_path": dest_path,
                    "portrait_base64": b64_url,
                    "character": self._serialize_character(char),
                }
            return {"success": True, "portrait_path": dest_path, "portrait_base64": b64_url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_character_portrait_base64(self, char_id: int, image_base64: str) -> Dict[str, Any]:
        """Guarda un retrato en formato Base64 directamente en la ficha del héroe y lo persiste en disco."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        try:
            dest_dir = os.path.join(self._base_dir, "data", "characters", "portraits")
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = f"portrait_char_{char_id}.png"
            dest_path = os.path.join(dest_dir, dest_file)

            pure_b64 = image_base64
            if "," in image_base64:
                pure_b64 = image_base64.split(",")[1]

            with open(dest_path, "wb") as f:
                f.write(base64.b64decode(pure_b64))

            char.portrait_path = dest_path
            char.portrait_base64 = image_base64
            self._db.save_character(char, set_active=self._is_active_character_id(char_id))
            return {
                "success": True,
                "portrait_base64": image_base64,
                "portrait_path": dest_path,
                "character": self._serialize_character(char)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_ai_portrait(
        self,
        prompt: str,
        provider: str = "google",
        api_key: str = "",
        api_url: str = "",
        model: str = ""
    ) -> Dict[str, Any]:
        """
        Genera un retrato con IA llamando directamente a Google Imagen 3, OpenAI DALL-E o Pollinations.ai.
        """
        import httpx

        provider_clean = (provider or "google").strip().lower()
        prompt_clean = prompt.strip()
        if not prompt_clean:
            return {"success": False, "error": "El prompt de apariencia no puede estar vacío."}

        try:
            if provider_clean == "pollinations":
                clean_desc = prompt_clean[:1800].strip()
                import urllib.parse
                encoded = urllib.parse.quote(clean_desc)
                endpoint = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed=42&model=flux&enhance=false"
                resp = httpx.get(endpoint, timeout=45.0, follow_redirects=True)
                if resp.status_code == 200 and resp.content:
                    b64 = base64.b64encode(resp.content).decode("utf-8")
                    return {"success": True, "image_base64": f"data:image/jpeg;base64,{b64}"}
                return {"success": False, "error": f"Pollinations respondió con error HTTP {resp.status_code}"}

            elif provider_clean == "google":
                key = api_key.strip()
                if not key:
                    return {"success": False, "error": "Falta la API Key de Google AI Studio."}
                m = model.strip() or "imagen-3.0-generate-002"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:predict?key={key}"
                payload = {
                    "instances": [{"prompt": prompt_clean}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "1:1", "outputOptions": {"mimeType": "image/jpeg"}}
                }
                resp = httpx.post(url, json=payload, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    preds = data.get("predictions", [])
                    if preds and "bytesBase64Encoded" in preds[0]:
                        b64_raw = preds[0]["bytesBase64Encoded"]
                        return {"success": True, "image_base64": f"data:image/jpeg;base64,{b64_raw}"}
                    return {"success": False, "error": "Formato de respuesta desconocido de Google Imagen."}
                elif resp.status_code == 403:
                    return {"success": False, "error": "Acceso denegado (403). Verifica que la API Key de Google AI Studio sea válida."}
                return {"success": False, "error": f"Error de Google AI ({resp.status_code}): {resp.text[:200]}"}

            elif provider_clean == "openai":
                key = api_key.strip()
                if not key:
                    return {"success": False, "error": "Falta la API Key de OpenAI."}
                url = api_url.strip() or "https://api.openai.com/v1/images/generations"
                m = model.strip() or "dall-e-3"
                payload = {"model": m, "prompt": prompt_clean, "n": 1, "size": "1024x1024", "response_format": "b64_json"}
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                resp = httpx.post(url, json=payload, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    b64_raw = data.get("data", [{}])[0].get("b64_json", "")
                    if b64_raw:
                        return {"success": True, "image_base64": f"data:image/png;base64,{b64_raw}"}
                return {"success": False, "error": f"Error de OpenAI ({resp.status_code}): {resp.text[:200]}"}

            return {"success": False, "error": f"Proveedor '{provider}' no soportado."}
        except Exception as e:
            return {"success": False, "error": f"Excepción durante la generación de imagen: {str(e)}"}

    def export_character_json(self, char_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Exporta la ficha a un archivo JSON estándar."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        if not target_path:
            if not self._window:
                return {"success": False, "error": "Ventana no disponible para diálogo de guardado."}
            file_types = ("Archivos JSON (*.json)", "Todos los Archivos (*.*)")
            save_name = f"{char.name.replace(' ', '_')}.json"
            res = self._window.create_file_dialog(webview.SAVE_DIALOG, save_filename=save_name, file_types=file_types)
            if not res:
                return {"success": False, "error": "Exportación cancelada."}
            target_path = res if isinstance(res, str) else res[0]

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(char.to_dict(), f, indent=2, ensure_ascii=False)
            return {"success": True, "path": target_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_character_json(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Importa un personaje desde un archivo JSON y lo guarda en SQLite."""
        if not file_path:
            if not self._window:
                return {"success": False, "error": "Ventana no disponible para diálogo de archivo."}
            file_types = ("Archivos JSON (*.json)", "Todos los Archivos (*.*)")
            res = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if not res or len(res) == 0:
                return {"success": False, "error": "Importación cancelada."}
            file_path = res[0]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            char = CharacterSheet.from_dict(data)
            char.id = None
            char_id = self._db.save_character(char, set_active=True)
            saved = self._db.get_character_by_id(char_id)
            return {"success": True, "id": char_id, "character": self._serialize_character(saved)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_character_pdf(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Importa un personaje desde una hoja PDF AcroForm editable oficial."""
        if not file_path:
            if not self._window:
                return {"success": False, "error": "Ventana no disponible para diálogo de archivo."}
            file_types = ("Hojas de Personaje PDF (*.pdf)", "Todos los Archivos (*.*)")
            res = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if not res or len(res) == 0:
                return {"success": False, "error": "Importación cancelada."}
            file_path = res[0]

        if not os.path.exists(file_path):
            return {"success": False, "error": f"Archivo PDF no encontrado: {file_path}"}

        try:
            char = UniversalAcroFormHandler.load_character_from_pdf(file_path)
            char_id = self._db.save_character(char, set_active=True)
            saved = self._db.get_character_by_id(char_id)
            return {"success": True, "id": char_id, "character": self._serialize_character(saved)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # TALESPIRE BRIDGE & BANDEJA DE DADOS
    # =========================================================================

    def get_talespire_status(self) -> Dict[str, Any]:
        """Estado actual de TaleSpire en el equipo."""
        return {
            "is_installed": self._ts.is_installed,
            "is_running": self._ts.is_process_running(),
            "is_connected": self._ts.is_session_connected(),
            "state_label": self._ts.state.value,
            "symbiote_connected": bool(self._session_server and getattr(self._session_server, "is_symbiote_connected", False)),
            "symbiote_folder_installed": bool(self._ts.symbiote_folder_installed),
            "symbiote_install_path": self._ts.symbiote_install_path,
        }

    def reinstall_talespire_symbiote(self) -> Dict[str, Any]:
        """Reinstala o actualiza el Symbiote en la carpeta oficial de TaleSpire."""
        sym_src = os.path.join(self._base_dir, "talespire_symbiote")
        ok, msg, path = self._ts.install_or_update_symbiote(sym_src)
        return {"success": ok, "message": msg, "path": path}

    def open_talespire_symbiotes_folder(self) -> Dict[str, Any]:
        """Abre la carpeta oficial de Symbiotes de TaleSpire en el explorador del sistema."""
        p = self._ts.find_symbiotes_directory()
        if not p or not os.path.exists(p):
            return {"success": False, "error": "Carpeta de Symbiotes no encontrada en el equipo."}
        try:
            import subprocess
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])
            return {"success": True, "path": p}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def connect_talespire(self) -> Dict[str, Any]:
        """Conecta manualmente la sesión con TaleSpire."""
        success, message = self._ts.connect()
        return {"success": success, "message": message}

    def disconnect_talespire(self) -> Dict[str, Any]:
        """Desconecta de TaleSpire y vuelve a modo local."""
        self._ts.disconnect()
        return {"success": True, "message": "Sesión desconectada de TaleSpire."}

    def roll_dice(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una tirada de dados combinada usando core/rules.py (soporta normal, ventaja y desventaja)
        y la registra en el Session Roll Ledger.
        Si TaleSpire está conectado y activo, despacha al tablero 3D sin inventar resultados paralelos.
        """
        pool_raw = request.get("dice", {"20": 1})
        modifier = int(request.get("modifier", 0))
        mode = str(request.get("mode", "normal")).lower()
        if mode not in ("normal", "advantage", "disadvantage"):
            mode = "normal"
        label = str(request.get("label", "Tirada")).strip() or "Tirada"
        send_ts = bool(request.get("send_to_talespire", True))

        pool = {int(k): int(v) for k, v in pool_raw.items() if int(v) > 0}
        if not pool:
            pool = {20: 1}

        # Si hay ventaja/desventaja en 1d20, para TaleSpire se envían 2d20
        ts_pool = dict(pool)
        if mode in ("advantage", "disadvantage") and ts_pool.get(20) == 1:
            ts_pool[20] = 2

        ts_sent = False
        if send_ts and self._ts.is_session_connected():
            try:
                tag_suffix = " (Ventaja)" if mode == "advantage" else (" (Desventaja)" if mode == "disadvantage" else "")
                url = self._ts.build_pool_url(ts_pool, modifier=modifier, label=f"{label}{tag_suffix}")
                ts_sent = self._ts.send_roll(url)
                if ts_sent:
                    ts_mode = self._db.get_setting("talespire_mode", "dm")
                    self._ts.execute_throw_gesture(ts_mode=ts_mode)
            except Exception as e:
                print(f"[DesktopBridge] Error enviando a TaleSpire: {e}")

        active_char = self._db.get_active_character()
        char_name = active_char.name if active_char else "Héroe"

        if ts_sent:
            # Cumplimiento estricto de INTEGRACION_TALESPIRE_DICE_BRIDGE.md (Sección 9.2):
            # No inventar números aleatorios locales cuando TaleSpire 3D resuelve la física.
            dice_repr = " + ".join([f"{c}d{s}" for s, c in sorted(ts_pool.items(), key=lambda x: -x[0])])
            mod_repr = f"+{modifier}" if modifier > 0 else (f"{modifier}" if modifier < 0 else "")
            formula_str = f"{dice_repr}{mod_repr}"
            detail_str = "🎲 En mesa 3D (TaleSpire)"

            SessionRollLedger.get_current().record_roll(
                character_name=char_name,
                reason=label,
                formula=formula_str,
                detail=detail_str,
                total=0,
                is_crit=False,
                is_fumble=False,
                channel="TaleSpire 3D",
            )

            return {
                "total": 0,
                "dice_rolls": [],
                "modifier": modifier,
                "mode": mode,
                "label": label,
                "detail": detail_str,
                "formula": formula_str,
                "is_crit": False,
                "is_fumble": False,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "talespire_sent": True,
            }

        # Resolución mediante el motor de reglas local (core/rules.py)
        pool_res = roll_dice_pool(pool, modifier=modifier, mode=mode)

        # rolls_flat contendrá el detalle para renderizar los dados 2D animados en la interfaz
        rolls_flat: List[Dict[str, int]] = []
        for sides in sorted(pool.keys(), key=lambda f: (0 if f == 20 else 1, -f)):
            count = pool[sides]
            if sides == 20 and count == 1 and mode in ("advantage", "disadvantage"):
                # Extraer el valor seleccionado para visualización
                sel_val = pool_res["subtotal"] - sum(r["roll"] for r in rolls_flat)
                rolls_flat.append({"sides": 20, "roll": sel_val})
            else:
                import random as _rnd
                # Reconstruir desglose individual a partir del detalle de roll_dice_pool
                pass

        # Extraer cada dado individual del detalle generado por roll_dice_pool para la animación 2D
        import re
        rolls_flat = []
        for match in re.finditer(r"(\d+)d(\d+)(?:\[(\d+),\s*(\d+)\s*->\s*(\d+)\]|\(([\d,\s]+)\))", pool_res["detail"]):
            sides_m = int(match.group(2))
            if match.group(5) is not None:
                rolls_flat.append({"sides": sides_m, "roll": int(match.group(5))})
            elif match.group(6):
                for num_str in match.group(6).split(","):
                    rolls_flat.append({"sides": sides_m, "roll": int(num_str.strip())})

        dc_val = request.get("dc")
        target_dc = int(dc_val) if dc_val is not None and str(dc_val).isdigit() else None
        is_death_save = bool(request.get("is_death_save") or "muerte" in label.lower())
        is_saving_throw = bool(request.get("is_saving_throw") or is_death_save or "salvaci" in label.lower())
        if is_death_save and target_dc is None:
            target_dc = 10

        success_val = None
        success_cnt = 0
        failure_cnt = 0
        if is_death_save:
            if pool_res["is_crit"]:
                success_val = True
                success_cnt = 2
            elif pool_res["is_fumble"]:
                success_val = False
                failure_cnt = 2
            elif pool_res["total"] >= 10:
                success_val = True
                success_cnt = 1
            else:
                success_val = False
                failure_cnt = 1
        elif target_dc is not None:
            success_val = (pool_res["total"] >= target_dc)

        result_detail = pool_res["detail"]
        if success_val is not None:
            verdict = "¡Éxito!" if success_val else "Fracaso"
            if is_death_save and pool_res["is_crit"]:
                verdict = "¡Éxito Crítico! (+2)"
            elif is_death_save and pool_res["is_fumble"]:
                verdict = "¡Fallo Crítico! (+2)"
            result_detail = f"{result_detail} -> {verdict}"

        SessionRollLedger.get_current().record_roll(
            character_name=char_name,
            reason=label,
            formula=pool_res["formula"],
            detail=result_detail,
            total=pool_res["total"],
            is_crit=pool_res["is_crit"],
            is_fumble=pool_res["is_fumble"],
            channel="Motor Local",
        )

        return {
            "total": pool_res["total"],
            "dice_rolls": rolls_flat,
            "modifier": modifier,
            "mode": mode,
            "label": label,
            "detail": result_detail,
            "formula": pool_res["formula"],
            "is_crit": pool_res["is_crit"],
            "is_fumble": pool_res["is_fumble"],
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "talespire_sent": False,
            "dc": target_dc,
            "is_saving_throw": is_saving_throw,
            "is_death_save": is_death_save,
            "success": success_val,
            "success_count": success_cnt,
            "failure_count": failure_cnt,
        }

    def get_roll_history(self) -> List[Dict[str, Any]]:
        """Retorna el historial completo de tiradas de la sesión activa."""
        entries = SessionRollLedger.get_current().get_history()
        return [
            {
                "id": e.id,
                "time_str": e.time_str,
                "character_name": e.character_name,
                "reason": e.reason,
                "formula": e.formula,
                "detail": e.detail,
                "total": e.total,
                "is_crit": e.is_crit,
                "is_fumble": e.is_fumble,
                "channel": e.channel,
            }
            for e in entries
        ]

    def clear_roll_history(self) -> bool:
        """Limpia el historial de tiradas de la sesión."""
        SessionRollLedger.get_current().clear_history()
        return True

    def trigger_talespire_gesture(self) -> bool:
        """Simula manualmente el gesto de lanzamiento en TaleSpire."""
        ts_mode = self._db.get_setting("talespire_mode", "dm")
        return self._ts.execute_throw_gesture(ts_mode=ts_mode)

    # =========================================================================
    # FORJA DE PERSONAJES (OKF + POINT BUY + QUICK BUILD + RANDOMIZE)
    # =========================================================================

    def get_builder_catalog(self, edition: Optional[str] = None, lang: str = "es") -> Dict[str, Any]:
        """
        Devuelve el catálogo dinámico completo desde OkfEngine para poblar la Forja:
        especies, linajes, clases, subclases, trasfondos, dotes de origen y condiciones.
        Adapta niveles de subclase según la edición activa (5.5e 2024 vs 5e 2014) e idioma.
        """
        ed = edition or self._db.get_setting("dnd_edition", "5.5e")
        is_2024 = (ed == "5.5e")

        subclass_lvl_2014 = {
            "Clérigo": 1,
            "Brujo": 1,
            "Hechicero": 1,
            "Druida": 2,
            "Mago": 2,
        }

        default_bonuses = {
            "Humano": {"FUE": 1, "DES": 1, "CON": 1, "INT": 1, "SAB": 1, "CAR": 1},
            "Elfo": {"DES": 2, "INT": 1},
            "Enano": {"CON": 2, "SAB": 1},
            "Mediano": {"DES": 2, "CAR": 1},
            "Tiefling": {"CAR": 2, "INT": 1},
            "Dracónido": {"FUE": 2, "CAR": 1},
            "Semielfo": {"CAR": 2, "DES": 1, "CON": 1},
            "Orco": {"FUE": 2, "CON": 1},
            "Semiorco": {"FUE": 2, "CON": 1},
            "Gnomo": {"INT": 2, "DES": 1},
            "Goliath": {"FUE": 2, "CON": 1},
            "Aasimar": {"CAR": 2, "SAB": 1},
        }

        raw_species = self._okf.get_species(lang=lang)
        species_out = []
        for sp in raw_species:
            sp_name = sp["nombre"]
            lineages = self._okf.get_lineages(sp["id"], lang=lang) or self._okf.get_lineages(sp_name, lang=lang)
            subrace_names = [lin["nombre"] for lin in lineages] if lineages else ["Estándar" if lang == "es" else "Standard"]
            raw_traits = sp.get("rasgos_principales", "")
            if isinstance(raw_traits, list):
                trait_items = [{"name": str(t), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits]
            elif isinstance(raw_traits, str) and raw_traits.strip():
                trait_items = [{"name": t.strip(), "desc": "Rasgo de especie oficial." if lang == "es" else "Official species trait."} for t in raw_traits.split(",") if t.strip()]
            else:
                trait_items = [{"name": f"Herencia de {sp_name}" if lang == "es" else f"{sp_name} Heritage", "desc": sp.get("sentidos", "Visión Normal" if lang == "es" else "Normal Vision")}]

            species_out.append({
                "id": sp["id"],
                "name": sp_name,
                "subraces": subrace_names,
                "speed": self._parse_speed_feet(sp.get("velocidad", "9 m")),
                "bonuses": default_bonuses.get(sp_name, {"FUE": 1, "CON": 1}),
                "traits": trait_items,
            })

        all_skill_names = list(SKILLS_MAP.keys())
        raw_classes = self._okf.get_classes(lang=lang)
        classes_out = []
        for c in raw_classes:
            c_name = c["nombre"]
            sub_lvl = 3 if is_2024 else subclass_lvl_2014.get(c_name, 3)
            subs = self._okf.get_subclasses(c_name, lang=lang)
            sub_names = [s["nombre"] for s in subs] if subs else [f"Arquetipo de {c_name}" if lang == "es" else f"{c_name} Archetype"]
            preset = CLASS_QUICK_PRESETS.get(c_name, CLASS_QUICK_PRESETS.get("Guerrero", {}))
            rec_skills = list(preset.get("skills", ["Atletismo", "Percepción"]))
            extra_skills = [sk for sk in all_skill_names if sk not in rec_skills][:6]
            skill_opts = rec_skills + extra_skills
            hit_die_val = int(c.get("hit_dice", CLASS_HIT_DICE.get(c_name, 8)))
            is_caster = c_name in CLASS_CASTING_ABILITY

            classes_out.append({
                "id": c["id"],
                "name": c_name,
                "hit_die": hit_die_val,
                "primary_ability": c.get("caracteristica_principal", "FUE"),
                "saves": list(c.get("saves", ["FUE", "CON"])),
                "skill_choices_count": 4 if c_name in ("Pícaro", "Rogue") else (3 if c_name in ("Bardo", "Bard", "Explorador", "Ranger") else 2),
                "skill_options": skill_opts,
                "subclasses": sub_names,
                "subclass_unlock_level": sub_lvl,
                "is_caster": is_caster,
            })

        raw_bgs = self._okf.get_backgrounds(lang=lang)
        bgs_out = []
        for bg in raw_bgs:
            bgs_out.append({
                "id": bg["id"],
                "name": bg["nombre"],
                "skills": list(bg.get("competencias_habilidades", ["Atletismo", "Supervivencia"])),
                "feature_name": bg.get("dote_concedida") or ("Dote de Origen" if lang == "es" else "Origin Feat"),
                "feature_desc": bg.get("descripcion_dote") or ("Concede capacidades adicionales según el manual oficial." if lang == "es" else "Grants additional capabilities according to official rules."),
            })

        return {
            "edition": ed,
            "species": species_out,
            "classes": classes_out,
            "backgrounds": bgs_out,
            "all_skills": all_skill_names,
        }

    def validate_point_buy(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Valida una distribución de compra por puntos usando PointBuyCalculator."""
        clean_scores = {k: int(v) for k, v in scores.items() if k in ("FUE", "DES", "CON", "INT", "SAB", "CAR")}
        return PointBuyCalculator.get_budget_status(clean_scores)

    def get_available_spells(
        self,
        class_name: Optional[str] = None,
        max_level: Optional[int] = None,
        query: str = "",
        school: Optional[str] = None,
        level: Optional[int] = None,
        limit: int = 150,
        lang: str = "es"
    ) -> List[Dict[str, Any]]:
        """Busca conjuros enriquecidos en OKF con filtros combinados y soporte multilingüe."""
        return self._okf.search_available_spells(
            query=query,
            class_name=class_name,
            level=level,
            max_level=max_level,
            school=school,
            limit=limit,
            lang=lang
        )

    def add_spell_to_character(self, char_id: int, spell_data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade un conjuro a la ficha del personaje y lo guarda en SQLite."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        s_name = str(spell_data.get("name", "")).strip()
        if not s_name:
            return {"success": False, "error": "Nombre de conjuro inválido"}

        for existing in char.spells:
            if existing.name.lower().strip() == s_name.lower():
                return {"success": True, "already_exists": True, "character": self._serialize_character(char)}

        new_spell = SpellItem(
            id=spell_data.get("id", s_name.lower().replace(" ", "_")),
            name=s_name,
            name_en=spell_data.get("name_en", s_name),
            level=int(spell_data.get("level", 0)),
            school=spell_data.get("school", "Evocación"),
            casting_time=spell_data.get("cast_time") or spell_data.get("casting_time", "1 acción"),
            range=spell_data.get("range_area") or spell_data.get("range", "18 m"),
            components=spell_data.get("components", "V, S"),
            duration=spell_data.get("duration", "Instantáneo"),
            concentration=bool(spell_data.get("concentration", False)),
            ritual=bool(spell_data.get("ritual", False)),
            description=spell_data.get("description") or spell_data.get("notes", ""),
            higher_levels=spell_data.get("higher_levels", ""),
            source=spell_data.get("source", "PHB 2024"),
            classes=spell_data.get("classes", [])
        )
        char.spells.append(new_spell)
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def remove_spell_from_character(self, char_id: int, spell_name: str) -> Dict[str, Any]:
        """Elimina un conjuro de la ficha del personaje y guarda en SQLite."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        clean = spell_name.strip().lower()
        char.spells = [s for s in char.spells if s.name.strip().lower() != clean]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def sync_character_features(self, char_id: int, lang: str = "es") -> Dict[str, Any]:
        """Sincroniza y recarga las características de clase, subclase y especie con compendio OKF."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "character": self._serialize_character(char)}

    def sync_compendium_from_srd(self, edition: str = "PHB 2024") -> Dict[str, Any]:
        """Sincroniza el compendio OKF importando datos atomizados desde SRD 5.1 / 2024."""
        importer = SrdImporter(self._okf)
        total = importer.import_all()
        return {"success": True, "total_entities": total}

    def get_class_progression_limits(self, char_class: str, level: int, edition: str = "5.5e") -> Dict[str, Any]:
        """Retorna límites de ranuras, conjuros preparados y dominio de armas según clase y edición."""
        return get_class_progression_limits(char_class, level, edition)

    def build_character_from_wizard(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye una instancia completa de CharacterSheet a partir de los datos
        del asistente (Wizard) y calcula todos sus derivados de reglas D&D 5e/5.5e.
        """
        name = str(payload.get("name", "Héroe")).strip() or "Héroe"
        char_class = str(payload.get("char_class", "Guerrero")).strip()
        subclass = str(payload.get("subclass", "")).strip()
        race = str(payload.get("race", "Humano")).strip()
        subrace = str(payload.get("subrace", "")).strip()
        level = int(payload.get("level", 1))
        background = str(payload.get("background", "Soldado")).strip()
        alignment = str(payload.get("alignment", "Neutral")).strip()

        scores_input = payload.get("scores", {"FUE": 10, "DES": 10, "CON": 10, "INT": 10, "SAB": 10, "CAR": 10})
        already_adjusted = bool(payload.get("scores_already_adjusted", False))

        # Modificadores de especie y trasfondo
        species_entry = self._okf.get_species_by_name(race)
        bg_entry = self._okf.get_background_by_name(background)
        bonuses_map = payload.get("assigned_bonuses") or {}

        abilities: Dict[str, Any] = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base_score = int(scores_input.get(stat, 10))
            if not already_adjusted:
                extra = int(bonuses_map.get(stat, 0))
                final_score = base_score + extra
            else:
                final_score = base_score

            mod = calc_modifier(final_score)
            abilities[stat] = {
                "base": final_score,
                "override": 0,
                "bonus": mod,
                "proficient": False,
                "save_bonus": mod,
            }

        prof_bonus = calc_proficiency_bonus(level)
        class_entry = self._okf.get_class_by_name(char_class)
        saves_keys = class_entry.get("saves", ["FUE", "CON"]) if class_entry else ["FUE", "CON"]
        saving_profs = list(saves_keys)
        for stat in saving_profs:
            if stat in abilities:
                abilities[stat]["proficient"] = True
                abilities[stat]["save_bonus"] = abilities[stat]["bonus"] + prof_bonus

        dex_mod = abilities.get("DES", {}).get("bonus", 0)
        con_mod = abilities.get("CON", {}).get("bonus", 0)

        # Dados de golpe y PG
        hd_faces = int(class_entry.get("hit_dice", CLASS_HIT_DICE.get(char_class, 8))) if class_entry else 8
        hp_lvl1 = hd_faces + con_mod
        avg_hd = (hd_faces // 2) + 1
        hp_max = max(1, hp_lvl1 + max(0, level - 1) * max(1, (avg_hd + con_mod)))

        # Clase de Armadura base (sin armadura: 10 + DES)
        ac = 10 + dex_mod
        if char_class == "Bárbaro":
            ac = 10 + dex_mod + con_mod
        elif char_class == "Monje":
            ac = 10 + dex_mod + abilities.get("SAB", {}).get("bonus", 0)

        speed_str = species_entry.get("velocidad", "9 m") if species_entry else "9 m"
        senses_str = species_entry.get("sentidos", "Visión Normal") if species_entry else "Visión Normal"

        # Habilidades seleccionadas
        selected_skills = payload.get("selected_skills", [])
        if not selected_skills and bg_entry:
            selected_skills = list(bg_entry.get("skills", ["Atletismo"]))

        skills_dict: Dict[str, Any] = {}
        for s_name, s_stat in SKILLS_MAP.items():
            is_prof = s_name in selected_skills
            stat_mod = abilities.get(s_stat, {}).get("bonus", 0)
            bonus = stat_mod + (prof_bonus if is_prof else 0)
            skills_dict[s_name] = {
                "proficient": is_prof,
                "bonus": bonus,
                "expertise": False,
            }

        preset = CLASS_QUICK_PRESETS.get(char_class, CLASS_QUICK_PRESETS.get("Guerrero", {}))
        weapons_list = []
        for w_tuple in preset.get("weapons", []):
            w_name = w_tuple[0]
            w_dmg_expr = w_tuple[1]
            w_notes = w_tuple[2]
            is_ranged = "Arco" in w_name or "Ballesta" in w_name or "Dardo" in w_name
            atk_stat = "DES" if (is_ranged or "Finesse" in w_notes or "Sutil" in w_notes) else "FUE"
            atk_mod = abilities.get(atk_stat, {}).get("bonus", 0)
            hit_dc = f"+{prof_bonus + atk_mod}"

            dmg_parts = w_dmg_expr.split(" ")
            dice_part = dmg_parts[0]
            type_part = dmg_parts[1] if len(dmg_parts) > 1 else "cortante"

            weapons_list.append(
                WeaponAction(
                    name=w_name,
                    type="A distancia" if is_ranged else "Cuerpo a cuerpo",
                    range_val="80/320 pies" if is_ranged else "5 pies (1 tile)",
                    hit_dc=hit_dc,
                    damage_dice=f"{dice_part}+{atk_mod}" if atk_mod > 0 else dice_part,
                    damage_type=type_part,
                    notes=w_notes,
                    proficient=True,
                )
            )

        # Conjuros y ranuras si es lanzador
        spell_slots = _compute_spell_slots_for_class(char_class, level)
        spells_input = payload.get("spells", [])
        spells_list = []
        for sp in spells_input:
            if isinstance(sp, str):
                s_entry = self._okf.get_spell_by_name(sp)
                if s_entry:
                    spells_list.append(
                        SpellItem(
                            id=s_entry["id"],
                            name=s_entry["nombre"],
                            name_en=s_entry.get("nombre_ingles", s_entry["nombre"]),
                            level=int(s_entry.get("nivel", 0)),
                            school=s_entry.get("escuela", "Evocación"),
                            casting_time=s_entry.get("tiempo_lanzamiento", "1 acción"),
                            range=s_entry.get("alcance", "18 m"),
                            components=s_entry.get("componentes", "V, S"),
                            duration=s_entry.get("duracion", "Instantáneo"),
                            concentration="Concentración" in s_entry.get("duracion", ""),
                            ritual=bool(s_entry.get("ritual", False)),
                            description=s_entry.get("descripcion", ""),
                        )
                    )
                else:
                    spells_list.append(SpellItem(id=sp.lower().replace(" ", "_"), name=sp, level=1))
            elif isinstance(sp, dict):
                spells_list.append(SpellItem.from_dict(sp))

        full_race = f"{race} ({subrace})" if subrace and subrace not in ("Estándar", "Standard") else race
        features_list = [
            CharacterFeature(
                id="feat_class_start",
                name=f"Entrenamiento de {char_class}",
                source=char_class,
                description=f"Competencias con armas, armaduras y habilidades de {char_class}.",
            ),
            CharacterFeature(
                id="feat_species_heritage",
                name=f"Herencia de {race}",
                source=full_race,
                description=f"Velocidad {speed_str}. Sentidos: {senses_str}.",
            ),
        ]
        if subclass:
            features_list.append(
                CharacterFeature(
                    id="feat_subclass",
                    name=f"Subclase: {subclass}",
                    source=char_class,
                    description=f"Especialización de {char_class} desbloqueada.",
                )
            )
        if bg_entry:
            features_list.append(
                CharacterFeature(
                    id="feat_bg",
                    name=bg_entry.get("feature_name", "Dote de Origen"),
                    source=f"Trasfondo ({background})",
                    description=bg_entry.get("feature_desc", ""),
                )
            )

        char = CharacterSheet(
            name=name,
            char_class=char_class,
            subclass=subclass,
            level=level,
            race=full_race,
            background=background,
            alignment=alignment,
            xp=0,
            hp_current=hp_max,
            hp_max=hp_max,
            hp_temp=0,
            hit_dice_max=level,
            hit_dice_current=level,
            hit_dice_faces=hd_faces,
            armor_class=ac,
            initiative_bonus=dex_mod,
            speed=speed_str,
            proficiency_bonus=prof_bonus,
            abilities=abilities,
            saving_throw_profs=saving_profs,
            skills=skills_dict,
            weapons=weapons_list,
            spell_slots=spell_slots,
            spells=spells_list,
            features=features_list,
            senses=senses_str,
        )
        return self._serialize_character(char)

    def generate_quick_build_preview(self, char_class: str, species: str = "Humano") -> Dict[str, Any]:
        """Calcula la previsualización completa de Quick Build (60s) usando core/quick_build.py."""
        raw_scores, final_scores, bg, plus2, plus1 = QuickBuildEngine.generate_quick_stats(char_class, species)
        preset = QuickBuildEngine.get_preset_for_class(char_class)
        spells_list = preset.get("cantrips", []) + preset.get("spells_known", [])
        return self.build_character_from_wizard({
            "name": f"{char_class} {species}",
            "char_class": char_class,
            "race": species,
            "level": 1,
            "background": bg,
            "scores": final_scores,
            "scores_already_adjusted": True,
            "selected_skills": preset.get("skills", []),
            "spells": spells_list,
        })

    def generate_random_character_preview(
        self,
        forced_class: Optional[str] = None,
        forced_species: Optional[str] = None,
        forced_level: int = 1
    ) -> Dict[str, Any]:
        """Genera una previsualización procedural aleatoria completa lista para la Forja."""
        rnd = RandomCharacterGenerator.generate_random_character(
            forced_class=forced_class,
            forced_species=forced_species,
            forced_level=int(forced_level or 1),
        )
        scores_map = rnd.get("final_abilities") or rnd.get("final_scores") or rnd.get("raw_scores", {})
        preset = rnd.get("preset", {})
        skills_list = rnd.get("skills") or preset.get("skills", ["Atletismo", "Percepción"])
        spells_list = preset.get("cantrips", []) + preset.get("spells_known", [])

        char_dict = self.build_character_from_wizard({
            "name": rnd.get("name", "Héroe del Destino"),
            "char_class": rnd.get("char_class", forced_class or "Guerrero"),
            "subclass": rnd.get("subclass", ""),
            "race": rnd.get("species", forced_species or "Humano"),
            "subrace": rnd.get("subrace", ""),
            "level": rnd.get("level", int(forced_level or 1)),
            "background": rnd.get("background", "Soldado"),
            "alignment": rnd.get("alignment", "Neutral"),
            "scores": scores_map,
            "scores_already_adjusted": True,
            "selected_skills": skills_list,
            "spells": spells_list,
        })
        return {
            "character": char_dict,
            "raw_rolls": rnd.get("raw_scores", {}),
            "biography": {
                "trait": rnd.get("personality_trait", ""),
                "ideal": rnd.get("ideal", ""),
                "bond": rnd.get("bond", ""),
                "flaw": rnd.get("flaw", ""),
            },
        }

    # =========================================================================
    # DIARIO DE CAMPAÑA & RED DE PERSONAJES
    # =========================================================================

    def get_character_journals(self, char_id: int) -> List[Dict[str, Any]]:
        """Retorna las crónicas de sesión del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return []
        return [
            {
                "id": int(s.id) if str(s.id).isdigit() else idx + 1,
                "date": s.date,
                "title": s.title,
                "summary": s.summary,
                "loot": s.loot,
                "xp_gained": int(s.xp_gained),
                "session_id": getattr(s, "session_id", "") or "",
            }
            for idx, s in enumerate(char.sessions)
        ]

    def save_character_journal(self, char_id: int, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda o actualiza una crónica de sesión en la ficha del héroe."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        j_id = str(journal_data.get("id", ""))
        existing = next((s for s in char.sessions if str(s.id) == j_id), None)
        if existing:
            existing.date = journal_data.get("date", existing.date)
            existing.title = journal_data.get("title", existing.title)
            existing.summary = journal_data.get("summary", existing.summary)
            existing.loot = journal_data.get("loot", existing.loot)
            existing.xp_gained = int(journal_data.get("xp_gained", existing.xp_gained))
            existing.session_id = journal_data.get("session_id", existing.session_id)
        else:
            new_sess = SessionLog(
                id=j_id or str(len(char.sessions) + 1),
                date=journal_data.get("date", datetime.now().strftime("%d/%m/%Y")),
                title=journal_data.get("title", "Nueva Crónica"),
                summary=journal_data.get("summary", ""),
                loot=journal_data.get("loot", ""),
                xp_gained=int(journal_data.get("xp_gained", 0)),
                session_id=journal_data.get("session_id", "")
            )
            char.sessions.append(new_sess)

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "sessions": self.get_character_journals(char_id)}

    def delete_character_journal(self, char_id: int, session_id: int) -> Dict[str, Any]:
        """Elimina una crónica de sesión por su ID."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        char.sessions = [s for s in char.sessions if str(s.id) != str(session_id)]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "sessions": self.get_character_journals(char_id)}

    def get_character_network(self, char_id: int) -> Dict[str, Any]:
        """Obtiene el grafo de vínculos sociales y lealtades del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"nodes": [], "edges": []}
        return {
            "nodes": [n.to_dict() if hasattr(n, "to_dict") else dict(n) for n in char.network_nodes],
            "edges": [e.to_dict() if hasattr(e, "to_dict") else dict(e) for e in char.network_edges],
        }

    def save_network_node(self, char_id: int, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda o actualiza un nodo en el mapa de relaciones."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        nid = str(node_data.get("id", ""))
        existing = next((n for n in char.network_nodes if n.id == nid), None)
        if existing:
            existing.name = node_data.get("name", existing.name)
            existing.role = node_data.get("role", existing.role)
            existing.description = node_data.get("description", existing.description)
            existing.x = float(node_data.get("x", existing.x))
            existing.y = float(node_data.get("y", existing.y))
        else:
            char.network_nodes.append(NetworkNode.from_dict(node_data))

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def delete_network_node(self, char_id: int, node_id: str) -> Dict[str, Any]:
        """Elimina un nodo y todas las aristas conectadas."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        char.network_nodes = [n for n in char.network_nodes if n.id != node_id]
        char.network_edges = [e for e in char.network_edges if e.source_id != node_id and e.target_id != node_id]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def save_network_edge(self, char_id: int, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda o actualiza una relación entre dos personajes."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        src = str(edge_data.get("source_id", ""))
        tgt = str(edge_data.get("target_id", ""))
        existing = next((e for e in char.network_edges if e.source_id == src and e.target_id == tgt), None)
        if existing:
            existing.relation = edge_data.get("relation", existing.relation)
        else:
            char.network_edges.append(NetworkEdge.from_dict(edge_data))

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    def delete_network_edge(self, char_id: int, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina una relación entre dos personajes."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        src = str(edge_data.get("source_id", ""))
        tgt = str(edge_data.get("target_id", ""))
        char.network_edges = [e for e in char.network_edges if not (e.source_id == src and e.target_id == tgt)]
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {"success": True, "network": self.get_character_network(char_id)}

    # =========================================================================
    # VISOR DE MANUALES & HOJAS PDF
    # =========================================================================

    def list_pdf_documents(self) -> List[Dict[str, Any]]:
        """Busca manuales y fichas PDF en el proyecto, detectando idioma (es/en)."""
        results = []
        search_dirs = [
            (os.path.join(self._base_dir, "data", "manuals", "es"), "es"),
            (os.path.join(self._base_dir, "data", "manuals", "en"), "en"),
            (os.path.join(self._base_dir, "data", "manuals"), "all"),
            (os.path.join(self._base_dir, "data", "characters"), "all"),
            (self._base_dir, "all"),
        ]
        for sdir, dir_lang in search_dirs:
            if os.path.exists(sdir) and os.path.isdir(sdir):
                for fname in os.listdir(sdir):
                    if fname.lower().endswith(".pdf"):
                        full = os.path.join(sdir, fname)
                        if not any(r["path"] == full for r in results):
                            detected_lang = dir_lang
                            if detected_lang == "all":
                                lower_name = fname.lower()
                                if "[en]" in lower_name or "_en" in lower_name or "player's handbook" in lower_name or "dungeon master" in lower_name or "monster manual" in lower_name:
                                    detected_lang = "en"
                                elif "[es]" in lower_name or "_es" in lower_name or "manual del jugador" in lower_name or "guia" in lower_name or "guía" in lower_name or "caldero" in lower_name:
                                    detected_lang = "es"

                            results.append({
                                "name": fname,
                                "path": full,
                                "lang": detected_lang
                            })
        return results

    def open_pdf_document(self, file_path: str) -> Dict[str, Any]:
        """Abre un documento PDF y retorna su metainformación."""
        if not os.path.isabs(file_path):
            file_path = os.path.join(self._base_dir, file_path)

        success = self._pdf_reader.open_document(file_path)
        if not success:
            return {"success": False, "error": f"No se pudo abrir el archivo {file_path}"}

        return {
            "success": True,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "page_count": self._pdf_reader.page_count,
            "toc": self._pdf_reader.get_toc(),
        }

    def render_pdf_page(self, page_num: int, zoom: float = 1.0, trim_margins: Optional[bool] = None) -> Dict[str, Any]:
        """Renderiza una página del PDF abierto a imagen base64 con opción de limpieza de marco."""
        if not self._pdf_reader.is_open:
            return {"success": False, "error": "No hay ningún PDF abierto."}

        b64 = self._pdf_reader.render_page_base64(page_num, zoom=zoom, trim_margins=trim_margins)
        links = self._pdf_reader.get_page_links(page_num, trim_margins=trim_margins)
        pw, ph = self._pdf_reader.get_page_dimensions(page_num, trim_margins=trim_margins)

        if b64 and not b64.startswith("data:"):
            b64 = f"data:image/png;base64,{b64}"

        return {
            "success": bool(b64),
            "page_num": page_num,
            "image_base64": b64,
            "links": links,
            "width": pw,
            "height": ph,
            "trimmed": self._pdf_reader._should_trim(trim_margins),
        }

    def export_character_pdf(self, char_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Exporta el personaje a una hoja PDF oficial editable AcroForm con selector de guardado nativo."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        if not target_path:
            if not self._window:
                return {"success": False, "error": "Ventana no disponible para diálogo de guardado."}
            file_types = ("Hojas de Personaje PDF (*.pdf)", "Todos los Archivos (*.*)")
            save_name = f"{char.name.replace(' ', '_')}_Sheet.pdf"
            res = self._window.create_file_dialog(webview.SAVE_DIALOG, save_filename=save_name, file_types=file_types)
            if not res:
                return {"success": False, "cancelled": True}
            target_path = res if isinstance(res, str) else res[0]

        try:
            template_path = os.path.join(self._base_dir, "data", "characters", "Artanis LVL 4.pdf")
            if not os.path.exists(template_path):
                template_path = None
            out_file = UniversalAcroFormHandler.fill_official_sheet(char, template_path=template_path, output_path=target_path)
            return {"success": True, "path": out_file}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # COMPENDIO OKF (MARKDOWN & REGLAS)
    # =========================================================================

    def get_compendium_categories(self, lang: str = "es") -> List[Dict[str, Any]]:
        """Lista las categorías disponibles en el compendio OKF con su conteo por idioma."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        if target_lang == "en":
            return [
                {"id": "clases", "label": "Classes & Subclasses", "count": self._okf.count_entities(["clase", "subclase"], lang=target_lang)},
                {"id": "especies_y_linajes", "label": "Species & Lineages", "count": self._okf.count_entities(["especie", "linaje"], lang=target_lang)},
                {"id": "conjuros", "label": "Spell Grimoire", "count": self._okf.count_entities("conjuro", lang=target_lang)},
                {"id": "trasfondos", "label": "Backgrounds", "count": self._okf.count_entities("trasfondo", lang=target_lang)},
                {"id": "dotes", "label": "Character Feats", "count": self._okf.count_entities("dote", lang=target_lang)},
                {"id": "equipo_y_armamento", "label": "Equipment & Weapons", "count": self._okf.count_entities("equipo", lang=target_lang)},
                {"id": "reglas_y_mecanicas", "label": "Rules & Mechanics", "count": self._okf.count_entities("regla", lang=target_lang)},
            ]
        return [
            {"id": "clases", "label": "Clases y Subclases", "count": self._okf.count_entities(["clase", "subclase"], lang=target_lang)},
            {"id": "especies_y_linajes", "label": "Especies y Linajes", "count": self._okf.count_entities(["especie", "linaje"], lang=target_lang)},
            {"id": "conjuros", "label": "Grimorio de Conjuros", "count": self._okf.count_entities("conjuro", lang=target_lang)},
            {"id": "trasfondos", "label": "Trasfondos", "count": self._okf.count_entities("trasfondo", lang=target_lang)},
            {"id": "dotes", "label": "Dotes de Personaje", "count": self._okf.count_entities("dote", lang=target_lang)},
            {"id": "equipo_y_armamento", "label": "Equipo y Armamento", "count": self._okf.count_entities("equipo", lang=target_lang)},
            {"id": "reglas_y_mecanicas", "label": "Reglas y Mecánicas", "count": self._okf.count_entities("regla", lang=target_lang)},
        ]

    def search_compendium(self, query: str = "", category: Optional[str] = None, lang: str = "es") -> List[Dict[str, Any]]:
        """Búsqueda de texto o listado por categoría en el compendio OKF según idioma."""
        query_clean = (query or "").strip()
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"

        category_type_map = {
            "clases": ["clase", "subclase"],
            "especies_y_linajes": ["especie", "linaje", "especie_linaje"],
            "conjuros": "conjuro",
            "trasfondos": "trasfondo",
            "dotes": "dote",
            "equipo_y_armamento": "equipo",
            "reglas_y_mecanicas": "regla",
        }

        tipo_filter = category_type_map.get(category) if category else None
        entities = self._okf.search_entities(query=query_clean, tipo=tipo_filter, limit=150, lang=target_lang)

        results = []
        for item in entities:
            item_tipo = item.get("tipo", "")
            snippet_parts = [item.get("fuente", "PHB 2024")]
            if "nivel" in item and item["nivel"] is not None:
                snippet_parts.append(f"Level {item['nivel']}" if target_lang == "en" else f"Nivel {item['nivel']}")
            if "escuela" in item and item["escuela"]:
                snippet_parts.append(str(item["escuela"]))
            if "dado_golpe" in item and item["dado_golpe"]:
                snippet_parts.append(f"HD: {item['dado_golpe']}" if target_lang == "en" else f"DG: {item['dado_golpe']}")
            if "dote_concedida" in item and item["dote_concedida"]:
                snippet_parts.append(f"Feat: {item['dote_concedida']}" if target_lang == "en" else f"Dote: {item['dote_concedida']}")
            if "caracteristicas_clave" in item and item["caracteristicas_clave"]:
                snippet_parts.append(f"{item['caracteristicas_clave']}")

            results.append({
                "id": item.get("id", ""),
                "name": item.get("nombre", item.get("id", "")),
                "category": item_tipo,
                "snippet": " • ".join(snippet_parts),
                "path": item.get("path", ""),
            })
        return results

    def get_compendium_entry(self, category: str, entry_name: str, lang: str = "es") -> Optional[Dict[str, Any]]:
        """Obtiene una entrada completa del compendio OKF con su markdown en el idioma solicitado."""
        target_lang = "en" if (lang or "").lower().startswith("en") else "es"
        query_id = entry_name.strip()
        clean = query_id.lower()
        clean_slug = clean.replace(" ", "_")
        clean_en = f"{clean_slug}_en"
        clean_base = clean_slug.replace("_en", "")

        matched = next(
            (
                item for item in self._okf._index
                if item.get("idioma", "es") == target_lang
                and (
                    item.get("id", "").lower() in (clean_slug, clean_en, clean_base)
                    or item.get("original_id", "").lower() in (clean_slug, clean_en, clean_base)
                    or item.get("nombre", "").lower() == clean
                    or item.get("nombre_ingles", "").lower() == clean
                    or item.get("nombre_espanol", "").lower() == clean
                )
            ),
            None
        )

        if not matched:
            matched = next(
                (
                    item for item in self._okf._index
                    if item.get("id", "").lower() in (clean_slug, clean_en, clean_base)
                    or item.get("nombre", "").lower() == clean
                ),
                None
            )

        if matched:
            rel_path = matched.get("path", "")
            full_path = os.path.join(self._base_dir, rel_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    return {
                        "name": matched.get("nombre", entry_name),
                        "category": matched.get("tipo", category),
                        "content": content,
                        "metadata": matched,
                    }
                except Exception as e:
                    return {"name": entry_name, "category": category, "content": f"Error leyendo archivo: {e}"}

        fallback_entry = self._okf.get_entity_detail(query_id)
        if fallback_entry:
            return fallback_entry

        return None

    def create_character_quick(self, char_class: str, species: str, background: str) -> Dict[str, Any]:
        """Crea un personaje en 60 segundos con valores óptimos por defecto."""
        preset = CLASS_QUICK_PRESETS.get(char_class, CLASS_QUICK_PRESETS.get("Guerrero", {}))
        hd_face = CLASS_HIT_DICE.get(char_class, 8)
        abilities_scores = preset.get("abilities", {"FUE": 15, "CON": 14, "DES": 13, "INT": 12, "SAB": 10, "CAR": 8})

        calc_mod = lambda score: (score - 10) // 2
        con_mod = calc_mod(abilities_scores.get("CON", 10))
        des_mod = calc_mod(abilities_scores.get("DES", 10))
        hp = hd_face + con_mod

        abilities: Dict[str, Any] = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = abilities_scores.get(stat, 10)
            mod = calc_mod(base)
            abilities[stat] = {
                "base": base,
                "override": 0,
                "bonus": mod,
                "proficient": False,
                "save_bonus": mod,
            }

        weapons = []
        for w_name, w_dmg, w_notes in preset.get("weapons", []):
            weapons.append({
                "name": w_name,
                "type": "Cuerpo a cuerpo" if "Arco" not in w_name and "Ballesta" not in w_name else "A distancia",
                "range_val": "5 pies" if "Arco" not in w_name and "Ballesta" not in w_name else "80/320",
                "hit_dc": f"+{2 + max(calc_mod(abilities_scores['FUE']), calc_mod(abilities_scores['DES']))}",
                "damage_dice": w_dmg.split(" ")[0],
                "damage_type": w_dmg.split(" ")[1] if len(w_dmg.split(" ")) > 1 else "cortante",
                "notes": w_notes,
                "proficient": True,
            })

        spells = []
        for sp_name in preset.get("cantrips", []):
            spells.append({"name": sp_name, "level": 0, "school": "Evocación", "prepared": True})
        for sp_name in preset.get("spells_known", []):
            spells.append({"name": sp_name, "level": 1, "school": "Evocación", "prepared": True})

        return {
            "name": f"Héroe {char_class}",
            "char_class": char_class,
            "subclass": "",
            "level": 1,
            "race": species,
            "background": bg,
            "alignment": "Neutral Bueno",
            "xp": 0,
            "inspiration": False,
            "proficiency_bonus": 2,
            "ac": 10 + des_mod,
            "speed": 30,
            "initiative": des_mod,
            "hp_current": hp,
            "hp_max": hp,
            "hp_temp": 0,
            "hit_dice_total": f"1d{hd_face}",
            "hit_dice_current": f"1d{hd_face}",
            "death_save_successes": 0,
            "death_save_failures": 0,
            "abilities": abilities,
            "skills": {s: {"proficient": True, "bonus": 2, "expertise": False} for s in preset.get("skills", [])},
            "spells": spells,
            "spell_slots_total": {"1": 2} if spells else {},
            "spell_slots_used": {},
            "weapon_actions": weapons,
            "features": [
                {"name": f"Competencias de {char_class}", "source": char_class, "description": f"Entrenado en el repertorio de combate de {char_class}."},
                {"name": f"Trasfondo {bg}", "source": bg, "description": f"Beneficio inicial concedido por la vida de {bg}."},
            ],
            "sessions": [],
            "network_nodes": [],
            "network_edges": [],
        }

    def generate_random_character(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Genera un personaje procedural completo con tiradas 4d6 descartando el menor."""
        opts = options or {}
        f_class = opts.get("forced_class")
        f_species = opts.get("forced_species")
        f_level = int(opts.get("forced_level", 1))

        raw = RandomCharacterGenerator.generate_random_character(
            forced_class=f_class,
            forced_species=f_species,
            forced_level=f_level
        )

        char_class = raw["char_class"]
        species = raw["species"]
        level = raw["level"]
        final_scores = raw["final_abilities"]

        calc_mod = lambda score: (score - 10) // 2
        con_mod = calc_mod(final_scores.get("CON", 10))
        des_mod = calc_mod(final_scores.get("DES", 10))
        hd_face = raw["hit_dice_faces"]

        abilities: Dict[str, Any] = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = final_scores.get(stat, 10)
            mod = calc_mod(base)
            abilities[stat] = {
                "base": base,
                "override": 0,
                "bonus": mod,
                "proficient": False,
                "save_bonus": mod,
            }

        preset = raw["preset"]
        weapons = []
        for w_name, w_dmg, w_notes in preset.get("weapons", []):
            weapons.append({
                "name": w_name,
                "type": "Cuerpo a cuerpo" if "Arco" not in w_name and "Ballesta" not in w_name else "A distancia",
                "range_val": "5 pies" if "Arco" not in w_name and "Ballesta" not in w_name else "80/320",
                "hit_dc": f"+{raw['proficiency_bonus'] + max(calc_mod(final_scores['FUE']), calc_mod(final_scores['DES']))}",
                "damage_dice": w_dmg.split(" ")[0],
                "damage_type": w_dmg.split(" ")[1] if len(w_dmg.split(" ")) > 1 else "cortante",
                "notes": w_notes,
                "proficient": True,
            })

        return {
            "name": raw["name"],
            "char_class": char_class,
            "subclass": "",
            "level": level,
            "race": species,
            "background": raw["background"],
            "alignment": raw["alignment"],
            "xp": 0,
            "inspiration": False,
            "proficiency_bonus": raw["proficiency_bonus"],
            "ac": raw["armor_class"],
            "speed": 30,
            "initiative": raw["initiative_bonus"],
            "hp_current": raw["hp_current"],
            "hp_max": raw["hp_max"],
            "hp_temp": 0,
            "hit_dice_total": f"{level}d{hd_face}",
            "hit_dice_current": f"{level}d{hd_face}",
            "death_save_successes": 0,
            "death_save_failures": 0,
            "abilities": abilities,
            "skills": {s: {"proficient": True, "bonus": raw["proficiency_bonus"], "expertise": False} for s in preset.get("skills", [])},
            "spells": [],
            "spell_slots_total": {},
            "spell_slots_used": {},
            "weapon_actions": weapons,
            "features": [
                {"name": "Personalidad", "source": "Trasfondo", "description": raw["personality_trait"]},
                {"name": "Ideal", "source": "Alineamiento", "description": raw["ideal"]},
                {"name": "Vínculo", "source": "Historia", "description": raw["bond"]},
                {"name": "Defecto", "source": "Historia", "description": raw["flaw"]},
            ],
            "sessions": [],
            "network_nodes": [],
            "network_edges": [],
        }

    def perform_rest(self, char_id: int, rest_type: str, hit_dice_spent: int = 0) -> Dict[str, Any]:
        """Aplica descanso corto o descanso largo y actualiza la base de datos."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        if rest_type == "long":
            char, message = perform_long_rest(char)
        else:
            char, message = perform_short_rest(char, hit_dice_spent=int(hit_dice_spent))

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {
            "success": True,
            "message": message,
            "character": self._serialize_character(char),
        }

    # =========================================================================
    # AJUSTES & TEMAS
    # =========================================================================

    def get_settings(self) -> Dict[str, Any]:
        """Retorna todos los ajustes configurados."""
        return {
            "theme": self._db.get_setting("theme", "dark-obsidian"),
            "dnd_edition": self._db.get_setting("dnd_edition", "5.5e"),
            "language": self._db.get_setting("language", "es"),
            "talespire_mode": self._db.get_setting("talespire_mode", "dm"),
            "talespire_enabled": self._db.get_setting("talespire_enabled", "true") == "true",
            "okf_path": self._db.get_setting("okf_path", os.path.join(self._base_dir, "okf_dnd5e")),
            "custom_themes_dir": os.path.join(self._base_dir, "themes"),
        }

    def set_setting(self, key: str, value: Any) -> bool:
        """Guarda un ajuste en la base de datos."""
        self._db.set_setting(key, str(value))
        return True

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Retorna temas base y temas personalizados en themes/ sin duplicar IDs."""
        themes_map: Dict[str, Dict[str, Any]] = {
            "dark-obsidian": {"id": "dark-obsidian", "name": "Obsidian & Steel (Oscuro)", "is_dark": True},
            "light-obsidian": {"id": "light-obsidian", "name": "Obsidian & Steel (Claro)", "is_dark": False},
            "dark-parchment": {"id": "dark-parchment", "name": "Illuminated Parchment (Oscuro)", "is_dark": True},
            "light-parchment": {"id": "light-parchment", "name": "Illuminated Parchment (Claro)", "is_dark": False},
            "dark-amethyst": {"id": "dark-amethyst", "name": "Arcane Amethyst (Oscuro)", "is_dark": True},
            "light-amethyst": {"id": "light-amethyst", "name": "Arcane Amethyst (Claro)", "is_dark": False},
            "dark-mithril": {"id": "dark-mithril", "name": "Mithril Scribe (Oscuro)", "is_dark": True},
            "light-mithril": {"id": "light-mithril", "name": "Mithril Scribe (Claro)", "is_dark": False},
        }
        themes_dir = os.path.join(self._base_dir, "themes")
        if os.path.exists(themes_dir):
            for entry in sorted(os.listdir(themes_dir)):
                theme_path = os.path.join(themes_dir, entry)
                if os.path.isdir(theme_path):
                    json_path = os.path.join(theme_path, "theme.json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            tid = meta.get("id", entry)
                            if tid not in themes_map:
                                themes_map[tid] = {
                                    "id": tid,
                                    "name": meta.get("name", entry),
                                    "is_dark": bool(meta.get("is_dark", True)),
                                }
                        except Exception:
                            pass
        return list(themes_map.values())

    # =========================================================================
    # DIÁLOGOS NATIVOS DE ARCHIVO (PyWebView)
    # =========================================================================

    def open_image_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar imagen de retrato."""
        if not self._window:
            return None
        file_types = ("Archivos de Imagen (*.png;*.jpg;*.jpeg;*.webp)", "Todos los Archivos (*.*)")
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None

    def open_pdf_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar un PDF de personaje o manual."""
        if not self._window:
            return None
        file_types = ("Archivos PDF (*.pdf)", "Todos los Archivos (*.*)")
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None

    # =========================================================================
    # MÉTODOS DE SESIÓN ONLINE DEL DM Y CLOUDFLARE TUNNELS
    # =========================================================================

    def start_dm_session(self, name: str = "Sesión de Campaña", campaignName: str = "Campaña Principal", sessionId: Optional[str] = None) -> Dict[str, Any]:
        """Inicia el servidor local WebSocket y levanta el túnel Cloudflare seguro."""
        import uuid
        sid = sessionId or f"sess_{uuid.uuid4().hex[:8]}"

        existing = self._db.get_dm_session(sid)
        if existing:
            name = existing.get("name") or name
            campaignName = existing.get("campaign_name") or campaignName

        # 1. Iniciar servidor FastAPI embebido
        port = self._session_server.start(sid, name, campaignName)

        # 2. Registrar o reactivar en SQLite
        self._db.create_dm_session(sid, name, campaignName)

        # 3. Iniciar Cloudflare Quick Tunnel en hilo secundario sin congelar el hilo de renderizado
        def on_url_ready(url: str):
            self._db.update_dm_session_tunnel(sid, url)

        self._tunnel_mgr.start_tunnel(port, on_url=on_url_ready)

        return self.get_dm_session_status()

    def dm_list_sessions(self) -> List[Dict[str, Any]]:
        """Lista las sesiones históricas para poder reanudarlas."""
        return self._db.list_dm_sessions()

    def stop_dm_session(self) -> Dict[str, Any]:
        """Cierra el túnel Cloudflare y marca la sesión como terminada."""
        current_sess = self._session_server.current_session_id
        if current_sess:
            self._db.close_dm_session(current_sess)

        self._tunnel_mgr.stop_tunnel()
        self._session_server.stop()

        return {"success": True, "is_running": False}

    def get_dm_session_status(self) -> Dict[str, Any]:
        """Obtiene el estado en tiempo real del túnel, la URL y los jugadores conectados."""
        session_id = self._session_server.current_session_id
        tunnel_url = self._tunnel_mgr.tunnel_url
        is_running = self._session_server.current_session_id is not None
        qr_code = self._tunnel_mgr.generate_qr_base64(tunnel_url) if tunnel_url else ""

        players = []
        if session_id:
            players = self._db.get_session_players(session_id)

        # Añadir bandera de si el socket está activo en este instante
        for p in players:
            token = p.get("player_token")
            p["is_online"] = token in self._session_server.manager.active_players

        return {
            "is_running": is_running,
            "session_id": session_id,
            "session_name": self._session_server.session_name,
            "campaign_name": self._session_server.campaign_name,
            "tunnel_url": tunnel_url,
            "qr_code": qr_code,
            "port": self._session_server.port,
            "players": players,
            "connected_count": len(self._session_server.manager.active_players),
        }

    def dm_apply_hp_change(self, player_token: str, delta: int) -> bool:
        """Aplica daño (delta < 0) o curación (delta > 0) a un jugador en tiempo real."""
        session_id = self._session_server.current_session_id
        if not session_id:
            return False

        # Actualizar en BD
        players = self._db.get_session_players(session_id)
        target = next((p for p in players if p["player_token"] == player_token), None)
        if target:
            new_hp = max(0, min(target["hp_max"], target["hp_current"] + delta))
            self._db.update_player_hp(session_id, player_token, new_hp)

        if delta < 0:
            self._session_server.apply_damage(player_token, abs(delta))
        elif delta > 0:
            self._session_server.apply_heal(player_token, delta)

        return True

    def dm_gift_item(self, player_token: str, item_data: Dict[str, Any]) -> bool:
        """Entrega un objeto Homebrew al inventario del jugador conectado."""
        return self._session_server.gift_homebrew_item(player_token, item_data)

    def dm_list_homebrew_items(self) -> List[Dict[str, Any]]:
        """Lista los objetos Homebrew guardados en la biblioteca del DM."""
        return self._db.list_homebrew_items()

    def dm_save_homebrew_item(self, item_data: Dict[str, Any]) -> str:
        """Guarda un objeto Homebrew creado por el DM."""
        return self._db.save_homebrew_item(item_data)

    def dm_delete_homebrew_item(self, item_id: str) -> bool:
        """Elimina un objeto Homebrew de la biblioteca."""
        return self._db.delete_homebrew_item(item_id)

    def dm_get_session_logs(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene la bitácora de eventos y tiradas de la sesión."""
        sess = session_id or self._session_server.current_session_id
        if not sess:
            # Obtener última sesión si no hay activa
            sessions = self._db.list_dm_sessions()
            if sessions:
                sess = sessions[0]["id"]
            else:
                return []
        return self._db.get_session_logs(sess)

    def dm_save_session_notes(self, notes: str, session_id: Optional[str] = None) -> bool:
        """Guarda las notas del DM para la sesión activa o especificada."""
        sid = session_id or self._session_server.current_session_id
        if not sid:
            return False
        return self._db.save_dm_session_notes(sid, notes)

    def dm_get_session_notes(self, session_id: Optional[str] = None) -> str:
        """Obtiene las notas del DM guardadas para la sesión indicada o la activa."""
        sid = session_id or self._session_server.current_session_id
        if not sid:
            sessions = self._db.list_dm_sessions()
            if sessions:
                sid = sessions[0]["id"]
            else:
                return ""
        session_info = self._db.get_dm_session(sid)
        if session_info and session_info.get("notes"):
            return str(session_info["notes"])
        return ""
