"""
Vista de Rasgos, Poderes & Dotes (Seguimiento de usos por descanso)
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet, CharacterFeature
from ...core.okf_engine import OkfEngine
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, COLOR_AMBER, COLOR_RED, COLOR_GREEN,
    create_card_container, create_badge, create_gold_button
)


class PowersView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        okf_engine: Optional[OkfEngine] = None,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.okf = okf_engine
        self.on_state_change = on_state_change
        self.expand = True

        self._build_ui()

    def _build_ui(self):
        feature_cards = []

        for feat in self.char.features:
            # Pips de usos si tiene usos limitados
            pips = []
            if feat.uses_max > 0:
                for pip_idx in range(feat.uses_max):
                    is_active = pip_idx < feat.uses_current
                    pip_btn = ft.Container(
                        width=18,
                        height=18,
                        border_radius=ft.border_radius.all(4),
                        bgcolor=GOLD_PRIMARY if is_active else "transparent",
                        border=ft.border.all(1, GOLD_PRIMARY),
                        tooltip=f"Uso {pip_idx + 1}: {'Disponible' if is_active else 'Gastado'}",
                        on_click=lambda e, f=feat, idx=pip_idx: self._toggle_use(f, idx)
                    )
                    pips.append(pip_btn)

            recharge_badge = create_badge(
                f"Recarga: {feat.recharge}",
                bg_color=BG_INPUT,
                text_color=COLOR_AMBER,
                border_color=COLOR_AMBER
            )
            source_badge = create_badge(
                feat.source,
                bg_color=BG_INPUT,
                text_color=TEXT_MUTED,
                border_color=BORDER_DIM
            )

            card_content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(feat.name, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.Row(
                                controls=[
                                    source_badge,
                                    recharge_badge,
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_color=COLOR_RED,
                                        icon_size=18,
                                        tooltip="Eliminar rasgo",
                                        on_click=lambda e, f=feat: self._remove_feat(f)
                                    )
                                ],
                                spacing=6
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(f"Usos ({feat.uses_current}/{feat.uses_max}):", size=12, color=TEXT_MUTED),
                            ft.Row(controls=pips, spacing=4)
                        ],
                        spacing=8
                    ) if feat.uses_max > 0 else ft.Container(),
                    ft.Text(feat.description, size=12, color="#e5e7eb", selectable=True),
                ],
                spacing=8
            )

            feature_cards.append(create_card_container(content=card_content))

        btn_add = create_gold_button(
            text="+ Añadir Dote (OKF)",
            icon=ft.Icons.ADD,
            on_click=self._open_feat_picker,
            tooltip="Explorar y añadir dotes oficiales del Manual 2024"
        )

        header_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("🌟 Rasgos de Clase, Linaje & Dotes", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ft.Text("Seguimiento interactivo de usos por descanso según los manuales oficiales.", size=12, color=TEXT_MUTED),
                    ],
                    spacing=2
                ),
                btn_add
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            wrap=True
        )

        self.content = ft.ListView(
            controls=[
                header_row,
                ft.Divider(color=BORDER_DIM, height=1),
                *feature_cards
            ],
            spacing=10,
            expand=True
        )

    def _toggle_use(self, feat: CharacterFeature, pip_idx: int):
        if pip_idx < feat.uses_current:
            feat.uses_current = max(0, feat.uses_current - 1)
        else:
            feat.uses_current = min(feat.uses_max, feat.uses_current + 1)

        self._build_ui()
        if self.page:
            self.update()
        if self.on_state_change:
            self.on_state_change()

    def _remove_feat(self, feat: CharacterFeature):
        if feat in self.char.features:
            self.char.features.remove(feat)
            self._build_ui()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Rasgo '{feat.name}' eliminado."))
                self.page.snack_bar.open = True
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

    def _open_feat_picker(self, e):
        if not self.okf:
            return

        search_field = ft.TextField(
            hint_text="Buscar dote oficial (74 disponibles)...",
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            color="#f0f2f5",
            expand=True,
            height=40,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6)
        )
        results_col = ft.ListView(height=320, spacing=8)

        def refresh_feats(q=""):
            results_col.controls.clear()
            feats = self.okf.search_entities(query=q, tipo="dote", limit=30)
            if not feats:
                results_col.controls.append(
                    ft.Container(
                        content=ft.Text("No se encontraron dotes.", color=TEXT_MUTED, italic=True),
                        padding=12
                    )
                )
            for f in feats:
                fname = f.get("nombre", "")
                fcat = f.get("categoria", "General")
                fpath = f.get("path")
                full_f = self.okf.read_entity_file(fpath) if fpath else None
                desc = full_f.get("body_markdown", "") if full_f else ""

                row = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(fname, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                    ft.Text(f"Categoría: {fcat} • PHB 2024", size=11, color=TEXT_MUTED),
                                ],
                                expand=True,
                                spacing=2
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
                                on_click=lambda ev, n=fname, d=desc: select_feat(n, d)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER_DIM),
                    border_radius=ft.border_radius.all(6),
                    padding=8
                )
                results_col.controls.append(row)
            if self.page:
                self.page.update()

        def select_feat(name: str, description: str):
            dialog.open = False
            if dialog in self.page.overlay:
                self.page.overlay.remove(dialog)
            new_f = CharacterFeature(
                name=name,
                source="PHB 2024",
                description=description,
                recharge="Pasivo",
                uses_max=0,
                uses_current=0
            )
            self.char.features.append(new_f)
            self._build_ui()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Dote '{name}' añadida con éxito."))
                self.page.snack_bar.open = True
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

        search_field.on_change = lambda ev: refresh_feats(ev.control.value)

        dialog = ft.AlertDialog(
            title=ft.Text("🌟 Catálogo de Dotes OKF (PHB 2024)", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Selecciona una de las 74 dotes oficiales del Manual 2024.", size=12, color=TEXT_MUTED),
                        search_field,
                        ft.Divider(color=BORDER_DIM, height=1),
                        results_col
                    ],
                    spacing=8
                ),
                width=620,
                height=420
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=GOLD_LIGHT), on_click=lambda ev: close_d())
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        def close_d():
            dialog.open = False
            if dialog in self.page.overlay:
                self.page.overlay.remove(dialog)
            self.page.update()

        refresh_feats()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._build_ui()
        if self.page:
            self.page.update()
