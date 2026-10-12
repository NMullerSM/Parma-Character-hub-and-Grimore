"""
Asistente de Creación Guiada de Personajes D&D 5e (PHB 2024 / OKF)
Permite a cualquier jugador forjar un aventurero paso a paso siguiendo las reglas oficiales del PHB 2024:
Paso 1: Clase (Dados de golpe, competencias, salvaciones)
Paso 2: Especie & Subraza / Linaje (Velocidad, tamaño, visión en la oscuridad, rasgos innatos)
Paso 3: Trasfondo (Dote de origen, competencias, +2/+1 a atributos)
Paso 4: Puntuaciones de Característica (Conjunto Estándar, Tiradas 4d6 descartando menor, o Manual)
Paso 5: Identidad, Retrato, Cálculo de PG/CA/CD Mágica y Generación Final
"""
import random
import flet as ft
from typing import Callable, Optional, Dict, Any, List
from ...core.models import CharacterSheet, CharacterFeature, WeaponAction, SpellSlotTier
from ...core.okf_engine import OkfEngine
from ...core.db import DatabaseManager
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
    "Humano": {
        "speed": "9 m", "darkvision": False, "size": "Mediano",
        "traits": "Dote adicional de origen, Inspiración heroica diaria.",
        "subspecies": {
            "Estándar": {"speed": "9 m", "traits": "Versatilidad humana, dote adicional de origen."},
            "Variante": {"speed": "9 m", "traits": "Dote de origen a elección, habilidad adicional."}
        }
    },
    "Elfo": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Visión en la oscuridad, Linaje élfico, Trance de 4 horas.",
        "subspecies": {
            "Alto Elfo": {"speed": "9 m", "traits": "Truco de mago a elección, idioma adicional, visión en la oscuridad (18m)."},
            "Elfo de los Bosques": {"speed": "10.5 m", "traits": "Velocidad 10.5m (35 pies), Máscara de la naturaleza para ocultarse en follaje."},
            "Drow (Elfo Oscuro)": {"speed": "9 m", "traits": "Visión en oscuridad superior (36m), Sensibilidad a la luz solar, Magia drow innata (Luces Danzantes, Fuego Feérico, Oscuridad)."},
            "Eladrín": {"speed": "9 m", "traits": "Paso Feérico (teleportación brumosa de 9m) con efectos estacionales."}
        }
    },
    "Enano": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Resistencia enana a veneno, Sentido de la piedra, herramientas.",
        "subspecies": {
            "Enano de las Colinas": {"speed": "9 m", "traits": "Dureza enana (+1 punto de golpe por nivel adicional)."},
            "Enano de las Montañas": {"speed": "9 m", "traits": "Competencia con armaduras ligeras y medias, fuerza telúrica."},
            "Duergar (Enano Gris)": {"speed": "9 m", "traits": "Visión superior (36m), Magia duergar (Agrandar e Invisibilidad innatas)."}
        }
    },
    "Mediano": {
        "speed": "9 m", "darkvision": False, "size": "Pequeño",
        "traits": "Suerte mediano (repite 1 natural en d20), Valiente, Agilidad.",
        "subspecies": {
            "Piesligeros": {"speed": "9 m", "traits": "Sigilo innato: ocultarse tras criaturas de tamaño mediano o mayor."},
            "Fornido": {"speed": "9 m", "traits": "Resistencia fornida: ventaja y resistencia contra veneno."}
        }
    },
    "Dracónido": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Arma de aliento elemental, Resistencia al daño de su color.",
        "subspecies": {
            "Cromático": {"speed": "9 m", "traits": "Aliento de línea o cono (1d10), Inmunidad cromática temporal (Niv 5)."},
            "Metálico": {"speed": "9 m", "traits": "Aliento elemental destructivo y segundo aliento incapacitante (Niv 5)."}
        }
    },
    "Gnomo": {
        "speed": "9 m", "darkvision": True, "size": "Pequeño",
        "traits": "Astucia gnoma (ventaja en salvaciones INT/SAB/CAR contra magia).",
        "subspecies": {
            "Gnomo de las Rocas": {"speed": "9 m", "traits": "Conocimiento de artífice en maquinaria y creación de juguetes mecánicos."},
            "Gnomo de los Bosques": {"speed": "9 m", "traits": "Truco Ilusión Menor innato y capacidad de comunicarse con bestias pequeñas."},
            "Gnomo de las Profundidades": {"speed": "9 m", "traits": "Visión en oscuridad 36m y camuflaje con la roca."}
        }
    },
    "Tiefling": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Visión en la oscuridad (18m), Taumaturgia, resistencia mágica.",
        "subspecies": {
            "Infernal": {"speed": "9 m", "traits": "Resistencia al fuego, Reprensión Infernal y Oscuridad."},
            "Abisal": {"speed": "9 m", "traits": "Resistencia al veneno, Rociada Venenosa y Rayo de Enfermedad."},
            "Ctónico": {"speed": "9 m", "traits": "Resistencia necrótica, Toque Helado y Falsa Vida."}
        }
    },
    "Goliat": {
        "speed": "10.5 m", "darkvision": False, "size": "Mediano",
        "traits": "Constitución poderosa, Resistencia de piedra a daño.",
        "subspecies": {
            "Linaje de las Colinas": {"speed": "10.5 m", "traits": "Fuerza titánica para derribar enemigos."},
            "Linaje de la Tormenta": {"speed": "10.5 m", "traits": "Resistencia y represalia eléctrica."}
        }
    },
    "Orco": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Acometida agresiva, Resistencia incansable ante la muerte.",
        "subspecies": {
            "Estándar": {"speed": "9 m", "traits": "Acometida como acción adicional y salvación heroica a 1 PG."}
        }
    },
    "Aasimar": {
        "speed": "9 m", "darkvision": True, "size": "Mediano",
        "traits": "Curación celestial, Resistencia necrótica/radiante.",
        "subspecies": {
            "Protector": {"speed": "9 m", "traits": "Alas luminosas incorpóreas con velocidad de vuelo y daño radiante."},
            "Vengador": {"speed": "9 m", "traits": "Mirada abrasadora e intimidación radiante."}
        }
    }
}


