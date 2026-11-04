"""
Sub-puente para gestión de sesión DM, túnel Cloudflare, LAN e invitaciones de jugadores.
"""
import os
import sys
import json
import uuid
from typing import Optional, Dict, Any, List


class SessionBridgeMixin:
    """Métodos de sesión DM, red LAN, túnel seguro y gestión de jugadores remotos."""

    def start_dm_session(
        self,
        name: str = "Sesión de Campaña",
        campaign_name: str = "Campaña Principal",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Inicia el servidor local WebSocket y levanta el túnel Cloudflare seguro."""
        sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"

        existing = self._db.get_dm_session(sid)
        if existing:
            name = existing.get("name") or name
            campaign_name = existing.get("campaign_name") or campaign_name

        # 1. Iniciar servidor FastAPI embebido
        port = self._session_server.start(sid, name, campaign_name)

        # 2. Registrar o reactivar en SQLite
        self._db.create_dm_session(sid, name, campaign_name)

        # 3. Generar token de invitación inicial para jugadores remotos (TOFU)
        self._session_server.create_invite(expires_seconds=7200)

        # 4. Iniciar Cloudflare Quick Tunnel en hilo secundario sin congelar el hilo de renderizado
        def on_url_ready(url: str):
            self._db.update_dm_session_tunnel(sid, url)

        self._tunnel_mgr.start_tunnel(port, on_url=on_url_ready)

        return self.get_dm_session_status()

    def dm_create_invitation(self, expires_seconds: int = 7200) -> Dict[str, Any]:
        """Crea una invitación temporal de un solo uso para unirse a la sesión."""
        token = self._session_server.create_invite(expires_seconds=expires_seconds)
        tunnel_url = self._tunnel_mgr.tunnel_url or f"http://127.0.0.1:{self._session_server.port}"
        invite_url = f"{tunnel_url}?invite={token}"
        qr = self._tunnel_mgr.generate_qr_base64(invite_url) if self._tunnel_mgr else ""
        return {
            "invite_token": token,
            "invite_url": invite_url,
            "qr_code": qr,
            "expires_seconds": expires_seconds,
        }

    def dm_approve_player(self, token_hash: str) -> bool:
        """Aprueba manualmente la conexión de un jugador a la sesión activa."""
        return self._session_server.approve_player(token_hash)

    def dm_revoke_player(self, token_hash: str) -> bool:
        """Revoca el acceso de un jugador a la sesión."""
        return self._session_server.revoke_player(token_hash)

    def dm_get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de solicitudes de aprobación de jugadores en espera."""
        return self._session_server.get_pending_approvals()

    def dm_list_trusted_players(self) -> List[Dict[str, Any]]:
        """Lista los jugadores de confianza registrados en la base de datos."""
        return self._db.list_trusted_players()

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
        invite_token = self._session_server.current_invite_token
        invite_url = f"{tunnel_url}?invite={invite_token}" if (tunnel_url and invite_token) else (tunnel_url or "")
        qr_code = self._tunnel_mgr.generate_qr_base64(invite_url) if invite_url else ""

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
            "invite_token": invite_token,
            "invite_url": invite_url,
            "qr_code": qr_code,
            "port": self._session_server.port,
            "players": players,
            "pending_approvals": self._session_server.get_pending_approvals(),
            "trusted_players": self._db.list_trusted_players(),
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

    def get_lan_connection_info(self, expires_seconds: int = 7200) -> Dict[str, Any]:
        """
        Genera (o reutiliza) una invitación apuntando a la IP LAN real del host en vez
        del túnel Cloudflare, para usar cuando no hay internet o el DM elige modo LAN
        local explícito.
        """
        if not self._session_server.current_session_id:
            return {"success": False, "error": "No hay una sesión DM activa."}

        token = self._session_server.current_invite_token or self._session_server.create_invite(
            expires_seconds=expires_seconds
        )
        lan_ip = self._tunnel_mgr.get_lan_ip()
        lan_url = self._tunnel_mgr.get_lan_url(self._session_server.port)
        invite_url = f"{lan_url}?invite={token}"
        qr_code = self._tunnel_mgr.generate_qr_base64(invite_url)

        return {
            "success": True,
            "lan_ip": lan_ip,
            "lan_url": lan_url,
            "invite_token": token,
            "invite_url": invite_url,
            "qr_code": qr_code,
        }
