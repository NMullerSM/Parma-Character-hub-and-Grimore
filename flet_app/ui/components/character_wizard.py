"""
Asistente de Creación Guiada de Personajes D&D 5e (PHB 2024 / OKF)
Permite a cualquier jugador forjar un aventurero paso a paso siguiendo las reglas oficiales del PHB 2024:
Paso 1: Clase (Dados de golpe, competencias, salvaciones)
Paso 2: Especie & Linaje (Velocidad, tamaño, visión en la oscuridad)
Paso 3: Trasfondo (Dote de origen, competencias, +2/+1 a atributos)
Paso 4: Puntuaciones de Característica (Standard Array 15, 14, 13, 12, 10, 8 + bonificadores)
Paso 5: Identidad, Cálculo de PG/CA/CD Mágica y Generación Final
"""
import flet as ft
from typing import Callable, Optional, Dict, Any, List
from ...core.models import CharacterSheet, CharacterFeature, WeaponAction, SpellSlotTier
from ...core.okf_engine import OkfEngine
from ...core.rules import (
    calc_modifier, calc_proficiency_bonus, CLASS_CASTING_ABILITY, get_spell_stats
)
from ..theme import (
    BG_PRIMARY, BG_SURFACE, BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE,
    COLOR_RED, COLOR_AMBER, create_card_container, create_badge, create_gold_button
)

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

CLASS_DEFAULTS = {
    "Bárbaro": {"hit_dice": 12, "saves": ["FUE", "CON"], "armor": "Ligeras, medias, escudos", "weapons": "Marciales, sencillas"},
    "Bardo": {"hit_dice": 8, "saves": ["DES", "CAR"], "armor": "Ligeras", "weapons": "Sencillas, estoque, arco corto"},
    "Clérigo": {"hit_dice": 8, "saves": ["SAB", "CAR"], "armor": "Ligeras, medias, escudos", "weapons": "Sencillas"},
    "Druida": {"hit_dice": 8, "saves": ["INT", "SAB"], "armor": "Ligeras, medias, escudos", "weapons": "Sencillas"},
    "Guerrero": {"hit_dice": 10, "saves": ["FUE", "CON"], "armor": "Todas las armaduras, escudos", "weapons": "Sencillas, marciales"},
    "Monje": {"hit_dice": 8, "saves": ["FUE", "DES"], "armor": "Ninguna", "weapons": "Sencillas, espadas cortas"},
    "Paladín": {"hit_dice": 10, "saves": ["SAB", "CAR"], "armor": "Todas las armaduras, escudos", "weapons": "Sencillas, marciales"},
    "Explorador": {"hit_dice": 10, "saves": ["FUE", "DES"], "armor": "Ligeras, medias, escudos", "weapons": "Sencillas, marciales"},
    "Pícaro": {"hit_dice": 8, "saves": ["DES", "INT"], "armor": "Ligeras", "weapons": "Sencillas, ballesta de mano, estoque"},
    "Hechicero": {"hit_dice": 6, "saves": ["CON", "CAR"], "armor": "Ninguna", "weapons": "Dagas, dardos, hondas"},
    "Brujo": {"hit_dice": 8, "saves": ["SAB", "CAR"], "armor": "Ligeras", "weapons": "Sencillas"},
    "Mago": {"hit_dice": 6, "saves": ["INT", "SAB"], "armor": "Ninguna", "weapons": "Dagas, dardos, hondas, bastones"}
}

BACKGROUND_FEATS = {
    "Acólito": ("Iniciado en la Magia", "Aprende 2 trucos y 1 conjuro de nivel 1."),
    "Animador": ("Músico", "Inspiras a tus aliados otorgándoles dados de inspiración tras un descanso."),
    "Artesano": ("Artesano Concienzudo", "Fabricas objetos con el doble de rapidez y menor coste."),
    "Charlatán": ("Habilidoso", "Obtienes competencia en 3 habilidades a tu elección."),
    "Criminal": ("Alerta", "Ganas +5 a iniciativa y no puedes ser sorprendido."),
    "Soldado": ("Curtido en Batalla", "Tus puntos de golpe máximos aumentan en 2 por nivel."),
    "Vagabundo": ("Afortunado", "Posees 3 puntos de suerte para repetir d20."),
    "Sabio": ("Iniciado en la Magia", "Aprende 2 trucos y 1 conjuro de nivel 1."),
    "Noble": ("Habilidoso", "Obtienes competencia en 3 habilidades adicionales."),
    "Guardia": ("Alerta", "Ganas +5 a iniciativa y vigilancia perpetua."),
    "Guía": ("Superviviente", "Ventaja en rastreo y supervivencia en exteriores.")
}

