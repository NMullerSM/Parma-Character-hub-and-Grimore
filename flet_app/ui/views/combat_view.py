"""
Vista de Combate & Estado (HP, Salvaciones de Muerte, Acciones de Armas y Espacios de Conjuro)
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet, WeaponAction
from ...core.rules import DND_CONDITIONS, perform_short_rest
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, COLOR_RED, COLOR_GREEN, COLOR_BLUE,
    create_card_container
)
from ..components.hero_header import HeroHeader
from ..components.slot_tracker import SlotTracker


class CombatView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        on_roll_request: Optional[Callable[[int, int, str], None]] = None,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.on_roll_request = on_roll_request
        self.on_state_change = on_state_change
        self.expand = True

        self._build_ui()

    def _build_ui(self):
        # Cabecera Operativa de Combate (Nombre, CA, Iniciativa, Velocidad, Competencia e Inspiración)
        self.hero_header = HeroHeader(char=self.char, on_change=self.on_state_change)

        # 1. Tarjeta de Salud y Puntos de Golpe
        hp_pct = max(0.0, min(1.0, self.char.hp_current / max(1, self.char.hp_max)))
        bar_color = COLOR_GREEN if hp_pct > 0.5 else (GOLD_PRIMARY if hp_pct > 0.25 else COLOR_RED)

        self.hp_text = ft.Text(
            f"{self.char.hp_current} / {self.char.hp_max} PG",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=GOLD_LIGHT
        )
        self.temp_hp_text = ft.Text(
            f"+{self.char.hp_temp} Temp" if self.char.hp_temp > 0 else "0 Temp",
            size=13,
            color=TEXT_MUTED
        )
        self.hp_bar = ft.ProgressBar(value=hp_pct, color=bar_color, bgcolor=BG_INPUT, height=10)

        # Controles de Curar / Dañar
        self.delta_input = ft.TextField(
            value="5",
            width=70,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.padding.all(4),
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff",
            cursor_color=GOLD_LIGHT,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        btn_heal = ft.ElevatedButton(
            text="Curar (+)",
            style=ft.ButtonStyle(bgcolor=COLOR_GREEN, color="#ffffff"),
            on_click=self._on_heal_click
        )
        btn_dmg = ft.ElevatedButton(
            text="Dañar (-)",
            style=ft.ButtonStyle(bgcolor=COLOR_RED, color="#ffffff"),
            on_click=self._on_damage_click
        )
        btn_temp = ft.OutlinedButton(
            text="Añadir Temp",
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._on_add_temp_click
        )

        # Fila interactiva de Dados de Golpe
        hd_curr = getattr(self.char, "hit_dice_current", self.char.level)
        hd_max = getattr(self.char, "hit_dice_max", self.char.level)
        hd_faces = getattr(self.char, "hit_dice_faces", 8)

        self.hit_dice_text = ft.Text(
            f"{hd_curr} / {hd_max} (d{hd_faces})",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=GOLD_LIGHT
        )

        btn_spend_hd = ft.OutlinedButton(
            text=f"Gastar 1d{hd_faces}",
            icon=ft.Icons.CASINO,
            style=ft.ButtonStyle(
                color=GOLD_LIGHT if hd_curr > 0 else TEXT_MUTED,
                side=ft.BorderSide(1, BORDER_GOLD if hd_curr > 0 else BORDER_DIM),
                padding=ft.padding.symmetric(horizontal=8, vertical=4)
            ),
            on_click=self._on_spend_hit_die,
            tooltip=f"Gasta 1 dado de golpe (1d{hd_faces} + CON) para recuperar salud",
            disabled=(hd_curr <= 0)
        )

        hit_dice_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CASINO, size=15, color=GOLD_PRIMARY),
                            ft.Text("Dados de Golpe:", size=11, color=TEXT_MUTED),
                            self.hit_dice_text,
                        ],
                        spacing=4
                    ),
                    btn_spend_hd
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=BG_INPUT,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.border_radius.all(6),
            margin=ft.margin.only(top=4)
        )

        health_card = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("❤️ Salud & Puntos de Golpe", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            self.temp_hp_text
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    self.hp_text,
                    self.hp_bar,
                    ft.Row(
                        controls=[self.delta_input, btn_heal, btn_dmg, btn_temp],
                        wrap=True,
                        spacing=8
                    ),
                    ft.Divider(color=BORDER_DIM, height=1),
                    hit_dice_row
                ],
                spacing=8
            )
        )

        # 2. Salvaciones Contra la Muerte
        self.death_successes_row = self._create_death_save_boxes(
            count=getattr(self.char, "death_save_successes", getattr(self.char, "death_saves_success", 0)),
            active_color=COLOR_GREEN,
            label="Éxitos (3 = Estable)",
            on_toggle=lambda idx: self._toggle_death_save("success", idx)
        )
        self.death_failures_row = self._create_death_save_boxes(
            count=getattr(self.char, "death_save_failures", getattr(self.char, "death_saves_failure", 0)),
            active_color=COLOR_RED,
            label="Fallos (3 = Muerte)",
            on_toggle=lambda idx: self._toggle_death_save("failure", idx)
        )

        btn_roll_death_save = ft.OutlinedButton(
            text="Tirar Salvación Muerte",
            icon=ft.Icons.CASINO,
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._on_roll_death_save
        )

        death_saves_card = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("💀 Salvaciones Contra la Muerte", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            btn_roll_death_save
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True
                    ),
                    self.death_successes_row,
                    self.death_failures_row
                ],
                spacing=8
            )
        )

        # 3. Acciones de Armas y Ataques
        weapon_rows = []
        for wpn in self.char.weapons:
            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(wpn.name, size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                ft.Text(
                                    f"Daño: {wpn.damage} ({wpn.damage_type}) • {wpn.notes}" if wpn.notes else f"Daño: {wpn.damage} ({wpn.damage_type})",
                                    size=11,
                                    color=TEXT_MUTED
                                )
                            ],
                            expand=True,
                            spacing=2
                        ),
                        ft.ElevatedButton(
                            text=f"Ataque {wpn.attack_bonus}",
                            color="#000000",
                            bgcolor=GOLD_PRIMARY,
                            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                            on_click=lambda e, w=wpn: self._roll_attack(w)
                        ),
                        ft.OutlinedButton(
                            text=f"Daño",
                            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                            on_click=lambda e, w=wpn: self._roll_damage(w)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=COLOR_RED,
                            icon_size=18,
                            tooltip="Eliminar arma",
                            on_click=lambda e, w=wpn: self._remove_weapon(w)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=10
            )
            weapon_rows.append(row)

        weapons_card = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("⚔️ Armas & Ataques de Combate", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.OutlinedButton(
                                text="+ Añadir Arma",
                                icon=ft.Icons.ADD,
                                style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
                                on_click=self._open_add_weapon_dialog
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Column(controls=weapon_rows, spacing=8)
                ],
                spacing=10
            )
        )

        # 3. Gestor de Condiciones de Combate
        condition_chips = []
        active_conditions = set(getattr(self.char, "conditions", []))
        for cond in DND_CONDITIONS:
            cname = cond["name"]
            is_active = cname in active_conditions
            ccolor = cond.get("color", GOLD_PRIMARY)
            chip = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK if is_active else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            size=12,
                            color="#ffffff" if is_active else TEXT_MUTED
                        ),
                        ft.Text(
                            cname,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                            color="#ffffff" if is_active else TEXT_MUTED
                        )
                    ],
                    spacing=4
                ),
                bgcolor=ccolor if is_active else BG_INPUT,
                border=ft.border.all(1, ccolor if is_active else BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                tooltip=cond["description"],
                on_click=lambda e, name=cname: self._toggle_condition(name)
            )
            condition_chips.append(chip)

        conditions_card = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("⚡ Condiciones & Estados", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.Text(f"{len(active_conditions)} activas" if active_conditions else "Sin estados activos", size=11, color=TEXT_MUTED)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=condition_chips,
                        wrap=True,
                        spacing=6
                    )
                ],
                spacing=8
            )
        )

        # 4. Contador de Espacios de Conjuro
        self.slot_tracker = SlotTracker(
            spell_slots=self.char.spell_slots,
            on_slot_change=self.on_state_change
        )

        self.content = ft.ListView(
            controls=[
                self.hero_header,
                ft.ResponsiveRow(
                    controls=[
                        ft.Column(controls=[health_card, death_saves_card], col={"sm": 12, "md": 6}),
                        ft.Column(controls=[conditions_card, self.slot_tracker], col={"sm": 12, "md": 6})
                    ],
                    spacing=12
                ),
                weapons_card
            ],
            spacing=12,
            expand=True
        )

    def _get_delta(self) -> int:
        try:
            return max(1, int(self.delta_input.value))
        except ValueError:
            return 1

    def _on_heal_click(self, e):
        delta = self._get_delta()
        self.char.hp_current = min(self.char.hp_max, self.char.hp_current + delta)
        self._update_health_display()

    def _on_damage_click(self, e):
        delta = self._get_delta()
        if self.char.hp_temp > 0:
            if delta <= self.char.hp_temp:
                self.char.hp_temp -= delta
                delta = 0
            else:
                delta -= self.char.hp_temp
                self.char.hp_temp = 0

        self.char.hp_current = max(0, self.char.hp_current - delta)
        self._update_health_display()

    def _on_add_temp_click(self, e):
        delta = self._get_delta()
        self.char.hp_temp = delta
        self._update_health_display()

    def _create_death_save_boxes(self, count: int, active_color: str, label: str, on_toggle) -> ft.Row:
        boxes = []
        for i in range(3):
            is_active = i < count
            box = ft.Container(
                width=24,
                height=24,
                border_radius=ft.border_radius.all(4),
                bgcolor=active_color if is_active else "transparent",
                border=ft.border.all(2, active_color),
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.CHECK, size=16, color="#ffffff") if is_active else None,
                on_click=lambda e, idx=i: on_toggle(idx)
            )
            boxes.append(box)

        return ft.Row(
            controls=[
                ft.Text(label, size=12, color=TEXT_MUTED, width=130),
                *boxes
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _toggle_death_save(self, save_type: str, idx: int):
        field_name = "death_saves_success" if save_type == "success" else "death_saves_failure"
        curr = getattr(self.char, field_name, 0)
        new_val = idx + 1 if idx >= curr else idx
        setattr(self.char, field_name, new_val)
        self._build_ui()
        if self.page:
            self.update()
        if self.on_state_change:
            self.on_state_change()

    def _on_roll_death_save(self, e):
        if self.on_roll_request:
            self.on_roll_request(20, 0, "Salvación Contra la Muerte (DC 10)")

    def _remove_weapon(self, wpn: WeaponAction):
        if wpn in self.char.weapons:
            self.char.weapons.remove(wpn)
            self._build_ui()
            if self.page:
                self.update()
            if self.on_state_change:
                self.on_state_change()

    def _open_add_weapon_dialog(self, e):
        name_input = ft.TextField(label="Nombre del Arma / Ataque", value="Espada Corta", border_color=BORDER_DIM, color="#ffffff")
        atk_input = ft.TextField(label="Bono de Ataque", value="+5", width=120, border_color=BORDER_DIM, color="#ffffff")
        dmg_input = ft.TextField(label="Daño (ej: 1d6+3)", value="1d6+3", width=140, border_color=BORDER_DIM, color="#ffffff")
        type_input = ft.TextField(label="Tipo de Daño", value="perforante", width=160, border_color=BORDER_DIM, color="#ffffff")
        notes_input = ft.TextField(label="Propiedades / Notas", value="Sutil, ligera", border_color=BORDER_DIM, color="#ffffff")

        def save_weapon(ev):
            if self.page:
                self.page.close(dialog)
            new_wpn = WeaponAction(
                name=name_input.value or "Ataque",
                attack_bonus=atk_input.value or "+0",
                damage=dmg_input.value or "1d4",
                damage_type=type_input.value or "contundente",
                notes=notes_input.value or ""
            )
            self.char.weapons.append(new_wpn)
            self._build_ui()
            if self.page:
                self.update()
            if self.on_state_change:
                self.on_state_change()

        def close_d(ev):
            if self.page:
                self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("⚔️ Añadir Arma o Acción de Ataque", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=[name_input, ft.Row([atk_input, dmg_input, type_input], spacing=8), notes_input],
                    spacing=10
                ),
                width=500,
                height=240
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=close_d),
                ft.ElevatedButton(
                    "Guardar Arma",
                    color="#000000",
                    bgcolor=GOLD_PRIMARY,
                    style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                    on_click=save_weapon
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if self.page:
            self.page.open(dialog)

    def _update_health_display(self):
        hp_pct = max(0.0, min(1.0, self.char.hp_current / max(1, self.char.hp_max)))
        self.hp_text.value = f"{self.char.hp_current} / {self.char.hp_max} PG"
        self.temp_hp_text.value = f"+{self.char.hp_temp} Temp" if self.char.hp_temp > 0 else "0 Temp"
        self.hp_bar.value = hp_pct
        self.hp_bar.color = COLOR_GREEN if hp_pct > 0.5 else (GOLD_PRIMARY if hp_pct > 0.25 else COLOR_RED)
        if self.page:
            self.update()
        if self.on_state_change:
            self.on_state_change()

    def _roll_attack(self, wpn: WeaponAction):
        if not self.on_roll_request:
            return
        mod = 0
        try:
            mod = int(wpn.attack_bonus.replace("+", ""))
        except ValueError:
            pass
        self.on_roll_request(20, mod, f"Ataque con {wpn.name}")

    def _roll_damage(self, wpn: WeaponAction):
        if not self.on_roll_request:
            return
        sides = 8
        mod = 0
        import re
        m = re.search(r"(\d+)?d(\d+)(?:\+(\d+))?", wpn.damage)
        if m:
            sides = int(m.group(2))
            mod = int(m.group(3)) if m.group(3) else 0
        self.on_roll_request(sides, mod, f"Daño de {wpn.name}")

    def _toggle_condition(self, cond_name: str):
        if not hasattr(self.char, "conditions") or not isinstance(self.char.conditions, list):
            self.char.conditions = []
        if cond_name in self.char.conditions:
            self.char.conditions.remove(cond_name)
        else:
            self.char.conditions.append(cond_name)
        self._build_ui()
        if self.page:
            self.update()
        if self.on_state_change:
            self.on_state_change()

    def _on_spend_hit_die(self, e):
        char, msg = perform_short_rest(self.char, hit_dice_spent=1)
        self._build_ui()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.update()
        if self.on_state_change:
            self.on_state_change()

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._build_ui()
        if self.page:
            self.update()

    def attach_file_picker(self, picker: ft.FilePicker):
        self.hero_header.attach_file_picker(picker)

