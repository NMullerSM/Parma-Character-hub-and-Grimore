"""
Componente AbilityMatrix: Matriz Interactiva de Puntuaciones de Característica.
Soporta los 4 métodos oficiales:
1. Point Buy (Compra por Puntos de 27 pts con presupuesto en vivo y botones +/-)
2. Conjunto Estándar (15, 14, 13, 12, 10, 8 con dropdowns excluyentes)
3. Tiradas 4d6 (descartando el dado menor con tirador interactivo)
4. Manual / Entrada libre
Desglose transparente: Base + Bono Trasfondo/Raza = Puntuación Total ➔ Modificador.
"""
import random
import flet as ft
from typing import Dict, Callable, Optional, List
from ...core.point_buy import PointBuyCalculator
from ...core.rules import calc_modifier
from ..theme import (
    TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD, TTUI_GOLD_LIGHT,
    TTUI_PARCHMENT, TTUI_RUNIC_GREY, TTUI_CRIMSON, BG_INPUT, BG_CARD,
    BORDER_DIM, BORDER_GOLD, create_badge, create_gold_button
)

STAT_KEYS = ["FUE", "DES", "CON", "INT", "SAB", "CAR"]
STAT_LABELS = {
    "FUE": "Fuerza",
    "DES": "Destreza",
    "CON": "Constitución",
    "INT": "Inteligencia",
    "SAB": "Sabiduría",
    "CAR": "Carisma"
}
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]


