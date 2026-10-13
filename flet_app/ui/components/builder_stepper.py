"""
Componente BuilderStepper: Barra de Navegación Horizontal de 7 Fases.
Inspirado en el stepper de D&D Beyond con indicadores de fase,
estados completados y badges de alerta para elecciones pendientes.
"""
import flet as ft
from typing import Callable, Dict, List, Optional
from ..theme import (
    TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD, TTUI_GOLD_LIGHT,
    TTUI_PARCHMENT, TTUI_RUNIC_GREY, TTUI_CRIMSON, BG_INPUT, BORDER_DIM
)

BUILDER_STEPS = [
    {"index": 1, "label": "1. Reglas", "icon": ft.Icons.TUNE},
    {"index": 2, "label": "2. Especie", "icon": ft.Icons.FINGERPRINT},
    {"index": 3, "label": "3. Clase", "icon": ft.Icons.SHIELD},
    {"index": 4, "label": "4. Atributos", "icon": ft.Icons.BAR_CHART},
    {"index": 5, "label": "5. Trasfondo", "icon": ft.Icons.AUTO_STORIES},
    {"index": 6, "label": "6. Equipo", "icon": ft.Icons.BACKPACK},
    {"index": 7, "label": "7. Conjuros", "icon": ft.Icons.AUTO_AWESOME},
]

class BuilderStepper(ft.Container):
    def __init__(
        self,
        current_step: int = 1,
        on_step_change: Optional[Callable[[int], None]] = None,
        pending_choices: Optional[Dict[int, str]] = None
    ):
        self.current_step = current_step
        self.on_step_change = on_step_change
        self.pending_choices = pending_choices or {}
        self.step_buttons: List[ft.Control] = []

        self.row_container = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=6
        )

        super().__init__(
            content=self.row_container,
            bgcolor=TTUI_SURFACE_CARD,
            border=ft.border.all(1, TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(horizontal=8, vertical=6)
        )
        self._build_steps()

    def _build_steps(self):
        self.row_container.controls.clear()
        self.step_buttons.clear()

        for step in BUILDER_STEPS:
            idx = step["index"]
            is_active = (self.current_step == idx)
            is_past = (self.current_step > idx)
            pending_text = self.pending_choices.get(idx, "")

            # Color y estilo de la pastilla
            if is_active:
                bg = BG_INPUT
                border_color = TTUI_GOLD
                text_color = TTUI_GOLD_LIGHT
                icon_color = TTUI_GOLD
            elif is_past:
                bg = TTUI_SURFACE_CARD
                border_color = BORDER_DIM
                text_color = TTUI_PARCHMENT
                icon_color = "#22c55e"  # Checkmark verde de completado
            else:
                bg = TTUI_SURFACE_CARD
                border_color = BORDER_DIM
                text_color = TTUI_RUNIC_GREY
                icon_color = TTUI_RUNIC_GREY

            btn_content = [
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if (is_past and not pending_text) else step["icon"],
                    size=15,
                    color=icon_color
                ),
                ft.Text(step["label"], size=12, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL, color=text_color)
            ]

            if pending_text and not is_active:
                # Badge de elecciones pendientes
                btn_content.append(
                    ft.Container(
                        content=ft.Text("!", size=10, weight=ft.FontWeight.BOLD, color="#ffffff"),
                        bgcolor=TTUI_CRIMSON,
                        border_radius=ft.border_radius.all(8),
                        padding=ft.padding.symmetric(horizontal=5, vertical=1)
                    )
                )

            item = ft.Container(
                content=ft.Row(controls=btn_content, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=bg,
                border=ft.border.all(1.5 if is_active else 1, border_color),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                on_click=lambda e, target_idx=idx: self._on_step_click(target_idx),
                tooltip=f"Ir a {step['label']}"
            )
            self.step_buttons.append(item)
            self.row_container.controls.append(item)

    def _on_step_click(self, step_idx: int):
        self.set_current_step(step_idx)
        if self.on_step_change:
            self.on_step_change(step_idx)

    def set_current_step(self, step_idx: int):
        self.current_step = step_idx
        self._build_steps()
        if self.page:
            self.update()

    def set_pending_choices(self, choices: Dict[int, str]):
        self.pending_choices = choices
        self._build_steps()
        if self.page:
            self.update()
