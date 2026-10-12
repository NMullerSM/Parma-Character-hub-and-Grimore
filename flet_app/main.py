"""
Visualizador & Editor D&D 5e (Flet Desktop Application)
Punto de Entrada Principal y Coordinador de Estado.
"""
import os
import sys
from pathlib import Path

# Permitir ejecutar directamente: python flet_app/main.py o python main.py
if __name__ == "__main__" and not __package__:
    import importlib
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    __package__ = "flet_app"
    importlib.import_module("flet_app")

import re
import json
import flet as ft
from typing import Optional

from .core.models import CharacterSheet
from .core.rules import perform_short_rest, perform_long_rest
from .core.okf_engine import OkfEngine
from .core.pdf_engine import UniversalAcroFormHandler
from .core.db import DatabaseManager

from .ui.theme import (
    BG_PRIMARY, BG_SURFACE, BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_GOLD, BORDER_DIM,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_RED, create_gold_button,
    create_badge, get_app_theme
)
from .ui.components.dice_tray import DiceTray
from .ui.components.rules_dialog import RulesDialog
from .ui.components.character_wizard import CharacterCreatorWizard
from .ui.views.combat_view import CombatView
from .ui.views.sheet_view import SheetView
from .ui.views.spells_view import SpellsView
from .ui.views.powers_view import PowersView
from .ui.views.journal_view import JournalView
from .ui.views.network_view import NetworkView
from .ui.views.pdf_viewer import PdfViewerView
from .ui.views.okf_view import OkfCompendiumView