class AbilityMatrix(ft.Container):
    def __init__(
        self,
        raw_scores: Optional[Dict[str, int]] = None,
        bg_plus2: str = "FUE",
        bg_plus1: str = "CON",
        mode: str = "point_buy",  # "point_buy", "standard", "dice", "manual"
        on_scores_changed: Optional[Callable[[Dict[str, int]], None]] = None
    ):
        self.mode = mode
        self.bg_plus2 = bg_plus2
        self.bg_plus1 = bg_plus1
        self.on_scores_changed = on_scores_changed

        if raw_scores:
            self.raw_scores = dict(raw_scores)
        else:
            if self.mode == "point_buy":
                self.raw_scores = PointBuyCalculator.get_initial_scores()
            else:
                self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}

        self.rolled_pool: List[int] = []

        self.main_column = ft.Column(spacing=10, expand=True)

        super().__init__(
            content=self.main_column,
            bgcolor=TTUI_SURFACE_CARD,
            border=ft.border.all(1, TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(8),
            padding=14,
            expand=True
        )
        self._build_ui()

    def set_background_bonuses(self, plus2: str, plus1: str):
        self.bg_plus2 = plus2
        self.bg_plus1 = plus1
        self._build_ui()
        if self.page:
            self.update()

    def _set_mode(self, new_mode: str):
        self.mode = new_mode
        if self.mode == "point_buy":
            self.raw_scores = PointBuyCalculator.get_initial_scores()
        elif self.mode == "standard":
            self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}
        elif self.mode == "dice":
            if not self.rolled_pool:
                self._roll_dice()
        self._build_ui()
        self._notify_change()
        if self.page:
            self.update()

    def _roll_dice(self, e=None):
        results = []
        for _ in range(6):
            d = [random.randint(1, 6) for _ in range(4)]
            d.sort()
            results.append(sum(d[1:]))
        results.sort(reverse=True)
        self.rolled_pool = results
        for i, s in enumerate(STAT_KEYS):
            self.raw_scores[s] = results[i]
        self._build_ui()
        self._notify_change()
        if self.page:
            self.update()

    def _notify_change(self):
        if self.on_scores_changed:
            self.on_scores_changed(self.raw_scores)

    def _build_ui(self):
        self.main_column.controls.clear()

        # Barra de cambio de modo
        mode_buttons = [
            ft.ElevatedButton(
                text="⚖️ Compra por Puntos (Point Buy)",
                bgcolor=TTUI_GOLD if self.mode == "point_buy" else BG_INPUT,
                color="#000000" if self.mode == "point_buy" else TTUI_GOLD_LIGHT,
                style=ft.ButtonStyle(
                    bgcolor=TTUI_GOLD if self.mode == "point_buy" else BG_INPUT,
                    color="#000000" if self.mode == "point_buy" else TTUI_GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if self.mode == "point_buy" else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e: self._set_mode("point_buy")
            ),
            ft.ElevatedButton(
                text="📊 Conjunto Estándar",
                bgcolor=TTUI_GOLD if self.mode == "standard" else BG_INPUT,
                color="#000000" if self.mode == "standard" else TTUI_GOLD_LIGHT,
                style=ft.ButtonStyle(
                    bgcolor=TTUI_GOLD if self.mode == "standard" else BG_INPUT,
                    color="#000000" if self.mode == "standard" else TTUI_GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if self.mode == "standard" else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e: self._set_mode("standard")
            ),
            ft.ElevatedButton(
                text="🎲 Tiradas 4d6",
                bgcolor=TTUI_GOLD if self.mode == "dice" else BG_INPUT,
                color="#000000" if self.mode == "dice" else TTUI_GOLD_LIGHT,
                style=ft.ButtonStyle(
                    bgcolor=TTUI_GOLD if self.mode == "dice" else BG_INPUT,
                    color="#000000" if self.mode == "dice" else TTUI_GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if self.mode == "dice" else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e: self._set_mode("dice")
            ),
            ft.ElevatedButton(
                text="✍️ Manual",
                bgcolor=TTUI_GOLD if self.mode == "manual" else BG_INPUT,
                color="#000000" if self.mode == "manual" else TTUI_GOLD_LIGHT,
                style=ft.ButtonStyle(
                    bgcolor=TTUI_GOLD if self.mode == "manual" else BG_INPUT,
                    color="#000000" if self.mode == "manual" else TTUI_GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if self.mode == "manual" else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e: self._set_mode("manual")
            ),
        ]
        self.main_column.controls.append(ft.Row(controls=mode_buttons, wrap=True, spacing=8))

        # Información y banner según el modo
        if self.mode == "point_buy":
            remaining = PointBuyCalculator.get_remaining_points(self.raw_scores)
            used = PointBuyCalculator.calculate_used_points(self.raw_scores)
            budget_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.SAVINGS_OUTLINED, color=TTUI_GOLD, size=20),
                            ft.Text(f"Presupuesto de Compra: {remaining} puntos restantes de 27 (Gastados: {used})", size=13, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                        ], spacing=8),
                        create_badge(f"{remaining} pts libres", bg_color=BG_INPUT, text_color=TTUI_GOLD if remaining >= 0 else TTUI_CRIMSON, border_color=BORDER_GOLD)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                bgcolor=BG_INPUT,
                border=ft.border.all(1, TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.symmetric(horizontal=12, vertical=8)
            )
            self.main_column.controls.append(budget_banner)

        elif self.mode == "dice":
            rolled_str = ", ".join(str(v) for v in self.rolled_pool)
            dice_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.CASINO, color=TTUI_GOLD, size=20),
                            ft.Text(f"Tiradas 4d6 obtenidas: [{rolled_str}]", size=13, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                        ], spacing=8),
                        ft.OutlinedButton(
                            text="🎲 Re-tirar Dados",
                            style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                            on_click=self._roll_dice
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER_GOLD),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.symmetric(horizontal=12, vertical=8)
            )
            self.main_column.controls.append(dice_banner)

        # Matriz de Características
        rows = []
        for stat in STAT_KEYS:
            base_score = self.raw_scores.get(stat, 8)
            bg_add = (2 if self.bg_plus2 == stat else (1 if self.bg_plus1 == stat else 0))
            final_score = base_score + bg_add
            mod = calc_modifier(final_score)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)

            # Control de puntuación base según modo
            if self.mode == "point_buy":
                can_dec = PointBuyCalculator.can_decrement(self.raw_scores, stat)
                can_inc = PointBuyCalculator.can_increment(self.raw_scores, stat)

                def on_dec(e, s=stat):
                    if PointBuyCalculator.decrement(self.raw_scores, s):
                        self._build_ui()
                        self._notify_change()
                        self.page.update()

                def on_inc(e, s=stat):
                    if PointBuyCalculator.increment(self.raw_scores, s):
                        self._build_ui()
                        self._notify_change()
                        self.page.update()

                score_selector = ft.Row(
                    controls=[
                        ft.IconButton(ft.Icons.REMOVE, icon_size=16, disabled=not can_dec, icon_color=TTUI_GOLD_LIGHT, on_click=on_dec),
                        ft.Container(
                            content=ft.Text(str(base_score), size=16, weight=ft.FontWeight.BOLD, color="#ffffff"),
                            alignment=ft.alignment.center,
                            width=36
                        ),
                        ft.IconButton(ft.Icons.ADD, icon_size=16, disabled=not can_inc, icon_color=TTUI_GOLD_LIGHT, on_click=on_inc),
                    ],
                    spacing=0,
                    alignment=ft.MainAxisAlignment.CENTER
                )

            elif self.mode == "standard":
                def on_std_change(e, s=stat):
                    try:
                        self.raw_scores[s] = int(e.control.value)
                        self._build_ui()
                        self._notify_change()
                        self.page.update()
                    except ValueError:
                        pass

                opts = [ft.dropdown.Option(str(v), str(v)) for v in STANDARD_ARRAY]
                score_selector = ft.Dropdown(
                    value=str(base_score),
                    options=opts,
                    width=90,
                    dense=True,
                    border_color=BORDER_DIM,
                    on_change=on_std_change
                )

            elif self.mode == "dice":
                def on_dice_change(e, s=stat):
                    try:
                        self.raw_scores[s] = int(e.control.value)
                        self._build_ui()
                        self._notify_change()
                        self.page.update()
                    except ValueError:
                        pass

                dice_opts = [ft.dropdown.Option(str(v), str(v)) for v in sorted(list(set(self.rolled_pool)), reverse=True)]
                score_selector = ft.Dropdown(
                    value=str(base_score),
                    options=dice_opts,
                    width=90,
                    dense=True,
                    border_color=BORDER_DIM,
                    on_change=on_dice_change
                )

            else:  # Manual
                def on_manual_change(e, s=stat):
                    try:
                        val = int(e.control.value or "8")
                        self.raw_scores[s] = max(1, min(30, val))
                        self._build_ui()
                        self._notify_change()
                        self.page.update()
                    except ValueError:
                        pass

                score_selector = ft.TextField(
                    value=str(base_score),
                    width=75,
                    height=38,
                    dense=True,
                    text_align=ft.TextAlign.CENTER,
                    border_color=BORDER_DIM,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=on_manual_change
                )

            # Tarjeta de la fila
            row_card = ft.Container(
                content=ft.Row(
                    controls=[
                        # Columna 1: Nombre y etiqueta
                        ft.Column(
                            controls=[
                                ft.Text(f"{stat} ({STAT_LABELS[stat]})", size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                                ft.Text(f"+{bg_add} por Trasfondo" if bg_add > 0 else "Sin bono", size=11, color=TTUI_GOLD if bg_add > 0 else TTUI_RUNIC_GREY)
                            ],
                            width=140,
                            spacing=1
                        ),
                        # Columna 2: Selector de puntuación base
                        score_selector,
                        # Columna 3: Conector
                        ft.Text("➔ Total:", size=12, color=TTUI_RUNIC_GREY),
                        # Columna 4: Puntuación Final
                        ft.Text(str(final_score), size=18, weight=ft.FontWeight.BOLD, color="#ffffff"),
                        # Columna 5: Modificador
                        create_badge(f"Mod {mod_str}", bg_color=BG_INPUT, text_color=TTUI_GOLD_LIGHT, border_color=BORDER_GOLD)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border=ft.border.all(1, TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(6)
            )
            rows.append(row_card)

        self.main_column.controls.append(ft.Column(controls=rows, spacing=6))
