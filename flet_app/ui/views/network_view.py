"""
Vista de Red de Personajes & Relaciones de Campaña
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet, NetworkNode
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, COLOR_RED, COLOR_GREEN, COLOR_BLUE,
    COLOR_PURPLE, create_card_container, create_badge
)

ROLE_COLORS = {
    "ally": (COLOR_GREEN, "Aliado"),
    "villain": (COLOR_RED, "Villano"),
    "contact": (COLOR_BLUE, "Contacto"),
    "companion": (GOLD_PRIMARY, "Compañero"),
    "enigma": (COLOR_PURPLE, "Enigma"),
    "neutral": (TEXT_MUTED, "Neutral"),
}


class NetworkView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.on_state_change = on_state_change
        self.filter_role = "all"
        self.expand = True

        self._build_ui()

    def _build_ui(self):
        # Campos para nuevo personaje
        self.name_input = ft.TextField(
            label="Nombre del Personaje",
            expand=True,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )
        self.role_dropdown = ft.Dropdown(
            label="Rol en Campaña",
            width=160,
            value="ally",
            border_color=BORDER_DIM,
            options=[
                ft.dropdown.Option("ally", "Aliado"),
                ft.dropdown.Option("villain", "Villano"),
                ft.dropdown.Option("contact", "Contacto"),
                ft.dropdown.Option("companion", "Compañero"),
                ft.dropdown.Option("enigma", "Enigma"),
                ft.dropdown.Option("neutral", "Neutral"),
            ]
        )
        self.desc_input = ft.TextField(
            label="Descripción / Secretos / Relación",
            expand=True,
            multiline=True,
            max_lines=3,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )

        btn_add = ft.ElevatedButton(
            text="+ Añadir Personaje",
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#111",
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._on_add_node
        )

        new_node_box = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Text("👥 Añadir Personaje a la Red", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(controls=[self.name_input, self.role_dropdown], spacing=8),
                    self.desc_input,
                    ft.Row(controls=[btn_add], alignment=ft.MainAxisAlignment.END)
                ],
                spacing=10
            )
        )

        # Rejilla de Personajes
        self.cards_grid = ft.ResponsiveRow(spacing=10)
        self._populate_cards()

        self.content = ft.ListView(
            controls=[
                ft.Text("🌐 Red de Personajes & Aliados de la Campaña", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ft.Text("Directorio de personajes conocidos, sus facciones, lealtades y secretos.", size=12, color=TEXT_MUTED),
                ft.Divider(color=BORDER_DIM, height=1),
                new_node_box,
                ft.Text("Directorio de la Campaña", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                self.cards_grid
            ],
            spacing=12,
            expand=True
        )

    def _populate_cards(self):
        self.cards_grid.controls.clear()
        if not self.char.network_nodes:
            self.cards_grid.controls.append(
                ft.Container(
                    content=ft.Text("Aún no hay personajes en el directorio. ¡Añade uno arriba!", size=12, color=TEXT_MUTED, italic=True),
                    padding=16,
                    col={"sm": 12}
                )
            )
            return

        for node in self.char.network_nodes:
            color, role_label = ROLE_COLORS.get(node.role, (TEXT_MUTED, "Otro"))
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.CircleAvatar(
                                            content=ft.Text(node.name[:2].upper(), size=12, weight=ft.FontWeight.BOLD, color="#fff"),
                                            bgcolor=BG_INPUT,
                                            radius=18
                                        ),
                                        ft.Text(node.name, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                    ],
                                    spacing=8
                                ),
                                create_badge(role_label, bg_color=BG_INPUT, text_color=color, border_color=color),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(node.description or "Sin descripción.", size=12, color="#d1d5db"),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=COLOR_RED,
                                    icon_size=16,
                                    tooltip="Eliminar personaje",
                                    on_click=lambda e, n=node: self._remove_node(n)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=8
                ),
                bgcolor=BG_CARD,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                padding=12,
                col={"sm": 12, "md": 6, "lg": 4}
            )
            self.cards_grid.controls.append(card)

    def _on_add_node(self, e):
        name = self.name_input.value.strip()
        if not name:
            return

        node = NetworkNode(
            id=str(len(self.char.network_nodes) + 1),
            name=name,
            role=self.role_dropdown.value,
            description=self.desc_input.value.strip()
        )
        self.char.network_nodes.append(node)

        self.name_input.value = ""
        self.desc_input.value = ""

        self._populate_cards()
        if self.page:
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def _remove_node(self, node: NetworkNode):
        if node in self.char.network_nodes:
            self.char.network_nodes.remove(node)
            self._populate_cards()
            if self.page:
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._populate_cards()
        if self.page:
            self.update()
