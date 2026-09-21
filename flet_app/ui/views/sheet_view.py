"""
Vista de Hoja Clásica (Atributos, Salvaciones, Habilidades, Percepción Pasiva y Competencias)
"""
import flet as ft
from typing import Callable, Optional
from ...core.models import CharacterSheet
from ...core.rules import (
    SKILLS_MAP, calc_modifier, calc_proficiency_bonus,
    get_skill_modifier, get_saving_throw_modifier
)
from ..theme import (
    BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, create_card_container
)


class SheetView(ft.Container):
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
        # 1. Columna de Atributos & Salvaciones
        ability_cards = []
        for stat_name in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            score = self.char.abilities.get(stat_name, 10)
            mod = calc_modifier(score)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)

            is_save_prof = stat_name in self.char.saving_throw_profs
            save_mod = get_saving_throw_modifier(self.char, stat_name)
            save_str = f"+{save_mod}" if save_mod >= 0 else str(save_mod)

            card = ft.Container(
                content=ft.Row(
                    controls=[
                        # Caja de Atributo
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(stat_name, size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                    ft.Text(mod_str, size=20, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                    ft.Text(f"Puntuación: {score}", size=10, color=TEXT_MUTED),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2
                            ),
                            bgcolor=BG_INPUT,
                            border=ft.border.all(1, BORDER_DIM),
                            border_radius=ft.border_radius.all(6),
                            padding=8,
                            width=95
                        ),
                        # Tirada de Salvación
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CHECK_CIRCLE if is_save_prof else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                            size=16,
                                            color=GOLD_PRIMARY if is_save_prof else TEXT_MUTED
                                        ),
                                        ft.Text(f"Salvación: {save_str}", size=13, weight=ft.FontWeight.BOLD, color="#fff")
                                    ],
                                    spacing=4
                                ),
                                ft.TextButton(
                                    text="Tirar Salvación",
                                    icon=ft.Icons.CASINO,
                                    style=ft.ButtonStyle(color=GOLD_LIGHT),
                                    on_click=lambda e, s=stat_name, m=save_mod: self._roll_save(s, m)
                                )
                            ],
                            spacing=2,
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=BG_CARD,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=8
            )
            ability_cards.append(card)

        col_abilities = ft.Column(
            controls=[
                ft.Text("🛡️ Puntuaciones & Salvaciones", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                *ability_cards
            ],
            spacing=8
        )

        # 2. Columna de Habilidades (18 skills)
        skill_rows = []
        for skill_name, stat_assoc in sorted(SKILLS_MAP.items(), key=lambda x: x[0]):
            prof_type = self.char.skills.get(skill_name, "none")
            bonus = get_skill_modifier(self.char, skill_name)
            bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)

            dot_color = TEXT_MUTED
            dot_icon = ft.Icons.CIRCLE_OUTLINED
            if prof_type == "expertise":
                dot_color = GOLD_PRIMARY
                dot_icon = ft.Icons.STAR
            elif prof_type == "proficient":
                dot_color = COLOR_BLUE
                dot_icon = ft.Icons.CHECK_CIRCLE

            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(dot_icon, size=15, color=dot_color),
                        ft.Text(skill_name, size=12, color="#fff", expand=True),
                        ft.Text(f"({stat_assoc})", size=10, color=TEXT_MUTED),
                        ft.Text(bonus_str, size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ft.IconButton(
                            icon=ft.Icons.CASINO,
                            icon_size=16,
                            icon_color=GOLD_LIGHT,
                            tooltip=f"Tirar {skill_name}",
                            on_click=lambda e, sk=skill_name, b=bonus: self._roll_skill(sk, b)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=ft.border_radius.all(4)
            )
            skill_rows.append(row)

        col_skills = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Text("📜 Habilidades (Competencias)", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Column(controls=skill_rows, spacing=2)
                ],
                spacing=8
            )
        )

        # 3. Columna de Sentidos, Idiomas y Otras Competencias
        wis_mod = calc_modifier(self.char.abilities.get("SAB", 10))
        perc_prof = self.char.skills.get("Percepción", "none")
        prof_bonus = calc_proficiency_bonus(self.char.level)
        passive_perc = 10 + wis_mod + (prof_bonus * 2 if perc_prof == "expertise" else (prof_bonus if perc_prof == "proficient" else 0))

        col_senses = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Text("👁️ Sentidos & Pasivas", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Percepción Pasiva (Sabiduría):", size=13, color=TEXT_MUTED),
                                ft.Text(str(passive_perc), size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        bgcolor=BG_INPUT,
                        padding=8,
                        border_radius=ft.border_radius.all(6)
                    ),
                    ft.Text("Visión en la Oscuridad Superior (Drow 36m)", size=12, color="#fff"),
                    ft.Divider(color=BORDER_DIM, height=1),
                    ft.Text("🗣️ Idiomas", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text(self.char.languages or "Común, Élfico", size=12, color="#fff"),
                    ft.Divider(color=BORDER_DIM, height=1),
                    ft.Text("🛡️ Otras Competencias", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text(self.char.proficiencies_extra or "Armaduras ligeras, armas sencillas, ballesta de mano, estoque.", size=12, color=TEXT_MUTED),
                ],
                spacing=10
            )
        )

        self.content = ft.ListView(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        ft.Column(controls=[col_abilities], col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Column(controls=[col_skills], col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Column(controls=[col_senses], col={"sm": 12, "md": 12, "lg": 4}),
                    ],
                    spacing=12
                )
            ],
            expand=True
        )

    def _roll_save(self, stat_name: str, modifier: int):
        if self.on_roll_request:
            self.on_roll_request(20, modifier, f"Salvación de {stat_name}")

    def _roll_skill(self, skill_name: str, modifier: int):
        if self.on_roll_request:
            self.on_roll_request(20, modifier, f"Prueba de {skill_name}")

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._build_ui()
        if self.page:
            self.update()
