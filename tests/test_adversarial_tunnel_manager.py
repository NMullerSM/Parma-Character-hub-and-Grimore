"""
Tests adversariales de desktop_api/tunnel_manager.py.

Hallazgos cubiertos (auditoría 2026-11-08, grupo 2 del plan PLAN-AUDITORIA-2026-11-08):
- A1b: start_tunnel no es atómico. Dos disparos concurrentes o un doble clic antes de que
  salga la URL lanzan dos procesos cloudflared; el segundo queda huérfano.
- A2: la descarga y el chmod escriben sobre el binario resuelto por get_binary_path()
  (que puede venir del PATH o del bundle), en vez de confinarse a user_data_dir/bin.

Invariantes:
- I2-a: nunca hay más de un proceso cloudflared vivo lanzado por la app.
- I2-b: la app nunca escribe, borra ni cambia permisos fuera de get_user_data_dir().
- I2-c (compat): un cloudflared del PATH sigue siendo utilizable para ejecutar.

Las pruebas usan un doble de subprocess.Popen y un monkeypatch de get_user_data_dir para no
tocar ~/.local/share/parma reales ni lanzar procesos.
"""
import hashlib
import io
import os
import stat
import sys
import threading
import time

import pytest

from desktop_api import tunnel_manager
from desktop_api.tunnel_manager import CloudflareTunnelManager


class FakeProc:
    """Doble de Popen: el stdout queda bloqueado hasta que el test lo libera con _release."""

    instances = []

    def __init__(self, cmd, **kwargs):
        time.sleep(0.05)  # ensancha la ventana de carrera de A1b
        self._release = threading.Event()
        self._done = False
        self.stdout = self._lines()
        FakeProc.instances.append(self)

    def _lines(self):
        self._release.wait(5)
        if False:
            yield ""

    def poll(self):
        return 0 if self._done else None

    def terminate(self):
        self._done = True  # no libera el stdout: eso lo hace el test

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminate()


def _make_mgr(tmp_path, monkeypatch):
    monkeypatch.setattr(tunnel_manager, "get_user_data_dir", lambda: str(tmp_path / "ud"))
    return CloudflareTunnelManager(base_dir=str(tmp_path / "bundle"))


@pytest.fixture
def fake_popen(monkeypatch):
    FakeProc.instances = []
    monkeypatch.setattr(tunnel_manager.subprocess, "Popen", FakeProc)
    yield FakeProc
    for proc in FakeProc.instances:
        proc._release.set()


@pytest.fixture
def tunnel_mgr(tmp_path, monkeypatch, fake_popen):
    mgr = _make_mgr(tmp_path, monkeypatch)
    mgr.get_binary_path = lambda: "/fake/cloudflared"
    mgr.is_binary_available = lambda: True
    return mgr


# ---------------------------------------------------------------------------
# A1b: start_tunnel atómico (invariante I2-a)
# ---------------------------------------------------------------------------


def test_doble_disparo_concurrente_lanza_un_solo_proceso(tunnel_mgr, fake_popen):
    """
    Invariante I2-a. Categoría: concurrencia. Hallazgo A1b.
    8 hilos llaman start_tunnel a la vez; solo debe existir un cloudflared.
    """
    barrier = threading.Barrier(8)
    results = []

    def worker():
        barrier.wait()
        results.append(tunnel_mgr.start_tunnel(8765))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)

    assert len(results) == 8
    assert all(results)
    assert len(fake_popen.instances) == 1


def test_doble_clic_antes_de_url_reemplaza_callback_sin_lanzar_otro(tunnel_mgr, fake_popen):
    """
    Invariante I2-a. Categoría: concurrencia (doble clic). Hallazgo A1b.
    Con la URL todavía sin salir por stdout, el segundo clic no lanza proceso y su
    on_url queda como callback pendiente (el último interesado recibe la URL).
    """

    def cb1(url):
        pass

    def cb2(url):
        pass

    assert tunnel_mgr.start_tunnel(8765, on_url=cb1) is True
    assert tunnel_mgr.start_tunnel(8765, on_url=cb2) is True

    assert len(fake_popen.instances) == 1
    assert tunnel_mgr._on_url_callback is cb2


def test_stop_y_restart_crea_proceso_nuevo_y_el_viejo_termina(tunnel_mgr, fake_popen):
    """
    Invariante I2-a. Categoría: regresión (ciclo de vida normal). Hallazgo A1b.
    Guardia de regresión: start -> stop -> start deja dos procesos en total, y el primero
    ya terminó (poll() == 0). Debe pasar también antes del arreglo.
    """
    assert tunnel_mgr.start_tunnel(8765) is True
    first = fake_popen.instances[0]

    tunnel_mgr.stop_tunnel()
    assert tunnel_mgr.start_tunnel(8765) is True

    assert len(fake_popen.instances) == 2
    assert first.poll() == 0


def test_lector_viejo_no_apaga_el_tunel_nuevo(tunnel_mgr, fake_popen):
    """
    Invariante I2-a. Categoría: concurrencia (lector residual). Hallazgo A1b.
    Tras stop + start, el lector del proceso viejo termina más tarde y no debe poner
    is_running en False ni tocar el proceso nuevo.
    """
    assert tunnel_mgr.start_tunnel(8765) is True
    p1 = fake_popen.instances[0]
    tunnel_mgr.stop_tunnel()
    assert tunnel_mgr.start_tunnel(8765) is True
    p2 = fake_popen.instances[1]

    p1._release.set()
    time.sleep(0.2)

    assert tunnel_mgr.is_running is True
    assert tunnel_mgr.process is p2


