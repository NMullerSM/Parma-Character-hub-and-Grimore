"""
Vista de Compendio & Árbol de Conocimiento Atómico OKF (Open Knowledge Format)
Navegación visual del árbol de categorías: Conjuros (378), Dotes (74), Especies, Trasfondos y Clases.
"""
import flet as ft
from typing import Callable, Optional, Dict, Any, List
from ...core.models import CharacterSheet, SpellItem, CharacterFeature
from ...core.okf_engine import OkfEngine
from ..theme import (
    BG_CARD, BG_CARD_ALT, BG_INPUT, BG_SURFACE, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_AMBER, COLOR_PURPLE,
    COLOR_RED, create_card_container, create_badge
)


class OkfCompendiumView(ft.Container):
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
        self.expand = True

        self.current_category = "conjuro"
        self.search_query = ""
        self.spell_class = "all"
        self.spell_level = "all"
        self.feat_category = "all"

        self._build_ui()

    def update_data(self, new_char: CharacterSheet):
        self.char = new_char
        self._refresh_results()

    def _build_ui(self):
        # 1. Selector de Categoría Principal del Árbol OKF
        categories = [
            ("conjuro", "✨ Conjuros (378)"),
            ("dote", "🌟 Dotes (74)"),
            ("especie", "🧬 Especies & Linajes (11)"),
            ("trasfondo", "📜 Trasfondos (17)"),
            ("clase", "⚔️ Clases & Subclases (13)"),
            ("regla", "📖 Reglas & Mecánicas"),
        ]

        cat_buttons = []
        for cat_id, cat_label in categories:
            is_active = self.current_category == cat_id
            btn = ft.ElevatedButton(
                text=cat_label,
                style=ft.ButtonStyle(
                    bgcolor=GOLD_PRIMARY if is_active else BG_INPUT,
                    color="#111111" if is_active else GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if is_active else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e, cid=cat_id: self._select_category(cid)
            )
            cat_buttons.append(btn)

        self.category_row = ft.Row(
            controls=cat_buttons,
            wrap=True,
            spacing=8
        )

        # 2. Barra de Búsqueda y Filtros Específicos
        self.search_input = ft.TextField(
            hint_text="Buscar por nombre, escuela, requisito o etiqueta...",
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            color="#f0f2f5",
            cursor_color=GOLD_LIGHT,
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            expand=True,
            height=42,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_change=self._on_search_change
        )

        # Filtro de Clase para Conjuros
        self.class_dropdown = ft.Dropdown(
            label="Clase",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            width=150,
            value=self.spell_class,
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            options=[
                ft.dropdown.Option("all", "Todas"),
                ft.dropdown.Option("Bardo", "Bardo"),
                ft.dropdown.Option("Brujo", "Brujo"),
                ft.dropdown.Option("Clérigo", "Clérigo"),
                ft.dropdown.Option("Druida", "Druida"),
                ft.dropdown.Option("Explorador", "Explorador"),
                ft.dropdown.Option("Guerrero", "Guerrero"),
                ft.dropdown.Option("Hechicero", "Hechicero"),
                ft.dropdown.Option("Mago", "Mago"),
                ft.dropdown.Option("Paladín", "Paladín"),
                ft.dropdown.Option("Pícaro", "Pícaro"),
            ],
            on_change=self._on_class_change
        )

        # Filtro de Nivel para Conjuros
        self.level_dropdown = ft.Dropdown(
            label="Nivel",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            width=130,
            value=self.spell_level,
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            options=[
                ft.dropdown.Option("all", "Todos"),
                ft.dropdown.Option("0", "Trucos"),
                ft.dropdown.Option("1", "Niv 1"),
                ft.dropdown.Option("2", "Niv 2"),
                ft.dropdown.Option("3", "Niv 3"),
                ft.dropdown.Option("4", "Niv 4"),
                ft.dropdown.Option("5", "Niv 5"),
                ft.dropdown.Option("6", "Niv 6"),
                ft.dropdown.Option("7", "Niv 7"),
                ft.dropdown.Option("8", "Niv 8"),
                ft.dropdown.Option("9", "Niv 9"),
            ],
            on_change=self._on_level_change
        )

        self.filter_bar = ft.Row(
            controls=[self.search_input, self.class_dropdown, self.level_dropdown],
            wrap=True,
            spacing=8
        )

        # 3. Lista de Tarjetas OKF
        self.cards_column = ft.Column(spacing=10)
        self._refresh_results()

        self.content = ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("🌳 Árbol de Conocimiento Atómico OKF", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.Text(
                                "Base de conocimiento íntegra del Manual del Jugador 2024: 378 conjuros con sus clases, 74 dotes y reglas.",
                                size=12,
                                color=TEXT_MUTED
                            ),
                            ft.Divider(color=BORDER_DIM, height=1),
                            self.category_row,
                            self.filter_bar,
                        ],
                        spacing=8
                    ),
                    bgcolor=BG_SURFACE,
                    border=ft.border.all(1, BORDER_DIM),
                    border_radius=ft.border_radius.all(8),
                    padding=12
                ),
                self.cards_column
            ],
            spacing=10,
            expand=True
        )

    def _select_category(self, cat_id: str):
        self.current_category = cat_id
        # Mostrar u ocultar filtros según categoría
        is_conjuro = (cat_id == "conjuro")
        self.class_dropdown.visible = is_conjuro
        self.level_dropdown.visible = is_conjuro
        self._build_ui()
        if self.page:
            self.page.update()

    def _on_search_change(self, e):
        self.search_query = e.control.value
        self._refresh_results()
        if self.page:
            self.page.update()

    def _on_class_change(self, e):
        self.spell_class = e.control.value
        self._refresh_results()
        if self.page:
            self.page.update()

    def _on_level_change(self, e):
        self.spell_level = e.control.value
        self._refresh_results()
        if self.page:
            self.page.update()

    def _refresh_results(self):
        self.cards_column.controls.clear()

        # Obtener resultados según categoría
        lvl = None if self.spell_level == "all" else int(self.spell_level)
        cls_filter = None if self.spell_class == "all" else self.spell_class

        target_type = self.current_category
        # En caso de especie o clase, mapear subclases y linajes
        extra_types = []
        if target_type == "especie":
            extra_types = ["linaje"]
        elif target_type == "clase":
            extra_types = ["subclase"]

        results = self.okf.search_entities(
            query=self.search_query,
            tipo=target_type if not extra_types else None,
            nivel=lvl if target_type == "conjuro" else None,
            clase=cls_filter if target_type == "conjuro" else None,
            limit=60
        )

        if extra_types:
            results = [r for r in results if r.get("tipo") in [target_type, *extra_types]]

        if not results:
            self.cards_column.controls.append(
                ft.Container(
                    content=ft.Text("No se encontraron entidades que coincidan con la búsqueda.", size=13, color=TEXT_MUTED, italic=True),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            return

        for item in results:
            card = self._render_entity_card(item)
            self.cards_column.controls.append(card)

    def _render_entity_card(self, item: Dict[str, Any]) -> ft.Container:
        eid = item.get("id", "")
        tipo = item.get("tipo", "")
        nombre = item.get("nombre", "")
        nombre_en = item.get("nombre_ingles", "")
        fuente = item.get("fuente", "PHB 2024")
        pagina = item.get("pagina", "")

        # Píldoras de cabecera
        header_pills = [
            create_badge(f"Pág. {pagina}" if pagina else fuente, bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM)
        ]

        # Detalles específicos según tipo
        sub_info_controls = []
        action_btn = None

        if tipo == "conjuro":
            nivel = item.get("nivel", 0)
            escuela = item.get("escuela", "Magia")
            clases = item.get("clases", [])
            tiempo = item.get("tiempo_lanzamiento", "1 acción")
            alcance = item.get("alcance", "18 m")
            duracion = item.get("duracion", "Instantáneo")
            componentes = item.get("componentes", "V, S")
            concentracion = item.get("concentracion", False)
            ritual = item.get("ritual", False)

            header_pills.insert(0, create_badge("Truco" if nivel == 0 else f"Nivel {nivel}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD))
            header_pills.append(create_badge(escuela, bg_color=BG_INPUT, text_color=COLOR_PURPLE, border_color=COLOR_PURPLE))

            # Badges de clases permitidas
            class_pills = [
                create_badge(c, bg_color="#1e180a", text_color=GOLD_LIGHT, border_color="#5a451b")
                for c in clases
            ]

            meta_pills = [
                create_badge(f"Tiempo: {tiempo}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Alcance: {alcance}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Duración: {duracion}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Comp: {componentes}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
            ]
            if concentracion:
                meta_pills.append(create_badge("Concentración", bg_color=BG_INPUT, text_color=COLOR_AMBER, border_color=COLOR_AMBER))
            if ritual:
                meta_pills.append(create_badge("Ritual", bg_color=BG_INPUT, text_color=COLOR_PURPLE, border_color=COLOR_PURPLE))

            # Verificar si ya está aprendido por el personaje
            is_learned = any(sp.id == eid or sp.name.lower() == nombre.lower() for sp in self.char.spells)

            if is_learned:
                action_btn = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=COLOR_GREEN),
                            ft.Text("En tu Ficha", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=COLOR_RED,
                                icon_size=16,
                                tooltip="Quitar de mi ficha",
                                on_click=lambda e, sid=eid, nm=nombre: self._remove_spell_from_char(sid, nm)
                            )
                        ],
                        spacing=4
                    )
                )
            else:
                action_btn = ft.ElevatedButton(
                    text="+ Añadir a mi Ficha",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=GOLD_PRIMARY,
                        color="#111111",
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, sid=eid: self._add_spell_to_char(sid)
                )

            sub_info_controls = [
                ft.Row(controls=class_pills, wrap=True, spacing=4) if class_pills else ft.Container(),
                ft.Row(controls=meta_pills, wrap=True, spacing=4)
            ]

        elif tipo == "dote":
            categoria = item.get("categoria", "General")
            header_pills.insert(0, create_badge(f"Dote {categoria}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD))

            # Botón de añadir a rasgos
            is_present = any(f.name.lower() == nombre.lower() for f in self.char.features)
            if is_present:
                action_btn = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=COLOR_GREEN),
                            ft.Text("En tus Rasgos", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GREEN)
                        ],
                        spacing=4
                    )
                )
            else:
                action_btn = ft.ElevatedButton(
                    text="+ Añadir a Rasgos",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=BG_INPUT,
                        color=GOLD_LIGHT,
                        side=ft.BorderSide(1, BORDER_GOLD),
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, item_data=item: self._add_feat_to_char(item_data)
                )

        # Leer archivo completo si tiene cuerpo markdown
        file_path = item.get("path")
        full_entity = self.okf.read_entity_file(file_path) if file_path else None
        body_text = ""
        if full_entity:
            body_text = full_entity.get("body_markdown", "")
            # Limpiar encabezados duplicados del markdown
            lines = body_text.split("\n")
            cleaned_lines = [l for l in lines if not l.startswith("# ")]
            body_text = "\n".join(cleaned_lines).strip()

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Cabecera de la Tarjeta
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(nombre, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                            ft.Text(f"({nombre_en})" if nombre_en else "", size=11, color=TEXT_MUTED),
                                        ],
                                        spacing=6
                                    ),
                                    ft.Row(controls=header_pills, wrap=True, spacing=4)
                                ],
                                spacing=4,
                                expand=True
                            ),
                            action_btn if action_btn else ft.Container()
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START
                    ),
                    *sub_info_controls,
                    # Contenido de la Tarjeta
                    ft.Container(
                        content=ft.Text(body_text, size=12, color="#e5e7eb", selectable=True),
                        bgcolor=BG_INPUT,
                        border=ft.border.all(1, BORDER_DIM),
                        border_radius=ft.border_radius.all(6),
                        padding=10
                    ) if body_text else ft.Container()
                ],
                spacing=8
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

    def _add_spell_to_char(self, spell_id: str):
        spell = self.okf.get_spell_item(spell_id)
        if not spell:
            return

        # Evitar duplicados
        if not any(s.id == spell.id or s.name.lower() == spell.name.lower() for s in self.char.spells):
            self.char.spells.append(spell)
            if self.on_state_change:
                self.on_state_change()
            self._refresh_results()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Conjuro '{spell.name}' añadido a la ficha."))
                self.page.snack_bar.open = True
                self.page.update()

    def _remove_spell_from_char(self, spell_id: str, name: str):
        self.char.spells = [s for s in self.char.spells if s.id != spell_id and s.name.lower() != name.lower()]
        if self.on_state_change:
            self.on_state_change()
        self._refresh_results()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Conjuro '{name}' eliminado de la ficha."))
            self.page.snack_bar.open = True
            self.page.update()

    def _add_feat_to_char(self, item: Dict[str, Any]):
        nombre = item.get("nombre", "Nueva Dote")
        fuente = item.get("fuente", "PHB 2024")
        file_path = item.get("path")
        full_entity = self.okf.read_entity_file(file_path) if file_path else None
        desc = full_entity.get("body_markdown", "") if full_entity else ""

        new_feat = CharacterFeature(
            name=nombre,
            source=fuente,
            description=desc,
            recharge="Pasivo",
            uses_max=0,
            uses_current=0
        )
        self.char.features.append(new_feat)
        if self.on_state_change:
            self.on_state_change()
        self._refresh_results()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Dote '{nombre}' añadida a tus rasgos."))
            self.page.snack_bar.open = True
            self.page.update()
