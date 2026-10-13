"""
Componente BuilderHeader: Barra Superior Flotante de Identidad Reactiva.
Inspirado en la cabecera persistente de D&D Beyond:
Muestra permanentemente el Avatar, Nombre, Especie, Nivel, Clase actual, PG y CA
actualizándose en tiempo real ante cualquier cambio del creador.
"""
import flet as ft
from typing import Optional, Callable
from ..theme import (
    TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD, TTUI_GOLD_LIGHT,
    TTUI_PARCHMENT, TTUI_RUNIC_GREY, TTUI_CRIMSON, create_badge, BG_INPUT
)

class BuilderHeader(ft.Container):
    def __init__(
        self,
        char_name: str = "Nuevo Aventurero",
        char_class: str = "Guerrero",
        char_species: str = "Humano",
        char_level: int = 1,
        hp_max: int = 12,
        armor_class: int = 15,
        portrait_path: str = "",
        on_name_change: Optional[Callable[[str], None]] = None
    ):
        self.char_name = char_name
        self.char_class = char_class
        self.char_species = char_species
        self.char_level = char_level
        self.hp_max = hp_max
        self.armor_class = armor_class
        self.portrait_path = portrait_path
        self.on_name_change = on_name_change

        self.name_text = ft.Text(
            self.char_name,
            size=16,
            weight=ft.FontWeight.BOLD,
            color=TTUI_GOLD_LIGHT
        )
        self.identity_subtext = ft.Text(
            f"{self.char_species} • {self.char_class} Niv {self.char_level}",
            size=12,
            color=TTUI_RUNIC_GREY
        )
        self.hp_badge = create_badge(
            f"❤️ {self.hp_max} PG",
            bg_color=BG_INPUT,
            text_color="#22c55e",
            border_color="#22c55e"
        )
        self.ac_badge = create_badge(
            f"🛡️ {self.armor_class} CA",
            bg_color=BG_INPUT,
            text_color=TTUI_GOLD_LIGHT,
            border_color=TTUI_GOLD
        )
        self.avatar_view = self._build_avatar()

        content = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        self.avatar_view,
                        ft.Column(
                            controls=[
                                self.name_text,
                                self.identity_subtext
                            ],
                            spacing=1,
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Row(
                    controls=[
                        self.hp_badge,
                        self.ac_badge,
                        create_badge("PHB 2024", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=TTUI_BORDER_SLATE)
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        super().__init__(
            content=content,
            bgcolor=TTUI_SURFACE_CARD,
            border=ft.border.all(1, TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(horizontal=14, vertical=10)
        )

    def _build_avatar(self) -> ft.Control:
        if self.portrait_path:
            return ft.CircleAvatar(
                background_image_src=self.portrait_path,
                radius=20
            )
        initials = (self.char_name[:2] if self.char_name else "AV").upper()
        return ft.CircleAvatar(
            content=ft.Text(initials, size=12, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
            bgcolor=BG_INPUT,
            radius=20
        )

    def update_identity(
        self,
        name: Optional[str] = None,
        char_class: Optional[str] = None,
        species: Optional[str] = None,
        level: Optional[int] = None,
        hp: Optional[int] = None,
        ac: Optional[int] = None,
        portrait: Optional[str] = None
    ):
        if name is not None:
            self.char_name = name
            self.name_text.value = name
        if char_class is not None:
            self.char_class = char_class
        if species is not None:
            self.char_species = species
        if level is not None:
            self.char_level = level
        if hp is not None:
            self.hp_max = hp
            self.hp_badge.content.value = f"❤️ {hp} PG"
        if ac is not None:
            self.armor_class = ac
            self.ac_badge.content.value = f"🛡️ {ac} CA"
        if portrait is not None:
            self.portrait_path = portrait

        self.identity_subtext.value = f"{self.char_species} • {self.char_class} Niv {self.char_level}"

        # Reconstruir avatar si cambió la ruta o las iniciales
        new_avatar = self._build_avatar()
        self.content.controls[0].controls[0] = new_avatar
        if self.page:
            self.update()
