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

import json
import flet as ft
from typing import Optional

from .core.models import CharacterSheet
from .core.rules import perform_short_rest, perform_long_rest
from .core.okf_engine import OkfEngine
from .core.pdf_engine import UniversalAcroFormHandler

from .ui.theme import (
    BG_PRIMARY, BG_SURFACE, BG_CARD, BORDER_GOLD, BORDER_DIM,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, create_gold_button,
    get_app_theme
)
from .ui.components.dice_tray import DiceTray
from .ui.components.rules_dialog import RulesDialog
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
    page.window.min_width = 1040
    page.window.min_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = get_app_theme()
    page.bgcolor = BG_PRIMARY
    page.padding = 12

    # Rutas base del repo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artanis_pdf_path = os.path.join(base_dir, "Artanis LVL 4.pdf")

    # 1. Inicialización de Motores
    okf = OkfEngine(os.path.join(base_dir, "okf_dnd5e"))

    # Cargar personaje inicial
    if os.path.exists(artanis_pdf_path):
        char = UniversalAcroFormHandler.load_character_from_pdf(artanis_pdf_path)
    else:
        char = UniversalAcroFormHandler.get_blank_character()

    # 2. Componentes de Interfaz
    dice_tray = DiceTray()
    dice_tray.visible = False  # Oculto por defecto, alternable con botón 🎲 Dados

    def on_roll_request(sides: int, mod: int, reason: str):
        # Desplegar bandeja si estaba oculta y tirar
        dice_tray.visible = True
        page.update()
        dice_tray.do_roll(sides, custom_mod=mod, reason=reason)

    # Vistas Modulares (CombatView contiene la cabecera operativa de combate de Artanis)
    combat_view = CombatView(char=char, on_roll_request=on_roll_request, on_state_change=lambda: notify_state_changed())
    sheet_view = SheetView(char=char, on_roll_request=on_roll_request, on_state_change=lambda: notify_state_changed())
    spells_view = SpellsView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    powers_view = PowersView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    okf_view = OkfCompendiumView(char=char, okf_engine=okf, on_state_change=lambda: notify_state_changed())
    journal_view = JournalView(char=char, on_state_change=lambda: notify_state_changed())
    network_view = NetworkView(char=char, on_state_change=lambda: notify_state_changed())
    pdf_viewer = PdfViewerView(default_doc="Manual del Jugador 2024.pdf")
    rules_dialog = RulesDialog(page=page)

    def notify_state_changed():
        combat_view.update_data(char)
        okf_view.update_data(char)
        page.update()

    def refresh_all_views(new_char: CharacterSheet):
        nonlocal char
        char = new_char
        combat_view.update_data(char)
        sheet_view.update_data(char)
        spells_view.update_data(char)
        powers_view.update_data(char)
        okf_view.update_data(char)
        journal_view.update_data(char)
        network_view.update_data(char)
        page.update()

    # 3. Acciones de Barra Superior
    def on_new_blank(e):
        new_char = UniversalAcroFormHandler.get_blank_character()
        refresh_all_views(new_char)
        page.snack_bar = ft.SnackBar(ft.Text("Nueva hoja en blanco creada con éxito."))
        page.snack_bar.open = True
        page.update()

    def on_load_artanis(e):
        if os.path.exists(artanis_pdf_path):
            artanis_char = UniversalAcroFormHandler.load_character_from_pdf(artanis_pdf_path)
            refresh_all_views(artanis_char)
            page.snack_bar = ft.SnackBar(ft.Text("Hoja de Artanis LVL 4 cargada."))
            page.snack_bar.open = True
            page.update()

    def on_short_rest(e):
        nonlocal char
        char, msg = perform_short_rest(char)
        refresh_all_views(char)
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def on_long_rest(e):
        nonlocal char
        char, msg = perform_long_rest(char)
        refresh_all_views(char)
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def toggle_dice(e):
        dice_tray.visible = not dice_tray.visible
        page.update()

    # File Pickers para PDF y JSON
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            if file_path:
                try:
                    loaded = UniversalAcroFormHandler.load_character_from_pdf(file_path)
                    refresh_all_views(loaded)
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ficha cargada con éxito desde {os.path.basename(file_path)}"))
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error al leer PDF: {ex}"))
                    page.snack_bar.open = True
                    page.update()

    def on_json_save_result(e: ft.FilePickerResultEvent):
        if e.path:
            save_path = e.path
            if not save_path.lower().endswith(".json"):
                save_path += ".json"
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(char.to_dict(), f, indent=2, ensure_ascii=False)
                page.snack_bar = ft.SnackBar(ft.Text(f"Ficha guardada con éxito en {os.path.basename(save_path)}"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar JSON: {ex}"))
                page.snack_bar.open = True
                page.update()

    def on_json_load_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            fpath = e.files[0].path
            if fpath:
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    loaded = CharacterSheet.from_dict(data)
                    refresh_all_views(loaded)
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ficha cargada desde {os.path.basename(fpath)}"))
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error al cargar JSON: {ex}"))
                    page.snack_bar.open = True
                    page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    save_json_picker = ft.FilePicker(on_result=on_json_save_result)
    load_json_picker = ft.FilePicker(on_result=on_json_load_result)
    page.overlay.extend([file_picker, save_json_picker, load_json_picker])

    def on_open_pdf_dialog(e):
        file_picker.pick_files(
            dialog_title="Seleccionar Hoja de Personaje PDF",
            allowed_extensions=["pdf"],
            allow_multiple=False
        )

    def on_save_json_click(e):
        char_name = char.name.strip() if char.name else "personaje"
        save_json_picker.save_file(
            dialog_title="Guardar Hoja de Personaje (JSON)",
            file_name=f"{char_name}.json",
            allowed_extensions=["json"]
        )

    def on_load_json_click(e):
        load_json_picker.pick_files(
            dialog_title="Cargar Hoja de Personaje (JSON)",
            allowed_extensions=["json"],
            allow_multiple=False
        )

    def on_open_rules_click(e):
        rules_dialog.show()

    # Barra de Acciones Superior Completa
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
                    ],
                    spacing=8
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Nueva Hoja",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_new_blank,
                            tooltip="Crear una ficha limpia en blanco"
                        ),
                        ft.ElevatedButton(
                            text="Ejemplo: Artanis 4",
                            color="#000000",
                            bgcolor=GOLD_PRIMARY,
                            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
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
                        ft.OutlinedButton(
                            text="Guardar JSON",
                            icon=ft.Icons.SAVE,
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_save_json_click,
                            tooltip="Guardar cambios y progreso en archivo JSON"
                        ),
                        ft.OutlinedButton(
                            text="Cargar JSON",
                            icon=ft.Icons.UPLOAD_FILE,
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=on_load_json_click,
                            tooltip="Cargar ficha guardada en formato JSON"
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
            ft.Container(
                content=dice_tray,
                width=320,
                visible=False,
                ref=ft.Ref[ft.Container]()
            )
        ],
        expand=True,
        spacing=10
    )

    # Conectar visibilidad de bandeja de dados al layout lateral
    def on_dice_visibility_toggle(e):
        dice_tray.visible = not dice_tray.visible
        page.update()

    page.add(
        top_toolbar,
        main_layout
    )


if __name__ == "__main__":
    ft.app(target=main)
