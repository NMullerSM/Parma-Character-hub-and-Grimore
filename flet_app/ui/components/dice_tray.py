"""
Componente DiceTray (Tirador de Dados Interactivo con Historial y Ventaja/Desventaja)
"""
import flet as ft
from ...core.rules import roll_dice
from ..theme import (
    BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_GOLD, BORDER_DIM,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_RED
)


class DiceTray(ft.Container):
    def __init__(self, on_roll_event=None):
        super().__init__()
        self.on_roll_event = on_roll_event
        self.bgcolor = BG_CARD
        self.border = ft.border.all(1, BORDER_GOLD)
        self.border_radius = ft.border_radius.all(10)
        self.padding = 14
        self.mode = "normal"
        self.mod_val = 0

        self._build_ui()

    def _build_ui(self):
        # Selector de Modo
        self.mode_group = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="normal", label="Normal"),
                    ft.Radio(value="advantage", label="Ventaja"),
                    ft.Radio(value="disadvantage", label="Desventaja"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            value="normal",
            on_change=self._on_mode_change
        )

        # Modificador Numérico
        self.mod_input = ft.TextField(
            value="0",
            label="Mod",
            width=70,
            height=40,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.padding.all(4),
            border_color=BORDER_DIM,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_mod_change
        )

        # Botones de Dados
        dice_defs = [
            (20, "d20", True),
            (4, "d4", False),
            (6, "d6", False),
            (8, "d8", False),
            (10, "d10", False),
            (12, "d12", False),
            (100, "d100", False),
        ]

        dice_buttons = []
        for sides, label, is_hero in dice_defs:
            if is_hero:
                btn = ft.ElevatedButton(
                    text=f"🎲 {label}",
                    color="#000000",
                    bgcolor=GOLD_PRIMARY,
                    style=ft.ButtonStyle(
                        bgcolor=GOLD_PRIMARY,
                        color="#000000",
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, s=sides: self.do_roll(s)
                )
            else:
                btn = ft.OutlinedButton(
                    text=label,
                    style=ft.ButtonStyle(
                        color=GOLD_LIGHT,
                        side=ft.BorderSide(1, BORDER_DIM),
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, s=sides: self.do_roll(s)
                )
            dice_buttons.append(btn)

        # Lista con historial de tiradas
        self.log_column = ft.Column(
            controls=[
                ft.Text("Historial de tiradas vacío.", size=12, color=TEXT_MUTED, italic=True)
            ],
            scroll=ft.ScrollMode.AUTO,
            height=130,
            spacing=4
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("🎲 Tirador de Dados", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP,
                            icon_size=18,
                            icon_color=TEXT_MUTED,
                            tooltip="Limpiar historial",
                            on_click=self._clear_log
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Row(controls=dice_buttons, wrap=True, spacing=6),
                ft.Row(
                    controls=[self.mode_group, self.mod_input],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Divider(color=BORDER_DIM, height=1),
                self.log_column
            ],
            spacing=8
        )

    def _on_mode_change(self, e):
        self.mode = e.control.value

    def _on_mod_change(self, e):
        try:
            self.mod_val = int(e.control.value)
        except ValueError:
            self.mod_val = 0

    def _clear_log(self, e):
        self.log_column.controls = [
            ft.Text("Historial de tiradas vacío.", size=12, color=TEXT_MUTED, italic=True)
        ]
        if self.page:
            self.update()

    def do_roll(self, sides: int, custom_mod: int = None, custom_mode: str = None, reason: str = ""):
        mod = custom_mod if custom_mod is not None else self.mod_val
        mode = custom_mode if custom_mode is not None else self.mode
        res = roll_dice(sides=sides, mode=mode, modifier=mod)

        # Si el log estaba vacío, limpiar placeholder
        if len(self.log_column.controls) == 1 and isinstance(self.log_column.controls[0], ft.Text) and self.log_column.controls[0].italic:
            self.log_column.controls.clear()

        # Color según crítico / pifia
        color = GOLD_LIGHT
        badge_text = ""
        if res["is_crit"]:
            color = COLOR_GREEN
            badge_text = " [¡CRÍTICO!]"
        elif res["is_fumble"]:
            color = COLOR_RED
            badge_text = " [¡PIFIA!]"

        prefix = f"{reason}: " if reason else ""
        entry = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{prefix}{res['detail']}{badge_text}", size=12, color=color, weight=ft.FontWeight.W_500),
                ]
            ),
            bgcolor=BG_INPUT,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.border_radius.all(4)
        )

        self.log_column.controls.insert(0, entry)
        if len(self.log_column.controls) > 30:
            self.log_column.controls.pop()

        if self.page:
            self.update()

        if self.on_roll_event:
            self.on_roll_event(res)
