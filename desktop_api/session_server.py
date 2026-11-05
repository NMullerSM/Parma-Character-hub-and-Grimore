"""
Servidor HTTP y WebSocket local para sesiones DM Online (Parma D&D).
Ejecuta FastAPI + Uvicorn de forma asíncrona en un hilo daemon, permitiendo
a jugadores conectarse mediante navegadores web a través de Cloudflare Tunnels.
"""
import os
import json
import time
import socket
import secrets
import hashlib
import hmac
import asyncio
import threading
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


def is_local_request(client_host: str, headers: Dict[str, str]) -> bool:
    """
    Determina si la conexión se origina en el loopback local sin pasar por proxies/túneles.
    Si incluye cabeceras de Cloudflare (cf-connecting-ip, cf-ray), se trata como remoto.
    """
    if "cf-connecting-ip" in headers or "cf-ray" in headers:
        return False
    if client_host in ("127.0.0.1", "::1", "localhost", "testclient"):
        return True
    return False


class ConnectionManager:
    """Administra conexiones WebSocket activas entre el DM y los Jugadores."""

    def __init__(self):
        # player_token -> WebSocket
        self.active_players: Dict[str, WebSocket] = {}
        # Conexiones de consolas DM activas
        self.dm_sockets: List[WebSocket] = []
        # Conexión dedicada del TaleSpire Symbiote
        self.symbiote_socket: Optional[WebSocket] = None

    async def connect_player(self, player_token: str, websocket: WebSocket):
        await websocket.accept()
        self.active_players[player_token] = websocket

    async def connect_dm(self, websocket: WebSocket):
        await websocket.accept()
        self.dm_sockets.append(websocket)

    async def connect_symbiote(self, websocket: WebSocket):
        await websocket.accept()
        self.symbiote_socket = websocket

    def disconnect_player(self, player_token: str):
        if player_token in self.active_players:
            del self.active_players[player_token]

    def disconnect_dm(self, websocket: WebSocket):
        if websocket in self.dm_sockets:
            self.dm_sockets.remove(websocket)

    def disconnect_symbiote(self):
        self.symbiote_socket = None

    def is_symbiote_connected(self) -> bool:
        return self.symbiote_socket is not None

    async def send_to_symbiote(self, message: Dict[str, Any]) -> bool:
        if not self.symbiote_socket:
            return False
        try:
            await self.symbiote_socket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception:
            self.symbiote_socket = None
            return False

    async def broadcast_to_all(self, message: Dict[str, Any]):
        text = json.dumps(message, ensure_ascii=False)
        # Enviar a todos los jugadores
        for ws in list(self.active_players.values()):
            try:
                await ws.send_text(text)
            except Exception:
                pass
        # Enviar a consolas DM
        for ws in list(self.dm_sockets):
            try:
                await ws.send_text(text)
            except Exception:
                pass

    async def send_to_player(self, player_token: str, message: Dict[str, Any]) -> bool:
        ws = self.active_players.get(player_token)
        if not ws:
            return False
        try:
            await ws.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception:
            return False

    async def send_to_dm(self, message: Dict[str, Any]):
        text = json.dumps(message, ensure_ascii=False)
        for ws in list(self.dm_sockets):
            try:
                await ws.send_text(text)
            except Exception:
                pass


def find_free_port(start_port: int = 8765) -> int:
    """Encuentra un puerto TCP disponible para el servidor."""
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


