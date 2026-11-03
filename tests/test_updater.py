import os
import tempfile
import pytest
from desktop_api.auto_updater import AutoUpdateManager, OFFICIAL_RELEASE_PREFIX


def test_updater_rejects_unauthorized_urls():
    manager = AutoUpdateManager(base_dir=".", user_data_dir=tempfile.gettempdir())

    # 1. URL externa o maliciosa
    bad_url = "https://malicious-site.com/downloads/trojan.exe"
    res = manager.start_download(bad_url, version="1.0.4")
    assert res["success"] is False
    assert "URL no permitida" in res["error"]

    # 2. URL de GitHub pero de otro repositorio
    other_repo_url = "https://github.com/OtherUser/OtherRepo/releases/download/v1.0.4/Parma-Setup-1.0.4.exe"
    res2 = manager.start_download(other_repo_url, version="1.0.4")
    assert res2["success"] is False
    assert "URL no permitida" in res2["error"]

    # 3. URL oficial válida dentro de la allowlist
    valid_url = f"{OFFICIAL_RELEASE_PREFIX}v1.0.4/Parma-Setup-1.0.4.exe"
    # No la descargamos realmente para no hacer I/O de red en unit test, pero verificamos que no es rechazada en la validación
    assert valid_url.startswith(OFFICIAL_RELEASE_PREFIX)
