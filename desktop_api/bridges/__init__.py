"""
Módulos y mixins de puente RPC para DesktopBridge.
"""
from .character_bridge import CharacterBridgeMixin, FULL_CASTER_SLOTS, _compute_spell_slots_for_class
from .talespire_bridge import TaleSpireBridgeMixin
from .pdf_bridge import PdfBridgeMixin
from .media_bridge import MediaBridgeMixin
from .session_bridge import SessionBridgeMixin
from .updater_bridge import UpdaterBridgeMixin
from .compendium_bridge import CompendiumBridgeMixin

__all__ = [
    "CharacterBridgeMixin",
    "TaleSpireBridgeMixin",
    "PdfBridgeMixin",
    "MediaBridgeMixin",
    "SessionBridgeMixin",
    "UpdaterBridgeMixin",
    "CompendiumBridgeMixin",
    "FULL_CASTER_SLOTS",
    "_compute_spell_slots_for_class",
]
