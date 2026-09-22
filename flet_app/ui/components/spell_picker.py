"""
Componente SpellPickerDialog (Buscador y Selector de Conjuros del Repositorio Atómico OKF)
"""
import flet as ft
from typing import Callable, Optional
from ...core.okf_engine import OkfEngine
from ...core.models import SpellItem
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_GOLD, BORDER_DIM, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, create_badge
)


class SpellPickerDialog:
    def __init__(self, page: ft.Page, okf_engine: OkfEngine, on_spell_selected: Callable[[SpellItem], None]):
        self.page = page
        self.okf = okf_engine
        self.on_spell_selected = on_spell_selected
        self.search_query = ""
        self.selected_level: Optional[int] = None
        self.selected_class: str = "all"

        self._build_dialog()

    def _build_dialog(self):
        self.search_field = ft.TextField(
            hint_text="Buscar por nombre, escuela, daño o componentes...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8),
            expand=True,
            on_change=self._on_search_change
        )

        self.class_dropdown = ft.Dropdown(
            label="Clase",
            width=150,
            border_color=BORDER_DIM,
            value="all",
            options=[
                ft.dropdown.Option("all", "Todas las Clases"),
                ft.dropdown.Option("Bardo", "Bardo"),
                ft.dropdown.Option("Brujo", "Brujo"),
                ft.dropdown.Option("Clérigo", "Clérigo"),
                ft.dropdown.Option("Druida", "Druida"),
                ft.dropdown.Option("Explorador", "Explorador"),
                ft.dropdown.Option("Guerrero", "Guerrero"),
                ft.dropdown.Option("Hechicero", "Hechicero"),
                ft.dropdown.Option("Mago", "Mago"),
                ft.dropdown.Option("Paladín", "Paladín"),
                ft.dropdown.Option("Pícaro", "Pícaro"),
            ],
            on_change=self._on_class_change
        )

        self.level_dropdown = ft.Dropdown(
            label="Nivel",
            width=140,
            border_color=BORDER_DIM,
            value="all",
            options=[
                ft.dropdown.Option("all", "Todos"),
                ft.dropdown.Option("0", "Trucos"),
                ft.dropdown.Option("1", "Nivel 1"),
                ft.dropdown.Option("2", "Nivel 2"),
                ft.dropdown.Option("3", "Nivel 3"),
                ft.dropdown.Option("4", "Nivel 4"),
                ft.dropdown.Option("5", "Nivel 5"),
                ft.dropdown.Option("6", "Nivel 6"),
                ft.dropdown.Option("7", "Nivel 7"),
                ft.dropdown.Option("8", "Nivel 8"),
                ft.dropdown.Option("9", "Nivel 9"),
            ],
            on_change=self._on_level_change
        )

        self.results_list = ft.ListView(
            expand=True,
            spacing=8,
            height=340
        )

        self.dialog = ft.AlertDialog(
            title=ft.Text("✨ Catálogo de Conjuros OKF (PHB 2024)", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Explora los 378 conjuros oficiales del Manual del Jugador 2024 clasificados por nivel y clase.",
                            size=12,
                            color=TEXT_MUTED
                        ),
                        ft.Row(controls=[self.search_field, self.class_dropdown, self.level_dropdown], spacing=8),
                        ft.Divider(color=BORDER_DIM, height=1),
                        self.results_list
                    ],
                    spacing=10
                ),
                width=720,
                height=480
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def show(self):
        self._refresh_results()
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close_dialog(self, e=None):
        self.dialog.open = False
        if self.dialog in self.page.overlay:
            self.page.overlay.remove(self.dialog)
        self.page.update()

    def _on_search_change(self, e):
        self.search_query = e.control.value
        self._refresh_results()

    def _on_class_change(self, e):
        self.selected_class = e.control.value
        self._refresh_results()

    def _on_level_change(self, e):
        val = e.control.value
        self.selected_level = None if val == "all" else int(val)
        self._refresh_results()

    def _refresh_results(self):
        self.results_list.controls.clear()
        results = self.okf.search_entities(
            query=self.search_query,
            tipo="conjuro",
            nivel=self.selected_level,
            clase=self.selected_class,
            limit=50
        )

        if not results:
            self.results_list.controls.append(
                ft.Container(
                    content=ft.Text("No se encontraron conjuros con ese criterio.", size=13, color=TEXT_MUTED, italic=True),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
        else:
            for item in results:
                entity_id = item.get("id")
                name = item.get("nombre", "")
                name_en = item.get("nombre_ingles", "")
                level = item.get("nivel", 0)
                school = item.get("escuela", "Magia")
                source = item.get("fuente", "PHB 2024")
                classes = item.get("clases", [])

                class_badges = [
                    create_badge(c, bg_color=BG_CARD, text_color=GOLD_LIGHT, border_color=BORDER_DIM)
                    for c in classes
                ]

                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                            ft.Text(f"({name_en})" if name_en else "", size=11, color=TEXT_MUTED),
                                        ],
                                        spacing=6
                                    ),
                                    ft.Text(
                                        f"Nivel {level if level > 0 else 'Truco'} • {school} • {source}",
                                        size=11,
                                        color=TEXT_MUTED
                                    ),
                                    ft.Row(controls=class_badges, wrap=True, spacing=4) if class_badges else ft.Container()
                                ],
                                spacing=4,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                text="+ Añadir",
                                color="#000000",
                                bgcolor=GOLD_PRIMARY,
                                style=ft.ButtonStyle(
                                    bgcolor=GOLD_PRIMARY,
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=4)
                                ),
                                on_click=lambda e, eid=entity_id: self._select_spell(eid)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER_DIM),
                    border_radius=ft.border_radius.all(6),
                    padding=10
                )
                self.results_list.controls.append(card)

        if self.page:
            self.page.update()

    def _select_spell(self, entity_id: str):
        spell = self.okf.get_spell_item(entity_id)
        self._close_dialog()
        if spell and self.on_spell_selected:
            self.on_spell_selected(spell)
