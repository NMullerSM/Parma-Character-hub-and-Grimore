"""
Constructor Estándar de Personajes D&D 5e en 7 Fases (StandardBuilderDialog).
Consumo dinámico de Open Knowledge Format (OKF) con filtrado de manuales (PHB 2024, TCE, XGE)
y cumplimiento estricto de la Ley de Hick (reducción de carga cognitiva y eliminación de saturación de iconos).

Fase 1: Configuración de Reglas y Fuentes Oficiales (PHB 2024/2014, Tasha TCE, Xanathar XGE, Hitos vs XP, PG fijos vs manuales)
Fase 2: Especie y Linajes (Velocidad, tamaño, visión en la oscuridad y rasgos)
Fase 3: Clase y Progresión (Niveles 1-20, dado de golpe, salvaciones y subclases dinámicas OKF)
Fase 4: Atributos con Matriz Interactiva (Point Buy 27 pts, Standard Array, 4d6, Manual)
Fase 5: Trasfondo, Dotes de Origen, Alineamiento e Identidad Gráfica
Fase 6: Equipamiento Inicial, Armas y Monedero
Fase 7: Conjuros, CD de Salvación y Grimorio de Clase
"""
import os
import flet as ft
from typing import Callable, Optional, Dict, Any, List

from ...core.models import CharacterSheet, CharacterFeature, WeaponAction, SpellSlotTier
from ...core.okf_engine import OkfEngine
from ...core.db import DatabaseManager
from ...core.rules import calc_modifier, calc_proficiency_bonus, CLASS_CASTING_ABILITY
from ..theme import (
    TTUI_BG_CANVAS, TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD,
    TTUI_GOLD_LIGHT, TTUI_CRIMSON, TTUI_PARCHMENT, TTUI_RUNIC_GREY,
    BG_INPUT, BG_CARD, BG_CARD_ALT, BORDER_DIM, BORDER_GOLD, COLOR_GREEN,
    create_badge
)

from .builder_header import BuilderHeader
from .builder_stepper import BuilderStepper
from .ability_matrix import AbilityMatrix
from .okf_drawer import OkfDrawer


