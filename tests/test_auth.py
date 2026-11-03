import os
import tempfile
import hashlib
import pytest
from core.db import DatabaseManager
from desktop_api.session_server import is_local_request, DmSessionServer


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    yield db
    if os.path.exists(path):
        os.remove(path)
    bak = f"{path}.bak_v0"
    if os.path.exists(bak):
        os.remove(bak)


def test_is_local_request():
    # Loopback directo
    assert is_local_request("127.0.0.1", {}) is True
    assert is_local_request("::1", {}) is True
    assert is_local_request("localhost", {}) is True

    # Cloudflare Tunnel proxy (llega a loopback pero con cabeceras CF)
    assert is_local_request("127.0.0.1", {"cf-connecting-ip": "203.0.113.195"}) is False
    assert is_local_request("127.0.0.1", {"cf-ray": "8e31bf1234567890-EZE"}) is False

    # IP de red local o pública
    assert is_local_request("192.168.1.50", {}) is False
    assert is_local_request("10.0.0.12", {}) is False


def test_invitation_lifecycle(temp_db):
    session_id = "test_sess_001"
    token = "secret_invite_abc123"

    # 1. Crear invitación válida
    assert temp_db.create_invitation(session_id, token, expires_seconds=3600) is True

    # 2. Consultar invitación
    inv = temp_db.get_invitation(token)
    assert inv is not None
    assert inv["session_id"] == session_id
    assert inv["is_used"] == 0

    # 3. Marcar como consumida
    player_key = "player_key_xyz789"
    key_hash = hashlib.sha256(player_key.encode("utf-8")).hexdigest()
    assert temp_db.mark_invitation_used(token, key_hash) is True

    # 4. Una invitación usada no puede recuperarse como válida
    assert temp_db.get_invitation(token) is None


def test_invitation_expired(temp_db):
    session_id = "test_sess_002"
    token = "expired_invite_999"

    # Crear invitación expirada (-10 segundos)
    assert temp_db.create_invitation(session_id, token, expires_seconds=-10) is True

    # Debe ser rechazada
    assert temp_db.get_invitation(token) is None


def test_trusted_players_approval_and_revocation(temp_db):
    player_key = "secure_random_key_player_1"
    key_hash = hashlib.sha256(player_key.encode("utf-8")).hexdigest()

    # 1. Registro inicial sin aprobación
    temp_db.register_trusted_player("Thorin", key_hash, approved=False)
    player = temp_db.get_trusted_player_by_hash(key_hash)
    assert player is not None
    assert player["name"] == "Thorin"
    assert player["approved_by_dm"] == 0
    assert player["is_revoked"] == 0

    # 2. Aprobación por el DM
    assert temp_db.approve_trusted_player(key_hash) is True
    player = temp_db.get_trusted_player_by_hash(key_hash)
    assert player["approved_by_dm"] == 1

    # 3. Revocación
    assert temp_db.revoke_trusted_player(key_hash) is True
    player = temp_db.get_trusted_player_by_hash(key_hash)
    assert player["is_revoked"] == 1
    assert player["approved_by_dm"] == 0
