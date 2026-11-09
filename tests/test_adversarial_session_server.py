"""
Tests adversariales de desktop_api/session_server.py (auditoría 2026-11-08, grupo 1).

Hallazgos cubiertos: C1 (path traversal en serve_spa), C2 (join sin aprobación,
CORS amplio, sin rate-limit) y A1a (carreras en ConnectionManager / aprobación /
revocación).

Invariantes protegidos (ver plan PLAN-AUDITORIA-2026-11-08, grupo 1):
  I1-a  ningún request HTTP lee archivos fuera de frontend/dist.
  I1-b  ningún cliente remoto entra a la sesión en vivo sin aprobación del DM.
  I1-c  un remoto no agota memoria/DB con requests repetidos.
  I1-d  un jugador revocado nunca queda en active_players ni recibe DM_APPROVAL_GRANTED.
  I1-e  (compat) tokens p_ y invitaciones válidas siguen funcionando, con aprobación
        del DM; loopback y LAN no cambian.

Categorías de ataque: seguridad, input malformado, agotamiento, concurrencia,
fallo parcial, regresión / compatibilidad.
"""
import asyncio
import hashlib
import os
import threading
import time
import types
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import desktop_api.session_server as sm
from core.db import DatabaseManager
from desktop_api.session_server import ConnectionManager, DmSessionServer

REMOTE = {"cf-ray": "8e31bf1234567890-EZE"}


def _h(tok: str) -> str:
    return hashlib.sha256(tok.encode("utf-8")).hexdigest()


