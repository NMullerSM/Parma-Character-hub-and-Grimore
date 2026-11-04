"""
Sub-puente para integración con TaleSpire, bandeja de dados 3D y registro de tiradas (SessionRollLedger).
"""
import os
import sys
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from core.rules import roll_dice_pool
from core.session_ledger import SessionRollLedger


class TaleSpireBridgeMixin:
    """Métodos de conexión a TaleSpire, Symbiotes, lanzamiento y bandeja de dados."""

    def get_talespire_status(self) -> Dict[str, Any]:
        """Estado actual de TaleSpire en el equipo."""
        return {
            "is_installed": self._ts.is_installed,
            "is_running": self._ts.is_process_running(),
            "is_connected": self._ts.is_session_connected(),
            "state_label": self._ts.state.value,
            "symbiote_connected": bool(self._session_server and self._session_server.is_symbiote_connected()),
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
        auto_throw = self._db.get_setting("talespire_auto_throw", "true") == "true"
        ts_mode = self._db.get_setting("talespire_mode", "dm")

        active_char = self._db.get_active_character()
        char_name = active_char.name if active_char else "Héroe"

        if send_ts:
            # 1. Si el Symbiote WebSocket está conectado en vivo, despachar directamente por WebSocket
            if self._session_server and self._session_server.is_symbiote_connected():
                try:
                    dice_repr = " + ".join([f"{c}d{s}" for s, c in sorted(ts_pool.items(), key=lambda x: -x[0])])
                    mod_repr = f"+{modifier}" if modifier > 0 else (f"{modifier}" if modifier < 0 else "")
                    formula_str = f"{dice_repr}{mod_repr}"
                    ts_sent = self._session_server.dispatch_dice_to_symbiote(
                        formula=formula_str,
                        label=label,
                        mode=mode,
                        actor_name=char_name,
                    )
                except Exception as e:
                    print(f"[DesktopBridge] Error despachando a Symbiote: {e}")

            # 2. Si no fue enviado por Symbiote, usar Named Pipe / URL URI Scheme
            if not ts_sent and self._ts.is_session_connected():
                try:
                    tag_suffix = " (Ventaja)" if mode == "advantage" else (" (Desventaja)" if mode == "disadvantage" else "")
                    url = self._ts.build_pool_url(ts_pool, modifier=modifier, label=f"{label}{tag_suffix}")
                    ts_sent = self._ts.send_roll(url)
                except Exception as e:
                    print(f"[DesktopBridge] Error enviando a TaleSpire por Pipe/URI: {e}")

            # 3. Si se colocaron los dados en TaleSpire y auto_throw está activado, ejecutar el micro-gesto físico
            if ts_sent and auto_throw:
                try:
                    self._ts.execute_throw_gesture(ts_mode=ts_mode)
                except Exception as e:
                    print(f"[DesktopBridge] Error ejecutando gesto de lanzamiento: {e}")

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
        rolls_flat: List[Dict[str, int]] = []
        for sides in sorted(pool.keys(), key=lambda f: (0 if f == 20 else 1, -f)):
            count = pool[sides]
            if sides == 20 and count == 1 and mode in ("advantage", "disadvantage"):
                # Extraer el valor seleccionado para visualización
                sel_val = pool_res["subtotal"] - sum(r["roll"] for r in rolls_flat)
                rolls_flat.append({"sides": 20, "roll": sel_val})
            else:
                pass

        # Extraer cada dado individual del detalle generado por roll_dice_pool para la animación 2D
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
