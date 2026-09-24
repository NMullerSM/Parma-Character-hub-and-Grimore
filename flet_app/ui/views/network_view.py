"""
Vista de Red de Personajes & Relaciones de Campaña (Canvas Interactivo 2D)
Permite visualizar, arrastrar personajes, trazar conexiones vectoriales y alternar con directorio.
"""
import math
import flet as ft
import flet.canvas as cv
from typing import Callable, Optional, Dict, Any, List
from ...core.models import CharacterSheet, NetworkNode, NetworkEdge
from ...core.db import DatabaseManager
from ..theme import (
    BG_PRIMARY, BG_CARD, BG_CARD_ALT, BG_INPUT, BG_SURFACE, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_RED, COLOR_GREEN, COLOR_BLUE,
    COLOR_PURPLE, COLOR_AMBER, create_card_container, create_badge, create_gold_button
)

ROLE_CONFIG = {
    "ally": (COLOR_GREEN, "Aliado"),
    "villain": (COLOR_RED, "Villano / Rival"),
    "contact": (COLOR_BLUE, "Contacto"),
    "companion": (GOLD_PRIMARY, "Compañero"),
    "enigma": (COLOR_PURPLE, "Enigma"),
    "neutral": (TEXT_MUTED, "Neutral"),
}

RELATION_COLORS = {
    "Aliado": COLOR_GREEN,
    "Amigo": COLOR_GREEN,
    "Enemigo": COLOR_RED,
    "Rival": COLOR_RED,
    "Mentor": COLOR_BLUE,
    "Deuda": COLOR_AMBER,
    "Pacto": COLOR_PURPLE,
    "Familiar": GOLD_PRIMARY,
    "Neutral": TEXT_MUTED
}


