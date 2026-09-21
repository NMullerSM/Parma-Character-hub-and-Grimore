"""
Componente SlotTracker (Contador Interactivo de Espacios de Conjuro Niveles 1 a 9)
"""
import flet as ft
from typing import Dict, Callable, Optional
from ...core.models import SpellSlotTier
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, COLOR_BLUE, COLOR_BLUE_DIM,
    GOLD_LIGHT, TEXT_MUTED
)


class SlotTracker(ft.Container):
    def __init__(
        self,
        spell_slots: Dict[str, SpellSlotTier],
        on_slot_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.spell_slots = spell_slots
        self.on_slot_change = on_slot_change
        self.bgcolor = BG_CARD
        self.border = ft.border.all(1, BORDER_DIM)
        self.border_radius = ft.border_radius.all(8)
        self.padding = 12

        self._build_ui()

    def _build_ui(self):
        tier_boxes = []

        for lvl_str in sorted(self.spell_slots.keys(), key=lambda k: int(k)):
            tier = self.spell_slots[lvl_str]
            if tier.total <= 0:
                continue

            pips = []
            for pip_idx in range(tier.total):
                is_active = pip_idx < tier.current
                pip_btn = ft.Container(
                    width=18,
                    height=18,
                    border_radius=ft.border_radius.all(4),
                    bgcolor=COLOR_BLUE if is_active else "transparent",
                    border=ft.border.all(1, COLOR_BLUE),
                    tooltip=f"Nivel {tier.level}: {'Disponible' if is_active else 'Gastado'}",
                    on_click=lambda e, t=tier, idx=pip_idx: self._toggle_pip(t, idx)
                )
                pips.append(pip_btn)

            box = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"NIVEL {tier.level}", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                        ft.Row(controls=pips, spacing=4),
                        ft.Text(f"{tier.current}/{tier.total}", size=10, color=GOLD_LIGHT),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4
                ),
                bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=8
            )
            tier_boxes.append(box)

        if not tier_boxes:
            self.content = ft.Text("No hay espacios de conjuro activos para esta clase.", size=12, color=TEXT_MUTED, italic=True)
        else:
            self.content = ft.Column(
                controls=[
                    ft.Text("✨ Espacios de Conjuro", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(controls=tier_boxes, wrap=True, spacing=8)
                ],
                spacing=8
            )

    def _toggle_pip(self, tier: SpellSlotTier, pip_idx: int):
        # Si se hace clic en un pip disponible, se gasta uno; si está vacío, se recupera
        if pip_idx < tier.current:
            tier.current = max(0, tier.current - 1)
        else:
            tier.current = min(tier.total, tier.current + 1)

        self._build_ui()
        if self.page:
            self.update()

        if self.on_slot_change:
            self.on_slot_change()

    def update_slots(self, spell_slots: Dict[str, SpellSlotTier]):
        self.spell_slots = spell_slots
        self._build_ui()
        if self.page:
            self.update()