class StandardBuilderDialog:
    def __init__(
        self,
        page: ft.Page,
        okf_engine: OkfEngine,
        on_character_created: Callable[[CharacterSheet], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.okf = okf_engine
        self.on_character_created = on_character_created
        self.on_cancel = on_cancel

        self.current_step = 1

        # Preferencias de reglas y fuentes de conocimiento (Fase 1)
        self.rules_edition = "2024"  # "2024" o "2014"
        self.include_tasha = True
        self.include_xanathar = True
        self.advancement_type = "milestone"  # "milestone" o "xp"
        self.hp_type = "fixed"  # "fixed" o "manual"
        self.encumbrance_rule = "standard"  # "off", "standard", "variant"

        # Estado del personaje en construcción
        self.char_name = "Nuevo Aventurero"
        self.char_level = 1
        self.char_class = "Guerrero"
        self.char_subclass = ""
        self.char_species = "Humano"
        self.char_subspecies = "Estándar"
        self.char_background = "Soldado"
        self.char_alignment = "Neutral Bueno"
        self.char_portrait_path = ""

        # Bonos de trasfondo (+2 y +1)
        self.bg_plus2 = "FUE"
        self.bg_plus1 = "CON"

        # Atributos base
        self.raw_scores = {"FUE": 15, "DES": 14, "CON": 13, "INT": 12, "SAB": 10, "CAR": 8}

        # Equipo y monedero
        self.starting_gold = 100
        self.equipment_mode = "pack"  # "pack" o "gold"
        self.currencies = {"CP": 0, "SP": 0, "EP": 0, "GP": 15, "PP": 0}

        # Componentes modulares
        self.header = BuilderHeader(
            char_name=self.char_name,
            char_class=self.char_class,
            char_species=self.char_species,
            char_level=self.char_level,
            hp_max=12,
            armor_class=15,
            portrait_path=self.char_portrait_path
        )
        self.stepper = BuilderStepper(
            current_step=1,
            on_step_change=self._go_to_step
        )
        self.drawer = OkfDrawer(
            okf_engine=self.okf,
            on_select_item=self._on_item_selected_from_drawer
        )
        self.ability_matrix = AbilityMatrix(
            raw_scores=self.raw_scores,
            bg_plus2=self.bg_plus2,
            bg_plus1=self.bg_plus1,
            mode="point_buy",
            on_scores_changed=self._on_scores_changed
        )

        # FilePicker para foto de retrato
        self.portrait_picker = ft.FilePicker(on_result=self._on_portrait_selected)
        if self.portrait_picker not in self.page.overlay:
            self.page.overlay.append(self.portrait_picker)

        self.content_container = ft.Container(expand=True, padding=8)
        self._build_dialog()

    @property
    def allowed_sources(self) -> List[str]:
        """Calcula dinámicamente las fuentes oficiales permitidas según la configuración."""
        sources = [self.rules_edition]
        if self.include_tasha:
            sources.append("tasha")
        if self.include_xanathar:
            sources.append("xanathar")
        return sources

    def show(self):
        self.current_step = 1
        self._update_view()
        self.page.open(self.dialog)

    def close(self):
        if self.on_cancel:
            self.on_cancel()
        self.page.close(self.dialog)

    def _go_to_step(self, step_idx: int):
        self.current_step = step_idx
        self._update_view()

    def _on_scores_changed(self, new_scores: Dict[str, int]):
        self.raw_scores = new_scores
        self._recalc_header_stats()

    def _get_active_class_info(self) -> Dict[str, Any]:
        """Recupera la información de la clase activa desde OKF."""
        classes = self.okf.get_classes(self.allowed_sources)
        for c in classes:
            if c["nombre"] == self.char_class:
                return c
        return classes[0] if classes else {
            "hit_dice": 8, "saves": ["CON", "FUE"], "armor": "Ligeras", "weapons": "Sencillas"
        }

    def _get_active_species_info(self) -> Dict[str, Any]:
        """Recupera la información de la especie activa desde OKF."""
        species = self.okf.get_species(self.allowed_sources)
        for s in species:
            if s["nombre"] == self.char_species:
                return s
        return species[0] if species else {
            "velocidad": "9 m", "darkvision": False, "tamano": "Mediano", "rasgos_principales": ""
        }

    def _recalc_header_stats(self):
        con_score = self.raw_scores.get("CON", 10) + (2 if self.bg_plus2 == "CON" else (1 if self.bg_plus1 == "CON" else 0))
        des_score = self.raw_scores.get("DES", 10) + (2 if self.bg_plus2 == "DES" else (1 if self.bg_plus1 == "DES" else 0))
        con_mod = calc_modifier(con_score)
        des_mod = calc_modifier(des_score)

        c_info = self._get_active_class_info()
        hd = c_info.get("hit_dice", 8)
        hp = max(1, hd + con_mod) + (max(0, self.char_level - 1) * max(1, (hd // 2) + 1 + con_mod))
        if "colinas" in self.char_subspecies.lower():
            hp += self.char_level
        ac = 10 + des_mod

        display_class = f"{self.char_class} ({self.char_subclass})" if self.char_subclass else self.char_class
        display_species = f"{self.char_species} ({self.char_subspecies})" if self.char_subspecies else self.char_species

        self.header.update_identity(
            name=self.char_name,
            char_class=display_class,
            species=display_species,
            level=self.char_level,
            hp=hp,
            ac=ac,
            portrait=self.char_portrait_path
        )

    def _build_dialog(self):
        self.btn_prev = ft.OutlinedButton(
            text="Anterior",
            style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, side=ft.BorderSide(1, TTUI_BORDER_SLATE)),
            on_click=self._prev_step,
            visible=False
        )
        self.btn_next = ft.ElevatedButton(
            text="Siguiente Fase",
            bgcolor=TTUI_GOLD,
            color="#000000",
            style=ft.ButtonStyle(bgcolor=TTUI_GOLD, color="#000000"),
            on_click=self._next_step
        )

        self.btn_exit = ft.TextButton(
            text="Cancelar / Salir",
            style=ft.ButtonStyle(color=TTUI_RUNIC_GREY),
            tooltip="Cerrar el creador de personajes sin guardar",
            on_click=lambda e: self.close()
        )

        center_body = ft.Row(
            controls=[
                self.content_container,
                self.drawer
            ],
            expand=True,
            spacing=4
        )

        self.dialog = ft.AlertDialog(
            modal=False,
            title=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(content=self.header, expand=True),
                            ft.IconButton(
                                ft.Icons.CLOSE,
                                icon_color=TTUI_RUNIC_GREY,
                                tooltip="Cerrar creador de personajes",
                                on_click=lambda e: self.close()
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    self.stepper
                ],
                spacing=8
            ),
            content=ft.Container(
                content=center_body,
                width=1040,
                height=530
            ),
            actions=[
                ft.Row([self.btn_prev, self.btn_exit], spacing=10),
                self.btn_next
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _prev_step(self, e):
        if self.current_step > 1:
            self.current_step -= 1
            self._update_view()

    def _next_step(self, e):
        if self.current_step < 7:
            self.current_step += 1
            self._update_view()
        else:
            self._finish_and_forge()

    def _update_view(self):
        self.stepper.set_current_step(self.current_step)
        self.btn_prev.visible = (self.current_step > 1)

        if self.current_step == 7:
            self.btn_next.text = "Forjar y Cargar Personaje"
            self.btn_next.bgcolor = COLOR_GREEN
            self.btn_next.color = "#ffffff"
            self.btn_next.style = ft.ButtonStyle(bgcolor=COLOR_GREEN, color="#ffffff")
        else:
            self.btn_next.text = "Siguiente Fase"
            self.btn_next.bgcolor = TTUI_GOLD
            self.btn_next.color = "#000000"
            self.btn_next.style = ft.ButtonStyle(bgcolor=TTUI_GOLD, color="#000000")

        self._recalc_header_stats()

        if self.current_step == 1:
            self._render_step1_rules()
        elif self.current_step == 2:
            self._render_step2_species()
        elif self.current_step == 3:
            self._render_step3_class()
        elif self.current_step == 4:
            self._render_step4_abilities()
        elif self.current_step == 5:
            self._render_step5_description()
        elif self.current_step == 6:
            self._render_step6_equipment()
        elif self.current_step == 7:
            self._render_step7_spells()

        if self.page:
            self.page.update()

    # --- FASE 1: REGLAS & FUENTES ---
    def _render_step1_rules(self):
        def on_edition_change(e):
            self.rules_edition = list(e.control.selected)[0]
            self._update_view()

        def on_tasha_toggle(e):
            self.include_tasha = e.control.value
            self._update_view()

        def on_xanathar_toggle(e):
            self.include_xanathar = e.control.value
            self._update_view()

        rules_view = ft.ListView(
            controls=[
                ft.Text("Preferencias de Reglas y Fuentes OKF", size=15, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ft.Text("Selecciona los manuales de referencia y las directrices de mesa que gobernarán a tu aventurero:", size=12, color=TTUI_RUNIC_GREY),
                ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                ft.Row([
                    ft.Text("Edición Oficial:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_PARCHMENT, width=200),
                    ft.SegmentedButton(
                        selected={self.rules_edition},
                        segments=[
                            ft.Segment(value="2024", label=ft.Text("PHB 2024 (Remastered)")),
                            ft.Segment(value="2014", label=ft.Text("PHB 2014 (Legacy)")),
                        ],
                        on_change=on_edition_change
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Manuales Suplementarios:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_PARCHMENT, width=200),
                    ft.Row([
                        ft.Checkbox(
                            label="Caldero de Tasha para Todo (TCE)",
                            value=self.include_tasha,
                            on_change=on_tasha_toggle,
                            active_color=TTUI_GOLD
                        ),
                        ft.Checkbox(
                            label="Guía de Xanathar para Todo (XGE)",
                            value=self.include_xanathar,
                            on_change=on_xanathar_toggle,
                            active_color=TTUI_GOLD
                        )
                    ], spacing=12)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                ft.Row([
                    ft.Text("Avance de Nivel:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_PARCHMENT, width=200),
                    ft.SegmentedButton(
                        selected={self.advancement_type},
                        segments=[
                            ft.Segment(value="milestone", label=ft.Text("Por Hitos (Narrativo)")),
                            ft.Segment(value="xp", label=ft.Text("Por Puntos de PX")),
                        ],
                        on_change=lambda e: setattr(self, "advancement_type", list(e.control.selected)[0])
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Cálculo de Puntos de Golpe:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_PARCHMENT, width=200),
                    ft.SegmentedButton(
                        selected={self.hp_type},
                        segments=[
                            ft.Segment(value="fixed", label=ft.Text("Fijo (Promedio Oficial)")),
                            ft.Segment(value="manual", label=ft.Text("Tirada Manual")),
                        ],
                        on_change=lambda e: setattr(self, "hp_type", list(e.control.selected)[0])
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Capacidad de Carga:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_PARCHMENT, width=200),
                    ft.SegmentedButton(
                        selected={self.encumbrance_rule},
                        segments=[
                            ft.Segment(value="standard", label=ft.Text("Estándar (15 × FUE)")),
                            ft.Segment(value="variant", label=ft.Text("Variante de Carga")),
                            ft.Segment(value="off", label=ft.Text("Desactivada")),
                        ],
                        on_change=lambda e: setattr(self, "encumbrance_rule", list(e.control.selected)[0])
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=12,
            expand=True
        )
        self.content_container.content = rules_view

    # --- FASE 2: ESPECIE & LINEAGES ---
    def _render_step2_species(self):
        species_list = self.okf.get_species(self.allowed_sources)
        if not species_list:
            self.content_container.content = ft.Text("No se encontraron especies en OKF con las fuentes seleccionadas.", color=TTUI_RUNIC_GREY)
            return

        # Asegurar especie válida
        species_names = [s["nombre"] for s in species_list]
        if self.char_species not in species_names:
            self.char_species = species_names[0]

        species_cards = []
        for s_info in species_list:
            sp_name = s_info["nombre"]
            is_sel = (self.char_species == sp_name)
            speed = s_info.get("velocidad", "9 m")
            size = s_info.get("tamano", "Mediano")
            has_dv = s_info.get("darkvision", False)
            traits = s_info.get("rasgos_principales", "")

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(sp_name, size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT if is_sel else "#ffffff"),
                        create_badge(speed, bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD if is_sel else TTUI_BORDER_SLATE)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"Tamaño: {size} • Visión: {'Oscuridad' if has_dv else 'Normal'}", size=11, color=TTUI_RUNIC_GREY),
                    ft.Text(traits, size=10, color=TTUI_PARCHMENT, max_lines=2, no_wrap=False),
                    ft.TextButton(
                        "Ver en OKF",
                        style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, padding=ft.padding.all(2)),
                        on_click=lambda e, s_ent=s_info: self.drawer.show_entity(s_ent)
                    )
                ], spacing=3),
                padding=8,
                width=220,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, TTUI_GOLD if is_sel else TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(6),
                on_click=lambda e, sn=sp_name: self._set_species(sn)
            )
            species_cards.append(card)

        # Cargar linajes de la especie activa desde OKF
        lineages = self.okf.get_lineages(self.char_species, self.allowed_sources)
        sub_chips = []

        if lineages:
            lineage_names = [l["nombre"] for l in lineages]
            if self.char_subspecies not in lineage_names:
                self.char_subspecies = lineage_names[0]

            for lin in lineages:
                l_name = lin["nombre"]
                is_sub_sel = (self.char_subspecies == l_name)
                sub_chip = ft.Container(
                    content=ft.Row([
                        ft.Text(f"● " if is_sub_sel else "○ ", size=12, color=TTUI_GOLD if is_sub_sel else TTUI_RUNIC_GREY),
                        ft.Text(l_name, size=11, weight=ft.FontWeight.BOLD if is_sub_sel else ft.FontWeight.NORMAL, color=TTUI_GOLD_LIGHT if is_sub_sel else TTUI_PARCHMENT),
                        ft.TextButton(
                            "Detalles",
                            style=ft.ButtonStyle(color=TTUI_RUNIC_GREY, padding=ft.padding.all(2)),
                            on_click=lambda e, lent=lin: self.drawer.show_entity(lent)
                        )
                    ], spacing=6),
                    bgcolor=BG_CARD_ALT if is_sub_sel else BG_INPUT,
                    border=ft.border.all(1.5 if is_sub_sel else 1, TTUI_GOLD if is_sub_sel else TTUI_BORDER_SLATE),
                    border_radius=ft.border_radius.all(6),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    on_click=lambda e, ln=l_name: self._set_subspecies(ln)
                )
                sub_chips.append(sub_chip)
        else:
            self.char_subspecies = "Estándar"
            sub_chips.append(
                ft.Text("Esta especie no cuenta con variantes o subrazas adicionales en las fuentes activas.", size=11, color=TTUI_RUNIC_GREY)
            )

        self.content_container.content = ft.ListView(
            controls=[
                ft.Text("Selecciona tu Especie Heroica:", size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ft.Row(controls=species_cards, wrap=True, spacing=8),
                ft.Text(f"Linajes / Subrazas de {self.char_species}:", size=13, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ft.Column(controls=sub_chips, spacing=6)
            ],
            spacing=10,
            expand=True
        )

    def _set_species(self, sp: str):
        self.char_species = sp
        lineages = self.okf.get_lineages(sp, self.allowed_sources)
        self.char_subspecies = lineages[0]["nombre"] if lineages else "Estándar"
        self._update_view()

    def _set_subspecies(self, sub: str):
        self.char_subspecies = sub
        self._update_view()

    # --- FASE 3: CLASE & PROGRESIÓN ---
    def _render_step3_class(self):
        classes = self.okf.get_classes(self.allowed_sources)
        if not classes:
            self.content_container.content = ft.Text("No se encontraron clases en OKF.", color=TTUI_RUNIC_GREY)
            return

        class_names = [c["nombre"] for c in classes]
        if self.char_class not in class_names:
            self.char_class = class_names[0]

        class_cards = []
        for c_info in classes:
            c_name = c_info["nombre"]
            is_sel = (self.char_class == c_name)
            hd = c_info.get("hit_dice", 8)
            saves = c_info.get("saves", [])
            armor = c_info.get("armor", "")

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(c_name, size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT if is_sel else "#ffffff"),
                        create_badge(f"d{hd}", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD if is_sel else TTUI_BORDER_SLATE)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"Salvaciones: {', '.join(saves)}", size=11, color=TTUI_RUNIC_GREY),
                    ft.Text(f"Armadura: {armor}", size=10, color=TTUI_PARCHMENT, max_lines=1, no_wrap=True),
                    ft.TextButton(
                        "Ver en OKF",
                        style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, padding=ft.padding.all(2)),
                        on_click=lambda e, cent=c_info: self.drawer.show_entity(cent)
                    )
                ], spacing=3),
                padding=8,
                width=220,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, TTUI_GOLD if is_sel else TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(6),
                on_click=lambda e, cn=c_name: self._set_class(cn)
            )
            class_cards.append(card)

        # Selector de Nivel
        level_opts = [ft.dropdown.Option(str(i), f"Nivel {i}") for i in range(1, 21)]
        level_dd = ft.Dropdown(
            label="Nivel de Clase",
            value=str(self.char_level),
            options=level_opts,
            width=130,
            border_color=BORDER_GOLD,
            on_change=lambda e: self._set_level(int(e.control.value))
        )

        # Subclases dinámicas desde OKF
        active_class_info = self._get_active_class_info()
        sub_req = active_class_info.get("subclass_level", 3)
        can_have_sub = (self.char_level >= sub_req)

        okf_subclasses = self.okf.get_subclasses(self.char_class, self.allowed_sources, max_level=self.char_level)
        sub_opts = [ft.dropdown.Option("", "Sin subclase seleccionada")]
        for s in okf_subclasses:
            sub_opts.append(ft.dropdown.Option(s["nombre"], f"{s['nombre']} ({s['fuente']})"))

        sub_dd = ft.Dropdown(
            label=f"Arquetipo / Subclase (Desbloqueado en Niv {sub_req})",
            value=self.char_subclass if can_have_sub else "",
            options=sub_opts,
            width=380,
            disabled=not can_have_sub,
            border_color=BORDER_GOLD if can_have_sub else TTUI_BORDER_SLATE,
            on_change=lambda e: self._set_subclass(e.control.value)
        )

        controls_list = [
            ft.Row([level_dd, sub_dd], spacing=12),
            ft.Text("Selecciona tu Clase Heroica:", size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
            ft.Row(controls=class_cards, wrap=True, spacing=8),
        ]

        # Si hay una subclase seleccionada, ofrecer verla en OKF
        if can_have_sub and self.char_subclass:
            sub_ent = next((s for s in okf_subclasses if s["nombre"] == self.char_subclass), None)
            if sub_ent:
                controls_list.insert(1, ft.Row([
                    ft.Text(f"Subclase seleccionada: {self.char_subclass}", size=12, color=TTUI_GOLD_LIGHT),
                    ft.TextButton(
                        "Ver detalles de subclase en OKF",
                        style=ft.ButtonStyle(color=TTUI_GOLD),
                        on_click=lambda e, sent=sub_ent: self.drawer.show_entity(sent)
                    )
                ], spacing=10))

        self.content_container.content = ft.ListView(
            controls=controls_list,
            spacing=10,
            expand=True
        )

    def _set_class(self, cn: str):
        self.char_class = cn
        self.char_subclass = ""
        self._update_view()

    def _set_level(self, lvl: int):
        self.char_level = lvl
        active_class_info = self._get_active_class_info()
        sub_req = active_class_info.get("subclass_level", 3)
        if self.char_level < sub_req:
            self.char_subclass = ""
        self._update_view()

    def _set_subclass(self, sub_name: str):
        self.char_subclass = sub_name
        self._update_view()

    # --- FASE 4: ATRIBUTOS ---
    def _render_step4_abilities(self):
        self.ability_matrix.set_background_bonuses(self.bg_plus2, self.bg_plus1)
        self.content_container.content = self.ability_matrix

    # --- FASE 5: TRASFONDO & IDENTIDAD ---
    def _render_step5_description(self):
        backgrounds = self.okf.get_backgrounds(self.allowed_sources)
        if not backgrounds:
            self.content_container.content = ft.Text("No se encontraron trasfondos en OKF.", color=TTUI_RUNIC_GREY)
            return

        bg_names = [b["nombre"] for b in backgrounds]
        if self.char_background not in bg_names:
            self.char_background = bg_names[0]

        bg_cards = []
        for b_info in backgrounds:
            bg_name = b_info["nombre"]
            is_sel = (self.char_background == bg_name)
            feat = b_info.get("dote_concedida", "Dote de Origen")
            stats = b_info.get("caracteristicas_clave", "")
            skills = b_info.get("habilidades_competentes", "")

            card = ft.Container(
                content=ft.Column([
                    ft.Text(bg_name, size=13, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT if is_sel else "#ffffff"),
                    ft.Text(f"Dote: {feat}", size=11, color=TTUI_GOLD, weight=ft.FontWeight.W_600),
                    ft.Text(f"Atributos: {stats}", size=10, color=TTUI_PARCHMENT, max_lines=1),
                    ft.Text(f"Habilidades: {skills}", size=10, color=TTUI_RUNIC_GREY, max_lines=1),
                    ft.TextButton(
                        "Ver en OKF",
                        style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, padding=ft.padding.all(2)),
                        on_click=lambda e, bent=b_info: self.drawer.show_entity(bent)
                    )
                ], spacing=2),
                padding=8,
                width=220,
                bgcolor=BG_CARD_ALT if is_sel else BG_INPUT,
                border=ft.border.all(1.5 if is_sel else 1, TTUI_GOLD if is_sel else TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(6),
                on_click=lambda e, bn=bg_name: self._set_background(bn)
            )
            bg_cards.append(card)

        stat_opts = [
            ft.dropdown.Option("FUE", "Fuerza (FUE)"),
            ft.dropdown.Option("DES", "Destreza (DES)"),
            ft.dropdown.Option("CON", "Constitución (CON)"),
            ft.dropdown.Option("INT", "Inteligencia (INT)"),
            ft.dropdown.Option("SAB", "Sabiduría (SAB)"),
            ft.dropdown.Option("CAR", "Carisma (CAR)"),
        ]

        def on_p2_change(e):
            self.bg_plus2 = e.control.value
            if self.bg_plus1 == self.bg_plus2:
                for s in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
                    if s != self.bg_plus2:
                        self.bg_plus1 = s
                        break
            self._update_view()

        def on_p1_change(e):
            self.bg_plus1 = e.control.value
            if self.bg_plus1 == self.bg_plus2:
                for s in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
                    if s != self.bg_plus1:
                        self.bg_plus2 = s
                        break
            self._update_view()

        bonuses_row = ft.Row([
            ft.Dropdown(label="Bono de Trasfondo +2", value=self.bg_plus2, options=stat_opts, width=200, border_color=BORDER_GOLD, on_change=on_p2_change),
            ft.Dropdown(label="Bono de Trasfondo +1", value=self.bg_plus1, options=stat_opts, width=200, border_color=TTUI_BORDER_SLATE, on_change=on_p1_change),
        ], spacing=12)

        name_field = ft.TextField(
            label="Nombre del Aventurero",
            value=self.char_name,
            border_color=BORDER_GOLD,
            expand=True,
            on_change=lambda e: (setattr(self, "char_name", e.control.value), self._recalc_header_stats())
        )

        align_dd = ft.Dropdown(
            label="Alineamiento",
            value=self.char_alignment,
            width=180,
            options=[
                ft.dropdown.Option("Legal Bueno", "Legal Bueno"),
                ft.dropdown.Option("Neutral Bueno", "Neutral Bueno"),
                ft.dropdown.Option("Caótico Bueno", "Caótico Bueno"),
                ft.dropdown.Option("Legal Neutral", "Legal Neutral"),
                ft.dropdown.Option("Neutral", "Neutral Auténtico"),
                ft.dropdown.Option("Caótico Neutral", "Caótico Neutral"),
                ft.dropdown.Option("Legal Maligno", "Legal Maligno"),
            ],
            border_color=TTUI_BORDER_SLATE,
            on_change=lambda e: setattr(self, "char_alignment", e.control.value)
        )

        btn_portrait = ft.ElevatedButton(
            text="Subir Foto de Disco...",
            icon=ft.Icons.UPLOAD_FILE,
            style=ft.ButtonStyle(bgcolor=BG_INPUT, color=TTUI_GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
            on_click=lambda e: self.portrait_picker.pick_files(
                dialog_title="Seleccionar Retrato",
                allowed_extensions=["png", "jpg", "jpeg", "webp"]
            )
        )

        self.content_container.content = ft.ListView(
            controls=[
                ft.Row([name_field, align_dd, btn_portrait], spacing=8),
                bonuses_row,
                ft.Text("Selecciona tu Trasfondo Oficial (Otorga Dote de Origen en PHB 2024):", size=14, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ft.Row(controls=bg_cards, wrap=True, spacing=8),
            ],
            spacing=10,
            expand=True
        )

    def _set_background(self, bn: str):
        self.char_background = bn
        self._update_view()

    def _on_portrait_selected(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            src = e.files[0].path
            if src:
                db = DatabaseManager()
                saved_path = db.save_portrait_file(src, self.char_name)
                self.char_portrait_path = saved_path
                self._update_view()

    # --- FASE 6: EQUIPO & RIQUEZA ---
    def _render_step6_equipment(self):
        eq_view = ft.ListView(
            controls=[
                ft.Text("Equipamiento Inicial & Monedero", size=15, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ft.Text("Elige si inicias con el paquete estándar de tu clase o con oro inicial para comprar en tienda:", size=12, color=TTUI_RUNIC_GREY),
                ft.SegmentedButton(
                    selected={self.equipment_mode},
                    segments=[
                        ft.Segment(value="pack", label=ft.Text("Paquete de Equipo de Clase")),
                        ft.Segment(value="gold", label=ft.Text(f"Oro Inicial ({self.starting_gold} PO)")),
                    ],
                    on_change=lambda e: (setattr(self, "equipment_mode", list(e.control.selected)[0]), self._update_view())
                ),
                ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                ft.Container(
                    content=ft.Row([
                        create_badge(f"PO (Oro): {self.currencies['GP']} po", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD),
                        create_badge(f"PP (Plata): {self.currencies['SP']} sp", bg_color=BG_INPUT, text_color=TTUI_PARCHMENT, border_color=TTUI_BORDER_SLATE),
                        create_badge(f"PC (Cobre): {self.currencies['CP']} cp", bg_color=BG_INPUT, text_color=TTUI_RUNIC_GREY, border_color=TTUI_BORDER_SLATE),
                    ], spacing=10),
                    bgcolor=BG_CARD,
                    padding=10,
                    border_radius=ft.border_radius.all(6)
                ),
                ft.Text(
                    f"Armas y armaduras asignadas automáticamente para {self.char_class}: Armadura según competencias, armas de clase y bolsa de explorador.",
                    size=12,
                    color=TTUI_PARCHMENT
                )
            ],
            spacing=10,
            expand=True
        )
        self.content_container.content = eq_view

    # --- FASE 7: CONJUROS & ESPACIOS ---
    def _render_step7_spells(self):
        cast_stat = CLASS_CASTING_ABILITY.get(self.char_class, "CAR")
        is_caster = (self.char_class in ["Bardo", "Clérigo", "Druida", "Hechicero", "Brujo", "Mago", "Paladín", "Explorador"])

        if not is_caster:
            spells_view = ft.Container(
                content=ft.Column([
                    ft.Text(f"{self.char_class} es una clase marcial no lanzadora de conjuros.", size=15, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                    ft.Text("Tu personaje utilizará proezas físicas, maniobras y ataques marciales.", size=12, color=TTUI_RUNIC_GREY),
                    ft.Text("Puedes completar tu personaje directamente pulsando el botón inferior.", size=12, color=TTUI_PARCHMENT),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                expand=True
            )
            self.content_container.content = spells_view
            return

        cast_score = self.raw_scores.get(cast_stat, 10) + (2 if self.bg_plus2 == cast_stat else (1 if self.bg_plus1 == cast_stat else 0))
        cast_mod = calc_modifier(cast_score)
        pb = calc_proficiency_bonus(self.char_level)
        spell_dc = 8 + pb + cast_mod
        spell_atk = f"+{pb + cast_mod}" if (pb + cast_mod) >= 0 else str(pb + cast_mod)

        stat_banner = ft.Container(
            content=ft.Row([
                create_badge(f"Aptitud: {cast_stat} ({cast_score})", bg_color=BG_INPUT, text_color=TTUI_GOLD_LIGHT, border_color=BORDER_GOLD),
                create_badge(f"CD de Salvación: CD {spell_dc}", bg_color=BG_INPUT, text_color="#a855f7", border_color="#a855f7"),
                create_badge(f"Ataque Mágico: {spell_atk}", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD),
            ], spacing=10),
            bgcolor=BG_INPUT,
            padding=10,
            border_radius=ft.border_radius.all(6),
            border=ft.border.all(1, TTUI_BORDER_SLATE)
        )

        # Buscar conjuros de nivel 0 y 1 para la clase activa en OKF
        spells_okf = self.okf.get_spells_for_class(
            class_name=self.char_class,
            max_spell_level=1,
            min_spell_level=0,
            allowed_sources=self.allowed_sources
        )

        spell_chips = []
        for sp in spells_okf[:24]:
            sp_name = sp.get("nombre", "")
            sp_lvl = sp.get("nivel", 0)
            chip = ft.Container(
                content=ft.Row([
                    ft.Text(f"Niv {sp_lvl}" if sp_lvl > 0 else "Truco", size=10, color=TTUI_GOLD, weight=ft.FontWeight.BOLD),
                    ft.Text(sp_name, size=11, color=TTUI_PARCHMENT),
                ], spacing=6),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border=ft.border.all(1, TTUI_BORDER_SLATE),
                border_radius=ft.border_radius.all(4),
                on_click=lambda e, sent=sp: self.drawer.show_entity(sent)
            )
            spell_chips.append(chip)

        spells_view = ft.ListView(
            controls=[
                ft.Text(f"Lanzamiento de Conjuros ({self.char_class})", size=15, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                stat_banner,
                ft.Text("Conjuros y trucos disponibles en tu grimorio de clase (haz clic para inspeccionar en OKF):", size=12, color=TTUI_PARCHMENT),
                ft.Row(controls=spell_chips, wrap=True, spacing=6)
            ],
            spacing=10,
            expand=True
        )
        self.content_container.content = spells_view

    def _on_item_selected_from_drawer(self, item: Dict[str, Any]):
        pass

    # --- FORJA FINAL ---
    def _finish_and_forge(self):
        # 1. Atributos finales
        final_abilities = {}
        for s in ["FUE", "DES", "CON", "INT", "SAB", "CAR"]:
            base = self.raw_scores.get(s, 10)
            add = (2 if self.bg_plus2 == s else (1 if self.bg_plus1 == s else 0))
            final_abilities[s] = base + add

        con_mod = calc_modifier(final_abilities["CON"])
        des_mod = calc_modifier(final_abilities["DES"])

        # 2. Información de clase desde OKF
        class_info = self._get_active_class_info()
        hd = class_info.get("hit_dice", 8)
        hp = max(1, hd + con_mod) + (max(0, self.char_level - 1) * max(1, (hd // 2) + 1 + con_mod))
        if "colinas" in self.char_subspecies.lower():
            hp += self.char_level

        ca = 10 + des_mod
        pb = calc_proficiency_bonus(self.char_level)

        # 3. Información de especie y linaje desde OKF
        spec_info = self._get_active_species_info()
        speed = spec_info.get("velocidad", "9 m")
        has_dv = spec_info.get("darkvision", False)
        senses = "Visión Normal (sin visión en la oscuridad)"
        if has_dv or "drow" in self.char_subspecies.lower() or "duergar" in self.char_subspecies.lower():
            if "drow" in self.char_subspecies.lower() or "duergar" in self.char_subspecies.lower():
                senses = "Visión en la Oscuridad Superior (36 m)"
            else:
                senses = "Visión en la Oscuridad (18 m)"

        # 4. Información de trasfondo desde OKF
        backgrounds = self.okf.get_backgrounds(self.allowed_sources)
        bg_info = next((b for b in backgrounds if b["nombre"] == self.char_background), {})
        feat_name = bg_info.get("dote_concedida", "Dote de Origen")

        display_race = f"{self.char_species} ({self.char_subspecies})" if self.char_subspecies else self.char_species

        features = [
            CharacterFeature(
                name=feat_name,
                source=f"Trasfondo ({self.char_background})",
                description=f"Dote de origen concedida por el trasfondo {self.char_background}.",
                recharge="Pasivo"
            ),
            CharacterFeature(
                name=f"Rasgos de {display_race}",
                source=f"Especie ({display_race})",
                description=spec_info.get("rasgos_principales", ""),
                recharge="Pasivo"
            )
        ]

        if self.char_subclass:
            features.append(
                CharacterFeature(
                    name=f"Arquetipo: {self.char_subclass}",
                    source=f"Subclase ({self.char_class})",
                    description=f"Subclase {self.char_subclass} desbloqueada en nivel {class_info.get('subclass_level', 3)}.",
                    recharge="Pasivo"
                )
            )

        weapons = [
            WeaponAction(name="Espada Corta", attack_bonus=f"+{des_mod + pb}", damage=f"1d6+{des_mod}", damage_type="Perforante", notes="Sutil, Ligera"),
            WeaponAction(name="Daga", attack_bonus=f"+{des_mod + pb}", damage=f"1d4+{des_mod}", damage_type="Perforante", notes="Arrojadiza (6/18m)")
        ]

        slots = {}
        if self.char_class in ["Bardo", "Clérigo", "Druida", "Hechicero", "Mago"]:
            slots["1"] = SpellSlotTier(level=1, total=2 if self.char_level == 1 else 4, current=2 if self.char_level == 1 else 4)
        elif self.char_class == "Brujo":
            slots["1"] = SpellSlotTier(level=1, total=1 if self.char_level == 1 else 2, current=1 if self.char_level == 1 else 2)

        new_char = CharacterSheet(
            name=self.char_name.strip() or "Nuevo Aventurero",
            char_class=self.char_class,
            subclass=self.char_subclass,
            level=self.char_level,
            race=display_race,
            background=self.char_background,
            alignment=self.char_alignment,
            senses=senses,
            portrait_path=self.char_portrait_path,
            xp=0,
            hp_current=hp,
            hp_max=hp,
            hit_dice_max=self.char_level,
            hit_dice_current=self.char_level,
            hit_dice_faces=hd,
            armor_class=ca,
            initiative_bonus=des_mod,
            speed=speed,
            proficiency_bonus=pb,
            abilities=final_abilities,
            saving_throw_profs=class_info.get("saves", []),
            features=features,
            weapons=weapons,
            spell_slots=slots
        )

        self.close()
        if self.on_character_created:
            self.on_character_created(new_char)
