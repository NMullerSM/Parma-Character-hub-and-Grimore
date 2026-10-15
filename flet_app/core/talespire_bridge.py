"""
Módulo de Integración y Puente con TaleSpire.
Soporta detección tripartita de instalación, control de proceso en memoria,
sesión persistente sin desconexiones falsas y formateo de pools combinados.
"""
import sys
import os
import subprocess
from enum import Enum
from typing import Optional, Dict, Any, List

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
    Implementa máquina de estados estables para partidas de larga duración (3-5 hrs).
    """

    def __init__(self, timeout_ms: int = 50, cache_ttl: float = 3.0):
        self.timeout_ms = timeout_ms
        self.cache_ttl = cache_ttl
        self.state: TaleSpireState = TaleSpireState.NOT_INSTALLED
        self.is_installed: bool = False
        self._check_installation()


    def _check_installation(self) -> bool:
        """Verifica si TaleSpire está instalado mediante el registro de Windows o Steam."""
        if sys.platform != "win32":
            # Soporte experimental para Wine/Proton en Linux
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
        ]
        return any(os.path.exists(p) for p in potential_paths)

    def is_process_running(self) -> bool:
        """Comprueba de forma ligera si el proceso TaleSpire.exe está en memoria."""
        if sys.platform != "win32":
            return False

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
        Simula el gesto físico de lanzamiento en TaleSpire con micro-impulso instantáneo.
        Calibra la altura según ts_mode y medidas de píxeles reales:
          - 'dm': ~17.5% de altura desde el borde inferior (modo GM / Build Mode: centrado en la bandeja
                  de dados d4..d20 a 180-190px del fondo, seguro por encima de la barra 'Open Library').
          - 'player': ~15.5% de altura desde el borde inferior (modo jugador / mesa limpia).
        Garantiza sincronización con el bucle de fotogramas de Unity (60 FPS) restaurando el cursor en ~25ms.
        """
        if sys.platform != "win32":
            return False

        import threading

        def _run_gesture():
            try:
                import ctypes
                from ctypes import wintypes
                import time

                user32 = ctypes.windll.user32

                # 0. Habilitar consciencia de DPI para coordenadas físicas reales precisas
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
                except Exception:
                    try:
                        user32.SetProcessDPIAware()
                    except Exception:
                        pass

                MOUSEEVENTF_LEFTDOWN = 0x0002
                MOUSEEVENTF_LEFTUP = 0x0004

                orig_pos = wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(orig_pos))
                prev_hwnd = user32.GetForegroundWindow()

                # Ratio vertical calibrado con la caja real de dados preparados [1 D20] / Staged Tray:
                # - Modo GM / Build Mode: La caja [1 D20] está exactamente al 30.0% de altura desde el fondo (Y = 756px en 1080p).
                # - Modo Jugador: Al desaparecer la barra 'Open Library' (~6% de altura / 65px), la bandeja baja esa misma
                #   distancia proporcional, situándose al 24.0% de altura desde el fondo (Y = 821px en 1080p).
                ratio = 0.300 if ts_mode == "dm" else 0.240

                # 1. Localizar ventana de TaleSpire y calcular coordenadas relativas dinámicas
                hwnd = user32.FindWindowW(None, "TaleSpire")
                if not hwnd:
                    hwnd = user32.FindWindowW("UnityWndClass", "TaleSpire")

                if hwnd and user32.IsWindow(hwnd):
                    rect = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    tray_x = rect.left + w // 2
                    tray_y = rect.bottom - int(h * ratio)
                    if prev_hwnd != hwnd:
                        user32.SetForegroundWindow(hwnd)
                else:
                    sw = user32.GetSystemMetrics(0)
                    sh = user32.GetSystemMetrics(1)
                    tray_x = sw // 2
                    tray_y = sh - int(sh * ratio)

                # 1. Espera de animación de despliegue del cajón (TweenForward en TaleSpire dura ~200ms)
                # Al recibir la URL por el Pipe, TaleSpire anima la bandeja hacia arriba desde el fondo.
                # Esta pausa garantiza que la bandeja esté 100% desplegada en Y=756px y TaleSpire tenga el foco activo.
                time.sleep(0.220)

                # 2. Posicionamiento instantáneo en la caja de dados preparados [1 D20]
                user32.SetCursorPos(tray_x, tray_y)
                time.sleep(0.015)

                # 3. Agarre firme del paquete de dados (LEFTDOWN)
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                # 25ms para asegurar que Unity InputSystem (60Hz) registre el estado Down en UIDiceTray
                time.sleep(0.025)

                # 4. Arrastre vertical multi-cuadro interpolado (6 pasos progresivos hacia la mesa 3D)
                # En Unity, DiceBoardTool requiere registrar _velocity y _velocityOneFrameBack en fotogramas sucesivos
                flick_distance = 320
                steps = 6
                step_dist = flick_distance // steps
                step_delay = 0.016  # 16ms = exactamente 1 cuadro a 60 FPS

                curr_y = tray_y
                for _ in range(steps):
                    curr_y -= step_dist
                    user32.SetCursorPos(tray_x, curr_y)
                    user32.mouse_event(0x0001, 0, 0, 0, 0)  # MOUSEEVENTF_MOVE
                    time.sleep(step_delay)

                # 5. Soltar dados en pleno vuelo hacia la mesa 3D (LEFTUP)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                # 30ms para que DiceBoardTool.End() calcule el impulso y despache ThrowDice()
                time.sleep(0.030)

                # 6. Restaurar cursor original y foco de forma inmediata
                user32.SetCursorPos(orig_pos.x, orig_pos.y)
                if prev_hwnd and prev_hwnd != hwnd:
                    user32.SetForegroundWindow(prev_hwnd)
            except Exception:
                pass

        threading.Thread(target=_run_gesture, daemon=True).start()
        return True