def _wait_until(cond, timeout: float = 1.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return cond()


def _bind_loop(srv, client) -> None:
    # En producción lo fija start(); con TestClient se toma el loop del portal.
    srv.loop = client.portal.call(asyncio.get_running_loop)


@pytest.fixture
def env(tmp_path):
    base = tmp_path / "base"
    dist = base / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("INDEX")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    secret = tmp_path / "secret.txt"
    secret.write_text("TOPSECRET")
    db = DatabaseManager(db_path=str(tmp_path / "t.db"))
    db.create_dm_session("s1", "Sesion", "Camp")   # FK obligatoria para upsert_session_player
    srv = DmSessionServer(db, str(base))
    srv.current_session_id = "s1"
    srv.approval_timeout_seconds = 1.0             # evita esperas de 120 s
    return srv, db, secret


# ---------------------------------------------------------------------------
# C1 — Path traversal en serve_spa
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("headers", [None, REMOTE], ids=["local", "remoto"])
def test_c1_traversal_codificado_no_sirve_fuera_de_dist(env, headers):
    """I1-a | seguridad | C1: '..%2F' codificado no escapa de frontend/dist (local y remoto)."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.get("/..%2F..%2F..%2Fsecret.txt", headers=headers)
    assert r.status_code == 404
    assert "TOPSECRET" not in r.text


def test_c1_ruta_absoluta_codificada_no_sirve_archivo(env):
    """I1-a | seguridad | C1: ruta absoluta codificada (os.path.join descartaba dist)."""
    srv, _, secret = env
    client = TestClient(srv.app)
    path = "/%2F" + str(secret).lstrip("/").replace("/", "%2F")
    r = client.get(path)
    assert r.status_code == 404
    assert "TOPSECRET" not in r.text


def test_c1_backslashes_no_sirve_archivo(env):
    """I1-a | seguridad | C1: vector Windows con '\\' codificado."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.get("/..%5C..%5C..%5Csecret.txt")
    assert r.status_code == 404
    assert "TOPSECRET" not in r.text


def test_c1_byte_nul_responde_404_no_500(env):
    """I1-a | input malformado | C1: byte NUL en la ruta responde 404, nunca 500."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.get("/index.html%00.png")
    assert r.status_code == 404


@pytest.mark.skipif(os.name == "nt", reason="crear symlinks requiere privilegios en Windows")
def test_c1_symlink_dentro_de_dist_que_apunta_afuera(env):
    """I1-a | seguridad | C1: symlink dentro de dist que apunta a un archivo externo."""
    srv, _, secret = env
    dist = os.path.join(srv.base_dir, "frontend", "dist")
    os.symlink(str(secret), os.path.join(dist, "link.txt"))
    client = TestClient(srv.app)
    r = client.get("/link.txt")
    assert r.status_code == 404
    assert "TOPSECRET" not in r.text


def test_c1_guardia_archivos_legitimos(env):
    """Regresión | C1: archivos legítimos de dist siguen sirviéndose."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.get("/assets/app.js")
    assert r.status_code == 200
    assert "console.log(1)" in r.text
    r = client.get("/index.html")
    assert r.status_code == 200
    assert "INDEX" in r.text


def test_c1_guardia_rutas_spa_inexistentes(env):
    """Regresión | C1: rutas SPA inexistentes devuelven index.html."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.get("/sheet/123")
    assert r.status_code == 200 and "INDEX" in r.text
    r = client.get("/")
    assert r.status_code == 200 and "INDEX" in r.text


# ---------------------------------------------------------------------------
# C2 — Join sin aprobación, CORS amplio, sin rate-limit
# ---------------------------------------------------------------------------

def test_c2_join_p_sin_invitacion_queda_pendiente(env):
    """I1-b | seguridad / bypass | C2: join remoto con p_ no entra al roster."""
    srv, db, _ = env
    client = TestClient(srv.app)
    r = client.post(
        "/api/player/join",
        json={"token": "p_evil1234", "character": {"name": "Intruso"}},
        headers=REMOTE,
    )
    assert r.status_code == 202
    assert r.json()["pending_approval"] is True
    assert db.get_session_players("s1") == []


def test_c2_join_con_invitacion_valida_queda_pendiente(env):
    """I1-b | seguridad | C2: invitación válida registra pendiente, consume la invitación y no entra al roster."""
    srv, db, _ = env
    db.create_invitation("s1", "inv_ok_1", 3600)
    client = TestClient(srv.app)
    r = client.post(
        "/api/player/join",
        json={"token": "p_inv1", "invite": "inv_ok_1", "character": {"name": "Invitado"}},
        headers=REMOTE,
    )
    assert r.status_code == 202
    assert db.get_invitation("inv_ok_1") is None
    assert db.get_session_players("s1") == []


def test_c2_join_de_jugador_ya_aprobado_entra(env):
    """I1-e | regresión (compat) | C2: jugador aprobado en la DB entra a la sesión (200)."""
    srv, db, _ = env
    db.register_trusted_player("Ya", _h("p_ok"), approved=True)
    client = TestClient(srv.app)
    r = client.post(
        "/api/player/join",
        json={"token": "p_ok", "character": {"name": "Aprobado"}},
        headers=REMOTE,
    )
    assert r.status_code == 200
    assert any(p["player_token"] == "p_ok" for p in db.get_session_players("s1"))


def test_c2_flujo_completo_legitimo_1_0_3(env):
    """I1-e | compat | C2: join p_ (202) -> WS -> aprobación del DM -> SHEET_SYNC -> join 200."""
    srv, db, _ = env
    tok = "p_xyz"
    with TestClient(srv.app) as client:
        _bind_loop(srv, client)
        r = client.post("/api/player/join", json={"token": tok, "character": {"name": "Thorin"}}, headers=REMOTE)
        assert r.status_code == 202
        with client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE) as ws:
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
            srv.approve_player(_h(tok))
            assert ws.receive_json()["type"] == "DM_APPROVAL_GRANTED"
            ws.send_json({"type": "SHEET_SYNC", "character": {"name": "Thorin", "level": 3}})
            assert _wait_until(
                lambda: any(p["player_token"] == tok and p["character_level"] == 3
                            for p in db.get_session_players("s1"))
            )
        r2 = client.post("/api/player/join", json={"token": tok, "character": {"name": "Thorin"}}, headers=REMOTE)
        assert r2.status_code == 200


def test_c2_join_local_sin_cambios(env):
    """I1-e | regresión | C2: join local entra directo al roster."""
    srv, db, _ = env
    client = TestClient(srv.app)
    r = client.post("/api/player/join", json={"token": "p_local1", "character": {"name": "Local"}})
    assert r.status_code == 200
    assert any(p["player_token"] == "p_local1" for p in db.get_session_players("s1"))


def test_c2_valores_no_numericos_no_causan_500(env):
    """Input malformado | C2: level/hp_max/ac no numéricos usan defaults (200, nunca 500)."""
    srv, db, _ = env
    client = TestClient(srv.app)
    r = client.post(
        "/api/player/join",
        json={"token": "p_m1", "character": {"name": "Raro", "level": "abc", "hp_max": "x", "ac": None}},
    )
    assert r.status_code == 200
    row = next(p for p in db.get_session_players("s1") if p["player_token"] == "p_m1")
    assert row["character_level"] == 1
    assert row["hp_max"] == 10
    assert row["ac"] == 10


def test_c2_cuerpo_invalido_responde_400(env):
    """Input malformado | C2: cuerpo no JSON o JSON no-objeto responde 400."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.post("/api/player/join", content=b"not json",
                    headers={"content-type": "application/json"})
    assert r.status_code == 400
    r = client.post("/api/player/join", json=[1, 2])
    assert r.status_code == 400


