"""
Gestor de Historial de Tiradas de Sesión (Session Roll Ledger).
Persistencia en memoria volátil (RAM) con ciclo de vida efímero y destrucción
garantizada al concluir la partida o cerrar la aplicación.
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RollEntry:
    """Registro atómico de una tirada realizada durante la sesión de juego."""
    id: int
    timestamp: float
    time_str: str
    character_name: str
    reason: str
    formula: str
    detail: str
    total: int
    is_crit: bool
    is_fumble: bool
    channel: str  # 'TaleSpire 3D' o 'Motor Local'


class SessionRollLedger:
    """
    Libro de registro de tiradas de la sesión activa.
    Diseñado como singleton en memoria estricta para garantizar que
    al finalizar la sesión o cerrar la ventana no quede ningún residuo
    en bases de datos ni archivos persistentes.
    """
    _instance: Optional['SessionRollLedger'] = None

    def __init__(self):
        self.session_active: bool = True
        self.session_start_time: float = time.time()
        self.entries: List[RollEntry] = []
        self._next_id: int = 1

    @classmethod
    def get_current(cls) -> 'SessionRollLedger':
        """Retorna la instancia activa del libro de sesión o inicializa una nueva."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_roll(
        self,
        character_name: str,
        reason: str,
        formula: str,
        detail: str,
        total: int,
        is_crit: bool = False,
        is_fumble: bool = False,
        channel: str = "Motor Local"
    ) -> RollEntry:
        """Registra una tirada en la memoria volátil de la sesión."""
        now = time.time()
        entry = RollEntry(
            id=self._next_id,
            timestamp=now,
            time_str=time.strftime("%H:%M:%S", time.localtime(now)),
            character_name=character_name or "Héroe",
            reason=reason or "Tirada Libre",
            formula=formula,
            detail=detail,
            total=total,
            is_crit=is_crit,
            is_fumble=is_fumble,
            channel=channel
        )
        self._next_id += 1
        # Insertar al inicio para visualización cronológica inversa
        self.entries.insert(0, entry)
        return entry

    def get_history(self) -> List[RollEntry]:
        """Retorna una copia defensiva de todas las tiradas de la sesión activa."""
        return list(self.entries)

    def clear_history(self) -> None:
        """Limpia el historial de tiradas sin destruir la sesión."""
        self.entries.clear()

    def destroy_session(self) -> None:
        """
        Destruye y purga completamente el registro de tiradas de la sesión.
        Garantiza que al terminar la sesión o cerrar la app se libere la memoria RAM.
        """
        self.entries.clear()
        self._next_id = 1
        self.session_active = False
        SessionRollLedger._instance = None
