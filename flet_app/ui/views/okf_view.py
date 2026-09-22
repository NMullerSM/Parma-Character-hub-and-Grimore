"""
Vista de Compendio & Árbol de Conocimiento Atómico OKF (Open Knowledge Format)
Diseño Maestro-Detalle (Dual Panel): Lista rápida a la izquierda e Inspector detallado a la derecha.
"""
import flet as ft
from typing import Callable, Optional, Dict, Any, List
from ...core.models import CharacterSheet, SpellItem, CharacterFeature
from ...core.okf_engine import OkfEngine
from ..theme import (
    BG_PRIMARY, BG_CARD, BG_CARD_ALT, BG_INPUT, BG_SURFACE, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_AMBER, COLOR_PURPLE,
    COLOR_RED, create_card_container, create_badge, create_gold_button
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
        self.bgcolor = BG_PRIMARY

        self.current_category = "conjuro"
        self.search_query = ""
        self.spell_class = "all"
        self.spell_level = "all"
        self.selected_item: Optional[Dict[str, Any]] = None
        self.results_cache: List[Dict[str, Any]] = []

        self._build_ui()

    def update_data(self, new_char: CharacterSheet):
        self.char = new_char
        self._refresh_results(keep_selection=True)
        if self.page:
            self.update()

    def _build_ui(self):
        # 1. Selector de Categorías (Chips Horizontales)
        categories = [
            ("conjuro", "✨ Conjuros (378)"),
            ("dote", "🌟 Dotes (74)"),
            ("especie", "🧬 Especies & Linajes (11)"),
            ("trasfondo", "📜 Trasfondos (17)"),
            ("clase", "⚔️ Clases & Subclases (13)"),
            ("regla", "📖 Reglas & Mecánicas"),
        ]

        self.cat_buttons = {}
        cat_button_list = []
        for cat_id, cat_label in categories:
            is_active = (self.current_category == cat_id)
            btn = ft.ElevatedButton(
                text=cat_label,
                color="#000000" if is_active else GOLD_LIGHT,
                bgcolor=GOLD_PRIMARY if is_active else BG_INPUT,
                style=ft.ButtonStyle(
                    bgcolor=GOLD_PRIMARY if is_active else BG_INPUT,
                    color="#000000" if is_active else GOLD_LIGHT,
                    side=ft.BorderSide(1, BORDER_GOLD if is_active else BORDER_DIM),
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6)
                ),
                on_click=lambda e, cid=cat_id: self._select_category(cid)
            )
            self.cat_buttons[cat_id] = btn
            cat_button_list.append(btn)

        self.category_row = ft.Row(
            controls=cat_button_list,
            wrap=True,
            spacing=8
        )

        # 2. Barra de Búsqueda y Filtros Compacta
        self.search_input = ft.TextField(
            hint_text="Buscar por nombre, escuela, requisito o etiqueta...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, size=12),
            color="#ffffff",
            cursor_color=GOLD_LIGHT,
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            expand=True,
            height=38,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
            on_change=self._on_search_change
        )

        self.class_dropdown = ft.Dropdown(
            label="Clase",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=10),
            width=140,
            height=40,
            text_size=11,
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

        self.level_dropdown = ft.Dropdown(
            label="Nivel",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=10),
            width=110,
            height=40,
            text_size=11,
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

        is_conjuro = (self.current_category == "conjuro")
        self.class_dropdown.visible = is_conjuro
        self.level_dropdown.visible = is_conjuro

        self.filter_bar = ft.Row(
            controls=[self.search_input, self.class_dropdown, self.level_dropdown],
            spacing=8
        )

        header_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.category_row,
                    self.filter_bar
                ],
                spacing=8
            ),
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=10,
            margin=ft.margin.only(bottom=8)
        )

        # 3. Paneles Maestro y Detalle (Dual Panel Layout)
        self.count_label = ft.Text("0 elementos", size=11, color=TEXT_MUTED)
        self.master_list = ft.ListView(
            controls=[],
            spacing=6,
            expand=True,
            padding=ft.padding.only(right=4)
        )

        self.master_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Índice de Entidades", size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            self.count_label
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(color=BORDER_DIM, height=1),
                    self.master_list
                ],
                spacing=6,
                expand=True
            ),
            width=380,
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=10
        )

        self.detail_container = ft.Container(
            content=ft.Container(),
            expand=True,
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=16
        )

        body_row = ft.Row(
            controls=[
                self.master_panel,
                self.detail_container
            ],
            expand=True,
            spacing=10
        )

        self.content = ft.Column(
            controls=[
                header_container,
                body_row
            ],
            expand=True,
            spacing=0
        )

        self._refresh_results()

    def _select_category(self, cat_id: str):
        self.current_category = cat_id
        self.selected_item = None

        # Actualizar estilos visuales de botones sin reconstruir la UI
        for cid, btn in self.cat_buttons.items():
            active = (cid == cat_id)
            btn.color = "#000000" if active else GOLD_LIGHT
            btn.bgcolor = GOLD_PRIMARY if active else BG_INPUT
            btn.style = ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if active else BG_INPUT,
                color="#000000" if active else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if active else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=12, vertical=6)
            )

        # Mostrar filtros sólo para conjuros
        is_conjuro = (cat_id == "conjuro")
        self.class_dropdown.visible = is_conjuro
        self.level_dropdown.visible = is_conjuro

        self._refresh_results()
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

    def _refresh_results(self, keep_selection: bool = False):
        self.master_list.controls.clear()

        lvl = None if self.spell_level == "all" else int(self.spell_level)
        cls_filter = None if self.spell_class == "all" else self.spell_class

        target_type = self.current_category
        tipo_query = target_type
        if target_type == "especie":
            tipo_query = ["especie", "linaje"]
        elif target_type == "clase":
            tipo_query = ["clase", "subclase"]

        results = self.okf.search_entities(
            query=self.search_query,
            tipo=tipo_query,
            nivel=lvl if target_type == "conjuro" else None,
            clase=cls_filter if target_type == "conjuro" else None,
            limit=500
        )

        self.results_cache = results
        self.count_label.value = f"{len(results)} encontrados"

        if not results:
            self.master_list.controls.append(
                ft.Container(
                    content=ft.Text("Sin resultados.", size=12, color=TEXT_MUTED, italic=True),
                    padding=16,
                    alignment=ft.alignment.center
                )
            )
            self._render_empty_detail()
            return

        # Si no hay selección o la selección ya no está en los resultados, seleccionar el primero
        if not keep_selection or not self.selected_item:
            self.selected_item = results[0]
        else:
            # Verificar si el elemento seleccionado sigue existiendo
            matched = next((r for r in results if r.get("id") == self.selected_item.get("id")), None)
            if matched:
                self.selected_item = matched
            else:
                self.selected_item = results[0]

        for item in results:
            tile = self._create_compact_tile(item)
            self.master_list.controls.append(tile)

        self._render_detail(self.selected_item)

    def _create_compact_tile(self, item: Dict[str, Any]) -> ft.Container:
        eid = item.get("id", "")
        nombre = item.get("nombre", "")
        tipo = item.get("tipo", "")
        is_selected = (self.selected_item and self.selected_item.get("id") == eid)

        tag_text = ""
        tag_color = TEXT_MUTED
        if tipo == "conjuro":
            lvl = item.get("nivel", 0)
            tag_text = "Truco" if lvl == 0 else f"Niv {lvl}"
            tag_color = GOLD_LIGHT if lvl > 0 else TEXT_MUTED
        elif tipo == "dote":
            tag_text = item.get("categoria", "General")
            tag_color = COLOR_AMBER
        elif tipo in ["clase", "subclase"]:
            tag_text = "Subclase" if tipo == "subclase" else "Clase"
            tag_color = COLOR_PURPLE
        elif tipo in ["especie", "linaje"]:
            tag_text = "Linaje" if tipo == "linaje" else "Especie"
            tag_color = COLOR_GREEN

        # Indicador si ya está en la ficha
        in_char = False
        if tipo == "conjuro":
            in_char = any(sp.id == eid or sp.name.lower() == nombre.lower() for sp in self.char.spells)
        elif tipo == "dote":
            in_char = any(f.name.lower() == nombre.lower() for f in self.char.features)

        status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=COLOR_GREEN) if in_char else None

        content_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(nombre, size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT if is_selected else "#ffffff", no_wrap=True),
                                status_icon if status_icon else ft.Container()
                            ],
                            spacing=4
                        ),
                        ft.Text(f"{tag_text} • {item.get('fuente', 'PHB')}", size=10, color=TEXT_MUTED)
                    ],
                    spacing=2,
                    expand=True
                ),
                ft.Container(
                    content=ft.Text(tag_text, size=9, weight=ft.FontWeight.W_600, color=tag_color),
                    bgcolor=BG_INPUT,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=ft.border_radius.all(4),
                    border=ft.border.all(1, BORDER_DIM)
                ) if tag_text else ft.Container()
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        return ft.Container(
            content=content_row,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            bgcolor=BG_CARD_ALT if is_selected else BG_INPUT,
            border=ft.border.all(1.5 if is_selected else 1, BORDER_GOLD if is_selected else BORDER_DIM),
            border_radius=ft.border_radius.all(6),
            on_click=lambda e, it=item: self._on_select_item(it)
        )

    def _on_select_item(self, item: Dict[str, Any]):
        self.selected_item = item
        # Re-renderizar tiles para reflejar selección
        for ctrl in self.master_list.controls:
            if isinstance(ctrl, ft.Container):
                ctrl.bgcolor = BG_INPUT
                ctrl.border = ft.border.all(1, BORDER_DIM)
        # Actualizar lista y detalle
        self._refresh_results(keep_selection=True)
        if self.page:
            self.page.update()

    def _render_empty_detail(self):
        self.detail_container.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=TEXT_MUTED),
                    ft.Text("No hay ningún elemento seleccionado", size=14, color=TEXT_MUTED),
                    ft.Text("Prueba ajustando los filtros de búsqueda o categoría.", size=12, color=TEXT_MUTED)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            alignment=ft.alignment.center
        )

    def _render_detail(self, item: Dict[str, Any]):
        if not item:
            self._render_empty_detail()
            return

        eid = item.get("id", "")
        tipo = item.get("tipo", "")
        nombre = item.get("nombre", "")
        nombre_en = item.get("nombre_ingles", "")
        fuente = item.get("fuente", "PHB 2024")
        pagina = item.get("pagina", "")

        header_badges = [
            create_badge(f"Pág. {pagina}" if pagina else fuente, bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM)
        ]

        action_btn = None
        sub_badges = []

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

            header_badges.insert(0, create_badge("Truco" if nivel == 0 else f"Nivel {nivel}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD))
            header_badges.append(create_badge(escuela, bg_color=BG_INPUT, text_color=COLOR_PURPLE, border_color=COLOR_PURPLE))

            class_pills = [
                create_badge(c, bg_color="#1e180a", text_color=GOLD_LIGHT, border_color="#5a451b")
                for c in clases
            ]

            tech_pills = [
                create_badge(f"Tiempo: {tiempo}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Alcance: {alcance}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Duración: {duracion}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
                create_badge(f"Comp: {componentes}", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM),
            ]
            if concentracion:
                tech_pills.append(create_badge("Concentración", bg_color=BG_INPUT, text_color=COLOR_AMBER, border_color=COLOR_AMBER))
            if ritual:
                tech_pills.append(create_badge("Ritual", bg_color=BG_INPUT, text_color=COLOR_PURPLE, border_color=COLOR_PURPLE))

            is_learned = any(sp.id == eid or sp.name.lower() == nombre.lower() for sp in self.char.spells)
            if is_learned:
                action_btn = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=COLOR_GREEN),
                            ft.Text("En tu Ficha", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=COLOR_RED,
                                icon_size=18,
                                tooltip="Quitar de mi ficha",
                                on_click=lambda e, sid=eid, nm=nombre: self._remove_spell_from_char(sid, nm)
                            )
                        ],
                        spacing=6
                    )
                )
            else:
                action_btn = ft.ElevatedButton(
                    text="+ Añadir a mi Ficha",
                    icon=ft.Icons.ADD,
                    color="#000000",
                    bgcolor=GOLD_PRIMARY,
                    style=ft.ButtonStyle(
                        bgcolor=GOLD_PRIMARY,
                        color="#000000",
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, sid=eid: self._add_spell_to_char(sid)
                )

            sub_badges = [
                ft.Row(controls=class_pills, wrap=True, spacing=4) if class_pills else ft.Container(),
                ft.Row(controls=tech_pills, wrap=True, spacing=4)
            ]

        elif tipo == "dote":
            categoria = item.get("categoria", "General")
            header_badges.insert(0, create_badge(f"Dote {categoria}", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD))

            is_present = any(f.name.lower() == nombre.lower() for f in self.char.features)
            if is_present:
                action_btn = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=COLOR_GREEN),
                            ft.Text("En tus Rasgos", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GREEN)
                        ],
                        spacing=6
                    )
                )
            else:
                action_btn = ft.ElevatedButton(
                    text="+ Añadir a Rasgos",
                    icon=ft.Icons.ADD,
                    color=GOLD_LIGHT,
                    bgcolor=BG_INPUT,
                    style=ft.ButtonStyle(
                        bgcolor=BG_INPUT,
                        color=GOLD_LIGHT,
                        side=ft.BorderSide(1, BORDER_GOLD),
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    on_click=lambda e, it=item: self._add_feat_to_char(it)
                )

        # Cargar Markdown bajo demanda
        file_path = item.get("path")
        full_entity = self.okf.read_entity_file(file_path) if file_path else None
        body_text = ""
        if full_entity:
            body_text = full_entity.get("body_markdown", "")
            lines = body_text.split("\n")
            cleaned_lines = [l for l in lines if not l.startswith("# ")]
            body_text = "\n".join(cleaned_lines).strip()

        detail_content = ft.ListView(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(nombre, size=20, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                        ft.Text(f"({nombre_en})" if nombre_en else "", size=13, color=TEXT_MUTED),
                                    ],
                                    spacing=8
                                ),
                                ft.Row(controls=header_badges, wrap=True, spacing=4)
                            ],
                            spacing=4,
                            expand=True
                        ),
                        action_btn if action_btn else ft.Container()
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                *sub_badges,
                ft.Divider(color=BORDER_DIM, height=1),
                ft.Container(
                    content=ft.Text(body_text or "Sin descripción detallada.", size=13, color="#f0f2f5", selectable=True),
                    bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER_DIM),
                    border_radius=ft.border_radius.all(6),
                    padding=12
                )
            ],
            spacing=10,
            expand=True
        )

        self.detail_container.content = detail_content
        if self.page:
            try:
                self.detail_container.update()
            except Exception:
                pass

    def _add_spell_to_char(self, spell_id: str):
        spell = self.okf.get_spell_item(spell_id)
        if not spell:
            return

        if not any(s.id == spell.id or s.name.lower() == spell.name.lower() for s in self.char.spells):
            self.char.spells.append(spell)
            if self.on_state_change:
                self.on_state_change()
            self._refresh_results(keep_selection=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Conjuro '{spell.name}' añadido a la ficha."))
                self.page.snack_bar.open = True
                self.page.update()

    def _remove_spell_from_char(self, spell_id: str, name: str):
        self.char.spells = [s for s in self.char.spells if s.id != spell_id and s.name.lower() != name.lower()]
        if self.on_state_change:
            self.on_state_change()
        self._refresh_results(keep_selection=True)
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
        self._refresh_results(keep_selection=True)
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Dote '{nombre}' añadida a tus rasgos."))
            self.page.snack_bar.open = True
            self.page.update()