def test_c2_rate_limit_join_por_ip(env):
    """I1-c | agotamiento | C2: 5 joins por minuto por IP; el 6.º responde 429."""
    srv, _, _ = env
    client = TestClient(srv.app)
    headers = {"cf-ray": "x", "cf-connecting-ip": "203.0.113.9"}
    codes = [
        client.post("/api/player/join", json={"token": f"p_rl{i}", "character": {"name": "R"}},
                    headers=headers).status_code
        for i in range(6)
    ]
    assert codes[:5] == [202] * 5
    assert codes[5] == 429


def test_c2_rate_limit_no_afecta_otra_ip_ni_local(env):
    """Regresión | C2: tras agotar una IP, otra IP y el loopback siguen funcionando."""
    srv, _, _ = env
    client = TestClient(srv.app)
    for i in range(6):
        client.post("/api/player/join", json={"token": f"p_a{i}", "character": {"name": "A"}},
                    headers={"cf-ray": "x", "cf-connecting-ip": "203.0.113.9"})
    r = client.post("/api/player/join", json={"token": "p_b1", "character": {"name": "B"}},
                    headers={"cf-ray": "x", "cf-connecting-ip": "203.0.113.10"})
    assert r.status_code == 202
    for i in range(20):
        r = client.post("/api/player/join", json={"token": f"p_loc{i}", "character": {"name": "L"}})
        assert r.status_code == 200


def test_c2_rate_limit_handshake_ws(env):
    """I1-c | agotamiento | C2: 10 handshakes WS remotos por minuto; el 11.º cierra con 4429."""
    srv, _, _ = env
    client = TestClient(srv.app)
    for _ in range(10):
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws?token=bad&role=player", headers=REMOTE):
                pass
        assert exc.value.code == 4401
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws?token=bad&role=player", headers=REMOTE):
            pass
    assert exc.value.code == 4429


def test_c2_tope_de_pendientes(env):
    """I1-c | agotamiento | C2: con el tope de pendientes lleno, el siguiente WS cierra con 4429."""
    srv, _, _ = env
    srv.max_pending_approvals = 2
    client = TestClient(srv.app)
    with ExitStack() as stack:
        for tok in ("p_cap1", "p_cap2"):
            ws = stack.enter_context(client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE))
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws?token=p_cap3&role=player", headers=REMOTE):
                pass
        assert exc.value.code == 4429


