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
import platform
import subprocess
import threading
import urllib.request
import io
import base64
from typing import Optional, Callable, Dict, Any

try:
    import qrcode
except ImportError:
    qrcode = None


class CloudflareTunnelManager:
    """Administra la descarga, ejecución y captura de URL de cloudflared."""

    CLOUDFLARED_URLS = {
        "Windows": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
        "Linux": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
        "Darwin": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64",
    }

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.bin_dir = os.path.join(base_dir, "data", "bin")
        os.makedirs(self.bin_dir, exist_ok=True)
        self.os_type = platform.system()
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self.is_running = False
        self._on_url_callback: Optional[Callable[[str], None]] = None

    def get_binary_path(self) -> str:
        """Retorna la ruta hacia el ejecutable de cloudflared."""
        exe_name = "cloudflared.exe" if self.os_type == "Windows" else "cloudflared"
        # 1. Verificar si existe en data/bin
        local_bin = os.path.join(self.bin_dir, exe_name)
        if os.path.isfile(local_bin) and os.access(local_bin, os.X_OK if self.os_type != "Windows" else os.R_OK):
            return local_bin

        # 2. Verificar si está en el PATH del sistema
        which_path = shutil.which("cloudflared")
        if which_path:
            return which_path

        return local_bin

    def is_binary_available(self) -> bool:
        """Indica si cloudflared ya está disponible localmente."""
        path = self.get_binary_path()
        return os.path.isfile(path) or bool(shutil.which("cloudflared"))

    def download_binary(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Descarga el binario oficial de Cloudflare si no existe."""
        dest = self.get_binary_path()
        if os.path.exists(dest) and os.path.getsize(dest) > 1000000:
            return True

        url = self.CLOUDFLARED_URLS.get(self.os_type)
        if not url:
            if progress_callback:
                progress_callback(f"Sistema no soportado para descarga automática: {self.os_type}")
            return False

        try:
            if progress_callback:
                progress_callback(f"Descargando cloudflared oficial ({self.os_type})...")
            
            # Descargar archivo temporal y luego mover
            tmp_dest = f"{dest}.tmp"
            urllib.request.urlretrieve(url, tmp_dest)
            
            if os.path.exists(dest):
                try:
                    os.remove(dest)
                except Exception:
                    pass
            os.rename(tmp_dest, dest)

            if self.os_type != "Windows":
                # Otorgar permisos de ejecución en Linux y Mac
                os.chmod(dest, 0o755)

            if progress_callback:
                progress_callback("cloudflared descargado e instalado con éxito.")
            return True
        except Exception as e:
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
        if self.is_running and self.tunnel_url:
            if on_url:
                on_url(self.tunnel_url)
            return True

        bin_path = self.get_binary_path()
        if not self.is_binary_available():
            if on_status:
                on_status("Descargando ejecutable de Cloudflare Tunnel...")
            success = self.download_binary(on_status)
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

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
            )
            self.is_running = True

            # Hilo de lectura para capturar la URL pública de trycloudflare.com
            reader_thread = threading.Thread(
                target=self._read_tunnel_output,
                args=(on_status,),
                daemon=True,
            )
            reader_thread.start()
            return True
        except Exception as e:
            if on_status:
                on_status(f"Error al iniciar túnel: {e}")
            return False

    def _read_tunnel_output(self, on_status: Optional[Callable[[str], None]]):
        """Monitorea la salida del túnel para extraer la URL HTTPS asignada."""
        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        if not self.process or not self.process.stdout:
            return

        for line in self.process.stdout:
            match = url_regex.search(line)
            if match and not self.tunnel_url:
                self.tunnel_url = match.group(0)
                if on_status:
                    on_status(f"Túnel activo: {self.tunnel_url}")
                if self._on_url_callback:
                    self._on_url_callback(self.tunnel_url)

        self.is_running = False

    def stop_tunnel(self):
        """Detiene y termina el proceso del túnel."""
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
