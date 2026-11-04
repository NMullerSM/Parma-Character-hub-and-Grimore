"""
Puente PyWebView (RPC / IPC) para D&D Sanctum - Fachada Unificada.
Conecta la interfaz de usuario React con los motores de negocio en Python.
Reúne mixins modulares especializados por dominio:
- CharacterBridgeMixin: CRUD de personajes, asistente Forja, compendio OKF, diarios, red y configuración.
- TaleSpireBridgeMixin: Conexión con TaleSpire, Symbiotes, lanzamiento de dados y SessionRollLedger.
- PdfBridgeMixin: Lectura, renderizado e importación/exportación de PDFs AcroForm.
- MediaBridgeMixin: Retratos de personajes, generación de imagen con IA y diálogos nativos.
- SessionBridgeMixin: Gestión de sesión DM online, LAN sin internet, túnel Cloudflare e invitaciones.
- UpdaterBridgeMixin: Auto-actualización y reinicio silencioso en segundo plano.
- CompendiumBridgeMixin: Búsqueda, filtrado y detalle sobre tablas relacionales compendium_* SQLite.
"""
import os
import sys
from typing import Optional

from core.paths import get_bundle_dir, get_user_data_dir, get_default_db_path
from core.db import DatabaseManager
from core.okf_engine import OkfEngine
from core.talespire_bridge import TaleSpireBridge
from core.pdf_engine import PdfReaderEngine
from .tunnel_manager import CloudflareTunnelManager
from .session_server import DmSessionServer
from .auto_updater import AutoUpdateManager

from .bridges import (
    CharacterBridgeMixin,
    TaleSpireBridgeMixin,
    PdfBridgeMixin,
    MediaBridgeMixin,
    SessionBridgeMixin,
    UpdaterBridgeMixin,
    CompendiumBridgeMixin,
    FULL_CASTER_SLOTS,
    _compute_spell_slots_for_class,
)


class DesktopBridge(
    CharacterBridgeMixin,
    TaleSpireBridgeMixin,
    PdfBridgeMixin,
    MediaBridgeMixin,
    SessionBridgeMixin,
    UpdaterBridgeMixin,
    CompendiumBridgeMixin,
):
    """
    Clase expuesta a JavaScript en 'window.pywebview.api'.
    Actúa como fachada unificada reuniendo todas las capacidades de los mixins modulares.
    Todos los métodos retornan tipos serializables a JSON (dict, list, str, int, bool).
    """

    def __init__(self, base_dir: Optional[str] = None):
        if not base_dir:
            base_dir = get_bundle_dir()
        self._base_dir = base_dir
        self._user_data_dir = get_user_data_dir()
        self._db = DatabaseManager(get_default_db_path())
        self._okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))
        self._ts = TaleSpireBridge()
        self._pdf_reader = PdfReaderEngine()
        self._tunnel_mgr = CloudflareTunnelManager(self._base_dir)
        self._session_server = DmSessionServer(self._db, self._base_dir)
        self._updater = AutoUpdateManager(self._base_dir, self._user_data_dir)
        self._window = None

        # Auto-iniciar servidor WebSocket en segundo plano para el Symbiote de TaleSpire y la API local
        try:
            self._session_server.ensure_running()
        except Exception as e:
            print(f"[DesktopBridge] Error iniciando DmSessionServer: {e}")

        # Migrar autosave_character.json si la base de datos está vacía
        autosave = os.path.join(self._user_data_dir, "autosave_character.json")
        if not os.path.exists(autosave):
            autosave = os.path.join(base_dir, "autosave_character.json")
        chars = self._db.list_characters()
        if not chars and os.path.exists(autosave):
            self._db.migrate_from_json(autosave)

    def set_window(self, window):
        """Asigna la ventana principal nativa de PyWebView."""
        self._window = window
        self._updater.set_window(window)