SPECIES_DEFAULTS = {
    "Humano": {"speed": "9 m", "darkvision": False, "size": "Mediano", "traits": "Dote adicional de origen, Inspiración heroica."},
    "Elfo": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Visión en la oscuridad (18m o 36m Drow), Linaje élfico, Trance."},
    "Enano": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Resistencia enana a veneno, Sentido de la piedra, +1 PG/nivel."},
    "Mediano": {"speed": "9 m", "darkvision": False, "size": "Pequeño", "traits": "Suerte mediano (repite 1 natural en d20), Valiente."},
    "Dracónido": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Arma de aliento elemental, Resistencia al daño."},
    "Gnomo": {"speed": "9 m", "darkvision": True, "size": "Pequeño", "traits": "Astucia gnoma (ventaja en salvaciones INT/SAB/CAR)."},
    "Goliat": {"speed": "10.5 m", "darkvision": False, "size": "Mediano", "traits": "Ascendencia de gigantes, Constitución poderosa."},
    "Orco": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Acometida agresiva, Resistencia incansable."},
    "Tiefling": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Resistencia al fuego, Taumaturgia innata, Linaje abisal/infernal."},
    "Aasimar": {"speed": "9 m", "darkvision": True, "size": "Mediano", "traits": "Curación celestial, Resistencia necrótica/radiante, Transformación."}
}


