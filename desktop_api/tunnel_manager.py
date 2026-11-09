"""
Gestor de Cloudflare Quick Tunnels para Parma D&D.
Permite exponer el servidor local del DM a internet de forma segura,
cero configuración de puertos y compatible con Windows, macOS y Linux.
"""
import os
import re
import sys
import time
import shutil
import hashlib
import hmac
import platform
import socket
import subprocess
import threading
import urllib.request
import io
import base64
from typing import Optional, Callable, Dict, Any

from core.paths import get_bundle_dir, get_user_data_dir

try:
    import qrcode
except ImportError:
    qrcode = None


class CloudflareTunnelManager:
    """Administra la descarga, ejecución y captura de URL de cloudflared."""

    CLOUDFLARED_VERSION = "2024.12.2"
    CLOUDFLARED_URLS = {
        "Windows": f"https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/cloudflared-windows-amd64.exe",
        "Linux": f"https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/cloudflared-linux-amd64",
        "Darwin": f"https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/cloudflared-darwin-amd64",
    }
    CLOUDFLARED_SHA256 = {
        "Windows": "c2f4a3c3ea4c62eed562ede027d586a6044d35517e335e642f4e9783e651e4a3",
        "Linux": "5237675a5e806120729acc78c5be02f9db5f406717699587abfa72b49b39fe40",
        "Darwin": "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5",
    }

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or get_bundle_dir()
        self.user_data_dir = get_user_data_dir()
        self.bin_dir = os.path.join(self.user_data_dir, "bin")
        os.makedirs(self.bin_dir, exist_ok=True)
        self.os_type = platform.system()
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self.is_running = False
        self._on_url_callback: Optional[Callable[[str], None]] = None
        # Reentrante: un on_status/on_url puede volver a entrar en start/stop.
        self._lock = threading.RLock()

    def _managed_binary_path(self) -> str:
        """Única ruta que la app instala/borra/chmodea: user_data_dir/bin."""
        exe_name = "cloudflared.exe" if self.os_type == "Windows" else "cloudflared"
        return os.path.join(self.bin_dir, exe_name)

    def get_binary_path(self) -> str:
        """Retorna la ruta hacia el ejecutable de cloudflared (resolución para EJECUTAR)."""
        exe_name = "cloudflared.exe" if self.os_type == "Windows" else "cloudflared"
        # 1. Verificar si existe en user_data_dir/bin
        local_bin = os.path.join(self.bin_dir, exe_name)
        if self.os_type != "Windows" and os.path.isfile(local_bin) and not os.access(local_bin, os.X_OK):
            try:
                os.chmod(local_bin, 0o755)
            except Exception:
                pass
        if os.path.isfile(local_bin) and os.access(local_bin, os.X_OK if self.os_type != "Windows" else os.R_OK):
            return local_bin

        # 2. Verificar si existe en bundle_dir/data/bin (solo lectura: nunca se chmodea)
        bundle_bin = os.path.join(self.base_dir, "data", "bin", exe_name)
        if os.path.isfile(bundle_bin) and os.access(bundle_bin, os.X_OK if self.os_type != "Windows" else os.R_OK):
            return bundle_bin

        # 3. Verificar si está en el PATH del sistema (se usa tal cual, sin verificar ni modificar)
        which_path = shutil.which("cloudflared")
        if which_path:
            return which_path

        return self._managed_binary_path()

    def is_binary_available(self) -> bool:
        """Indica si cloudflared ya está disponible localmente."""
        path = self.get_binary_path()
        return os.path.isfile(path) or bool(shutil.which("cloudflared"))

    def download_binary(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Descarga el binario oficial de Cloudflare y valida su hash SHA256 antes de instalar."""
        dest = self._managed_binary_path()
        expected_hash = self.CLOUDFLARED_SHA256.get(self.os_type)

        # Si ya existe en dest, verificar integridad si tenemos hash esperado
        if os.path.exists(dest) and os.path.getsize(dest) > 1000000:
            if expected_hash:
                hasher = hashlib.sha256()
                with open(dest, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                if hmac.compare_digest(hasher.hexdigest().lower(), expected_hash.lower()):
                    return True
                else:
                    # Archivo corrupto o alterado, se elimina y redescarga
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
            else:
                return True

        url = self.CLOUDFLARED_URLS.get(self.os_type)
        if not url:
            if progress_callback:
                progress_callback(f"Sistema no soportado para descarga automática: {self.os_type}")
            return False

        try:
            if progress_callback:
                progress_callback(f"Descargando cloudflared {self.CLOUDFLARED_VERSION} oficial ({self.os_type})...")

            # Descargar archivo temporal
            tmp_dest = f"{dest}.tmp"
            hasher = hashlib.sha256()
            with urllib.request.urlopen(url, timeout=60) as resp, open(tmp_dest, "wb") as out:
                while chunk := resp.read(65536):
                    out.write(chunk)
                    hasher.update(chunk)

            # Verificación de integridad SHA256 estricta
            calc_hash = hasher.hexdigest().lower()
            if expected_hash and not hmac.compare_digest(calc_hash, expected_hash.lower()):
                if os.path.exists(tmp_dest):
                    os.remove(tmp_dest)
                err_msg = f"Fallo de integridad: hash SHA256 de cloudflared no coincide ({calc_hash} != {expected_hash})"
                if progress_callback:
                    progress_callback(err_msg)
                return False

            if os.path.exists(dest):
                try:
                    os.remove(dest)
                except Exception:
                    pass
            os.rename(tmp_dest, dest)

            if self.os_type != "Windows":
                # Otorgar permisos de ejecución en Linux y Mac solo tras verificar el hash
                os.chmod(dest, 0o755)

            if progress_callback:
                progress_callback("cloudflared verificado e instalado con éxito.")
            return True
        except Exception as e:
            if os.path.exists(f"{dest}.tmp"):
                try:
                    os.remove(f"{dest}.tmp")
                except Exception:
                    pass
            if progress_callback:
                progress_callback(f"Error al descargar cloudflared: {e}")
            return False

    def start_tunnel(
        self,
        local_port: int,
        on_url: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Inicia el subproceso cloudflared para exponer local_port a internet."""
        with self._lock:
            proc_alive = self.process is not None and self.process.poll() is None
            if proc_alive:
                if self.tunnel_url:
                    if on_url:
                        on_url(self.tunnel_url)
                else:
                    # La URL todavía no salió por stdout: el último interesado la recibe.
                    self._on_url_callback = on_url
                return True
            if self.is_running and self.tunnel_url and self.process is None:
                # Modo fallback local ya activo (comportamiento actual, no cambiar)
                if on_url:
                    on_url(self.tunnel_url)
                return True

            bin_path = self.get_binary_path()
            if not self.is_binary_available():
                if on_status:
                    on_status("Descargando ejecutable de Cloudflare Tunnel...")
                success = self.download_binary(on_status)
                # Tras descargar, la ruta de ejecución debe resolver al binario gestionado.
                bin_path = self.get_binary_path()
                if not success or not os.path.exists(bin_path):
                    # Fallback amigable: permitir enlace local si falla descarga
                    fallback_url = f"http://127.0.0.1:{local_port}"
                    self.tunnel_url = fallback_url
                    self.is_running = True
                    if on_url:
                        on_url(fallback_url)
                    if on_status:
                        on_status(f"Modo Red Local / Fallback activo: {fallback_url}")
                    return True

            self._on_url_callback = on_url
            self.tunnel_url = None

            cmd = [
                bin_path,
                "tunnel",
                "--url",
                f"http://127.0.0.1:{local_port}",
                "--no-autoupdate",
            ]

            try:
                # En Windows ocultar ventana de consola
                creation_flags = 0
                if self.os_type == "Windows":
                    creation_flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=creation_flags,
                )
                self.process = proc
                self.is_running = True

                # Hilo de lectura para capturar la URL pública de trycloudflare.com
                reader_thread = threading.Thread(
                    target=self._read_tunnel_output,
                    args=(proc, on_status),
                    daemon=True,
                )
                reader_thread.start()
                return True
            except Exception as e:
                if on_status:
                    on_status(f"Error al iniciar túnel: {e}")
                return False

    def _read_tunnel_output(self, proc: subprocess.Popen, on_status: Optional[Callable[[str], None]]):
        """Monitorea la salida del túnel para extraer la URL HTTPS asignada."""
        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        if not proc or not proc.stdout:
            return

        for line in proc.stdout:
            match = url_regex.search(line)
            if match:
                with self._lock:
                    if self.process is not proc or self.tunnel_url:
                        continue
                    self.tunnel_url = match.group(0)
                    cb = self._on_url_callback
                if on_status:
                    on_status(f"Túnel activo: {self.tunnel_url}")
                if cb:
                    cb(self.tunnel_url)

        with self._lock:
            if self.process is proc:  # un lector viejo no apaga un túnel nuevo
                self.is_running = False

    def stop_tunnel(self):
        """Detiene y termina el proceso del túnel."""
        with self._lock:
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2.0)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                self.process = None
            self.is_running = False
            self.tunnel_url = None

    def get_lan_ip(self) -> str:
        """
        Detecta la IP real de la interfaz de red local activa del host (no 127.0.0.1),
        para poder exponer el servidor a otros dispositivos de la misma LAN cuando
        no hay internet o el DM elige modo LAN explícito.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.5)
                # No se envían datos: solo se usa para que el SO resuelva la interfaz
                # de salida activa hacia una red externa.
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                if ip and not ip.startswith("127."):
                    return ip
        except OSError:
            pass

        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip and not ip.startswith("127."):
                return ip
        except OSError:
            pass

        return "127.0.0.1"

    def get_lan_url(self, local_port: int) -> str:
        """Construye la URL http://IP_LAN:puerto para unirse desde la misma red local."""
        return f"http://{self.get_lan_ip()}:{local_port}"

    def generate_qr_base64(self, url: str) -> str:
        """Genera un código QR en base64 para que los jugadores lo escaneen."""
        if not qrcode or not url:
            return ""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0e1317", back_color="#ffffff")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            print(f"[TunnelManager] Error al generar QR: {e}")
            return ""