class DmSessionServer:
    """Servidor FastAPI embebido para la sesión del DM."""

    def __init__(self, db_manager, base_dir: str):
        self.db = db_manager
        self.base_dir = base_dir
        self.manager = ConnectionManager()
        self.current_session_id: Optional[str] = None
        self.session_name: str = "Partida D&D 5e"
        self.campaign_name: str = "Campaña Principal"
        self.port = find_free_port()
        self.server: Optional[uvicorn.Server] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Hardening 1.0.4: Autenticación, invitaciones y rate limiting
        self.current_invite_token: Optional[str] = None
        self.session_approved_hashes: set = set()
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_events: Dict[str, asyncio.Event] = {}
        self.msg_rate_records: Dict[str, List[float]] = {}
        
        self.app = self._create_app()

    def check_rate_limit(self, identifier: str, max_per_second: int = 25) -> bool:
        """Rate limiter por token/IP para evitar saturación de mensajes."""
        now = time.time()
        records = self.msg_rate_records.setdefault(identifier, [])
        records = [t for t in records if now - t < 1.0]
        if len(records) >= max_per_second:
            self.msg_rate_records[identifier] = records
            return False
        records.append(now)
        self.msg_rate_records[identifier] = records
        return True

    def create_invite(self, expires_seconds: int = 7200) -> str:
        """Genera y registra una invitación de un solo uso para la sesión actual."""
        token = secrets.token_urlsafe(16)
        self.current_invite_token = token
        if self.current_session_id:
            self.db.create_invitation(self.current_session_id, token, expires_seconds)
        return token

    def approve_player(self, token_hash: str) -> bool:
        """Aprueba un jugador en espera desde la consola del DM."""
        self.session_approved_hashes.add(token_hash)
        self.db.approve_trusted_player(token_hash)
        self.pending_approvals.pop(token_hash, None)
        event = self.approval_events.pop(token_hash, None)
        if event and self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(event.set)
        return True

    def revoke_player(self, token_hash: str) -> bool:
        """Revoca a un jugador y cierra cualquier conexión activa."""
        self.session_approved_hashes.discard(token_hash)
        self.db.revoke_trusted_player(token_hash)
        self.pending_approvals.pop(token_hash, None)
        event = self.approval_events.pop(token_hash, None)
        if event and self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(event.set)
        for tok, ws in list(self.manager.active_players.items()):
            h = hashlib.sha256(tok.encode("utf-8")).hexdigest()
            if h == token_hash:
                coro = ws.close(code=4403, reason="Acceso revocado por el DM")
                self.execute_async(coro)
                self.manager.disconnect_player(tok)
        return True

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Lista las solicitudes de jugadores pendientes de aprobación."""
        return [
            {
                "token_hash": h,
                "name": data.get("name", "Aventurero"),
                "connected_at": data.get("connected_at", 0),
                "player_token": data.get("token", ""),
            }
            for h, data in self.pending_approvals.items()
        ]

    def _create_app(self) -> FastAPI:
        app = FastAPI(title="Parma DM Online Hub")

        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.trycloudflare\.com)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        def _check_remote_access(
            request: Request,
            key: Optional[str] = None,
            token: Optional[str] = None,
            invite: Optional[str] = None
        ) -> bool:
            client_host = request.client.host if request.client else "unknown"
            headers = {k.lower(): v for k, v in request.headers.items()}
            if is_local_request(client_host, headers):
                return True

            # Chequeo para accesos remotos vía túnel o proxy
            auth_token = key or token or request.query_params.get("key") or request.query_params.get("token") or headers.get("x-session-token")
            if auth_token:
                token_hash = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()
                trusted = self.db.get_trusted_player_by_hash(token_hash)
                if trusted and trusted.get("approved_by_dm") and not trusted.get("is_revoked"):
                    return True

            inv_code = invite or request.query_params.get("invite") or headers.get("x-invite-code")
            if inv_code:
                if self.current_invite_token and inv_code == self.current_invite_token:
                    return True
                inv = self.db.get_invitation(inv_code)
                if inv:
                    return True

            return False

        @app.get("/api/session/info")
        async def session_info(
            request: Request,
            key: Optional[str] = None,
            token: Optional[str] = None,
            invite: Optional[str] = None
        ):
            if not _check_remote_access(request, key, token, invite):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Acceso no autorizado", "is_active": self.current_session_id is not None}
                )
            return {
                "session_id": self.current_session_id,
                "session_name": self.session_name,
                "campaign_name": self.campaign_name,
                "is_active": self.current_session_id is not None,
                "connected_count": len(self.manager.active_players),
            }

        @app.get("/api/session/players")
        async def session_players(
            request: Request,
            key: Optional[str] = None,
            token: Optional[str] = None,
            invite: Optional[str] = None
        ):
            if not _check_remote_access(request, key, token, invite):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Acceso no autorizado al listado de jugadores"}
                )
            if not self.current_session_id:
                return []
            return self.db.get_session_players(self.current_session_id)

        @app.post("/api/player/join")
        async def player_join(request: Request):
            client_host = request.client.host if request.client else "unknown"
            headers = {k.lower(): v for k, v in request.headers.items()}
            is_local = is_local_request(client_host, headers)

            data = await request.json()
            token = data.get("token") or f"usr_{secrets.token_hex(4)}"
            invite = data.get("invite")
            char = data.get("character") or {}
            char_name = char.get("name") or data.get("character_name") or "Aventurero Desconocido"

            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

            # Validación de seguridad para jugadores remotos
            if not is_local:
                trusted = self.db.get_trusted_player_by_hash(token_hash)
                if trusted and trusted.get("is_revoked"):
                    return JSONResponse(status_code=403, content={"success": False, "error": "Acceso revocado por el DM"})

                if not trusted:
                    if invite:
                        inv = self.db.get_invitation(invite)
                        if not inv:
                            return JSONResponse(status_code=401, content={"success": False, "error": "Invitación inválida o expirada"})
                        self.db.register_trusted_player(char_name, token_hash, approved=False)
                        self.db.mark_invitation_used(invite, token_hash)
                    elif token.startswith("p_"):
                        # Retrocompatibilidad para tokens existentes de 1.0.3
                        self.db.register_trusted_player(char_name, token_hash, approved=False)
                    else:
                        return JSONResponse(status_code=401, content={"success": False, "error": "Se requiere invitación válida o credencial registrada"})

            # Sanitización de rangos numéricos
            lvl = max(1, min(30, int(char.get("level", 1) or 1)))
            hp_max = max(1, min(9999, int(char.get("hp_max", 10) or 10)))
            hp_cur = max(0, min(hp_max, int(char.get("hp_current", hp_max) or hp_max)))
            ac = max(0, min(100, int(char.get("ac", 10) or 10)))

            if self.current_session_id:
                self.db.upsert_session_player(
                    session_id=self.current_session_id,
                    player_token=token,
                    character_name=char_name[:100],
                    character_id=char.get("id"),
                    character_class=str(char.get("char_class", ""))[:50],
                    character_level=lvl,
                    hp_current=hp_cur,
                    hp_max=hp_max,
                    ac=ac,
                    status="ALIVE",
                    data_json=json.dumps(char, ensure_ascii=False),
                )
                self.db.log_session_event(
                    session_id=self.current_session_id,
                    event_type="PLAYER_JOIN",
                    actor_name=char_name[:100],
                    details={"token": token, "level": lvl},
                )
                # Notificar a la consola DM
                await self.manager.send_to_dm({
                    "type": "PLAYER_JOINED",
                    "player_token": token,
                    "character_name": char_name[:100],
                    "character": char,
                })

            return {"success": True, "token": token, "session_id": self.current_session_id}

        @app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: Optional[str] = None,
            invite: Optional[str] = None,
            role: str = "player"
        ):
            client_host = websocket.client.host if websocket.client else "unknown"
            headers = {k.lower(): v for k, v in websocket.headers.items()}
            is_local = is_local_request(client_host, headers)

            # Blindaje 1: El rol 'dm' solo puede conectarse desde loopback local
            if role == "dm":
                if not is_local:
                    await websocket.close(code=4403, reason="Acceso DM denegado desde red externa")
                    return
                await self.manager.connect_dm(websocket)
                try:
                    while True:
                        msg_text = await websocket.receive_text()
                        if len(msg_text) > 65536:
                            continue
                        msg = json.loads(msg_text)
                        await self._handle_dm_ws_message(msg)
                except WebSocketDisconnect:
                    self.manager.disconnect_dm(websocket)
                return

            # Para jugadores:
            player_token = token or f"p_{secrets.token_hex(8)}"
            token_hash = hashlib.sha256(player_token.encode("utf-8")).hexdigest()

            # Blindaje 2: Si es remoto, autenticación obligatoria y aprobación del DM
            if not is_local:
                trusted = self.db.get_trusted_player_by_hash(token_hash)
                if trusted and trusted.get("is_revoked"):
                    await websocket.close(code=4403, reason="Acceso revocado por el DM")
                    return

                if not trusted:
                    if invite:
                        inv = self.db.get_invitation(invite)
                        if not inv:
                            await websocket.close(code=4401, reason="Invitación inválida o expirada")
                            return
                        self.db.register_trusted_player("Aventurero", token_hash, approved=False)
                        self.db.mark_invitation_used(invite, token_hash)
                    elif player_token.startswith("p_"):
                        # Compatibilidad con token existente 1.0.3
                        self.db.register_trusted_player("Aventurero 1.0.3", token_hash, approved=False)
                    else:
                        await websocket.close(code=4401, reason="Credencial requerida")
                        return

                # Flujo de aprobación obligatoria por el DM
                if token_hash not in self.session_approved_hashes:
                    approval_event = asyncio.Event()
                    self.approval_events[token_hash] = approval_event
                    self.pending_approvals[token_hash] = {
                        "websocket": websocket,
                        "token": player_token,
                        "token_hash": token_hash,
                        "name": trusted.get("name") if trusted else "Aventurero",
                        "connected_at": time.time(),
                    }

                    await websocket.accept()
                    await websocket.send_text(json.dumps({
                        "type": "PENDING_DM_APPROVAL",
                        "message": "Esperando aprobación del Dungeon Master...",
                    }, ensure_ascii=False))

                    await self.manager.send_to_dm({
                        "type": "PLAYER_APPROVAL_REQUEST",
                        "token_hash": token_hash,
                        "player_token": player_token,
                        "character_name": trusted.get("name") if trusted else "Aventurero",
                    })

                    try:
                        await asyncio.wait_for(approval_event.wait(), timeout=120.0)
                    except asyncio.TimeoutError:
                        self.pending_approvals.pop(token_hash, None)
                        self.approval_events.pop(token_hash, None)
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "APPROVAL_TIMEOUT",
                                "message": "Tiempo agotado sin confirmación del DM.",
                            }, ensure_ascii=False))
                            await websocket.close(code=4408, reason="Tiempo de aprobación agotado")
                        except Exception:
                            pass
                        return

                    self.manager.active_players[player_token] = websocket
                    await websocket.send_text(json.dumps({
                        "type": "DM_APPROVAL_GRANTED",
                        "message": "¡Aprobado por el Dungeon Master! Bienvenido a la sesión.",
                    }, ensure_ascii=False))
                else:
                    await self.manager.connect_player(player_token, websocket)
            else:
                # Conexión local sin barreras adicionales
                await self.manager.connect_player(player_token, websocket)

            # Notificar al DM que el socket está en línea
            await self.manager.send_to_dm({
                "type": "PLAYER_SOCKET_ONLINE",
                "player_token": player_token,
            })

            try:
                while True:
                    msg_text = await websocket.receive_text()
                    if len(msg_text) > 65536:
                        continue
                    if not self.check_rate_limit(player_token):
                        continue
                    msg = json.loads(msg_text)
                    await self._handle_player_ws_message(player_token, msg)
            except WebSocketDisconnect:
                self.manager.disconnect_player(player_token)
                await self.manager.send_to_dm({
                    "type": "PLAYER_SOCKET_OFFLINE",
                    "player_token": player_token,
                })

        @app.websocket("/ws/talespire")
        async def talespire_websocket_endpoint(websocket: WebSocket):
            client_host = websocket.client.host if websocket.client else "unknown"
            headers = {k.lower(): v for k, v in websocket.headers.items()}
            # Blindaje 3: TaleSpire solo alcanzable por loopback local
            if not is_local_request(client_host, headers):
                await websocket.close(code=4403, reason="TaleSpire Symbiote solo permitido en loopback local")
                return

            await self.manager.connect_symbiote(websocket)
            await self.manager.send_to_dm({
                "type": "TALESPIRE_SYMBIOTE_STATUS",
                "connected": True,
            })
            try:
                while True:
                    msg_text = await websocket.receive_text()
                    if len(msg_text) > 65536:
                        continue
                    msg = json.loads(msg_text)
                    await self._handle_symbiote_ws_message(msg)
            except WebSocketDisconnect:
                self.manager.disconnect_symbiote()
                await self.manager.send_to_dm({
                    "type": "TALESPIRE_SYMBIOTE_STATUS",
                    "connected": False,
                })

        # Servir build estática de frontend para los jugadores que entran por el túnel
        dist_dir = os.path.join(self.base_dir, "frontend", "dist")
        if not os.path.isdir(dist_dir):
            alt_dist = os.path.join(self.base_dir, "dist_ui")
            if os.path.isdir(alt_dist):
                dist_dir = alt_dist
            else:
                try:
                    from core.paths import get_bundle_dir
                    bundle_base = get_bundle_dir()
                    cand1 = os.path.join(bundle_base, "frontend", "dist")
                    cand2 = os.path.join(bundle_base, "dist_ui")
                    if os.path.isdir(cand1):
                        dist_dir = cand1
                    elif os.path.isdir(cand2):
                        dist_dir = cand2
                except Exception:
                    pass

        if os.path.isdir(dist_dir):
            assets_dir = os.path.join(dist_dir, "assets")
            if os.path.isdir(assets_dir):
                app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

            @app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                index_path = os.path.join(dist_dir, "index.html")
                target = os.path.join(dist_dir, full_path)
                if os.path.isfile(target):
                    return FileResponse(target)
                if os.path.isfile(index_path):
                    return FileResponse(index_path)
                return HTMLResponse("<h1>Parma D&D — Servidor Activo</h1><p>Conectando con el DM...</p>")
        else:
            @app.get("/{full_path:path}")
            async def serve_spa_fallback(full_path: str):
                return HTMLResponse("<h1>Parma D&D — Servidor Activo</h1><p>Conectando con el DM...</p>")

        return app

    async def _handle_player_ws_message(self, player_token: str, msg: Dict[str, Any]):
        msg_type = msg.get("type")
        if msg_type == "DICE_ROLL":
            # Tirada realizada por el jugador
            roll_data = msg.get("roll", {})
            actor = msg.get("character_name", "Jugador")
            if self.current_session_id:
                self.db.log_session_event(
                    session_id=self.current_session_id,
                    event_type="ROLL",
                    actor_name=actor,
                    details=roll_data,
                )
            # Retransmitir a todos (historial de tiradas compartido)
            await self.manager.broadcast_to_all({
                "type": "DICE_ROLL_SHARED",
                "player_token": player_token,
                "actor_name": actor,
                "roll": roll_data,
            })
        elif msg_type == "SHEET_SYNC":
            # Actualización de ficha del jugador
            char = msg.get("character", {})
            if self.current_session_id and char:
                self.db.upsert_session_player(
                    session_id=self.current_session_id,
                    player_token=player_token,
                    character_name=char.get("name", "Jugador"),
                    character_id=char.get("id"),
                    character_class=char.get("char_class", ""),
                    character_level=int(char.get("level", 1)),
                    hp_current=int(char.get("hp_current", 10)),
                    hp_max=int(char.get("hp_max", 10)),
                    ac=int(char.get("ac", 10)),
                    data_json=json.dumps(char, ensure_ascii=False),
                )
                await self.manager.send_to_dm({
                    "type": "PLAYER_SHEET_UPDATED",
                    "player_token": player_token,
                    "character": char,
                })

    async def _handle_dm_ws_message(self, msg: Dict[str, Any]):
        # Mensajes originados por el DM hacia jugadores
        pass

    async def _handle_symbiote_ws_message(self, msg: Dict[str, Any]):
        """Procesa eventos entrantes desde el TaleSpire Symbiote."""
        msg_type = msg.get("type")
        if msg_type == "SYMBIOTE_HELLO":
            await self.manager.send_to_symbiote({
                "type": "SYMBIOTE_ACK",
                "session_id": self.current_session_id,
            })
        elif msg_type == "DICE_ROLL_RESOLVED":
            total = int(msg.get("total", 0))
            groups = msg.get("groups", [])
            detail_parts = []
            for g in groups:
                name = g.get("name") or "Tirada"
                tot = g.get("total", 0)
                detail_parts.append(f"{name}: {tot}")
            detail_str = " | ".join(detail_parts) if detail_parts else f"🎲 Resultado 3D: {total}"

            # Registrar en el SessionRollLedger
            try:
                from core.session_ledger import SessionRollLedger
                SessionRollLedger.get_current().record_roll(
                    character_name="TaleSpire 3D",
                    reason="Tirada en Mesa 3D",
                    formula="Física 3D",
                    detail=detail_str,
                    total=total,
                    is_crit=False,
                    is_fumble=False,
                    channel="TaleSpire Symbiote",
                )
            except Exception as e:
                print(f"[DmSessionServer] Error registrando en Ledger: {e}")

            if self.current_session_id:
                self.db.log_session_event(
                    session_id=self.current_session_id,
                    event_type="ROLL_TALESPIRE_3D",
                    actor_name="TaleSpire 3D",
                    details={"total": total, "detail": detail_str, "groups": groups},
                )

            # Notificar a la consola DM y jugadores conectados
            await self.manager.broadcast_to_all({
                "type": "DICE_ROLL_SHARED",
                "player_token": "talespire_3d",
                "actor_name": "TaleSpire 3D",
                "roll": {
                    "total": total,
                    "detail": detail_str,
                    "formula": "Física 3D",
                    "label": "Tirada en Mesa TaleSpire",
                    "channel": "TaleSpire Symbiote",
                },
            })

    def start(self, session_id: Optional[str] = None, session_name: str = "Partida D&D 5e", campaign_name: str = "Campaña Principal") -> int:
        """Inicia el servidor en un hilo secundario daemon."""
        self.current_session_id = session_id
        self.session_name = session_name
        self.campaign_name = campaign_name

        if self.thread and self.thread.is_alive():
            return self.port

        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)

        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop
            loop.run_until_complete(self.server.serve())

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        return self.port

    def ensure_running(self) -> int:
        """Garantiza que el servidor local de WebSockets esté activo en segundo plano para el Symbiote y la API."""
        if self.thread and self.thread.is_alive():
            return self.port
        return self.start(session_id=self.current_session_id, session_name=self.session_name, campaign_name=self.campaign_name)

    def is_symbiote_connected(self) -> bool:
        """Indica si el Symbiote de TaleSpire está conectado en vivo vía WebSocket."""
        return self.manager.is_symbiote_connected()

    def dispatch_dice_to_symbiote(self, formula: str, label: str = "Tirada", mode: str = "normal", actor_name: str = "Parma") -> bool:
        """Despacha una fórmula de dados al Symbiote para que use TS.dice.putDiceInTray."""
        if not self.is_symbiote_connected():
            return False
        coro = self.manager.send_to_symbiote({
            "type": "DICE_ROLL_DISPATCH",
            "formula": formula,
            "label": label,
            "mode": mode,
            "actor_name": actor_name,
        })
        self.execute_async(coro)
        return True

    def stop_session(self):
        """Detiene la sesión online activa pero mantiene el servidor WebSocket corriendo para TaleSpire y la API local."""
        self.current_session_id = None

    def stop(self):
        """Detiene completamente el servidor Uvicorn."""
        if self.server:
            self.server.should_exit = True
        self.current_session_id = None

    def execute_async(self, coro):
        """Ejecuta una corutina de forma segura en el event loop del servidor."""
        if self.loop and self.loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None

    # Acciones disparadas por el DM hacia los jugadores
    def apply_damage(self, player_token: str, delta: int, actor_name: str = "DM") -> bool:
        """Ordena al jugador descontar vida (activa destello rojo de daño)."""
        safe_delta = max(1, min(9999, abs(int(delta))))
        if self.current_session_id:
            self.db.log_session_event(
                session_id=self.current_session_id,
                event_type="DAMAGE",
                actor_name=actor_name,
                details={"delta": safe_delta, "player_token": player_token},
            )
        coro = self.manager.send_to_player(player_token, {
            "type": "DM_APPLY_DAMAGE",
            "delta": safe_delta,
            "message": f"El DM te ha infligido {safe_delta} puntos de daño.",
        })
        self.execute_async(coro)
        return True

    def apply_heal(self, player_token: str, delta: int, actor_name: str = "DM") -> bool:
        """Ordena al jugador sumar vida (activa destello verde de curación)."""
        safe_delta = max(1, min(9999, abs(int(delta))))
        if self.current_session_id:
            self.db.log_session_event(
                session_id=self.current_session_id,
                event_type="HEAL",
                actor_name=actor_name,
                details={"delta": safe_delta, "player_token": player_token},
            )
        coro = self.manager.send_to_player(player_token, {
            "type": "DM_APPLY_HEAL",
            "delta": safe_delta,
            "message": f"El DM te ha curado {safe_delta} puntos de golpe.",
        })
        self.execute_async(coro)
        return True

    def gift_homebrew_item(self, player_token: str, item: Dict[str, Any], actor_name: str = "DM") -> bool:
        """Inyecta un objeto Homebrew directamente en el inventario del jugador."""
        item_name = item.get("name", "Objeto Mágico")
        if self.current_session_id:
            self.db.log_session_event(
                session_id=self.current_session_id,
                event_type="ITEM_GIFT",
                actor_name=actor_name,
                details={"item_name": item_name, "player_token": player_token},
            )
        coro = self.manager.send_to_player(player_token, {
            "type": "DM_GIFT_ITEM",
            "item": item,
            "message": f"¡El DM te ha entregado: {item_name}!",
        })
        self.execute_async(coro)
        return True