# ---------------------------------------------------------------------------
# A2: escrituras confinadas a user_data_dir (invariante I2-b, compat I2-c)
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, data):
        self._buf = io.BytesIO(data)

    def read(self, n=-1):
        return self._buf.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_urlopen(data):
    def _open(url, timeout=None):
        return _FakeResp(data)

    return _open


def _exe_name(mgr):
    return "cloudflared.exe" if mgr.os_type == "Windows" else "cloudflared"


def _sysbin_setup(tmp_path, monkeypatch, mgr, content):
    """Crea un cloudflared 'del PATH' de 2 MB con el contenido dado y lo expone con shutil.which."""
    sysbin_dir = tmp_path / "sysbin"
    sysbin_dir.mkdir()
    sysbin = sysbin_dir / _exe_name(mgr)
    sysbin.write_bytes(content)
    os.chmod(sysbin, 0o755)
    monkeypatch.setattr(
        tunnel_manager.shutil,
        "which",
        lambda name, *a, **k: str(sysbin) if name == "cloudflared" else None,
    )
    return sysbin


def _sha_and_mtime(path):
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return digest, os.stat(path).st_mtime_ns


def test_binario_del_path_no_se_modifica_al_descargar(tmp_path, monkeypatch):
    """
    Invariante I2-b. Categoría: seguridad / aislamiento. Hallazgo A2.
    Con un cloudflared válido en el PATH y ninguno gestionado, download_binary debe
    instalar en user_data_dir/bin y dejar el del PATH con el mismo contenido y mtime.
    """
    content = b"x" * (2 * 1024 * 1024)
    mgr = _make_mgr(tmp_path, monkeypatch)
    sysbin = _sysbin_setup(tmp_path, monkeypatch, mgr, content)
    before = _sha_and_mtime(sysbin)

    expected = hashlib.sha256(content).hexdigest()
    monkeypatch.setitem(CloudflareTunnelManager.CLOUDFLARED_SHA256, mgr.os_type, expected)
    monkeypatch.setattr(tunnel_manager.urllib.request, "urlopen", _fake_urlopen(content))

    assert mgr.download_binary() is True

    assert _sha_and_mtime(sysbin) == before
    assert os.path.isfile(os.path.join(mgr.bin_dir, _exe_name(mgr)))


def test_hash_incorrecto_no_deja_tmp_ni_toca_el_externo(tmp_path, monkeypatch):
    """
    Invariante I2-b. Categoría: seguridad (integridad). Hallazgo A2.
    Si el hash descargado no coincide con el pineado: download_binary devuelve False, no
    queda .tmp en bin_dir y el cloudflared del PATH sigue intacto (no se borra).
    """
    content = b"x" * (2 * 1024 * 1024)
    mgr = _make_mgr(tmp_path, monkeypatch)
    sysbin = _sysbin_setup(tmp_path, monkeypatch, mgr, content)
    before = _sha_and_mtime(sysbin)

    wrong = hashlib.sha256(b"otro contenido").hexdigest()
    monkeypatch.setitem(CloudflareTunnelManager.CLOUDFLARED_SHA256, mgr.os_type, wrong)
    monkeypatch.setattr(tunnel_manager.urllib.request, "urlopen", _fake_urlopen(content))

    assert mgr.download_binary() is False

    leftovers = [f for f in os.listdir(mgr.bin_dir) if f.endswith(".tmp")]
    assert leftovers == []
    assert os.path.isfile(sysbin)
    assert _sha_and_mtime(sysbin) == before


@pytest.mark.skipif(sys.platform == "win32", reason="chmod POSIX; en Windows no aplica")
def test_bundle_no_ejecutable_no_se_chmodea(tmp_path, monkeypatch):
    """
    Invariante I2-b. Categoría: aislamiento (bundle de solo lectura). Hallazgo A2.
    Un cloudflared del bundle sin bit de ejecución no debe recibir chmod; la resolución
    cae a la ruta gestionada en user_data_dir.
    """
    mgr = _make_mgr(tmp_path, monkeypatch)
    bundle_bin = tmp_path / "bundle" / "data" / "bin" / "cloudflared"
    bundle_bin.parent.mkdir(parents=True)
    bundle_bin.write_bytes(b"x" * 16)
    os.chmod(bundle_bin, 0o644)
    monkeypatch.setattr(tunnel_manager.shutil, "which", lambda *a, **k: None)

    resolved = mgr.get_binary_path()

    assert stat.S_IMODE(os.stat(bundle_bin).st_mode) == 0o644
    assert resolved == os.path.join(mgr.bin_dir, "cloudflared")


def test_binario_del_path_se_usa_para_ejecutar(tmp_path, monkeypatch):
    """
    Invariante I2-c (compat). Categoría: compatibilidad. Guardia de regresión.
    Sin binario gestionado ni del bundle, un cloudflared del PATH sigue siendo la ruta
    de ejecución (no se verifica ni se modifica).
    """
    mgr = _make_mgr(tmp_path, monkeypatch)
    monkeypatch.setattr(tunnel_manager.shutil, "which", lambda name, *a, **k: "/x/cloudflared")

    assert mgr.get_binary_path() == "/x/cloudflared"
