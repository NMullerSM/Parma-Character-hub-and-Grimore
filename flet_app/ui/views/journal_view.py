"""
Vista de Diario de Campaña & Crónica de Sesiones (Arquitectura Maestro-Detalle)
Permite redactar y consultar notas extensas de cada aventura con soporte completo para Markdown,
seguimiento de botín, registro de PX y filtrado ágil.
"""
import flet as ft
from datetime import datetime
from typing import Callable, Optional, List
from ...core.models import CharacterSheet, SessionLog
from ..theme import (
    BG_PRIMARY, BG_SURFACE, BG_CARD, BG_CARD_ALT, BG_INPUT, BORDER_DIM, BORDER_GOLD,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_RED, COLOR_BLUE,
    create_card_container, create_badge, create_gold_button
)


class JournalView(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        on_state_change: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.char = char
        self.on_state_change = on_state_change
        self.expand = True

        self.selected_session: Optional[SessionLog] = None
        self.search_query: str = ""
        self.active_tab_mode: str = "write"  # "write" o "read"

        if self.char.sessions:
            self.selected_session = self.char.sessions[-1]

        self._build_ui()

    def _build_ui(self):
        # 1. PANEL IZQUIERDO: Directorio y Línea Temporal de Sesiones
        self.badge_count = create_badge(
            f"{len(self.char.sessions)} Sesiones",
            bg_color=BG_INPUT,
            text_color=GOLD_LIGHT,
            border_color=BORDER_GOLD
        )

        btn_new_session = ft.ElevatedButton(
            text="+ Nueva Sesión",
            icon=ft.Icons.NOTE_ADD,
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#000000",
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._on_new_session_click
        )

        self.search_field = ft.TextField(
            hint_text="Buscar en crónicas...",
            prefix_icon=ft.Icons.SEARCH,
            height=38,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff",
            on_change=self._on_search_change
        )

        self.session_list = ft.ListView(
            spacing=6,
            expand=True
        )

        left_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("📖 Crónicas de Campaña", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            self.badge_count
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    btn_new_session,
                    self.search_field,
                    ft.Divider(color=BORDER_DIM, height=1),
                    self.session_list
                ],
                spacing=8,
                expand=True
            ),
            width=320,
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=12
        )

        # 2. PANEL DERECHO: Lector / Redactor Extenso
        self.right_panel = ft.Container(
            expand=True,
            bgcolor=BG_SURFACE,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=14
        )

        self.content = ft.Row(
            controls=[
                left_panel,
                self.right_panel
            ],
            expand=True,
            spacing=10
        )

        self._refresh_session_list()
        self._render_detail_pane()

    def _on_search_change(self, e):
        self.search_query = e.control.value.lower().strip() if e.control.value else ""
        self._refresh_session_list()
        if self.page:
            self.page.update()

    def _on_new_session_click(self, e):
        new_sess = SessionLog(
            id=str(len(self.char.sessions) + 1),
            date=datetime.now().strftime("%Y-%m-%d"),
            title=f"Sesión {len(self.char.sessions) + 1}: Nueva Aventura",
            summary="## Resumen de la Aventura\nEscribe aquí los acontecimientos principales de la sesión...\n\n### Encuentros y Combates\n- \n\n### PNJ y Secretos Descubiertos\n- \n",
            loot="",
            xp_gained=300
        )
        self.char.sessions.append(new_sess)
        self.char.xp += 300
        self.selected_session = new_sess
        self.active_tab_mode = "write"

        self._refresh_session_list()
        self._render_detail_pane()

        if self.page:
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def _select_session(self, sess: SessionLog):
        self.selected_session = sess
        self._refresh_session_list()
        self._render_detail_pane()
        if self.page:
            self.page.update()

    def _refresh_session_list(self):
        self.session_list.controls.clear()
        self.badge_count.content.value = f"{len(self.char.sessions)} Sesiones"

        filtered = [
            s for s in reversed(self.char.sessions)
            if not self.search_query or (self.search_query in s.title.lower() or self.search_query in s.summary.lower() or self.search_query in s.date.lower())
        ]

        if not filtered:
            self.session_list.controls.append(
                ft.Container(
                    content=ft.Text("Sin sesiones coincidentes.", size=12, color=TEXT_MUTED, italic=True),
                    padding=16,
                    alignment=ft.alignment.center
                )
            )
            return

        for sess in filtered:
            is_selected = (self.selected_session and self.selected_session.id == sess.id)

            snippet = sess.summary.replace("#", "").replace("*", "").strip()[:65]
            if len(sess.summary) > 65:
                snippet += "..."

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(sess.title, size=13, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT if is_selected else "#ffffff", max_lines=1, no_wrap=True, expand=True),
                                create_badge(f"+{sess.xp_gained} PX", bg_color=BG_INPUT, text_color=GOLD_PRIMARY, border_color=BORDER_GOLD if is_selected else BORDER_DIM)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(f"📅 {sess.date}", size=11, color=TEXT_MUTED),
                                ft.Text(f"💎 {sess.loot[:20]}..." if sess.loot else "", size=10, color=GOLD_PRIMARY if sess.loot else TEXT_MUTED, italic=True)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(snippet, size=11, color="#b0b5c0", max_lines=2, no_wrap=False) if snippet else ft.Container()
                    ],
                    spacing=3
                ),
                bgcolor=BG_CARD_ALT if is_selected else BG_INPUT,
                border=ft.border.all(1.5 if is_selected else 1, BORDER_GOLD if is_selected else BORDER_DIM),
                border_radius=ft.border_radius.all(6),
                padding=10,
                on_click=lambda e, s=sess: self._select_session(s)
            )
            self.session_list.controls.append(card)

    def _render_detail_pane(self):
        if not self.selected_session:
            self.right_panel.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_STORIES, size=64, color=TEXT_MUTED),
                        ft.Text("Ninguna sesión seleccionada", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                        ft.Text("Selecciona una crónica a la izquierda o pulsa '+ Nueva Sesión' para comenzar a escribir.", size=12, color=TEXT_MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8
                ),
                alignment=ft.alignment.center,
                expand=True
            )
            return

        sess = self.selected_session

        # Campos de edición de cabecera
        title_field = ft.TextField(
            label="Título de la Sesión",
            value=sess.title,
            border_color=BORDER_GOLD,
            color="#ffffff",
            expand=True,
            on_change=lambda e: self._on_field_edit("title", e.control.value)
        )
        date_field = ft.TextField(
            label="Fecha",
            value=sess.date,
            width=130,
            border_color=BORDER_DIM,
            on_change=lambda e: self._on_field_edit("date", e.control.value)
        )
        xp_field = ft.TextField(
            label="PX Obtenidos",
            value=str(sess.xp_gained),
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=BORDER_DIM,
            on_change=lambda e: self._on_field_edit("xp", e.control.value)
        )
        loot_field = ft.TextField(
            label="Tesoro & Botín Adquirido",
            value=sess.loot,
            hint_text="Ej. 200 PO, Pergamino de Bola de Fuego, Llave de rubí...",
            border_color=BORDER_DIM,
            expand=True,
            on_change=lambda e: self._on_field_edit("loot", e.control.value)
        )

        btn_save = ft.ElevatedButton(
            text="💾 Guardar Cambios",
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#000000",
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._on_save_session_click
        )

        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=COLOR_RED,
            tooltip="Eliminar esta crónica",
            on_click=self._on_delete_session_click
        )

        # Barra de Modo (Redactar vs Lectura Markdown)
        btn_mode_write = ft.ElevatedButton(
            text="✍️ Redactar Notas Extensas",
            color="#000000" if self.active_tab_mode == "write" else GOLD_LIGHT,
            bgcolor=GOLD_PRIMARY if self.active_tab_mode == "write" else BG_INPUT,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if self.active_tab_mode == "write" else BG_INPUT,
                color="#000000" if self.active_tab_mode == "write" else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if self.active_tab_mode == "write" else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=lambda e: self._set_note_mode("write")
        )

        btn_mode_read = ft.ElevatedButton(
            text="📖 Modo Lectura (Markdown)",
            color="#000000" if self.active_tab_mode == "read" else GOLD_LIGHT,
            bgcolor=GOLD_PRIMARY if self.active_tab_mode == "read" else BG_INPUT,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY if self.active_tab_mode == "read" else BG_INPUT,
                color="#000000" if self.active_tab_mode == "read" else GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_GOLD if self.active_tab_mode == "read" else BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=lambda e: self._set_note_mode("read")
        )

        mode_row = ft.Row(
            controls=[
                ft.Row([btn_mode_write, btn_mode_read], spacing=8),
                ft.Row([btn_save, btn_delete], spacing=6)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Editor de notas o Visor Markdown
        if self.active_tab_mode == "write":
            note_content = ft.TextField(
                value=sess.summary,
                multiline=True,
                expand=True,
                min_lines=15,
                border_color=BORDER_DIM,
                focused_border_color=BORDER_GOLD,
                color="#ffffff",
                cursor_color=GOLD_LIGHT,
                content_padding=ft.padding.all(14),
                hint_text="Escribe aquí la crónica completa de los acontecimientos, conversaciones con PNJ, decisiones heroicas y notas extensas. Soporta encabezados (#), listas (-) y negritas (**)...",
                on_change=lambda e: self._on_field_edit("summary", e.control.value)
            )
        else:
            note_content = ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Markdown(
                            value=sess.summary or "*No hay notas escritas para esta sesión aún.*",
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            selectable=True
                        )
                    ],
                    expand=True,
                    padding=12
                ),
                expand=True,
                bgcolor=BG_CARD,
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(6)
            )

        self.right_panel.content = ft.Column(
            controls=[
                ft.Row([title_field, date_field, xp_field], spacing=8),
                ft.Row([loot_field], spacing=8),
                mode_row,
                ft.Divider(color=BORDER_DIM, height=1),
                note_content
            ],
            spacing=8,
            expand=True
        )

    def _set_note_mode(self, mode: str):
        self.active_tab_mode = mode
        self._render_detail_pane()
        if self.page:
            self.page.update()

    def _on_field_edit(self, field_name: str, value: str):
        if not self.selected_session:
            return
        if field_name == "title":
            self.selected_session.title = value
        elif field_name == "date":
            self.selected_session.date = value
        elif field_name == "loot":
            self.selected_session.loot = value
        elif field_name == "summary":
            self.selected_session.summary = value
        elif field_name == "xp":
            try:
                self.selected_session.xp_gained = int(value)
            except ValueError:
                pass

    def _on_save_session_click(self, e):
        self._refresh_session_list()
        self._render_detail_pane()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("✨ Crónica guardada y sincronizada correctamente."))
            self.page.snack_bar.open = True
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def _on_delete_session_click(self, e):
        if not self.selected_session:
            return
        if self.selected_session in self.char.sessions:
            self.char.sessions.remove(self.selected_session)
            self.selected_session = self.char.sessions[-1] if self.char.sessions else None
            self._refresh_session_list()
            self._render_detail_pane()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("🗑️ Sesión eliminada."))
                self.page.snack_bar.open = True
                self.page.update()
            if self.on_state_change:
                self.on_state_change()

    def update_data(self, char: CharacterSheet):
        self.char = char
        if self.char.sessions:
            if not self.selected_session or not any(s.id == self.selected_session.id for s in self.char.sessions):
                self.selected_session = self.char.sessions[-1]
        else:
            self.selected_session = None
        self._refresh_session_list()
        self._render_detail_pane()
        if self.page:
            self.update()
