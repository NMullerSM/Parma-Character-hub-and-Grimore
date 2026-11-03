"""
Módulo de Actualización Automática en Segundo Plano (Auto-Updater Protocol).
Descarga binarios o instaladores en segundo plano sin congelar la interfaz ni cerrar
abruptamente el programa, ofreciendo progreso continuo (RPC) y reinicio silencioso
seguro con cero pérdida de datos (la base de datos y fichas en user_data_dir se preservan al 100%).
"""
import os
import sys
import time
import shutil
import hashlib
import hmac
import tempfile
import threading
import subprocess
import urllib.request
from typing import Optional, Dict, Any

OFFICIAL_RELEASE_PREFIX = "https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/download/"


class AutoUpdateManager:
    """
    Gestor de descargas asíncronas y aplicación de actualizaciones en caliente.
    """

    def __init__(self, base_dir: str, user_data_dir: str):
        self._base_dir = base_dir
        self._user_data_dir = user_data_dir
        self._window = None
        self._lock = threading.Lock()

        # Estado actual de la actualización
        self._status: str = "idle"  # "idle" | "downloading" | "ready_to_restart" | "error"
        self._percent: int = 0
        self._downloaded_bytes: int = 0
        self._total_bytes: int = 0
        self._downloaded_mb: float = 0.0
        self._total_mb: float = 0.0
        self._target_file: Optional[str] = None
        self._temp_dir: Optional[str] = None
        self._target_version: Optional[str] = None
        self._error_msg: Optional[str] = None
        self._worker_thread: Optional[threading.Thread] = None

    def set_window(self, window):
        self._window = window

    def get_progress(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "percent": self._percent,
                "downloaded_mb": self._downloaded_mb,
                "total_mb": self._total_mb,
                "error": self._error_msg,
                "version": self._target_version,
            }

    def start_download(self, download_url: str, version: str) -> Dict[str, Any]:
        # Verificación estricta de allowlist
        if not download_url or not download_url.startswith(OFFICIAL_RELEASE_PREFIX):
            return {
                "success": False,
                "error": f"URL no permitida por directiva de seguridad: {download_url}"
            }

        with self._lock:
            if self._status == "downloading":
                return {"success": True, "message": "Ya hay una descarga en curso"}

            self._status = "downloading"
            self._percent = 0
            self._downloaded_bytes = 0
            self._total_bytes = 0
            self._downloaded_mb = 0.0
            self._total_mb = 0.0
            self._target_version = version
            self._error_msg = None

            # Determinar extensión del archivo temporal según SO o URL
            ext = ".exe" if sys.platform == "win32" else (".deb" if download_url.endswith(".deb") else ".tar.gz")
            if download_url.endswith(".exe"):
                ext = ".exe"
            elif download_url.endswith(".deb"):
                ext = ".deb"
            elif download_url.endswith(".zip"):
                ext = ".zip"

            # Directorio temporal aleatorio no predecible
            self._temp_dir = tempfile.mkdtemp(prefix="parma_update_")
            filename = f"Parma-Setup-{version}{ext}"
            self._target_file = os.path.join(self._temp_dir, filename)

        self._worker_thread = threading.Thread(
            target=self._download_worker,
            args=(download_url, self._target_file),
            daemon=True,
        )
        self._worker_thread.start()
        return {"success": True, "message": "Descarga iniciada en segundo plano"}

    def _download_worker(self, url: str, destination_path: str):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Parma-AutoUpdater/1.0"},
            )
            hasher = hashlib.sha256()
            with urllib.request.urlopen(req, timeout=45) as response, open(destination_path, "wb") as out_file:
                content_len = response.headers.get("Content-Length")
                total_len = int(content_len) if content_len and content_len.isdigit() else 0

                with self._lock:
                    self._total_bytes = total_len
                    self._total_mb = round(total_len / (1024 * 1024), 2) if total_len > 0 else 0.0

                downloaded = 0
                chunk_size = 65536  # 64 KB

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)

                    with self._lock:
                        self._downloaded_bytes = downloaded
                        self._downloaded_mb = round(downloaded / (1024 * 1024), 2)
                        if total_len > 0:
                            self._percent = min(95, int((downloaded / total_len) * 95))
                        else:
                            self._percent = 50

            # Verificar integridad mínima de archivo
            if not os.path.exists(destination_path) or os.path.getsize(destination_path) == 0:
                raise RuntimeError("El archivo descargado está vacío o corrupto.")

            # Descargar y verificar manifiesto SHA256SUMS del release
            asset_filename = url.rsplit("/", 1)[-1]
            sha_url = f"{url.rsplit('/', 1)[0]}/SHA256SUMS"
            req_sha = urllib.request.Request(sha_url, headers={"User-Agent": "Parma-AutoUpdater/1.0"})

            try:
                with urllib.request.urlopen(req_sha, timeout=25) as sha_resp:
                    sha_content = sha_resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                raise RuntimeError(f"No se pudo obtener el manifiesto de integridad SHA256SUMS: {e}")

            expected_hash = None
            for line in sha_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    h, fname = parts[0], parts[1].lstrip("*")
                    if fname == asset_filename:
                        expected_hash = h.lower()
                        break

            if not expected_hash:
                raise RuntimeError(f"El archivo {asset_filename} no está registrado en el manifiesto oficial SHA256SUMS.")

            calculated_hash = hasher.hexdigest().lower()
            if not hmac.compare_digest(calculated_hash, expected_hash):
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                raise RuntimeError("Fallo crítico de integridad: el hash SHA256 no coincide con el manifiesto oficial.")

            with self._lock:
                self._percent = 100
                self._status = "ready_to_restart"

        except Exception as e:
            # En caso de fallo o verificación errónea, limpiar artefacto potencialmente alterado
            if destination_path and os.path.exists(destination_path):
                try:
                    os.remove(destination_path)
                except Exception:
                    pass
            with self._lock:
                self._status = "error"
                self._error_msg = str(e)

    def apply_update_and_restart(self) -> Dict[str, Any]:
        with self._lock:
            status = self._status
            target_path = self._target_file

        # Si estamos en modo desarrollo con git (sin instalador empaquetado)
        git_dir = os.path.join(self._base_dir, ".git")
        if not getattr(sys, "frozen", False) and os.path.exists(git_dir):
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self._base_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
                current_branch = res.stdout.strip() or "develop"
                subprocess.run(["git", "pull", "origin", current_branch], cwd=self._base_dir, check=True, timeout=30)
                if self._window:
                    self._window.destroy()
                return {"success": True, "mode": "git_pull", "branch": current_branch}
            except Exception as e:
                return {"success": False, "error": f"Error ejecutando git pull: {e}"}

        if status != "ready_to_restart" or not target_path or not os.path.exists(target_path):
            return {"success": False, "error": "No hay ningún instalador listo para aplicar."}

        try:
            if sys.platform == "win32":
                # Inno Setup: ejecución directa por lista de argumentos sin shell=True
                cmd = [target_path, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"]
                subprocess.Popen(cmd)
            elif sys.platform.startswith("linux"):
                if target_path.endswith(".deb"):
                    # Abrir el instalador deb gráfico del sistema
                    subprocess.Popen(["xdg-open", target_path])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(target_path)])
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", target_path])

            # Cerrar la ventana actual de Parma de forma segura
            def _close_app():
                time.sleep(1.0)
                if self._window:
                    self._window.destroy()
                else:
                    sys.exit(0)

            threading.Thread(target=_close_app, daemon=True).start()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
