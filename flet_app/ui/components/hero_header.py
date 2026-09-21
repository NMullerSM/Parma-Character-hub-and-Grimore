"""
Componente Hero Header (Ficha Principal y Resumen de Estado)
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_GOLD, BORDER_DIM, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, create_badge
)


class HeroHeader(ft.Container):
    def __init__(self, char: CharacterSheet, on_change: Optional[Callable[[], None]] = None):
        super().__init__()
        self.char = char
        self.on_change = on_change
        self.bgcolor = BG_CARD
        self.border = ft.border.all(1, BORDER_GOLD)
        self.border_radius = ft.border_radius.all(10)
        self.padding = 16
        self.margin = ft.margin.only(bottom=12)

        self._build_ui()

    def _build_ui(self):
        # Campo de Nombre
        self.name_field = ft.TextField(
            value=self.char.name,
            border=ft.InputBorder.UNDERLINE,
            border_color=BORDER_GOLD,
            cursor_color=GOLD_LIGHT,
            text_size=24,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color="#ffffff"),
            content_padding=ft.padding.all(4),
            on_change=self._on_name_change,
            expand=True
        )

        # Insignias de Clase, Nivel, Raza, etc.
        self.badges_row = ft.Row(
            controls=[
                create_badge(f"{self.char.char_class} ({self.char.subclass or 'Nivel ' + str(self.char.level)})"),
                create_badge(f"Nivel {self.char.level}"),
                create_badge(self.char.race),
                create_badge(self.char.background or "Aventurero"),
            ],
            wrap=True,
            spacing=6
        )

        # Pills de Estadísticas Clave
        self.pill_ac = self._create_stat_pill("CLASE DE ARMADURA", str(self.char.armor_class))
        self.pill_init = self._create_stat_pill("INICIATIVA", f"+{self.char.initiative_bonus}" if self.char.initiative_bonus >= 0 else str(self.char.initiative_bonus))
        self.pill_speed = self._create_stat_pill("VELOCIDAD", self.char.speed)
        self.pill_prof = self._create_stat_pill("COMPETENCIA", f"+{self.char.proficiency_bonus}")

        # Switch de Inspiración
        self.inspiration_switch = ft.Switch(
            label="Inspiración",
            label_style=ft.TextStyle(color="#f0f2f5", size=13, weight=ft.FontWeight.BOLD),
            value=self.char.inspiration,
            active_color=GOLD_PRIMARY,
            on_change=self._on_inspiration_toggle
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls=[self.name_field, self.badges_row],
                    col={"sm": 12, "md": 6, "lg": 5},
                    spacing=6
                ),
                ft.Row(
                    controls=[
                        self.pill_ac,
                        self.pill_init,
                        self.pill_speed,
                        self.pill_prof,
                        self.inspiration_switch
                    ],
                    col={"sm": 12, "md": 6, "lg": 7},
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                    spacing=10
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _create_stat_pill(self, label: str, value: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=9, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                    ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            ),
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(6),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            alignment=ft.alignment.center
        )

    def _on_name_change(self, e):
        self.char.name = e.control.value
        if self.on_change:
            self.on_change()

    def _on_inspiration_toggle(self, e):
        self.char.inspiration = e.control.value
        if self.on_change:
            self.on_change()

    def update_data(self, char: CharacterSheet):
        self.char = char
        self.name_field.value = char.name
        self.badges_row.controls = [
            create_badge(f"{char.char_class} ({char.subclass or 'Nivel ' + str(char.level)})"),
            create_badge(f"Nivel {char.level}"),
            create_badge(char.race),
            create_badge(char.background or "Aventurero"),
        ]
        self.inspiration_switch.value = char.inspiration
        if self.page:
            self.update()
