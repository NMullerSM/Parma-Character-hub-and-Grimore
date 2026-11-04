import pytest
from desktop_api.bridge import DesktopBridge
from desktop_api.bridges import (
    CharacterBridgeMixin,
    TaleSpireBridgeMixin,
    PdfBridgeMixin,
    MediaBridgeMixin,
    SessionBridgeMixin,
    UpdaterBridgeMixin,
    CompendiumBridgeMixin,
)


def test_desktop_bridge_inherits_all_mixins():
    assert issubclass(DesktopBridge, CharacterBridgeMixin)
    assert issubclass(DesktopBridge, TaleSpireBridgeMixin)
    assert issubclass(DesktopBridge, PdfBridgeMixin)
    assert issubclass(DesktopBridge, MediaBridgeMixin)
    assert issubclass(DesktopBridge, SessionBridgeMixin)
    assert issubclass(DesktopBridge, UpdaterBridgeMixin)
    assert issubclass(DesktopBridge, CompendiumBridgeMixin)


def test_desktop_bridge_methods_contract():
    expected_methods = [
        # Character
        "list_characters",
        "get_active_character",
        "get_character_by_id",
        "set_active_character",
        "save_character",
        "delete_character",
        "export_character_json",
        "import_character_json",
        "get_builder_catalog",
        "get_class_spells",
        "get_class_progression_limits",
        "get_available_spells",
        "add_spell_to_character",
        "remove_spell_from_character",
        "sync_character_features",
        "sync_compendium_from_srd",
        "build_character_from_wizard",
        "generate_quick_build_preview",
        "generate_random_character_preview",
        "get_character_journals",
        "save_character_journal",
        "delete_character_journal",
        "get_character_network",
        "save_network_node",
        "delete_network_node",
        "save_network_edge",
        "delete_network_edge",
        "get_compendium_categories",
        "search_compendium",
        "get_compendium_entry",
        "validate_point_buy",
        "get_quick_build_options",
        "generate_quick_character",
        "generate_random_character",
        "perform_rest",
        "get_settings",
        "set_setting",
        "get_available_themes",
        # TaleSpire
        "get_talespire_status",
        "reinstall_talespire_symbiote",
        "open_talespire_symbiotes_folder",
        "connect_talespire",
        "disconnect_talespire",
        "roll_dice",
        "get_roll_history",
        "clear_roll_history",
        "trigger_talespire_gesture",
        # PDF
        "open_pdf_dialog",
        "list_pdf_documents",
        "open_pdf_document",
        "render_pdf_page",
        "export_character_pdf",
        "import_character_pdf",
        # Media
        "open_image_dialog",
        "upload_character_portrait",
        "set_character_portrait_base64",
        "generate_ai_portrait",
        # Session
        "start_dm_session",
        "dm_create_invitation",
        "dm_approve_player",
        "dm_revoke_player",
        "dm_get_pending_approvals",
        "dm_list_trusted_players",
        "dm_list_sessions",
        "stop_dm_session",
        "get_dm_session_status",
        "dm_apply_hp_change",
        "dm_gift_item",
        "dm_list_homebrew_items",
        "dm_save_homebrew_item",
        "dm_delete_homebrew_item",
        "dm_get_session_logs",
        "dm_save_session_notes",
        "dm_get_session_notes",
        "get_lan_connection_info",
        # Updater
        "start_auto_update",
        "get_update_progress",
        "apply_update_and_restart",
        # Compendium (SQLite)
        "search_monsters",
        "get_monster_by_id",
        "search_spells",
        "get_spell_by_id",
        "search_items",
        "get_item_by_id",
        "get_compendium_counts",
    ]

    for method in expected_methods:
        assert hasattr(DesktopBridge, method), f"DesktopBridge falta el método: {method}"
        assert callable(getattr(DesktopBridge, method)), f"{method} debe ser invocable"