def test_c2_cors_origen_ajeno_rechazado(env):
    """I1-b | seguridad | C2: preflight desde un origen ajeno responde 400 sin ACAO."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.options("/api/player/join", headers={
        "Origin": "https://evil.trycloudflare.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_c2_cors_origen_del_tunel_activo(env):
    """Regresión | C2: el origen del túnel activo se permite, sin credenciales."""
    srv, _, _ = env
    srv.set_public_origin("https://good-tunnel.trycloudflare.com")
    client = TestClient(srv.app)
    r = client.options("/api/player/join", headers={
        "Origin": "https://good-tunnel.trycloudflare.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "https://good-tunnel.trycloudflare.com"
    assert "access-control-allow-credentials" not in r.headers


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://localhost:8080"])
def test_c2_cors_loopback_permitido(env, origin):
    """Regresión | C2: orígenes loopback (desktop y Vite dev) siguen permitidos."""
    srv, _, _ = env
    client = TestClient(srv.app)
    r = client.options("/api/player/join", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 200


def test_c2_rate_limit_info_remoto(env):
    """I1-c | agotamiento | C2: 30 consultas de info por minuto por IP; la 31.ª responde 429."""
    srv, _, _ = env
    client = TestClient(srv.app)
    codes = [client.get("/api/session/info", headers=REMOTE).status_code for _ in range(31)]
    assert codes[:30] == [401] * 30
    assert codes[30] == 429


def test_c2_poda_msg_rate_records(env, monkeypatch):
    """I1-c | agotamiento | C2: msg_rate_records se poda y no crece sin límite."""
    srv, _, _ = env
    clock = [1000.0]
    monkeypatch.setattr(sm, "time", types.SimpleNamespace(time=lambda: clock[0]))
    for i in range(5000):
        srv.check_rate_limit(f"x:{i}", 5, 60.0)
    clock[0] += 1000.0
    srv.check_rate_limit("x:final", 5, 60.0)
    assert len(srv.msg_rate_records) <= 4097


# ---------------------------------------------------------------------------
# A1a — Carreras en ConnectionManager / aprobación / revocación
# ---------------------------------------------------------------------------

def test_a1a_revocar_pendiente_no_aprueba(env):
    """I1-d | concurrencia / seguridad | A1a: revocar a un pendiente lo cierra (4403), no lo aprueba."""
    srv, _, _ = env
    tok = "p_attacker0001"
    with TestClient(srv.app) as client:
        _bind_loop(srv, client)
        with client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE) as ws:
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
            srv.revoke_player(_h(tok))
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 4403
    assert tok not in srv.manager.active_players
    assert _h(tok) not in srv.session_approved_hashes


def test_a1a_aprobar_pendiente_admite(env):
    """Regresión | A1a: aprobar a un pendiente envía DM_APPROVAL_GRANTED y lo registra."""
    srv, _, _ = env
    tok = "p_good0001"
    with TestClient(srv.app) as client:
        _bind_loop(srv, client)
        with client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE) as ws:
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
            srv.approve_player(_h(tok))
            assert ws.receive_json()["type"] == "DM_APPROVAL_GRANTED"
            assert tok in srv.manager.active_players


def test_a1a_revocar_conectado_lo_cierra(env):
    """I1-d | regresión | A1a: revocar a un jugador conectado cierra con 4403 y lo quita del manager."""
    srv, _, _ = env
    tok = "p_connected01"
    with TestClient(srv.app) as client:
        _bind_loop(srv, client)
        with client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE) as ws:
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
            srv.approve_player(_h(tok))
            assert ws.receive_json()["type"] == "DM_APPROVAL_GRANTED"
            srv.revoke_player(_h(tok))
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 4403
    assert tok not in srv.manager.active_players


def test_a1a_json_invalido_no_deja_fantasma(env):
    """Fallo parcial | A1a: JSON inválido no mata el loop ni deja al jugador como conectado."""
    srv, _, _ = env
    tok = "p_ghost0001"
    with TestClient(srv.app) as client:
        with client.websocket_connect(f"/ws?token={tok}&role=player") as ws:
            assert _wait_until(lambda: tok in srv.manager.active_players)
            ws.send_text("{no json")
            ws.send_text("[1,2]")
    assert _wait_until(lambda: tok not in srv.manager.active_players)


def test_a1a_reconexion_no_la_borra_al_cerrar_la_vieja(env):
    """Concurrencia | A1a: al cerrar una conexión vieja no se borra la reconexión del mismo token."""
    srv, _, _ = env
    tok = "p_same"
    with TestClient(srv.app) as client:
        ws1 = client.websocket_connect(f"/ws?token={tok}&role=player")
        ws1.__enter__()
        s1 = srv.manager.active_players[tok]
        ws2 = client.websocket_connect(f"/ws?token={tok}&role=player")
        ws2.__enter__()
        s2 = srv.manager.active_players[tok]
        assert s2 is not s1
        ws1.__exit__(None, None, None)  # cierra la conexión VIEJA
        try:
            time.sleep(0.3)  # dar tiempo a que el handler de ws1 ejecute su limpieza
            assert srv.manager.active_players.get(tok) is s2
        finally:
            ws2.__exit__(None, None, None)


def test_a1a_estres_de_hilos_sobre_el_manager(env):
    """Concurrencia | A1a: add/remove/snapshot/count desde 4 hilos no lanzan y quedan coherentes."""
    mgr = ConnectionManager()
    errors = []

    def worker(wid: int):
        try:
            for i in range(2000):
                tok = f"p_{wid}_{i % 50}"
                ws = object()  # dummy: el manager solo usa identidad
                mgr.add_player(tok, ws)
                mgr.snapshot_players()
                mgr.player_count()
                mgr.remove_player(tok, ws)
        except Exception as exc:  # pragma: no cover - solo si falla
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert mgr.player_count() == len(mgr.snapshot_players())


def test_a1a_timeout_de_aprobacion_limpia_pendientes(env):
    """Regresión | A1a: sin respuesta del DM, APPROVAL_TIMEOUT, cierre 4408 y pendientes vacíos."""
    srv, _, _ = env
    srv.approval_timeout_seconds = 0.5
    tok = "p_slowpoke01"
    with TestClient(srv.app) as client:
        with client.websocket_connect(f"/ws?token={tok}&role=player", headers=REMOTE) as ws:
            assert ws.receive_json()["type"] == "PENDING_DM_APPROVAL"
            assert ws.receive_json()["type"] == "APPROVAL_TIMEOUT"
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 4408
    assert srv.pending_approvals == {}
