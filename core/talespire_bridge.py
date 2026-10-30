"""
Módulo de Integración y Puente con TaleSpire.
Soporta detección tripartita de instalación, control de proceso en memoria,
sesión persistente sin desconexiones falsas y formateo de pools combinados.
"""
import sys
import os
import shutil
import subprocess
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple

PIPE_NAME = r'\\.\pipe\com.bouncyrock.talespire.lcm_pipe'
URI_SCHEME = "talespire://dice/"
ALLOWED_SIDES = {4, 6, 8, 10, 12, 20, 100}
MAX_DICE_COUNT = 40


class TaleSpireState(Enum):
    NOT_INSTALLED = "not_installed"        # No hay rastro de TaleSpire en el equipo
    INSTALLED_CLOSED = "installed_closed"  # Instalado pero el juego no está abierto
    RUNNING_IDLE = "running_idle"          # Abierto pero no conectado por el usuario
    CONNECTED = "connected"                # Sesión activa: tiradas enviadas al 3D


class TaleSpireBridge:
    """
    Controlador del canal IPC con TaleSpire.
    Implementa detección automática de instalación, auto-despliegue del Symbiote,
    y máquina de estados estables para partidas de larga duración (3-5 hrs).
    """

    def __init__(self, timeout_ms: int = 50, cache_ttl: float = 3.0):
        self.timeout_ms = timeout_ms
        self.cache_ttl = cache_ttl
        self.state: TaleSpireState = TaleSpireState.NOT_INSTALLED
        self.is_installed: bool = False
        self.symbiote_install_path: Optional[str] = None
        self.symbiote_folder_installed: bool = False
        self._check_installation()

    def find_symbiotes_directory(self) -> Optional[str]:
        """
        Localiza la carpeta oficial de Symbiotes de TaleSpire en Windows o Linux (Steam/Proton).
        Si la carpeta de datos del juego existe pero 'Symbiotes' aún no ha sido creada, la crea.
        """
        # 1. Variable de entorno personalizada si el usuario la definió
        custom_env = os.environ.get("TALESPIRE_SYMBIOTES_DIR")
        if custom_env and os.path.isdir(custom_env):
            return custom_env

        # 2. Rutas estándar en Windows
        if sys.platform == "win32":
            user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            app_data = os.environ.get("APPDATA", "")
            local_app_data = os.environ.get("LOCALAPPDATA", "")

            candidate_roots = [
                os.path.join(user_profile, "AppData", "LocalLow", "BouncyRock Entertainment", "TaleSpire"),
                os.path.join(user_profile, "AppData", "LocalLow", "Bouncyrock Entertainment", "TaleSpire"),
            ]
            if app_data:
                candidate_roots.extend([
                    os.path.abspath(os.path.join(app_data, "..", "LocalLow", "BouncyRock Entertainment", "TaleSpire")),
                    os.path.abspath(os.path.join(app_data, "..", "LocalLow", "Bouncyrock Entertainment", "TaleSpire")),
                ])
            if local_app_data:
                candidate_roots.extend([
                    os.path.abspath(os.path.join(local_app_data, "..", "LocalLow", "BouncyRock Entertainment", "TaleSpire")),
                    os.path.abspath(os.path.join(local_app_data, "..", "LocalLow", "Bouncyrock Entertainment", "TaleSpire")),
                ])

            for root in candidate_roots:
                if os.path.isdir(root):
                    sym_path = os.path.join(root, "Symbiotes")
                    try:
                        os.makedirs(sym_path, exist_ok=True)
                        return sym_path
                    except Exception:
                        if os.path.exists(sym_path):
                            return sym_path

        # 3. Rutas en Linux (Steam Proton / Wine)
        else:
            home = os.path.expanduser("~")
            steam_roots = [
                os.path.join(home, ".steam", "steam"),
                os.path.join(home, ".local", "share", "Steam"),
                os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam"),
                os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".steam", "steam"),
            ]

            # Bibliotecas adicionales configuradas en libraryfolders.vdf
            extra_libs = []
            for s_root in steam_roots:
                vdf_path = os.path.join(s_root, "steamapps", "libraryfolders.vdf")
                if os.path.isfile(vdf_path):
                    try:
                        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                if '"path"' in line:
                                    parts = line.split('"path"')
                                    if len(parts) > 1:
                                        raw_path = parts[1].strip().strip('"').replace('\\\\', '/')
                                        if os.path.isdir(raw_path) and raw_path not in extra_libs:
                                            extra_libs.append(raw_path)
                    except Exception:
                        pass

            all_search_roots = steam_roots + extra_libs
            app_ids = ["720620", "2881860"]
            bouncy_variants = ["BouncyRock Entertainment", "Bouncyrock Entertainment"]

            for root in all_search_roots:
                for app_id in app_ids:
                    pfx_users = os.path.join(root, "steamapps", "compatdata", app_id, "pfx", "drive_c", "users")
                    if os.path.isdir(pfx_users):
                        try:
                            user_dirs = [d for d in os.listdir(pfx_users) if os.path.isdir(os.path.join(pfx_users, d))]
                        except Exception:
                            user_dirs = ["steamuser"]

                        for u_name in user_dirs:
                            for b_var in bouncy_variants:
                                target_ts = os.path.join(pfx_users, u_name, "AppData", "LocalLow", b_var, "TaleSpire")
                                if os.path.isdir(target_ts):
                                    sym_path = os.path.join(target_ts, "Symbiotes")
                                    try:
                                        os.makedirs(sym_path, exist_ok=True)
                                        return sym_path
                                    except Exception:
                                        if os.path.exists(sym_path):
                                            return sym_path

        return None

    def install_or_update_symbiote(self, source_dir: str) -> Tuple[bool, str, Optional[str]]:
        """
        Instala o actualiza automáticamente los archivos del Symbiote dentro del
        directorio oficial de Symbiotes de TaleSpire.
        """
        if not source_dir or not os.path.isdir(source_dir):
            return False, f"Directorio fuente del Symbiote no encontrado: {source_dir}", None

        manifest_source = os.path.join(source_dir, "manifest.json")
        if not os.path.isfile(manifest_source):
            return False, f"El directorio {source_dir} no contiene manifest.json", None

        symbiotes_dir = self.find_symbiotes_directory()
        if not symbiotes_dir:
            return False, "No se detectó el directorio de Symbiotes de TaleSpire en el equipo", None

        target_dir = os.path.join(symbiotes_dir, "ParmaDiceBridge")
        try:
            os.makedirs(target_dir, exist_ok=True)
            copied_files = []
            for item in os.listdir(source_dir):
                s_item = os.path.join(source_dir, item)
                d_item = os.path.join(target_dir, item)
                if os.path.isfile(s_item):
                    shutil.copy2(s_item, d_item)
                    copied_files.append(item)
                elif os.path.isdir(s_item):
                    shutil.copytree(s_item, d_item, dirs_exist_ok=True)
                    copied_files.append(f"{item}/")

            self.symbiote_install_path = target_dir
            self.symbiote_folder_installed = True
            return True, f"Symbiote instalado/actualizado correctamente ({len(copied_files)} archivos)", target_dir
        except Exception as e:
            return False, f"Error al copiar archivos del Symbiote: {str(e)}", None

    def _check_installation(self) -> bool:
        """Verifica si TaleSpire está instalado mediante registro, carpetas de datos o ejecutables de Steam."""
        # 1. Comprobación mediante carpeta oficial de Symbiotes / AppData
        sym_dir = self.find_symbiotes_directory()
        if sym_dir:
            self.symbiote_install_path = os.path.join(sym_dir, "ParmaDiceBridge")
            self.symbiote_folder_installed = os.path.isdir(self.symbiote_install_path)
            self.is_installed = True
            self.state = TaleSpireState.INSTALLED_CLOSED
            return True

        if sys.platform != "win32":
            proton_found = self._check_proton_installation()
            self.is_installed = proton_found
            self.state = TaleSpireState.INSTALLED_CLOSED if proton_found else TaleSpireState.NOT_INSTALLED
            return proton_found

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"talespire\shell\open\command") as key:
                val, _ = winreg.QueryValueEx(key, "")
                if val and "TaleSpire" in val:
                    self.is_installed = True
                    self.state = TaleSpireState.INSTALLED_CLOSED
                    return True
        except (OSError, ImportError):
            pass

        steam_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\TaleSpire\TaleSpire.exe",
            r"C:\Program Files\Steam\steamapps\common\TaleSpire\TaleSpire.exe",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\TaleSpire\TaleSpire.exe"),
            os.path.expandvars(r"%ProgramFiles%\Steam\steamapps\common\TaleSpire\TaleSpire.exe"),
        ]
        for p in steam_paths:
            if os.path.exists(p):
                self.is_installed = True
                self.state = TaleSpireState.INSTALLED_CLOSED
                return True

        self.is_installed = False
        self.state = TaleSpireState.NOT_INSTALLED
        return False

    def _check_proton_installation(self) -> bool:
        home = os.path.expanduser("~")
        potential_paths = [
            os.path.join(home, ".steam/steam/steamapps/common/TaleSpire/TaleSpire.exe"),
            os.path.join(home, ".local/share/Steam/steamapps/common/TaleSpire/TaleSpire.exe"),
            os.path.join(home, ".steam/steam/steamapps/compatdata/720620"),
            os.path.join(home, ".local/share/Steam/steamapps/compatdata/720620"),
        ]
        return any(os.path.exists(p) for p in potential_paths)

    def is_process_running(self) -> bool:
        """Comprueba de forma ligera si el proceso TaleSpire.exe está en memoria (Windows o Linux/Proton)."""
        if sys.platform == "win32":
            try:
                creation_flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                output = subprocess.check_output(
                    'tasklist /FI "IMAGENAME eq TaleSpire.exe" /NH',
                    shell=True,
                    text=True,
                    creationflags=creation_flags
                )
                return "TaleSpire.exe" in output
            except Exception:
                return False
        else:
            try:
                out = subprocess.check_output(["pgrep", "-f", "-i", "TaleSpire"], text=True)
                return bool(out.strip())
            except Exception:
                return False

    def connect(self) -> tuple[bool, str]:
        """
        Engancha manualmente la sesión activa con TaleSpire.
        Informa de forma amigable si no está instalado o si no está abierto.
        """
        if not self.is_installed:
            # Reintentar verificación rápida por si se instaló recientemente
            if not self._check_installation():
                self.state = TaleSpireState.NOT_INSTALLED
                return False, "TaleSpire no está instalado en este sistema."

        if not self.is_process_running():
            self.state = TaleSpireState.INSTALLED_CLOSED
            return False, "TaleSpire no está abierto. Inicia el juego antes de conectar."

        self.state = TaleSpireState.CONNECTED
        return True, "Conectado exitosamente con TaleSpire."

    def disconnect(self) -> None:
        """Desconecta la sesión manual y vuelve a modo local sin cerrar el juego."""
        if self.is_installed:
            self.state = TaleSpireState.RUNNING_IDLE if self.is_process_running() else TaleSpireState.INSTALLED_CLOSED
        else:
            self.state = TaleSpireState.NOT_INSTALLED

    def is_session_connected(self) -> bool:
        """Verifica si la sesión debe despachar al juego."""
        if self.state != TaleSpireState.CONNECTED:
            return False
        if not self.is_process_running():
            self.state = TaleSpireState.INSTALLED_CLOSED
            return False
        return True

    def is_connected(self, force_refresh: bool = False) -> bool:
        """Alias retrocompatible para is_session_connected."""
        return self.is_session_connected()

    def build_roll_url(self, groups: List[Dict[str, Any]]) -> str:
        """
        Construye la URL 'talespire://dice/...' a partir de grupos de dados.
        Cada grupo es un dict:
          - 'label': str (opcional)
          - 'count': int (por defecto 1)
          - 'sides': int (4, 6, 8, 10, 12, 20, 100)
          - 'mod': int (modificador numérico opcional)
        """
        if not groups:
            return f"{URI_SCHEME}1d20"

        parts = []
        total_dice = 0

        for g in groups:
            count = max(1, int(g.get("count", 1)))
            sides = int(g.get("sides", 20))
            if sides not in ALLOWED_SIDES:
                sides = 20

            total_dice += count
            mod = int(g.get("mod", 0))
            raw_label = str(g.get("label", "")).strip()

            mod_str = f"+{mod}" if mod > 0 else (f"{mod}" if mod < 0 else "")
            core_roll = f"{count}d{sides}{mod_str}"

            if raw_label:
                clean_label = raw_label.replace(":", "").replace("/", "").replace("&", "")
                parts.append(f"{clean_label}:{core_roll}")
            else:
                parts.append(core_roll)

        if total_dice > MAX_DICE_COUNT:
            raise ValueError(
                f"TaleSpire no admite más de {MAX_DICE_COUNT} dados simultáneos "
                f"({total_dice} solicitados)."
            )

        return URI_SCHEME + "/".join(parts)

    def build_pool_url(self, pool: Dict[int, int], modifier: int = 0, label: str = "Tirada") -> str:
        """
        Construye la URL para un pool combinado de múltiples tipos de dados.
        Ej: pool = {20: 1, 6: 2, 8: 1}, modifier = 3
        Retorna URL con los dados combinados.
        """
        groups = []
        items = sorted(pool.items(), key=lambda x: -x[0])  # d20 primero, luego d12, etc.
        if not items:
            return f"{URI_SCHEME}1d20"

        for idx, (sides, count) in enumerate(items):
            if count <= 0:
                continue
            is_last = (idx == len(items) - 1)
            group_mod = modifier if is_last else 0
            group_label = f"{label} d{sides}" if len(items) > 1 else label
            groups.append({
                "label": group_label,
                "count": count,
                "sides": sides,
                "mod": group_mod
            })

        return self.build_roll_url(groups)

    def send_roll(self, roll_url: str) -> bool:
        """Escribe la tirada directamente al Pipe IPC de TaleSpire."""
        if not self.is_session_connected():
            return False

        try:
            with open(PIPE_NAME, 'w', encoding='utf-8', buffering=1) as pipe:
                pipe.write(f"{roll_url}\n")
                pipe.flush()
            return True
        except Exception:
            if not self.is_process_running():
                self.state = TaleSpireState.INSTALLED_CLOSED
            return False

    def execute_throw_gesture(self, ts_mode: str = "dm") -> bool:
        """
        [DESACTIVADO A FAVOR DEL SYMBIOTE OFICIAL]:
        La emulación de arrastre del cursor del sistema operativo ha sido reemplazada
        por el TaleSpire Symbiote oficial (talespire.dice.putDiceInTray), evitando
        movimientos invasivos de ratón en pantalla y permitiendo resolver las físicas
        de forma limpia directamente en el juego.
        """
        return True