def main(page: ft.Page):
    page.title = "Visualizador & Editor D&D 5e - Desktop"
    page.window.width = 1320
    page.window.height = 880
    page.window.min_width = 960
    page.window.min_height = 640
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = get_app_theme()
    page.bgcolor = BG_PRIMARY
    page.padding = 12

    # Rutas base del repo
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artanis_pdf_path = os.path.join(base_dir, "data", "characters", "Artanis LVL 4.pdf")
    if not os.path.exists(artanis_pdf_path):
        artanis_pdf_path = os.path.join(base_dir, "Artanis LVL 4.pdf")

    # 1. Inicialización de Motores y Persistencia SQLite
    okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))

    db_path = os.path.join(base_dir, "data", "dnd_database.db")
    db = DatabaseManager(db_path)

    autosave_path = os.path.join(base_dir, "autosave_character.json")

    # Cargar personaje inicial:
    # 1. Base de datos SQLite (personaje activo)
    # 2. Migración automática si existe autosave_character.json
    # 3. Artanis LVL 4.pdf
    # 4. Hoja limpia en blanco
    char = db.get_active_character()
    if not char and os.path.exists(autosave_path):
        char = db.migrate_from_json(autosave_path)
    if not char:
        if os.path.exists(artanis_pdf_path):
            try:
                char = UniversalAcroFormHandler.load_character_from_pdf(artanis_pdf_path)
                db.save_character(char, set_active=True)
            except Exception:
                char = UniversalAcroFormHandler.get_blank_character()
                db.save_character(char, set_active=True)
        else:
            char = UniversalAcroFormHandler.get_blank_character()
            db.save_character(char, set_active=True)

    # 2. Componentes de Interfaz
    dice_tray = DiceTray()
    dice_container = ft.Container(
        content=dice_tray,
        width=320,
        visible=False,
    )

    def on_roll_request(sides: int, mod: int, reason: str):
        dice_container.visible = True
        page.update()
        dice_tray.do_roll(sides, custom_mod=mod, reason=reason)

    # Control de Modo Zen Global (inmersivo para cualquier pestaña)
    is_global_zen = False

    def toggle_global_zen(e=None):
        nonlocal is_global_zen
        is_global_zen = not is_global_zen
        top_toolbar.visible = not is_global_zen
        if is_global_zen:
            dice_container.visible = False
            page.padding = 2
            btn_exit_zen.visible = True
        else:
            page.padding = 12
            btn_exit_zen.visible = False
        page.update()

    btn_exit_zen = ft.Container(
        top=8,
        right=14,
        content=ft.ElevatedButton(
            text="✕ Salir del Modo Zen (Esc)",
            icon=ft.Icons.FULLSCREEN_EXIT,
            color=GOLD_LIGHT,
            bgcolor="rgba(15, 23, 42, 0.92)",
            style=ft.ButtonStyle(
                bgcolor="rgba(15, 23, 42, 0.92)",
                color=GOLD_LIGHT,
                side=ft.BorderSide(1.5, BORDER_GOLD),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=toggle_global_zen,
            tooltip="Restaurar barra superior de navegación"
        ),
        visible=False
    )
    page.overlay.append(btn_exit_zen)

    def on_pdf_toggle_fullscreen(is_full: bool):
        top_toolbar.visible = not is_full
        dice_container.visible = False
        page.padding = 0 if is_full else 12
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            if is_global_zen:
                toggle_global_zen()
            elif pdf_viewer.is_zen:
                pdf_viewer._toggle_fullscreen()
    page.on_keyboard_event = on_keyboard

    # Vistas Modulares
    combat_view = CombatView(char=char, on_roll_request=on_roll_request, on_state_change=lambda: notify_state_changed())
    sheet_view = SheetView(char=char, on_roll_request=on_roll_request, on_state_change=lambda: notify_state_changed())
    spells_view = SpellsView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    powers_view = PowersView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    okf_view = OkfCompendiumView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    journal_view = JournalView(char=char, on_state_change=lambda: notify_state_changed())
    network_view = NetworkView(char=char, on_state_change=lambda: notify_state_changed())
    pdf_viewer = PdfViewerView(default_doc="Manual del Jugador 2024.pdf", on_toggle_zen=on_pdf_toggle_fullscreen)
    rules_dialog = RulesDialog(page=page)

    def _autosave():
        try:
            db.save_character(char, set_active=True)
            with open(autosave_path, "w", encoding="utf-8") as f:
                json.dump(char.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as ex:
            print(f"[Autosave Warning] {ex}")

    def notify_state_changed():
        _autosave()
        combat_view.update_data(char)
        sheet_view.update_data(char)
        okf_view.update_data(char)
        journal_view.update_data(char)
        network_view.update_data(char)
        page.update()

    def refresh_all_views(new_char: CharacterSheet):
        nonlocal char
        char = new_char
        _autosave()
        combat_view.update_data(char)
        sheet_view.update_data(char)
        spells_view.update_data(char)
        powers_view.update_data(char)
        okf_view.update_data(char)
        journal_view.update_data(char)
        network_view.update_data(char)
        page.update()

    # --- SELECTOR Y GESTOR DE PERSONAJES GUARDADOS ---
    char_selector = ft.Dropdown(
        width=210,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_color=BORDER_GOLD,
        color=GOLD_LIGHT,
        focused_border_color=GOLD_PRIMARY,
        tooltip="Seleccionar personaje activo"
    )

    def get_char_dropdown_options():
        saved = db.list_characters()
        options = []
        for h in saved:
            cid = str(h["id"])
            cname = h["name"]
            cclass = h.get("char_class", "")
            clevel = h.get("level", 1)
            options.append(ft.dropdown.Option(cid, f"🛡️ {cname} ({cclass} {clevel})"))
        return options, saved

    def update_char_selector():
        opts, saved = get_char_dropdown_options()
        char_selector.options = opts
        active_id = None
        for h in saved:
            if char and h["name"] == char.name:
                active_id = str(h["id"])
                break
        if not active_id and saved:
            active_id = str(saved[0]["id"])
        char_selector.value = active_id
        if char_selector.page:
            char_selector.update()

    def on_char_selector_change(e):
        selected_id = e.control.value
        if selected_id:
            loaded = db.set_active_character_by_id(int(selected_id))
            if loaded:
                refresh_all_views(loaded)
                page.snack_bar = ft.SnackBar(ft.Text(f"⚔️ Héroe activo: {loaded.name} ({loaded.char_class} Niv {loaded.level})"))
                page.snack_bar.open = True
                page.update()

    char_selector.on_change = on_char_selector_change

    # Control de exportación e importación de fichas
    pending_export_char: Optional[CharacterSheet] = None

    def on_json_import_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    imported_char = CharacterSheet.from_dict(data)
                    db.save_character(imported_char, set_active=True)
                    refresh_all_views(imported_char)
                    update_char_selector()
                    page.snack_bar = ft.SnackBar(ft.Text(f"📥 Héroe {imported_char.name} ({imported_char.char_class} Niv {imported_char.level}) importado y activado."))
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error al importar JSON: {ex}"))
                    page.snack_bar.open = True
                    page.update()

    def on_json_export_picked(e: ft.FilePickerResultEvent):
        nonlocal pending_export_char
        if e.path and pending_export_char:
            dest_path = e.path if e.path.endswith(".json") else f"{e.path}.json"
            try:
                with open(dest_path, "w", encoding="utf-8") as f:
                    json.dump(pending_export_char.to_dict(), f, indent=2, ensure_ascii=False)
                page.snack_bar = ft.SnackBar(ft.Text(f"💾 Ficha de {pending_export_char.name} exportada con éxito en {os.path.basename(dest_path)}"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error al exportar JSON: {ex}"))
                page.snack_bar.open = True
                page.update()
            finally:
                pending_export_char = None

    def on_pdf_export_picked(e: ft.FilePickerResultEvent):
        nonlocal pending_export_char
        if e.path and pending_export_char:
            dest_path = e.path if e.path.endswith(".pdf") else f"{e.path}.pdf"
            try:
                UniversalAcroFormHandler.export_character_to_pdf(pending_export_char, output_path=dest_path)
                page.snack_bar = ft.SnackBar(ft.Text(f"📜 Ficha PDF oficial generada en {os.path.basename(dest_path)}"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar PDF: {ex}"))
                page.snack_bar.open = True
                page.update()
            finally:
                pending_export_char = None

    json_import_picker = ft.FilePicker(on_result=on_json_import_picked)
    json_export_picker = ft.FilePicker(on_result=on_json_export_picked)
    pdf_export_picker = ft.FilePicker(on_result=on_pdf_export_picked)

    def open_heroes_manager_dialog(e=None):
        heroes_list_view = ft.ListView(spacing=8, expand=True)

        def populate_heroes():
            heroes_list_view.controls.clear()
            saved_heroes = db.list_characters()
            if not saved_heroes:
                heroes_list_view.controls.append(
                    ft.Container(
                        content=ft.Text("No hay personajes guardados aún. ¡Crea uno con el asistente!", size=13, color=TEXT_MUTED, italic=True),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
                if heroes_list_view.page:
                    heroes_list_view.update()
                return

            for h in saved_heroes:
                is_active = (char and h.get("name") == char.name)
                char_id = h.get("id")
                char_name = h.get("name", "Héroe sin nombre")
                char_class = h.get("char_class", "Aventurero")
                char_level = h.get("level", 1)
                char_race = h.get("race", "Desconocida")
                char_hp = f"{h.get('hp_current', 10)}/{h.get('hp_max', 10)} PG"
                portrait = h.get("portrait_path", "")

                avatar = ft.CircleAvatar(
                    content=ft.Text(char_name[:2].upper(), size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    background_image_src=portrait if portrait and os.path.exists(portrait) else None,
                    bgcolor=BG_INPUT,
                    radius=20
                )

                status_badge = create_badge("ACTIVO", bg_color=COLOR_GREEN, text_color="#ffffff", border_color=COLOR_GREEN) if is_active else None

                def on_load_hero(ev, cid=char_id):
                    loaded = db.set_active_character_by_id(cid)
                    if loaded:
                        refresh_all_views(loaded)
                        update_char_selector()
                        page.close(mgr_dialog)
                        page.snack_bar = ft.SnackBar(ft.Text(f"⚔️ Ficha de {loaded.name} ({loaded.char_class} Niv {loaded.level}) cargada."))
                        page.snack_bar.open = True
                        page.update()

                def on_delete_hero(ev, cid=char_id, cname=char_name):
                    db.delete_character(cid)
                    update_char_selector()
                    populate_heroes()
                    page.update()

                def on_export_json_hero(ev, cid=char_id, cname=char_name):
                    nonlocal pending_export_char
                    pending_export_char = db.get_character_by_id(cid) or char
                    safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', cname.strip().lower())
                    json_export_picker.save_file(
                        dialog_title=f"Exportar {cname} a JSON",
                        file_name=f"{safe_slug}.json",
                        allowed_extensions=["json"]
                    )

                def on_export_pdf_hero(ev, cid=char_id, cname=char_name):
                    nonlocal pending_export_char
                    pending_export_char = db.get_character_by_id(cid) or char
                    safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', cname.strip().lower())
                    pdf_export_picker.save_file(
                        dialog_title=f"Exportar {cname} a PDF Oficial",
                        file_name=f"{safe_slug}_oficial.pdf",
                        allowed_extensions=["pdf"]
                    )

                btn_load = ft.ElevatedButton(
                    text="Activo" if is_active else "Cargar",
                    icon=ft.Icons.CHECK if is_active else ft.Icons.PLAY_ARROW,
                    disabled=is_active,
                    style=ft.ButtonStyle(
                        bgcolor=GOLD_PRIMARY if not is_active else BG_INPUT,
                        color="#000000" if not is_active else TEXT_MUTED
                    ),
                    on_click=on_load_hero
                )

                btn_del = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=COLOR_RED,
                    icon_size=18,
                    tooltip=f"Eliminar {char_name}",
                    on_click=on_delete_hero
                )

                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    avatar,
                                    ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text(char_name, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                                    status_badge if status_badge else ft.Container()
                                                ],
                                                spacing=6
                                            ),
                                            ft.Text(f"{char_class} Niv {char_level} • {char_race} • ❤️ {char_hp}", size=12, color=TEXT_MUTED)
                                        ],
                                        spacing=2
                                    )
                                ],
                                spacing=12
                            ),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                                        icon_color=GOLD_LIGHT,
                                        icon_size=18,
                                        tooltip=f"Exportar {char_name} a JSON",
                                        on_click=on_export_json_hero
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                                        icon_color=COLOR_AMBER,
                                        icon_size=18,
                                        tooltip=f"Exportar {char_name} a PDF Oficial",
                                        on_click=on_export_pdf_hero
                                    ),
                                    btn_load,
                                    btn_del
                                ],
                                spacing=4
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor=BG_CARD,
                    border=ft.border.all(1, BORDER_GOLD if is_active else BORDER_DIM),
                    border_radius=ft.border_radius.all(8),
                    padding=10
                )
                heroes_list_view.controls.append(card)

            if heroes_list_view.page:
                heroes_list_view.update()

        populate_heroes()

        def on_new_from_dialog(ev):
            page.close(mgr_dialog)
            wizard.show()

        mgr_dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("🎭 Gestor de Héroes & Personajes", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            content=ft.Container(
                content=heroes_list_view,
                width=680,
                height=400
            ),
            actions=[
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="🧙 Crear Nuevo",
                            icon=ft.Icons.AUTO_AWESOME,
                            bgcolor=GOLD_PRIMARY,
                            color="#000000",
                            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                            on_click=on_new_from_dialog
                        ),
                        ft.ElevatedButton(
                            text="📥 Importar JSON",
                            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                            style=ft.ButtonStyle(bgcolor=BG_INPUT, color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            tooltip="Importar una ficha de personaje guardada en formato .json",
                            on_click=lambda ev: json_import_picker.pick_files(
                                dialog_title="Seleccionar ficha JSON de personaje",
                                allowed_extensions=["json"]
                            )
                        ),
                        ft.ElevatedButton(
                            text="📄 Importar PDF",
                            icon=ft.Icons.PICTURE_AS_PDF,
                            style=ft.ButtonStyle(bgcolor=BG_INPUT, color=TEXT_MUTED, side=ft.BorderSide(1, BORDER_DIM)),
                            tooltip="Importar una hoja editable oficial de D&D 5e en PDF",
                            on_click=lambda ev: pdf_character_picker.pick_files(
                                dialog_title="Seleccionar hoja de personaje PDF",
                                allowed_extensions=["pdf"]
                            )
                        )
                    ],
                    spacing=8
                ),
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=lambda ev: page.close(mgr_dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        page.open(mgr_dialog)

    btn_heroes = ft.ElevatedButton(
        text="👥 Mis Héroes",
        icon=ft.Icons.GROUPS,
        style=ft.ButtonStyle(
            bgcolor=BG_INPUT,
            color=GOLD_LIGHT,
            side=ft.BorderSide(1, BORDER_GOLD),
            shape=ft.RoundedRectangleBorder(radius=6)
        ),
        on_click=open_heroes_manager_dialog,
        tooltip="Ver y gestionar todos los personajes guardados"
    )

    # Asistente de Creación de Personajes PHB 2024
    def on_wizard_character_created(new_char: CharacterSheet):
        db.save_character(new_char, set_active=True)
        update_char_selector()
        refresh_all_views(new_char)
        tabs.selected_index = 1  # Ir directamente a la Hoja Clásica
        page.snack_bar = ft.SnackBar(ft.Text(f"✨ ¡Héroe {new_char.name} creado y guardado con éxito!"))
        page.snack_bar.open = True
        page.update()

    wizard = CharacterCreatorWizard(
        page=page,
        okf_engine=okf,
        on_character_created=on_wizard_character_created,
        on_open_manager=open_heroes_manager_dialog
    )

    # 3. Acciones de Barra Superior
    def on_new_blank(e):
        new_char = UniversalAcroFormHandler.get_blank_character()
        db.save_character(new_char, set_active=True)
        refresh_all_views(new_char)
        update_char_selector()
        page.snack_bar = ft.SnackBar(ft.Text("Nueva hoja limpia creada."))
        page.snack_bar.open = True
        page.update()

    def on_load_artanis(e):
        if os.path.exists(artanis_pdf_path):
            artanis_char = UniversalAcroFormHandler.load_character_from_pdf(artanis_pdf_path)
            db.save_character(artanis_char, set_active=True)
            refresh_all_views(artanis_char)
            update_char_selector()
            page.snack_bar = ft.SnackBar(ft.Text("Hoja de Artanis LVL 4 cargada."))
            page.snack_bar.open = True
            page.update()

    def on_short_rest(e):
        nonlocal char
        hd_curr = getattr(char, "hit_dice_current", char.level)
        hd_max = getattr(char, "hit_dice_max", char.level)
        hd_faces = getattr(char, "hit_dice_faces", 8)
        con_mod = (char.abilities.get("CON", 10) - 10) // 2
        con_str = f"+{con_mod}" if con_mod >= 0 else str(con_mod)

        dice_input = ft.TextField(
            value=str(min(1, hd_curr)),
            width=65,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.padding.all(4),
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        def do_rest(ev):
            page.close(rest_dialog)
            try:
                spent = max(0, min(hd_curr, int(dice_input.value or "0")))
            except ValueError:
                spent = 0
            nonlocal char
            char, msg = perform_short_rest(char, hit_dice_spent=spent)
            refresh_all_views(char)
            page.snack_bar = ft.SnackBar(ft.Text(msg))
            page.snack_bar.open = True
            page.update()

        info_text = (
            f"Dados de golpe disponibles: {hd_curr} / {hd_max} (d{hd_faces})\n"
            f"Modificador de Constitución: {con_str} por cada dado tirado.\n"
            f"Cada dado gastado restaurará 1d{hd_faces} + CON a tus PG.\n"
            "Tus poderes de recarga corta se renovarán automáticamente."
        )

        rest_dialog = ft.AlertDialog(
            title=ft.Text("☕ Descanso Corto (1 hora)", size=17, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(info_text, size=12, color="#e5e7eb"),
                        ft.Divider(color=BORDER_DIM, height=1),
                        ft.Row(
                            controls=[
                                ft.Text(f"Dados a gastar (0 a {hd_curr}):", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                dice_input,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                    ],
                    spacing=10
                ),
                width=450,
                height=180
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=lambda ev: page.close(rest_dialog)),
                ft.ElevatedButton(
                    text="Descansar",
                    icon=ft.Icons.BEDTIME,
                    bgcolor=GOLD_PRIMARY,
                    color="#000000",
                    style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                    on_click=do_rest
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.open(rest_dialog)

    def on_long_rest(e):
        nonlocal char
        char, msg = perform_long_rest(char)
        refresh_all_views(char)
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def toggle_dice(e):
        dice_container.visible = not dice_container.visible
        page.update()

    # File Pickers dedicados para cada flujo
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            if file_path:
                try:
                    loaded = UniversalAcroFormHandler.load_character_from_pdf(file_path)
                    db.save_character(loaded, set_active=True)
                    refresh_all_views(loaded)
                    update_char_selector()
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ficha cargada con éxito desde {os.path.basename(file_path)}"))
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error al leer PDF: {ex}"))
                    page.snack_bar.open = True
                    page.update()

    pdf_character_picker = ft.FilePicker(on_result=on_file_picked)
    portrait_picker_combat = ft.FilePicker()
    portrait_picker_sheet = ft.FilePicker()
    pdf_manual_picker = ft.FilePicker()

    page.overlay.extend([
        pdf_character_picker,
        json_import_picker,
        json_export_picker,
        pdf_export_picker,
        portrait_picker_combat,
        portrait_picker_sheet,
        pdf_manual_picker
    ])

    combat_view.attach_file_picker(portrait_picker_combat)
    sheet_view.attach_file_picker(portrait_picker_sheet)
    pdf_viewer.attach_file_picker(pdf_manual_picker)

    def on_open_pdf_dialog(e):
        pdf_character_picker.pick_files(
            dialog_title="Seleccionar Hoja de Personaje PDF",
            allowed_extensions=["pdf"],
            allow_multiple=False
        )

    def on_open_rules_click(e):
        rules_dialog.show()

    def on_quick_export_json(e):
        nonlocal pending_export_char
        if char:
            pending_export_char = char
            safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', char.name.strip().lower())
            json_export_picker.save_file(
                dialog_title=f"Exportar {char.name} a JSON",
                file_name=f"{safe_slug}.json",
                allowed_extensions=["json"]
            )

    def on_quick_export_pdf(e):
        nonlocal pending_export_char
        if char:
            pending_export_char = char
            safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', char.name.strip().lower())
            pdf_export_picker.save_file(
                dialog_title=f"Exportar {char.name} a PDF Oficial",
                file_name=f"{safe_slug}_oficial.pdf",
                allowed_extensions=["pdf"]
            )

    btn_export_menu = ft.PopupMenuButton(
        icon=ft.Icons.IOS_SHARE,
        tooltip="Exportar ficha activa (JSON / PDF)",
        items=[
            ft.PopupMenuItem(
                text="Exportar Ficha (.json)",
                icon=ft.Icons.FILE_DOWNLOAD,
                on_click=on_quick_export_json
            ),
            ft.PopupMenuItem(
                text="Exportar a PDF Oficial",
                icon=ft.Icons.PICTURE_AS_PDF,
                on_click=on_quick_export_pdf
            ),
        ]
    )

    # Barra de Acciones Superior Optimizada y Limpia
    top_toolbar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text("D&D 5e", size=11, weight=ft.FontWeight.BOLD, color="#000000"),
                            bgcolor=GOLD_PRIMARY,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=ft.border_radius.all(4)
                        ),
                        ft.Text("Visualizador & Editor", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ft.VerticalDivider(width=1, color=BORDER_DIM),
                        char_selector,
                        btn_heroes,
                        btn_export_menu,
                    ],
                    spacing=8
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="🧙 Crear Personaje",
                            icon=ft.Icons.AUTO_AWESOME,
                            bgcolor=GOLD_PRIMARY,
                            color="#000000",
                            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                            on_click=lambda e: wizard.show(),
                            tooltip="Asistente guiado paso a paso PHB 2024 / OKF"
                        ),
                        ft.OutlinedButton(
                            text="Ejemplo: Artanis 4",
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_load_artanis,
                            tooltip="Restaurar hoja de ejemplo Artanis LVL 4"
                        ),
                        ft.OutlinedButton(
                            text="Abrir PDF",
                            icon=ft.Icons.PICTURE_AS_PDF,
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_open_pdf_dialog,
                            tooltip="Importar hoja oficial desde un PDF"
                        ),
                        ft.VerticalDivider(width=1, color=BORDER_DIM),
                        ft.OutlinedButton(
                            text="Descanso Corto",
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_short_rest,
                            tooltip="Gastar dados de golpe para curar y activar Canción de Descanso"
                        ),
                        ft.ElevatedButton(
                            text="Descanso Largo",
                            color="#ffffff",
                            bgcolor=COLOR_GREEN,
                            style=ft.ButtonStyle(bgcolor=COLOR_GREEN, color="#ffffff"),
                            on_click=on_long_rest,
                            tooltip="Restaurar toda la salud, dados de golpe y espacios de conjuro"
                        ),
                        ft.ElevatedButton(
                            text="🎲 Dados",
                            color=GOLD_LIGHT,
                            bgcolor=BG_CARD,
                            style=ft.ButtonStyle(bgcolor=BG_CARD, color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                            on_click=toggle_dice,
                            tooltip="Mostrar u ocultar la bandeja interactiva de dados"
                        ),
                        ft.OutlinedButton(
                            text="📖 Reglas",
                            icon=ft.Icons.MENU_BOOK,
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                            on_click=on_open_rules_click,
                            tooltip="Compendio rápido de reglas oficiales D&D 5e"
                        ),
                        ft.ElevatedButton(
                            text="🧘 Modo Zen",
                            icon=ft.Icons.FIT_SCREEN,
                            color=GOLD_LIGHT,
                            bgcolor=BG_CARD,
                            style=ft.ButtonStyle(bgcolor=BG_CARD, color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                            on_click=toggle_global_zen,
                            tooltip="Modo Inmersivo Global: Oculta barras para maximizar el área de trabajo en cualquier pestaña"
                        ),
                    ],
                    wrap=True,
                    spacing=6
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            wrap=True
        ),
        bgcolor=BG_SURFACE,
        border=ft.border.all(1, BORDER_DIM),
        border_radius=ft.border_radius.all(8),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        margin=ft.margin.only(bottom=8)
    )

    update_char_selector()

    # 4. Pestañas de Navegación
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=250,
        divider_color=BORDER_DIM,
        indicator_color=BORDER_GOLD,
        label_color=GOLD_LIGHT,
        unselected_label_color=TEXT_MUTED,
        tabs=[
            ft.Tab(text="⚔️ Combate & Estado", content=combat_view),
            ft.Tab(text="📄 Hoja Clásica", content=sheet_view),
            ft.Tab(text="✨ Conjuros & Magia", content=spells_view),
            ft.Tab(text="🌟 Rasgos & Poderes", content=powers_view),
            ft.Tab(text="🌳 Árbol OKF", content=okf_view),
            ft.Tab(text="📘 Visor de Manuales", content=pdf_viewer),
            ft.Tab(text="📖 Diario de Campaña", content=journal_view),
            ft.Tab(text="🌐 Red de Personajes", content=network_view),
        ],
        expand=True
    )

    # Contenedor principal con soporte lateral de DiceTray (tabs ocupa toda la altura disponible)
    main_layout = ft.Row(
        controls=[
            tabs,
            dice_container
        ],
        expand=True,
        spacing=10
    )

    page.add(
        top_toolbar,
        main_layout
    )


if __name__ == "__main__":
    ft.app(target=main)
