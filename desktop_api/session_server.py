"""
Servidor HTTP y WebSocket local para sesiones DM Online (Parma D&D).
Ejecuta FastAPI + Uvicorn de forma asíncrona en un hilo daemon, permitiendo
a jugadores conectarse mediante navegadores web a través de Cloudflare Tunnels.
"""
import os
import json
import socket
import asyncio
import threading
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


class ConnectionManager:
    """Administra conexiones WebSocket activas entre el DM y los Jugadores."""

    def __init__(self):
        # player_token -> WebSocket
        self.active_players: Dict[str, WebSocket] = {}
        # Conexiones de consolas DM activas
        self.dm_sockets: List[WebSocket] = []

    async def connect_player(self, player_token: str, websocket: WebSocket):
        await websocket.accept()
        self.active_players[player_token] = websocket

    async def connect_dm(self, websocket: WebSocket):
        await websocket.accept()
        self.dm_sockets.append(websocket)

    def disconnect_player(self, player_token: str):
        if player_token in self.active_players:
            del self.active_players[player_token]

    def disconnect_dm(self, websocket: WebSocket):
        if websocket in self.dm_sockets:
            self.dm_sockets.remove(websocket)

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

    async def close_all(self, reason: str = "El DM ha finalizado la sesión online."):
        payload = json.dumps({"type": "SESSION_CLOSED", "message": reason}, ensure_ascii=False)
        for ws in list(self.active_players.values()):
            try:
                await ws.send_text(payload)
                await ws.close(code=1000, reason=reason)
            except Exception:
                pass
        self.active_players.clear()

        for ws in list(self.dm_sockets):
            try:
                await ws.send_text(payload)
                await ws.close(code=1000, reason=reason)
            except Exception:
                pass
        self.dm_sockets.clear()


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
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        app = FastAPI(title="Parma DM Online Hub")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/api/session/info")
        async def session_info():
            return {
                "session_id": self.current_session_id,
                "session_name": self.session_name,
                "campaign_name": self.campaign_name,
                "is_active": self.current_session_id is not None,
                "connected_count": len(self.manager.active_players),
            }

        @app.get("/api/session/players")
        async def session_players():
            if not self.current_session_id:
                return []
            players = self.db.get_session_players(self.current_session_id)
            for p in players:
                p["is_online"] = p.get("player_token") in self.manager.active_players
            return players

        @app.post("/api/player/join")
        async def player_join(request: Request):
            data = await request.json()
            token = data.get("token") or f"usr_{os.urandom(4).hex()}"
            char = data.get("character") or {}
            char_name = char.get("name") or data.get("character_name") or "Aventurero Desconocido"

            if self.current_session_id:
                self.db.upsert_session_player(
                    session_id=self.current_session_id,
                    player_token=token,
                    character_name=char_name,
                    character_id=char.get("id"),
                    character_class=char.get("char_class", ""),
                    character_level=int(char.get("level", 1)),
                    hp_current=int(char.get("hp_current", 10)),
                    hp_max=int(char.get("hp_max", 10)),
                    ac=int(char.get("ac", 10)),
                    status="ALIVE",
                    data_json=json.dumps(char, ensure_ascii=False),
                )
                self.db.log_session_event(
                    session_id=self.current_session_id,
                    event_type="PLAYER_JOIN",
                    actor_name=char_name,
                    details={"token": token, "level": char.get("level", 1)},
                )
                # Notificar a la consola DM y a los demás jugadores
                await self.manager.send_to_dm({
                    "type": "PLAYER_JOINED",
                    "player_token": token,
                    "character_name": char_name,
                    "character": char,
                })
                await self.manager.broadcast_to_all({
                    "type": "PLAYER_LIST_UPDATED",
                    "player_token": token,
                    "character_name": char_name,
                })

            return {
                "success": True,
                "token": token,
                "session_id": self.current_session_id,
                "session_name": self.session_name,
                "campaign_name": self.campaign_name,
            }

        @app.post("/api/player/leave")
        async def player_leave(request: Request):
            data = await request.json()
            token = data.get("token")
            if token and self.current_session_id:
                self.db.update_player_status(self.current_session_id, token, "OFFLINE")
                self.manager.disconnect_player(token)
                await self.manager.send_to_dm({
                    "type": "PLAYER_SOCKET_OFFLINE",
                    "player_token": token,
                })
                await self.manager.broadcast_to_all({
                    "type": "PLAYER_LIST_UPDATED",
                    "player_token": token,
                })
            return {"success": True}

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None, role: str = "player"):
            if role == "dm":
                await self.manager.connect_dm(websocket)
                try:
                    await websocket.send_text(json.dumps({
                        "type": "DM_CONNECTED",
                        "session_id": self.current_session_id,
                        "session_name": self.session_name,
                        "campaign_name": self.campaign_name,
                    }, ensure_ascii=False))
                    while True:
                        msg_text = await websocket.receive_text()
                        msg = json.loads(msg_text)
                        await self._handle_dm_ws_message(msg)
                except WebSocketDisconnect:
                    self.manager.disconnect_dm(websocket)
            else:
                player_token = token or f"p_{os.urandom(4).hex()}"
                await self.manager.connect_player(player_token, websocket)
                # Confirmar conexión al jugador
                try:
                    await websocket.send_text(json.dumps({
                        "type": "CONNECTION_ESTABLISHED",
                        "player_token": player_token,
                        "session_id": self.current_session_id,
                        "session_name": self.session_name,
                        "campaign_name": self.campaign_name,
                    }, ensure_ascii=False))
                except Exception:
                    pass

                # Si el jugador ya está en la DB, marcarlo como ALIVE
                if self.current_session_id:
                    self.db.update_player_status(self.current_session_id, player_token, "ALIVE")

                # Notificar a DM que el socket está en línea
                await self.manager.send_to_dm({
                    "type": "PLAYER_SOCKET_ONLINE",
                    "player_token": player_token,
                })
                await self.manager.broadcast_to_all({
                    "type": "PLAYER_LIST_UPDATED",
                    "player_token": player_token,
                })
                try:
                    while True:
                        msg_text = await websocket.receive_text()
                        msg = json.loads(msg_text)
                        await self._handle_player_ws_message(player_token, msg)
                except WebSocketDisconnect:
                    self.manager.disconnect_player(player_token)
                    if self.current_session_id:
                        self.db.update_player_status(self.current_session_id, player_token, "OFFLINE")
                    await self.manager.send_to_dm({
                        "type": "PLAYER_SOCKET_OFFLINE",
                        "player_token": player_token,
                    })
                    await self.manager.broadcast_to_all({
                        "type": "PLAYER_LIST_UPDATED",
                        "player_token": player_token,
                    })

        # Servir build estática de frontend para los jugadores que entran por el túnel
        dist_dir = os.path.join(self.base_dir, "frontend", "dist")
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

        return app

    async def _handle_player_ws_message(self, player_token: str, msg: Dict[str, Any]):
        msg_type = msg.get("type")
        if msg_type == "DICE_ROLL":
            # Tirada realizada por el jugador
            roll_data = msg.get("roll", {})
            actor = msg.get("character_name") or msg.get("actor_name") or "Jugador"
            if self.current_session_id:
                self.db.log_session_event(
                    session_id=self.current_session_id,
                    event_type="ROLL",
                    actor_name=actor,
                    details=roll_data,
                )
            # Retransmitir a todos (historial de tiradas compartido y animación en pantalla)
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
                char_name = char.get("name") or "Jugador"
                self.db.upsert_session_player(
                    session_id=self.current_session_id,
                    player_token=player_token,
                    character_name=char_name,
                    character_id=char.get("id"),
                    character_class=char.get("char_class", ""),
                    character_level=int(char.get("level", 1)),
                    hp_current=int(char.get("hp_current", 10)),
                    hp_max=int(char.get("hp_max", 10)),
                    ac=int(char.get("ac", 10)),
                    status="ALIVE",
                    data_json=json.dumps(char, ensure_ascii=False),
                )
                await self.manager.send_to_dm({
                    "type": "PLAYER_SHEET_UPDATED",
                    "player_token": player_token,
                    "character": char,
                })
                await self.manager.broadcast_to_all({
                    "type": "PLAYER_LIST_UPDATED",
                    "player_token": player_token,
                })

    async def _handle_dm_ws_message(self, msg: Dict[str, Any]):
        # Mensajes originados por el DM hacia jugadores
        pass

    def start(self, session_id: str, session_name: str, campaign_name: str = "Campaña Principal") -> int:
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

    def stop(self):
        """Detiene el servidor y desconecta limpiamente a todos los clientes notificándoles."""
        if self.loop and self.loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.manager.close_all("El DM ha finalizado la sesión online."),
                    self.loop
                )
                future.result(timeout=1.5)
            except Exception:
                pass

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
        if self.current_session_id:
            self.db.log_session_event(
                session_id=self.current_session_id,
                event_type="DAMAGE",
                actor_name=actor_name,
                details={"delta": delta, "player_token": player_token},
            )
        coro = self.manager.send_to_player(player_token, {
            "type": "DM_APPLY_DAMAGE",
            "delta": delta,
            "message": f"El DM te ha infligido {delta} puntos de daño.",
        })
        self.execute_async(coro)
        return True

    def apply_heal(self, player_token: str, delta: int, actor_name: str = "DM") -> bool:
        """Ordena al jugador sumar vida (activa destello verde de curación)."""
        if self.current_session_id:
            self.db.log_session_event(
                session_id=self.current_session_id,
                event_type="HEAL",
                actor_name=actor_name,
                details={"delta": delta, "player_token": player_token},
            )
        coro = self.manager.send_to_player(player_token, {
            "type": "DM_APPLY_HEAL",
            "delta": delta,
            "message": f"El DM te ha curado {delta} puntos de golpe.",
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