class CharacterCreatorWizard:
    def __init__(
        self,
        page: ft.Page,
        okf_engine: OkfEngine,
        on_character_created: Callable[[CharacterSheet], None],
        on_open_manager: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.okf = okf_engine
        self.on_character_created = on_character_created
        self.on_open_manager = on_open_manager

        self.current_step = 1  # 1: Clase, 2: Especie, 3: Trasfondo, 4: Atributos, 5: Revisión

        # Estado del personaje en creación
        self.char_name = "Nuevo Aventurero"
        self.char_class = "Guerrero"
        self.char_species = "Humano"
        self.char_subspecies = "Estándar"
        self.char_background = "Soldado"
        self.char_alignment = "Neutral Bueno"
        self.char_portrait_path = ""

        # Atributos base
        self.ability_mode = "standard"  # "standard", "dice", "manual"
        self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}
        self.rolled_scores = []
        self.bg_plus2 = "FUE"
        self.bg_plus1 = "CON"

        # FilePicker para foto de retrato
        self.portrait_picker = ft.FilePicker(on_result=self._on_portrait_selected)
        if self.portrait_picker not in self.page.overlay:
            self.page.overlay.append(self.portrait_picker)

        self._build_dialog()

    def show(self):
        self.current_step = 1
        self._update_step_content()
        self.page.open(self.dialog)

    def _close_dialog(self, e=None):
        self.page.close(self.dialog)

    def _on_open_saved_click(self, e):
        self._close_dialog()
        if self.on_open_manager:
            self.on_open_manager()

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

        btn_open_saved = ft.OutlinedButton(
            text="📂 Personajes Guardados",
            icon=ft.Icons.FOLDER_SHARED,
            style=ft.ButtonStyle(
                color=GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_DIM)
            ),
            tooltip="Ver o cargar personajes existentes en la base de datos",
            on_click=self._on_open_saved_click
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            on_dismiss=lambda e: None,
            title=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, color=GOLD_PRIMARY, size=24),
                            ft.Text("Forja de Personajes D&D 5e (PHB 2024)", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ],
                        spacing=8
                    ),
                    ft.Row(
                        controls=[
                            btn_open_saved,
                            ft.IconButton(ft.Icons.CLOSE, icon_color=TEXT_MUTED, on_click=self._close_dialog)
                        ],
                        spacing=4
                    )
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
                width=820,
                height=540
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
            self.step_indicator.value = "Paso 2 de 5: Elige tu Especie y Subraza / Linaje"
            self._build_step2_species()
        elif self.current_step == 3:
            self.step_indicator.value = "Paso 3 de 5: Elige tu Trasfondo (Dote de Origen y +2/+1)"
            self._build_step3_background()
        elif self.current_step == 4:
            self.step_indicator.value = "Paso 4 de 5: Puntuaciones de Característica"
            self._build_step4_abilities()
        elif self.current_step == 5:
            self.step_indicator.value = "Paso 5 de 5: Identidad, Retrato y Revisión Final"
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
                        ft.Text(f"Armadura: {info['armor']}", size=11, color=TEXT_MUTED, max_lines=1, no_wrap=True),
                    ],
                    spacing=4
                ),
                padding=10,
                width=180,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, cn=cls_name: self._set_class(cn)
            )
            class_cards.append(card)

        grid = ft.Row(controls=class_cards, wrap=True, spacing=10)
        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("Selecciona una de las 12 Clases oficiales de D&D 5e (PHB 2024):", size=13, color=TEXT_MUTED),
                grid
            ],
            spacing=10,
            expand=True
        )

    def _set_class(self, cls_name: str):
        self.char_class = cls_name
        self._build_step1_class()
        self.page.update()

    # --- PASO 2: ESPECIE & SUBRAZA ---
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
                width=185,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, sn=sp_name: self._set_species(sn)
            )
            species_cards.append(card)

        sel_info = SPECIES_DEFAULTS.get(self.char_species, SPECIES_DEFAULTS["Humano"])
        sub_options = sel_info.get("subspecies", {})

        # Asegurar subraza válida
        if self.char_subspecies not in sub_options and sub_options:
            self.char_subspecies = list(sub_options.keys())[0]

        sub_chips = []
        for sub_name, sub_data in sub_options.items():
            is_sub_sel = (self.char_subspecies == sub_name)
            sub_chip = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE if is_sub_sel else ft.Icons.RADIO_BUTTON_UNCHECKED, size=14, color=GOLD_PRIMARY if is_sub_sel else TEXT_MUTED),
                        ft.Text(sub_name, size=12, weight=ft.FontWeight.BOLD if is_sub_sel else ft.FontWeight.NORMAL, color=GOLD_LIGHT if is_sub_sel else "#f0f2f5"),
                    ],
                    spacing=6
                ),
                bgcolor=BG_CARD_ALT if is_sub_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sub_sel else 1, BORDER_GOLD if is_sub_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda e, sn=sub_name: self._set_subspecies(sn)
            )
            sub_chips.append(sub_chip)

        sub_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Linajes / Subrazas de {self.char_species}:", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(controls=sub_chips, wrap=True, spacing=8),
                ],
                spacing=8
            ),
            visible=bool(sub_options),
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=10
        )

        active_sub_traits = sub_options.get(self.char_subspecies, {}).get("traits", sel_info["traits"])
        active_sub_speed = sub_options.get(self.char_subspecies, {}).get("speed", sel_info["speed"])

        detail_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"Especie: {self.char_species}  ➔  {self.char_subspecies}", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            create_badge(f"Velocidad: {active_sub_speed}", bg_color=BG_INPUT, text_color=GOLD_PRIMARY, border_color=BORDER_GOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Text(f"Rasgos Biológicos & Mágicos: {active_sub_traits}", size=12, color="#f0f2f5"),
                ],
                spacing=6
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        grid = ft.Row(controls=species_cards, wrap=True, spacing=8)
        self.step_container.content = ft.ListView(
            controls=[
                ft.Text("1. Selecciona la especie base:", size=13, color=TEXT_MUTED),
                grid,
                sub_box,
                detail_box
            ],
            spacing=10,
            expand=True
        )

    def _set_species(self, sp_name: str):
        self.char_species = sp_name
        sub_options = SPECIES_DEFAULTS.get(sp_name, {}).get("subspecies", {})
        if sub_options:
            self.char_subspecies = list(sub_options.keys())[0]
        else:
            self.char_subspecies = ""
        self._build_step2_species()
        self.page.update()

    def _set_subspecies(self, sub_name: str):
        self.char_subspecies = sub_name
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
                width=220,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, BORDER_GOLD if is_sel else BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                on_click=lambda e, bn=bg_name: self._set_background(bn)
            )
            bg_cards.append(card)

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
            if self.bg_plus1 == self.bg_plus2:
                for opt in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
                    if opt != self.bg_plus2:
                        self.bg_plus1 = opt
                        break
            self._build_step3_background()
            self.page.update()

        def on_plus1_change(e):
            self.bg_plus1 = e.control.value
            if self.bg_plus1 == self.bg_plus2:
                for opt in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
                    if opt != self.bg_plus1:
                        self.bg_plus2 = opt
                        break
            self._build_step3_background()
            self.page.update()

        bonus_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Bonos de Atributo del Trasfondo (+2 y +1):", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
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

    # --- PASO 4: ATRIBUTOS (3 MODOS: ESTÁNDAR, 4D6, MANUAL) ---
    def _set_ability_mode(self, mode: str):
        self.ability_mode = mode
        if mode == "standard":
            self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}
        elif mode == "dice" and not self.rolled_scores:
            self._roll_4d6_scores()
        self._build_step4_abilities()
        self.page.update()

    def _roll_4d6_scores(self, e=None):
        results = []
        for _ in range(6):
            d4 = [random.randint(1, 6) for _ in range(4)]
            d4.sort()
            score = sum(d4[1:])  # suma los 3 mayores
            results.append(score)
        results.sort(reverse=True)
        self.rolled_scores = results
        # Asignar automáticamente en orden descendente inicial
        stats = ["FUE", "DES", "CON", "INT", "SAB", "CAR"]
        for i, s in enumerate(stats):
            self.raw_scores[s] = results[i]
        self._build_step4_abilities()
        if self.page:
            self.page.update()

    def _build_step4_abilities(self):
        stat_names = ["FUE", "DES", "CON", "INT", "SAB", "CAR"]
        stat_full = {"FUE": "Fuerza", "DES": "Destreza", "CON": "Constitución", "INT": "Inteligencia", "SAB": "Sabiduría", "CAR": "Carisma"}

        # Barra de selección de Modo
        mode_btn_std = ft.ElevatedButton(
            text="Conjunto Estándar",
            color="#000000" if self.ability_mode == "standard" else GOLD_LIGHT,
            bgcolor=GOLD_PRIMARY if self.ability_mode == "standard" else BG_INPUT,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if self.ability_mode == "standard" else BG_INPUT,
                color="#000000" if self.ability_mode == "standard" else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if self.ability_mode == "standard" else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=lambda e: self._set_ability_mode("standard"),
            tooltip="Valores oficiales fijos: 15, 14, 13, 12, 10, 8"
        )
        mode_btn_dice = ft.ElevatedButton(
            text="🎲 Tirar 4d6 (Menor Descartado)",
            color="#000000" if self.ability_mode == "dice" else GOLD_LIGHT,
            bgcolor=GOLD_PRIMARY if self.ability_mode == "dice" else BG_INPUT,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if self.ability_mode == "dice" else BG_INPUT,
                color="#000000" if self.ability_mode == "dice" else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if self.ability_mode == "dice" else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=lambda e: self._set_ability_mode("dice"),
            tooltip="Tirada aleatoria oficial de 4 dados de 6 caras descartando el más bajo"
        )
        mode_btn_manual = ft.ElevatedButton(
            text="✍️ Manual / Libre",
            color="#000000" if self.ability_mode == "manual" else GOLD_LIGHT,
            bgcolor=GOLD_PRIMARY if self.ability_mode == "manual" else BG_INPUT,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if self.ability_mode == "manual" else BG_INPUT,
                color="#000000" if self.ability_mode == "manual" else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if self.ability_mode == "manual" else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=lambda e: self._set_ability_mode("manual"),
            tooltip="Ingresa directamente cualquier puntuación numérica obtenida en mesa"
        )

        mode_bar = ft.Row([mode_btn_std, mode_btn_dice, mode_btn_manual], spacing=8, wrap=True)

        banner_controls = []
        if self.ability_mode == "dice":
            scores_str = ", ".join(str(s) for s in self.rolled_scores)
            banner_controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Row([
                                ft.Icon(ft.Icons.CASINO, color=GOLD_PRIMARY, size=20),
                                ft.Text(f"Puntuaciones 4d6 Obtenidas: {scores_str}", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ], spacing=8),
                            ft.OutlinedButton(
                                text="🎲 Re-tirar Dados",
                                style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                                on_click=self._roll_4d6_scores
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor=BG_SURFACE,
                    border=ft.border.all(1, BORDER_GOLD),
                    border_radius=ft.border_radius.all(6),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8)
                )
            ]

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

            if self.ability_mode == "manual":
                stat_control = ft.TextField(
                    value=str(base_score),
                    width=90,
                    text_size=13,
                    content_padding=ft.padding.all(8),
                    border_color=BORDER_DIM,
                    focused_border_color=BORDER_GOLD,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=make_change_handler()
                )
            elif self.ability_mode == "dice":
                # Dropdown con las opciones generadas
                opts = [ft.dropdown.Option(str(v), str(v)) for v in sorted(list(set(self.rolled_scores)), reverse=True)]
                stat_control = ft.Dropdown(
                    value=str(base_score),
                    options=opts,
                    width=100,
                    border_color=BORDER_DIM,
                    on_change=make_change_handler()
                )
            else:
                # Standard Array
                stat_control = ft.Dropdown(
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
                        stat_control,
                        ft.Text("➔ Total:", size=12, color=TEXT_MUTED),
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
                mode_bar,
                *banner_controls,
                ft.Text("Asigna las puntuaciones base a cada característica. Los bonos de tu trasfondo (+2 y +1) se suman automáticamente:", size=11, color=TEXT_MUTED),
                *rows
            ],
            spacing=8,
            expand=True
        )

    # --- PASO 5: REVISIÓN & FOTO DE RETRATO ---
    def _pick_portrait(self, e):
        self.portrait_picker.pick_files(
            dialog_title="Seleccionar Retrato del Personaje",
            allowed_extensions=["png", "jpg", "jpeg", "webp"],
            allow_multiple=False
        )

    def _on_portrait_selected(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            src = e.files[0].path
            if src:
                db = DatabaseManager()
                saved_path = db.save_portrait_file(src, self.char_name)
                self.char_portrait_path = saved_path
                self._build_step5_review()
                self.page.update()

    def _build_step5_review(self):
        con_score = self.raw_scores["CON"] + (2 if self.bg_plus2 == "CON" else (1 if self.bg_plus1 == "CON" else 0))
        con_mod = calc_modifier(con_score)
        hd = CLASS_DEFAULTS[self.char_class]["hit_dice"]
        level1_hp = max(1, hd + con_mod)

        des_score = self.raw_scores["DES"] + (2 if self.bg_plus2 == "DES" else (1 if self.bg_plus1 == "DES" else 0))
        des_mod = calc_modifier(des_score)
        base_ca = 10 + des_mod

        cast_stat = CLASS_CASTING_ABILITY.get(self.char_class, "CAR")
        cast_score = self.raw_scores[cast_stat] + (2 if self.bg_plus2 == cast_stat else (1 if self.bg_plus1 == cast_stat else 0))
        cast_mod = calc_modifier(cast_score)
        spell_dc = 8 + 2 + cast_mod

        name_field = ft.TextField(
            label="Nombre del Aventurero",
            value=self.char_name,
            border_color=BORDER_GOLD,
            color="#ffffff",
            expand=True,
            on_change=lambda e: setattr(self, "char_name", e.control.value)
        )

        align_dropdown = ft.Dropdown(
            label="Alineamiento Moral",
            value=self.char_alignment,
            width=200,
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

        # Sección de Foto de Retrato
        if self.char_portrait_path:
            portrait_preview = ft.Image(
                src=self.char_portrait_path,
                width=64,
                height=64,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(32)
            )
        else:
            portrait_preview = ft.CircleAvatar(
                content=ft.Text(self.char_name[:2].upper() if self.char_name else "AV", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                bgcolor=BG_INPUT,
                radius=28
            )

        portrait_row = ft.Container(
            content=ft.Row(
                controls=[
                    portrait_preview,
                    ft.Column(
                        controls=[
                            ft.Text("Retrato / Avatar del Héroe", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.Text(self.char_portrait_path or "Sin imagen asignada (se usará el blasón heráldico de clase)", size=11, color=TEXT_MUTED, max_lines=1, no_wrap=True),
                            ft.ElevatedButton(
                                text="📷 Subir Foto de Disco...",
                                icon=ft.Icons.UPLOAD_FILE,
                                style=ft.ButtonStyle(bgcolor=BG_INPUT, color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
                                on_click=self._pick_portrait
                            )
                        ],
                        spacing=4,
                        expand=True
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=10
        )

        display_race = f"{self.char_species} ({self.char_subspecies})" if self.char_subspecies else self.char_species

        summary_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📜 Resumen de Estadísticas de Nivel 1", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(
                        controls=[
                            create_badge(f"Clase: {self.char_class} (d{hd})", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD),
                            create_badge(f"Especie: {display_race}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD),
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
                    ft.Text(f"Dote de Origen: {BACKGROUND_FEATS.get(self.char_background, ('', ''))[0]}", size=12, color=GOLD_PRIMARY, italic=True)
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
                ft.Text("Asigna el nombre, imagen y revisa el cálculo final de tu héroe:", size=13, color=TEXT_MUTED),
                ft.Row([name_field, align_dropdown], spacing=10),
                portrait_row,
                summary_card
            ],
            spacing=10,
            expand=True
        )

    # --- GENERACIÓN FINAL DEL PERSONAJE ---
    def _generate_character(self):
        # 1. Calcular atributos finales
        final_abilities = {}
        for stat in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = self.raw_scores[stat]
            add = (2 if self.bg_plus2 == stat else (1 if self.bg_plus1 == stat else 0))
            final_abilities[stat] = base + add

        con_mod = calc_modifier(final_abilities["CON"])
        des_mod = calc_modifier(final_abilities["DES"])
        hd = CLASS_DEFAULTS[self.char_class]["hit_dice"]
        level1_hp = max(1, hd + con_mod)

        # Bono de dureza enana si aplica
        if self.char_subspecies == "Enano de las Colinas":
            level1_hp += 1

        ca = 10 + des_mod

        # 2. Dote de trasfondo
        feat_name, feat_desc = BACKGROUND_FEATS.get(self.char_background, ("Dote de Origen", "Dote inicial"))

        # Rasgos de especie y subraza
        sp_info = SPECIES_DEFAULTS.get(self.char_species, {})
        sub_info = sp_info.get("subspecies", {}).get(self.char_subspecies, {})
        sub_traits = sub_info.get("traits", sp_info.get("traits", ""))
        speed = sub_info.get("speed", sp_info.get("speed", "9 m"))

        display_race = f"{self.char_species} ({self.char_subspecies})" if self.char_subspecies else self.char_species

        features = [
            CharacterFeature(
                name=feat_name,
                source=f"Trasfondo ({self.char_background})",
                description=feat_desc,
                recharge="Pasivo"
            ),
            CharacterFeature(
                name=f"Rasgos de {display_race}",
                source=f"Especie ({display_race})",
                description=sub_traits,
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

        # 6. Determinar sentidos según especie y linaje
        spec_info = SPECIES_DEFAULTS.get(self.char_species, {})
        has_darkvision = spec_info.get("darkvision", False)
        senses = "Visión Normal (sin visión en la oscuridad)"
        if has_darkvision:
            if "36m" in sub_traits or "superior" in sub_traits.lower() or "drow" in self.char_subspecies.lower() or "duergar" in self.char_subspecies.lower() or "profundidades" in self.char_subspecies.lower():
                senses = "Visión en la Oscuridad Superior (36 m)"
            else:
                senses = "Visión en la Oscuridad (18 m)"

        new_char = CharacterSheet(
            name=self.char_name.strip() or "Nuevo Héroe",
            char_class=self.char_class,
            subclass="",
            level=1,
            race=display_race,
            background=self.char_background,
            alignment=self.char_alignment,
            senses=senses,
            portrait_path=self.char_portrait_path,
            xp=0,
            hp_current=level1_hp,
            hp_max=level1_hp,
            hit_dice_max=1,
            hit_dice_current=1,
            hit_dice_faces=CLASS_DEFAULTS[self.char_class]["hit_dice"],
            armor_class=ca,
            initiative_bonus=des_mod,
            speed=speed,
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