class NetworkView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.on_state_change = on_state_change
        self.expand = True
        self.bgcolor = BG_PRIMARY

        self.view_mode = "canvas"  # 'canvas' o 'directory'
        self.selected_node: Optional[NetworkNode] = None

        # Si hay nodos sin posición asignada, auto-organizar
        self._ensure_initial_positions()
        self._build_ui()

    def _ensure_initial_positions(self):
        nodes = self.char.network_nodes
        unpositioned = [n for n in nodes if n.x == 0.0 and n.y == 0.0]
        if unpositioned and len(nodes) > 0:
            self._auto_layout()

    def _auto_layout(self):
        nodes = self.char.network_nodes
        n = len(nodes)
        if n == 0:
            return
        center_x = 420.0
        center_y = 260.0
        radius = min(260.0, 80.0 + n * 30.0)
        for i, node in enumerate(nodes):
            angle = (2 * math.pi / n) * i
            node.x = max(20.0, center_x + radius * math.cos(angle) - 85.0)
            node.y = max(20.0, center_y + radius * math.sin(angle) - 40.0)

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._ensure_initial_positions()
        if hasattr(self, "badge_nodes") and self.badge_nodes.content:
            self.badge_nodes.content.value = f"{len(self.char.network_nodes)} Personajes"
        if hasattr(self, "badge_edges") and self.badge_edges.content:
            self.badge_edges.content.value = f"{len(self.char.network_edges)} Vínculos"
        if hasattr(self, "toolbar") and self.toolbar.page:
            self.toolbar.update()
        if self.view_mode == "canvas":
            self._render_canvas()
        else:
            self._populate_directory_cards()
        if self.page:
            self.update()

    def _build_ui(self):
        # Barra de Herramientas Superior del Canvas
        self.mode_button = ft.OutlinedButton(
            text="📋 Directorio de Fichas" if self.view_mode == "canvas" else "🎨 Canvas Interactivo",
            icon=ft.Icons.VIEW_LIST if self.view_mode == "canvas" else ft.Icons.SCATTER_PLOT,
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
            on_click=self._toggle_view_mode,
            tooltip="Alternar entre lienzo interactivo y lista detallada"
        )

        btn_add = ft.ElevatedButton(
            text="+ Nuevo Personaje",
            icon=ft.Icons.PERSON_ADD,
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
            on_click=self._open_add_character_dialog,
            tooltip="Añadir un nuevo personaje o contacto a la campaña"
        )

        btn_connect = ft.OutlinedButton(
            text="🔗 Conectar",
            icon=ft.Icons.LINK,
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._open_connect_dialog,
            tooltip="Trazar relación entre dos personajes"
        )

        btn_manage_edges = ft.OutlinedButton(
            text="Vínculos",
            icon=ft.Icons.HUB,
            style=ft.ButtonStyle(color=TEXT_MUTED, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._open_manage_edges_dialog,
            tooltip="Ver y eliminar relaciones de campaña"
        )

        btn_auto = ft.OutlinedButton(
            text="📐 Organizar",
            icon=ft.Icons.AUTO_AWESOME,
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._on_auto_layout_click,
            tooltip="Distribuir automáticamente en círculo armónico"
        )

        self.badge_nodes = create_badge(f"{len(self.char.network_nodes)} Personajes", bg_color=BG_INPUT, text_color=GOLD_LIGHT, border_color=BORDER_GOLD)
        self.badge_edges = create_badge(f"{len(self.char.network_edges)} Vínculos", bg_color=BG_INPUT, text_color=TEXT_MUTED, border_color=BORDER_DIM)

        self.toolbar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("🌐 Red de Personajes & Aliados", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            self.badge_nodes,
                            self.badge_edges,
                        ],
                        spacing=8
                    ),
                    ft.Row(
                        controls=[btn_add, btn_connect, btn_manage_edges, btn_auto, self.mode_button],
                        spacing=8,
                        wrap=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                wrap=True
            ),
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=8)
        )

        # Lienzo Interactivo 2D
        self.canvas_stack = ft.Stack(expand=True)
        self.canvas_container = ft.Container(
            content=self.canvas_stack,
            expand=True,
            bgcolor="#0a0c14",
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

        # Vista de Directorio Alternativa (Tarjetas en Lista)
        self.directory_grid = ft.ResponsiveRow(spacing=10)
        self.directory_container = ft.Container(
            content=ft.ListView(
                controls=[self.directory_grid],
                spacing=10,
                expand=True
            ),
            expand=True,
            visible=False
        )

        self.content = ft.Column(
            controls=[
                self.toolbar,
                self.canvas_container,
                self.directory_container
            ],
            expand=True,
            spacing=0
        )

        self._render_canvas()

    def _toggle_view_mode(self, e):
        if self.view_mode == "canvas":
            self.view_mode = "directory"
            self.canvas_container.visible = False
            self.directory_container.visible = True
            self.mode_button.text = "🎨 Canvas Interactivo"
            self.mode_button.icon = ft.Icons.SCATTER_PLOT
            self._populate_directory_cards()
        else:
            self.view_mode = "canvas"
            self.canvas_container.visible = True
            self.directory_container.visible = False
            self.mode_button.text = "📋 Directorio de Fichas"
            self.mode_button.icon = ft.Icons.VIEW_LIST
            self._render_canvas()

        if self.page:
            self.page.update()

    def _on_auto_layout_click(self, e):
        self._auto_layout()
        self._render_canvas()
        if self.page:
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def _render_canvas(self):
        self.canvas_stack.controls.clear()
        nodes = self.char.network_nodes
        edges = self.char.network_edges

        # 1. Capa de Fondo y Líneas Vectoriales de Conexión
        canvas_shapes = []
        node_map = {n.id: n for n in nodes}

        # Dibujar líneas de conexión entre nodos
        for edge in edges:
            src = node_map.get(edge.source_id)
            tgt = node_map.get(edge.target_id)
            if src and tgt:
                # Centro de cada tarjeta (ancho ~180, alto ~80)
                x1 = src.x + 90.0
                y1 = src.y + 40.0
                x2 = tgt.x + 90.0
                y2 = tgt.y + 40.0

                rel_color = RELATION_COLORS.get(edge.relation, GOLD_LIGHT)

                # Línea vectorial
                canvas_shapes.append(
                    cv.Line(
                        x1, y1, x2, y2,
                        paint=ft.Paint(
                            stroke_width=2.5,
                            color=rel_color,
                            style=ft.PaintingStyle.STROKE
                        )
                    )
                )

        # Capa de dibujo vectorial en el fondo (solo si hay líneas trazadas)
        if canvas_shapes:
            line_canvas = cv.Canvas(
                shapes=canvas_shapes,
                left=0,
                top=0,
                right=0,
                bottom=0
            )
            self.canvas_stack.controls.append(line_canvas)

        # 1.5 Etiquetas de Relación centradas sobre las líneas
        for edge in edges:
            src = node_map.get(edge.source_id)
            tgt = node_map.get(edge.target_id)
            if src and tgt:
                mid_x = (src.x + tgt.x) / 2.0 + 50.0
                mid_y = (src.y + tgt.y) / 2.0 + 25.0
                rel_color = RELATION_COLORS.get(edge.relation, GOLD_LIGHT)

                tag_box = ft.Container(
                    left=mid_x,
                    top=mid_y,
                    content=ft.Text(edge.relation, size=9, weight=ft.FontWeight.BOLD, color="#000000"),
                    bgcolor=rel_color,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=ft.border_radius.all(4),
                    border=ft.border.all(1, "#ffffff")
                )
                self.canvas_stack.controls.append(tag_box)

        # 2. Capa Superior: Nodos Interactivos Arrastrables
        if not nodes:
            self.canvas_stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.HUB_OUTLINED, size=56, color=TEXT_MUTED),
                            ft.Text("Lienzo de Red Vacío", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.Text("Pulsa '+ Nuevo Personaje' para añadir aliados, rivales o misterios a tu historia.", size=12, color=TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
            return

        for node in nodes:
            node_widget = self._create_draggable_node(node)
            self.canvas_stack.controls.append(node_widget)

        if self.canvas_stack.page:
            self.canvas_stack.update()

    def _create_draggable_node(self, node: NetworkNode) -> ft.Container:
        color, role_label = ROLE_CONFIG.get(node.role, (TEXT_MUTED, "Neutral"))

        # Tarjeta visual del nodo
        card_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.CircleAvatar(
                                        content=ft.Text(node.name[:2].upper(), size=10, weight=ft.FontWeight.BOLD, color="#ffffff"),
                                        bgcolor=BG_INPUT,
                                        radius=14
                                    ),
                                    ft.Text(node.name, size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT, no_wrap=True, max_lines=1),
                                ],
                                spacing=6,
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.Icons.INFO_OUTLINE,
                                icon_size=14,
                                icon_color=TEXT_MUTED,
                                tooltip="Ver detalles",
                                on_click=lambda e, n=node: self._show_node_details_dialog(n)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            create_badge(role_label, bg_color=BG_INPUT, text_color=color, border_color=color),
                            ft.Text("✥ Arrastrar", size=9, color=TEXT_MUTED, italic=True)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=4
            ),
            width=180,
            bgcolor=BG_CARD,
            border=ft.border.all(1.5, color),
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color="rgba(0, 0, 0, 0.5)")
        )

        # Manejador de Arrastre con GestureDetector
        gesture_box = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_update=lambda e, n=node: self._on_node_drag(e, n),
            content=card_content
        )

        # Posicionamiento absoluto dentro del Stack
        return ft.Container(
            left=node.x,
            top=node.y,
            content=gesture_box
        )

    def _on_node_drag(self, e: ft.DragUpdateEvent, node: NetworkNode):
        # Actualizar posición y delimitar dentro del lienzo
        node.x = max(10.0, min(1400.0, node.x + e.delta_x))
        node.y = max(10.0, min(900.0, node.y + e.delta_y))
        self._render_canvas()
        if self.canvas_stack.page:
            self.canvas_stack.update()
        if self.on_state_change:
            self.on_state_change()

    def _populate_directory_cards(self):
        self.directory_grid.controls.clear()
        if not self.char.network_nodes:
            self.directory_grid.controls.append(
                ft.Container(
                    content=ft.Text("Aún no hay personajes en el directorio. ¡Añade uno con '+ Nuevo Personaje'!", size=12, color=TEXT_MUTED, italic=True),
                    padding=16,
                    col={"sm": 12}
                )
            )
            return

        for node in self.char.network_nodes:
            color, role_label = ROLE_CONFIG.get(node.role, (TEXT_MUTED, "Otro"))
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.CircleAvatar(
                                            content=ft.Text(node.name[:2].upper(), size=12, weight=ft.FontWeight.BOLD, color="#ffffff"),
                                            bgcolor=BG_INPUT,
                                            radius=18
                                        ),
                                        ft.Text(node.name, size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                    ],
                                    spacing=8
                                ),
                                create_badge(role_label, bg_color=BG_INPUT, text_color=color, border_color=color),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(node.description or "Sin descripción.", size=12, color="#d1d5db"),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=COLOR_RED,
                                    icon_size=18,
                                    tooltip="Eliminar personaje",
                                    on_click=lambda e, n=node: self._remove_node(n)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=8
                ),
                bgcolor=BG_CARD,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(8),
                padding=12,
                col={"sm": 12, "md": 6, "lg": 4}
            )
            self.directory_grid.controls.append(card)

    def _open_add_character_dialog(self, e):
        name_input = ft.TextField(
            label="Nombre del Personaje",
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff"
        )
        role_dropdown = ft.Dropdown(
            label="Rol en la Campaña",
            value="ally",
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            options=[
                ft.dropdown.Option("ally", "Aliado"),
                ft.dropdown.Option("villain", "Villano / Rival"),
                ft.dropdown.Option("contact", "Contacto"),
                ft.dropdown.Option("companion", "Compañero"),
                ft.dropdown.Option("enigma", "Enigma"),
                ft.dropdown.Option("neutral", "Neutral"),
            ]
        )
        desc_input = ft.TextField(
            label="Descripción / Secretos / Relación",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff"
        )

        def save_character(ev):
            name = name_input.value.strip() if name_input.value else ""
            if not name:
                return
            if self.page:
                self.page.close(dialog)

            # Ubicación calculada para que no caiga fuera del canvas
            existing_count = len(self.char.network_nodes)
            angle = existing_count * 0.8
            new_x = 350.0 + 150.0 * math.cos(angle)
            new_y = 220.0 + 120.0 * math.sin(angle)

            new_node = NetworkNode(
                id=str(len(self.char.network_nodes) + 1),
                name=name,
                role=role_dropdown.value,
                description=desc_input.value.strip() if desc_input.value else "",
                x=new_x,
                y=new_y
            )
            self.char.network_nodes.append(new_node)
            self.update_data(self.char)
            if self.page:
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

        def close_dialog(ev):
            if self.page:
                self.page.close(dialog)

        # Opciones de importación rápida desde héroes guardados en la BD
        db_mgr = DatabaseManager()
        saved_heroes = db_mgr.list_characters()
        existing_names = {n.name.strip().lower() for n in self.char.network_nodes}
        importable = [h for h in saved_heroes if h["name"].strip().lower() not in existing_names]

        import_dropdown = None
        if importable:
            import_options = [
                ft.dropdown.Option(h["name"], f"📥 {h['name']} ({h.get('char_class', '')} Niv {h.get('level', 1)})")
                for h in importable
            ]
            def on_import_select(ev):
                if ev.control.value:
                    sel_h = next((h for h in importable if h["name"] == ev.control.value), None)
                    if sel_h:
                        name_input.value = sel_h["name"]
                        role_dropdown.value = "companion"
                        desc_input.value = f"{sel_h.get('race', '')} {sel_h.get('char_class', '')} Nivel {sel_h.get('level', 1)}. Héroe de la campaña."
                        dialog.update()

            import_dropdown = ft.Dropdown(
                label="⚡ Importar Héroe Guardado de la Campaña",
                hint_text="Elige un personaje existente para vincularlo...",
                options=import_options,
                border_color=BORDER_GOLD,
                on_change=on_import_select
            )

        dialog_controls = []
        if import_dropdown:
            dialog_controls.append(import_dropdown)
            dialog_controls.append(ft.Divider(color=BORDER_DIM, height=1))
        dialog_controls.extend([name_input, role_dropdown, desc_input])

        dialog = ft.AlertDialog(
            title=ft.Text("➕ Añadir Personaje a la Red", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=dialog_controls,
                    spacing=10
                ),
                width=460,
                height=300 if import_dropdown else 240
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=close_dialog),
                ft.ElevatedButton(
                    "Guardar Personaje",
                    color="#000000",
                    bgcolor=GOLD_PRIMARY,
                    style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                    on_click=save_character
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if self.page:
            self.page.open(dialog)

    def _open_connect_dialog(self, e):
        nodes = self.char.network_nodes
        if len(nodes) < 2:
            self.page.snack_bar = ft.SnackBar(ft.Text("Necesitas al menos 2 personajes para trazar una conexión."))
            self.page.snack_bar.open = True
            self.page.update()
            return

        node_options = [ft.dropdown.Option(n.id, n.name) for n in nodes]
        src_dropdown = ft.Dropdown(label="Personaje Origen", options=node_options, value=nodes[0].id, border_color=BORDER_DIM)
        tgt_dropdown = ft.Dropdown(label="Personaje Destino", options=node_options, value=nodes[1].id, border_color=BORDER_DIM)
        rel_dropdown = ft.Dropdown(
            label="Tipo de Relación",
            value="Aliado",
            border_color=BORDER_DIM,
            options=[
                ft.dropdown.Option("Aliado", "Aliado"),
                ft.dropdown.Option("Amigo", "Amigo"),
                ft.dropdown.Option("Enemigo", "Enemigo"),
                ft.dropdown.Option("Rival", "Rival"),
                ft.dropdown.Option("Mentor", "Mentor"),
                ft.dropdown.Option("Deuda", "Deuda"),
                ft.dropdown.Option("Pacto", "Pacto"),
                ft.dropdown.Option("Familiar", "Familiar"),
                ft.dropdown.Option("Neutral", "Neutral"),
            ]
        )

        def save_connection(ev):
            src_id = src_dropdown.value
            tgt_id = tgt_dropdown.value
            if src_id == tgt_id:
                self.page.snack_bar = ft.SnackBar(ft.Text("No puedes conectar un personaje consigo mismo."))
                self.page.snack_bar.open = True
                self.page.update()
                return

            if self.page:
                self.page.close(dialog)

            # Evitar conexión duplicada
            existing = any(
                (ed.source_id == src_id and ed.target_id == tgt_id) or
                (ed.source_id == tgt_id and ed.target_id == src_id)
                for ed in self.char.network_edges
            )
            if not existing:
                self.char.network_edges.append(
                    NetworkEdge(source_id=src_id, target_id=tgt_id, relation=rel_dropdown.value)
                )
                self.update_data(self.char)
                if self.page:
                    self.page.update()
                if self.on_state_change:
                    self.on_state_change()

        def close_dialog(ev):
            if self.page:
                self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("🔗 Conectar Personajes", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.Column(
                    controls=[src_dropdown, tgt_dropdown, rel_dropdown],
                    spacing=10
                ),
                width=420,
                height=220
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=close_dialog),
                ft.ElevatedButton(
                    "Crear Vínculo",
                    color="#000000",
                    bgcolor=GOLD_PRIMARY,
                    style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000"),
                    on_click=save_connection
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if self.page:
            self.page.open(dialog)

    def _open_manage_edges_dialog(self, e):
        edges = self.char.network_edges
        node_map = {n.id: n.name for n in self.char.network_nodes}

        rows = []
        for edge in edges:
            src_name = node_map.get(edge.source_id, "Desconocido")
            tgt_name = node_map.get(edge.target_id, "Desconocido")
            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(f"{src_name}  ⇄  {tgt_name}", size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        create_badge(edge.relation, bg_color=BG_INPUT, text_color=RELATION_COLORS.get(edge.relation, GOLD_LIGHT), border_color=BORDER_DIM),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=COLOR_RED,
                            icon_size=16,
                            tooltip="Eliminar vínculo",
                            on_click=lambda ev, ed=edge: self._delete_edge(ed)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                bgcolor=BG_INPUT,
                padding=6,
                border_radius=4
            )
            rows.append(row)

        def close_dialog(ev):
            if self.page:
                self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Hub de Vínculos de Campaña", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Container(
                content=ft.ListView(controls=rows or [ft.Text("No hay conexiones activas.", size=12, color=TEXT_MUTED)], spacing=6),
                width=450,
                height=260
            ),
            actions=[ft.TextButton("Cerrar", style=ft.ButtonStyle(color=GOLD_LIGHT), on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if self.page:
            self.page.open(dialog)

    def _delete_edge(self, edge: NetworkEdge):
        if edge in self.char.network_edges:
            self.char.network_edges.remove(edge)
            self.update_data(self.char)
            if self.on_state_change:
                self.on_state_change()

    def _show_node_details_dialog(self, node: NetworkNode):
        color, role_label = ROLE_CONFIG.get(node.role, (TEXT_MUTED, "Neutral"))

        def close_dialog(ev):
            if self.page:
                self.page.close(dialog)

        def delete_character(ev):
            if self.page:
                self.page.close(dialog)
            self._remove_node(node)

        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text(node.name, size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    create_badge(role_label, bg_color=BG_INPUT, text_color=color, border_color=color)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Descripción y Secretos de Campaña:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                        ft.Container(
                            content=ft.Text(node.description or "Sin notas adicionales registradas.", size=13, color="#f0f2f5"),
                            bgcolor=BG_INPUT,
                            padding=10,
                            border_radius=6,
                            border=ft.border.all(1, BORDER_DIM)
                        )
                    ],
                    spacing=8
                ),
                width=420,
                height=160
            ),
            actions=[
                ft.ElevatedButton("Eliminar", bgcolor=COLOR_RED, color="#ffffff", on_click=delete_character),
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=GOLD_LIGHT), on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if self.page:
            self.page.open(dialog)

    def _remove_node(self, node: NetworkNode):
        if node in self.char.network_nodes:
            self.char.network_nodes.remove(node)
            # Eliminar también cualquier arista conectada a este nodo
            self.char.network_edges = [
                e for e in self.char.network_edges
                if e.source_id != node.id and e.target_id != node.id
            ]
            self.update_data(self.char)
            if self.on_state_change:
                self.on_state_change()