class CharacterCreatorWizard:
    def __init__(
        self,
        page: ft.Page,
        okf_engine: OkfEngine,
        on_character_created: Callable[[CharacterSheet], None]
    ):
        self.page = page
        self.okf = okf_engine
        self.on_character_created = on_character_created

        self.current_step = 1  # 1: Clase, 2: Especie, 3: Trasfondo, 4: Atributos, 5: Revisión

        # Estado del personaje en creación
        self.char_name = "Nuevo Aventurero"
        self.char_class = "Guerrero"
        self.char_species = "Humano"
        self.char_subspecies = ""
        self.char_background = "Soldado"
        self.char_alignment = "Neutral Bueno"

        # Atributos base (Standard Array)
        self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}
        self.bg_plus2 = "FUE"
        self.bg_plus1 = "CON"

        self._build_dialog()

    def show(self):
        self.current_step = 1
        self._update_step_content()
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close_dialog(self, e=None):
        self.dialog.open = False
        if self.dialog in self.page.overlay:
            self.page.overlay.remove(self.dialog)
        self.page.update()

    def _build_dialog(self):
        self.step_indicator = ft.Text("Paso 1 de 5: Elige tu Clase", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT)
        self.step_container = ft.Container(expand=True, padding=10)

        self.btn_prev = ft.OutlinedButton(
            text="◄ Anterior",
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._prev_step,
            visible=False
        )

        self.btn_next = ft.ElevatedButton(
            text="Siguiente ►",
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
            on_click=self._next_step
        )

        self.dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, color=GOLD_PRIMARY, size=24),
                            ft.Text("Forja de Personajes D&D 5e (PHB 2024)", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ],
                        spacing=8
                    ),
                    ft.IconButton(ft.Icons.CLOSE, icon_color=TEXT_MUTED, on_click=self._close_dialog)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.step_indicator,
                        ft.Divider(color=BORDER_DIM, height=1),
                        self.step_container
                    ],
                    spacing=10
                ),
                width=800,
                height=520
            ),
            actions=[
                self.btn_prev,
                self.btn_next
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _prev_step(self, e):
        if self.current_step > 1:
            self.current_step -= 1
            self._update_step_content()
            self.page.update()

    def _next_step(self, e):
        if self.current_step < 5:
            self.current_step += 1
            self._update_step_content()
            self.page.update()
        else:
            self._generate_character()

    def _update_step_content(self):
        self.btn_prev.visible = (self.current_step > 1)
        if self.current_step == 5:
            self.btn_next.text = "⚔️ ¡Forjar y Cargar Personaje!"
            self.btn_next.bgcolor = COLOR_GREEN
            self.btn_next.color = "#ffffff"
            self.btn_next.style = ft.ButtonStyle(bgcolor=COLOR_GREEN, color="#ffffff")
        else:
            self.btn_next.text = "Siguiente ►"
            self.btn_next.bgcolor = GOLD_PRIMARY
            self.btn_next.color = "#000000"
            self.btn_next.style = ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000")

        if self.current_step == 1:
            self.step_indicator.value = "Paso 1 de 5: Elige tu Clase Heroica"
            self._build_step1_class()
        elif self.current_step == 2:
            self.step_indicator.value = "Paso 2 de 5: Elige tu Especie y Linaje"
            self._build_step2_species()
        elif self.current_step == 3:
            self.step_indicator.value = "Paso 3 de 5: Elige tu Trasfondo (Dote de Origen y +2/+1)"
            self._build_step3_background()
        elif self.current_step == 4:
            self.step_indicator.value = "Paso 4 de 5: Asigna tus Puntuaciones de Atributo"
            self._build_step4_abilities()
        elif self.current_step == 5:
            self.step_indicator.value = "Paso 5 de 5: Identidad y Revisión Final"
            self._build_step5_review()

    # --- PASO 1: CLASE ---
    def _build_step1_class(self):
        class_cards = []
        for cls_name, info in CLASS_DEFAULTS.items():
            is_sel = (self.char_class == cls_name)
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(cls_name, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT if is_sel else "#ffffff"),
                                create_badge(f"d{info['hit_dice']}", bg_color=BG_INPUT, text_color=GOLD_PRIMARY, border_color=BORDER_GOLD)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(f"Salvaciones: {', '.join(info['saves'])}", size=11, color=TEXT_MUTED),
                        ft.Text(f"Armaduras: {info['armor']}", size=10, color=TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=4
                ),
                padding=10,
                width=230,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, cn=cls_name: self._set_class(cn)
            )
            class_cards.append(card)

        # Panel de Detalle de la Clase Seleccionada
        sel_info = CLASS_DEFAULTS.get(self.char_class, CLASS_DEFAULTS["Guerrero"])
        detail_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Clase Seleccionada: {self.char_class}", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text(f"Dado de Golpe: 1d{sel_info['hit_dice']} por nivel • Puntos de Golpe en Nivel 1: {sel_info['hit_dice']} + mod CON.", size=12, color="#f0f2f5"),
                    ft.Text(f"Tiradas de Salvación: Competencia en {sel_info['saves'][0]} y {sel_info['saves'][1]}.", size=12, color=GOLD_LIGHT),
                    ft.Text(f"Competencia en Armas: {sel_info['weapons']}.", size=12, color=TEXT_MUTED),
                    ft.Text(f"Competencia en Armaduras: {sel_info['armor']}.", size=12, color=TEXT_MUTED),
                ],
                spacing=6
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        grid = ft.Row(controls=class_cards, wrap=True, spacing=10)
        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Selecciona la vocación heroica de tu personaje:", size=13, color=TEXT_MUTED),
                grid,
                detail_box
            ],
            spacing=10,
            expand=True
        )

    def _set_class(self, cls_name: str):
        self.char_class = cls_name
        self._build_step1_class()
        self.page.update()

    # --- PASO 2: ESPECIE ---
    def _build_step2_species(self):
        species_cards = []
        for sp_name, info in SPECIES_DEFAULTS.items():
            is_sel = (self.char_species == sp_name)
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(sp_name, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT if is_sel else "#ffffff"),
                                create_badge(info['speed'], bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(f"Tamaño: {info['size']} • Visión: {'Oscuridad' if info['darkvision'] else 'Normal'}", size=11, color=TEXT_MUTED),
                    ],
                    spacing=4
                ),
                padding=10,
                width=230,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, sn=sp_name: self._set_species(sn)
            )
            species_cards.append(card)

        sel_info = SPECIES_DEFAULTS.get(self.char_species, SPECIES_DEFAULTS["Humano"])
        detail_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Especie Seleccionada: {self.char_species}", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text(f"Velocidad: {sel_info['speed']} • Tamaño: {sel_info['size']}.", size=12, color="#f0f2f5"),
                    ft.Text(f"Rasgos Biológicos: {sel_info['traits']}", size=12, color=GOLD_LIGHT),
                ],
                spacing=6
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        grid = ft.Row(controls=species_cards, wrap=True, spacing=10)
        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Selecciona la especie o linaje de tu personaje:", size=13, color=TEXT_MUTED),
                grid,
                detail_box
            ],
            spacing=10,
            expand=True
        )

    def _set_species(self, sp_name: str):
        self.char_species = sp_name
        self._build_step2_species()
        self.page.update()

    # --- PASO 3: TRASFONDO ---
    def _build_step3_background(self):
        bg_cards = []
        for bg_name, (feat_name, feat_desc) in BACKGROUND_FEATS.items():
            is_sel = (self.char_background == bg_name)
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(bg_name, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT if is_sel else "#ffffff"),
                        ft.Text(f"Dote de Origen: {feat_name}", size=11, color=GOLD_PRIMARY, weight=ft.FontWeight.W_600),
                    ],
                    spacing=2
                ),
                padding=10,
                width=230,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, bn=bg_name: self._set_background(bn)
            )
            bg_cards.append(card)

        # Selectores para bono +2 y +1 del Trasfondo (Regla PHB 2024)
        stat_options = [
            ft.dropdown.Option("FUE", "Fuerza (FUE)"),
            ft.dropdown.Option("DES", "Destreza (DES)"),
            ft.dropdown.Option("CON", "Constitución (CON)"),
            ft.dropdown.Option("INT", "Inteligencia (INT)"),
            ft.dropdown.Option("SAB", "Sabiduría (SAB)"),
            ft.dropdown.Option("CAR", "Carisma (CAR)"),
        ]

        def on_plus2_change(e):
            self.bg_plus2 = e.control.value
            if self.bg_plus2 == self.bg_plus1:
                # Cambiar el otro para que no coincidan
                for opt in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
                    if opt != self.bg_plus2:
                        self.bg_plus1 = opt
                        break
            self._build_step3_background()
            self.page.update()

        def on_plus1_change(e):
            self.bg_plus1 = e.control.value
            self._build_step3_background()
            self.page.update()

        bonus_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Mejoras de Característica del Trasfondo (PHB 2024):", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text("En D&D 5e (2024), tu trasfondo te otorga un bono de +2 a un atributo y +1 a otro atributo:", size=11, color=TEXT_MUTED),
                    ft.Row(
                        controls=[
                            ft.Dropdown(label="Atributo con Bono +2", value=self.bg_plus2, options=stat_options, width=220, border_color=BORDER_GOLD, on_change=on_plus2_change),
                            ft.Dropdown(label="Atributo con Bono +1", value=self.bg_plus1, options=stat_options, width=220, border_color=BORDER_DIM, on_change=on_plus1_change),
                        ],
                        spacing=12
                    )
                ],
                spacing=8
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        grid = ft.Row(controls=bg_cards, wrap=True, spacing=10)
        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Selecciona tu trasfondo y asigna tus bonos de característica:", size=13, color=TEXT_MUTED),
                grid,
                bonus_box
            ],
            spacing=10,
            expand=True
        )

    def _set_background(self, bg_name: str):
        self.char_background = bg_name
        self._build_step3_background()
        self.page.update()

    # --- PASO 4: ATRIBUTOS (Standard Array) ---
    def _build_step4_abilities(self):
        stat_names = ["FUE", "DES", "CON", "INT", "SAB", "CAR"]
        stat_full = {"FUE": "Fuerza", "DES": "Destreza", "CON": "Constitución", "INT": "Inteligencia", "SAB": "Sabiduría", "CAR": "Carisma"}

        rows = []
        for stat in stat_names:
            base_score = self.raw_scores[stat]
            bg_add = (2 if self.bg_plus2 == stat else (1 if self.bg_plus1 == stat else 0))
            final_score = base_score + bg_add
            mod = calc_modifier(final_score)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)

            def make_change_handler(s=stat):
                def handler(e):
                    try:
                        self.raw_scores[s] = int(e.control.value)
                        self._build_step4_abilities()
                        self.page.update()
                    except ValueError:
                        pass
                return handler

            dropdown = ft.Dropdown(
                value=str(base_score),
                options=[
                    ft.dropdown.Option("15", "15 (Alto)"),
                    ft.dropdown.Option("14", "14"),
                    ft.dropdown.Option("13", "13"),
                    ft.dropdown.Option("12", "12"),
                    ft.dropdown.Option("10", "10 (Medio)"),
                    ft.dropdown.Option("8", "8 (Bajo)"),
                ],
                width=110,
                border_color=BORDER_DIM,
                on_change=make_change_handler()
            )

            bonus_badge = ft.Text(f"+{bg_add} Trasfondo" if bg_add > 0 else "—", size=11, color=GOLD_PRIMARY if bg_add > 0 else TEXT_MUTED)

            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"{stat} ({stat_full[stat]})", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                bonus_badge
                            ],
                            width=160,
                            spacing=2
                        ),
                        dropdown,
                        ft.Text("➔ Puntuación Final:", size=11, color=TEXT_MUTED),
                        ft.Text(str(final_score), size=16, weight=ft.FontWeight.BOLD, color="#ffffff"),
                        create_badge(f"Mod {mod_str}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=BG_INPUT,
                padding=8,
                border_radius=ft.border_radius.all(6),
                border=ft.border.all(1, BORDER_DIM)
            )
            rows.append(row)

        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Conjunto Estándar Oficial D&D 5e (15, 14, 13, 12, 10, 8):", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ft.Text("Asigna qué puntuación base va a cada característica. Los bonos de tu trasfondo (+2 y +1) se suman automáticamente:", size=11, color=TEXT_MUTED),
                *rows
            ],
            spacing=8,
            expand=True
        )

    # --- PASO 5: REVISIÓN & GENERACIÓN ---
    def _build_step5_review(self):
        # Calcular PGs de nivel 1
        con_score = self.raw_scores["CON"] + (2 if self.bg_plus2 == "CON" else (1 if self.bg_plus1 == "CON" else 0))
        con_mod = calc_modifier(con_score)
        hd = CLASS_DEFAULTS[self.char_class]["hit_dice"]
        level1_hp = max(1, hd + con_mod)

        # Calcular CA de nivel 1
        des_score = self.raw_scores["DES"] + (2 if self.bg_plus2 == "DES" else (1 if self.bg_plus1 == "DES" else 0))
        des_mod = calc_modifier(des_score)
        base_ca = 10 + des_mod

        # Calcular CD de conjuros (si aplica)
        cast_stat = CLASS_CASTING_ABILITY.get(self.char_class, "CAR")
        cast_score = self.raw_scores[cast_stat] + (2 if self.bg_plus2 == cast_stat else (1 if self.bg_plus1 == cast_stat else 0))
        cast_mod = calc_modifier(cast_score)
        spell_dc = 8 + 2 + cast_mod

        name_field = ft.TextField(
            label="Nombre del Aventurero",
            value=self.char_name,
            border_color=BORDER_GOLD,
            color="#ffffff",
            on_change=lambda e: setattr(self, "char_name", e.control.value)
        )

        align_dropdown = ft.Dropdown(
            label="Alineamiento Moral",
            value=self.char_alignment,
            options=[
                ft.dropdown.Option("Legal Bueno", "Legal Bueno"),
                ft.dropdown.Option("Neutral Bueno", "Neutral Bueno"),
                ft.dropdown.Option("Caótico Bueno", "Caótico Bueno"),
                ft.dropdown.Option("Legal Neutral", "Legal Neutral"),
                ft.dropdown.Option("Neutral", "Neutral Auténtico"),
                ft.dropdown.Option("Caótico Neutral", "Caótico Neutral"),
                ft.dropdown.Option("Legal Maligno", "Legal Maligno"),
            ],
            border_color=BORDER_DIM,
            on_change=lambda e: setattr(self, "char_alignment", e.control.value)
        )

        summary_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📜 Resumen de Estadísticas de Nivel 1", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(
                        controls=[
                            create_badge(f"Clase: {self.char_class} (d{hd})", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD),
                            create_badge(f"Especie: {self.char_species}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD),
                            create_badge(f"Trasfondo: {self.char_background}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD),
                        ],
                        wrap=True,
                        spacing=6
                    ),
                    ft.Divider(color=BORDER_DIM, height=1),
                    ft.Row(
                        controls=[
                            ft.Text(f"❤️ Puntos de Golpe: {level1_hp} PG", size=13, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                            ft.Text(f"🛡️ Clase de Armadura: {base_ca} CA", size=13, weight=ft.FontWeight.BOLD, color=GOLD_PRIMARY),
                            ft.Text(f"⚡ Iniciativa: {f'+{des_mod}' if des_mod >= 0 else str(des_mod)}", size=13, color=GOLD_LIGHT),
                            ft.Text(f"🔮 CD Conjuro ({cast_stat}): CD {spell_dc}", size=13, color=COLOR_PURPLE),
                        ],
                        wrap=True,
                        spacing=12
                    ),
                    ft.Text(f"Dote de Origen Adquirida: {BACKGROUND_FEATS.get(self.char_background, ('', ''))[0]}", size=12, color=GOLD_PRIMARY, italic=True)
                ],
                spacing=8
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Asigna el nombre y revisa el cálculo final de tu héroe:", size=13, color=TEXT_MUTED),
                ft.Row([name_field, align_dropdown], spacing=10),
                summary_card
            ],
            spacing=10,
            expand=True
        )

    def _generate_character(self):
        # 1. Puntuaciones finales
        final_abilities = {}
        for stat, base in self.raw_scores.items():
            bonus = (2 if self.bg_plus2 == stat else (1 if self.bg_plus1 == stat else 0))
            final_abilities[stat] = base + bonus

        # 2. HP y CA
        con_mod = calc_modifier(final_abilities["CON"])
        des_mod = calc_modifier(final_abilities["DES"])
        hd = CLASS_DEFAULTS[self.char_class]["hit_dice"]
        level1_hp = max(1, hd + con_mod)
        ca = 10 + des_mod

        # 3. Dote de origen
        feat_name, feat_desc = BACKGROUND_FEATS.get(self.char_background, ("Dote de Origen", "Dote de trasfondo"))
        features = [
            CharacterFeature(
                name=feat_name,
                source=f"Trasfondo ({self.char_background})",
                description=feat_desc,
                recharge="Pasivo"
            ),
            CharacterFeature(
                name=f"Rasgos de {self.char_species}",
                source=f"Especie ({self.char_species})",
                description=SPECIES_DEFAULTS.get(self.char_species, {}).get("traits", ""),
                recharge="Pasivo"
            )
        ]

        # 4. Armas iniciales según clase
        weapons = [
            WeaponAction(name="Espada Corta", attack_bonus=f"+{des_mod + 2}", damage=f"1d6+{des_mod}", damage_type="Perforante", notes="Sutil, Ligera"),
            WeaponAction(name="Daga", attack_bonus=f"+{des_mod + 2}", damage=f"1d4+{des_mod}", damage_type="Perforante", notes="Arrojadiza (6/18m)"),
        ]

        # 5. Espacios de conjuro si es clase mágica
        slots = {}
        if self.char_class in ["Bardo", "Clérigo", "Druida", "Hechicero", "Mago"]:
            slots["1"] = SpellSlotTier(level=1, total=2, current=2)
        elif self.char_class == "Brujo":
            slots["1"] = SpellSlotTier(level=1, total=1, current=1)

        new_char = CharacterSheet(
            name=self.char_name.strip() or "Nuevo Héroe",
            char_class=self.char_class,
            subclass="",
            level=1,
            race=self.char_species,
            background=self.char_background,
            alignment=self.char_alignment,
            xp=0,
            hp_current=level1_hp,
            hp_max=level1_hp,
            armor_class=ca,
            initiative_bonus=des_mod,
            speed=SPECIES_DEFAULTS.get(self.char_species, {}).get("speed", "9 m"),
            proficiency_bonus=2,
            abilities=final_abilities,
            saving_throw_profs=CLASS_DEFAULTS[self.char_class]["saves"],
            features=features,
            weapons=weapons,
            spell_slots=slots
        )

        self._close_dialog()
        if self.on_character_created:
            self.on_character_created(new_char)

        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✨ ¡{new_char.name} ({new_char.char_class} Nivel 1) ha sido forjado exitosamente!"))
            self.page.snack_bar.open = True
            self.page.update()
