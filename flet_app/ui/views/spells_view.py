"""
Vista de Conjuros & Magia (Catálogo OKF, Espacios y Hechizos por Nivel)
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet, SpellItem
from ...core.rules import calc_modifier, calc_proficiency_bonus
from ...core.okf_engine import OkfEngine
from ..theme import (
    BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_PURPLE, COLOR_AMBER,
    COLOR_RED, create_card_container, create_badge
)
from ..components.slot_tracker import SlotTracker
from ..components.spell_picker import SpellPickerDialog


class SpellsView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        okf_engine: OkfEngine,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.okf = okf_engine
        self.on_state_change = on_state_change
        self.filter_level = "all"
        self.expand = True

        self._build_ui()

    def _build_ui(self):
        # 1. Barra de Estadísticas Mágicas
        prof = calc_proficiency_bonus(self.char.level)
        cha_mod = calc_modifier(self.char.abilities.get("CAR", 10))
        save_dc = 8 + prof + cha_mod
        atk_bonus = f"+{prof + cha_mod}" if (prof + cha_mod) >= 0 else str(prof + cha_mod)

        stat_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self._create_magic_stat("APTITUD MÁGICA", "Carisma"),
                    self._create_magic_stat("CD SALVACIÓN CONJUROS", str(save_dc)),
                    self._create_magic_stat("BONIFICADOR ATAQUE", atk_bonus),
                    self._create_magic_stat("COMPETENCIA", f"+{prof}"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                wrap=True,
                spacing=10
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        # 2. Contador de Espacios de Conjuro
        self.slot_tracker = SlotTracker(
            spell_slots=self.char.spell_slots,
            on_slot_change=self.on_state_change
        )

        # 3. Barra de Acciones y Filtros
        btn_add_okf = ft.ElevatedButton(
            text="✨ + Añadir Conjuro (Catálogo OKF)",
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#111",
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._open_okf_picker
        )

        filter_dropdown = ft.Dropdown(
            label="Filtrar Nivel",
            width=160,
            value=self.filter_level,
            border_color=BORDER_DIM,
            options=[
                ft.dropdown.Option("all", "Todos"),
                ft.dropdown.Option("0", "Trucos (Niv 0)"),
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
            on_change=self._on_filter_change
        )

        action_bar = ft.Row(
            controls=[btn_add_okf, filter_dropdown],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 4. Lista de Conjuros
        self.spells_column = ft.Column(spacing=10)
        self._populate_spells()

        self.content = ft.ListView(
            controls=[
                stat_bar,
                self.slot_tracker,
                action_bar,
                self.spells_column
            ],
            spacing=12,
            expand=True
        )

    def _create_magic_stat(self, label: str, val: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=9, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                    ft.Text(val, size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            ),
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(6),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            alignment=ft.alignment.center
        )

    def _populate_spells(self):
        self.spells_column.controls.clear()

        # Agrupar por nivel
        spells_by_lvl = {}
        for sp in self.char.spells:
            if self.filter_level != "all" and str(sp.level) != self.filter_level:
                continue
            spells_by_lvl.setdefault(sp.level, []).append(sp)

        if not spells_by_lvl:
            self.spells_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay conjuros aprendidos que coincidan con el filtro. Haz clic en '+ Añadir Conjuro' para explorar el catálogo OKF.",
                        size=13,
                        color=TEXT_MUTED,
                        italic=True
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            return

        for lvl in sorted(spells_by_lvl.keys()):
            lvl_title = "Trucos (Nivel 0)" if lvl == 0 else f"Conjuros de Nivel {lvl}"
            cards_list = []

            for sp in spells_by_lvl[lvl]:
                pills = [
                    create_badge(f"Tiempo: {sp.casting_time}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                    create_badge(f"Alcance: {sp.range}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                    create_badge(f"Duración: {sp.duration}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                    create_badge(f"Comp: {sp.components}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                ]
                if sp.concentration:
                    pills.append(create_badge("Concentración", bg_color=BG_INPUT, text_color=COLOR_AMBER, border_color=COLOR_AMBER))
                if sp.ritual:
                    pills.append(create_badge("Ritual", bg_color=BG_INPUT, text_color=COLOR_PURPLE, border_color=COLOR_PURPLE))
                if sp.classes:
                    for cls in sp.classes:
                        pills.append(create_badge(cls, bg_color="#1e180a", text_color=GOLD_LIGHT, border_color="#5a451b"))

                # Botón para lanzar conjuro
                btn_cast = ft.ElevatedButton(
                    text="🎲 Lanzar",
                    icon=ft.Icons.AUTO_AWESOME,
                    style=ft.ButtonStyle(
                        bgcolor=BG_INPUT,
                        color=GOLD_LIGHT,
                        side=ft.BorderSide(1, BORDER_GOLD),
                        shape=ft.RoundedRectangleBorder(radius=4)
                    ),
                    on_click=lambda e, s=sp: self._cast_spell(s)
                )

                card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text(sp.name, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                                    ft.Text(f"({sp.name_en})" if sp.name_en else "", size=11, color=TEXT_MUTED),
                                                ],
                                                spacing=6
                                            ),
                                            ft.Text(f"{sp.school} • {sp.source}", size=11, color=TEXT_MUTED, italic=True),
                                        ],
                                        spacing=2
                                    ),
                                    ft.Row(
                                        controls=[
                                            btn_cast,
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color=COLOR_RED,
                                                icon_size=18,
                                                tooltip="Eliminar de la ficha",
                                                on_click=lambda e, s=sp: self._remove_spell(s)
                                            )
                                        ],
                                        spacing=4
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Row(controls=pills, wrap=True, spacing=6),
                            ft.Text(sp.description, size=12, color="#e5e7eb", selectable=True) if sp.description else ft.Container()
                        ],
                        spacing=8
                    ),
                    bgcolor=BG_CARD,
                    border=ft.border.all(1, BORDER_DIM),
                    border_radius=ft.border_radius.all(8),
                    padding=12
                )
                cards_list.append(card)

            section = ft.Column(
                controls=[
                    ft.Text(lvl_title, size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    *cards_list
                ],
                spacing=8
            )
            self.spells_column.controls.append(section)

    def _open_okf_picker(self, e):
        dialog = SpellPickerDialog(
            page=self.page,
            okf_engine=self.okf,
            on_spell_selected=self._on_spell_added
        )
        dialog.show()

    def _on_spell_added(self, spell: SpellItem):
        # Evitar duplicados
        if any(s.name.lower() == spell.name.lower() for s in self.char.spells):
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"El conjuro '{spell.name}' ya está en tu hoja."))
                self.page.snack_bar.open = True
                self.page.update()
            return

        self.char.spells.append(spell)
        self._populate_spells()
        if self.page:
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def _remove_spell(self, spell: SpellItem):
        if spell in self.char.spells:
            self.char.spells.remove(spell)
            self._populate_spells()
            if self.page:
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

    def _cast_spell(self, spell: SpellItem):
        """Lanzamiento de conjuro con descuento automático de espacios."""
        if spell.level == 0:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"🪄 ¡Has lanzado el truco '{spell.name}'! (Sin coste de espacio)"))
                self.page.snack_bar.open = True
                self.page.update()
            return

        lvl_str = str(spell.level)
        tier = self.char.spell_slots.get(lvl_str)
        if tier and tier.max > 0:
            if tier.used < tier.max:
                tier.used += 1
                self.slot_tracker.update_data(self.char.spell_slots)
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"✨ ¡Has lanzado '{spell.name}'! (Espacio Nivel {spell.level} gastado: {tier.used}/{tier.max})")
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                if self.on_state_change:
                    self.on_state_change()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"⚠️ ¡No te quedan espacios de conjuro de Nivel {spell.level}!")
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        else:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"🪄 ¡Has lanzado '{spell.name}'!"))
                self.page.snack_bar.open = True
                self.page.update()

    def _on_filter_change(self, e):
        self.filter_level = e.control.value
        self._populate_spells()
        if self.page:
            self.page.update()

    def update_data(self, new_char: CharacterSheet):
        self.char = new_char
        self.slot_tracker.update_data(self.char.spell_slots)
        self._populate_spells()
        if self.page:
            self.page.update()
