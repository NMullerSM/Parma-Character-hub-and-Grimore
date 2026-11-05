import types

from desktop_api.tunnel_manager import CloudflareTunnelManager
from desktop_api.bridge import DesktopBridge


def test_get_lan_ip_returns_non_loopback():
    mgr = CloudflareTunnelManager()
    ip = mgr.get_lan_ip()
    assert ip
    assert not ip.startswith("127.")


def test_get_lan_url_uses_lan_ip_and_port(monkeypatch):
    mgr = CloudflareTunnelManager()
    monkeypatch.setattr(mgr, "get_lan_ip", lambda: "192.168.1.50")
    assert mgr.get_lan_url(8765) == "http://192.168.1.50:8765"


def test_get_lan_ip_falls_back_to_loopback_without_network(monkeypatch):
    mgr = CloudflareTunnelManager()

    def _raise_oserror(*args, **kwargs):
        raise OSError("red no disponible")

    monkeypatch.setattr("socket.socket.connect", _raise_oserror)
    monkeypatch.setattr("socket.gethostbyname", _raise_oserror)
    assert mgr.get_lan_ip() == "127.0.0.1"


class _FakeSessionServer:
    """Doble de DmSessionServer con solo lo que usa get_lan_connection_info."""

    def __init__(self, port=8765, session_id="sess_test", invite_token=None):
        self.port = port
        self.current_session_id = session_id
        self.current_invite_token = invite_token
        self.created_invite_calls = 0

    def create_invite(self, expires_seconds=7200):
        self.created_invite_calls += 1
        self.current_invite_token = "generated_token_abc"
        return self.current_invite_token


def test_get_lan_connection_info_requires_active_session():
    fake_bridge = types.SimpleNamespace(
        _session_server=_FakeSessionServer(session_id=None),
        _tunnel_mgr=CloudflareTunnelManager(),
    )
    result = DesktopBridge.get_lan_connection_info(fake_bridge)
    assert result["success"] is False


def test_get_lan_connection_info_reuses_existing_invite(monkeypatch):
    server = _FakeSessionServer(port=9000, invite_token="existing_token")
    mgr = CloudflareTunnelManager()
    monkeypatch.setattr(mgr, "get_lan_ip", lambda: "10.0.0.5")
    fake_bridge = types.SimpleNamespace(_session_server=server, _tunnel_mgr=mgr)

    result = DesktopBridge.get_lan_connection_info(fake_bridge)

    assert result["success"] is True
    assert result["lan_ip"] == "10.0.0.5"
    assert result["lan_url"] == "http://10.0.0.5:9000"
    assert result["invite_token"] == "existing_token"
    assert result["invite_url"] == "http://10.0.0.5:9000?invite=existing_token"
    assert server.created_invite_calls == 0


def test_get_lan_connection_info_creates_invite_when_missing(monkeypatch):
    server = _FakeSessionServer(port=9001, invite_token=None)
    mgr = CloudflareTunnelManager()
    monkeypatch.setattr(mgr, "get_lan_ip", lambda: "10.0.0.5")
    fake_bridge = types.SimpleNamespace(_session_server=server, _tunnel_mgr=mgr)

    result = DesktopBridge.get_lan_connection_info(fake_bridge)

    assert result["success"] is True
    assert result["invite_token"] == "generated_token_abc"
    assert server.created_invite_calls == 1
