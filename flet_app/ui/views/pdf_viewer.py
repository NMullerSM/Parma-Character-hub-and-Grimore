"""
Vista de Visor de Manuales & PDFs (PyMuPDF, Navegación de Índice TOC, Enlaces y Caché Eficiente)
"""
import os
import flet as ft
from typing import Optional
from ...core.pdf_engine import PdfReaderEngine
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, create_card_container
)


class PdfViewerView(ft.Container):
    def __init__(self, default_doc: str = "Manual del Jugador 2024.pdf"):
        super().__init__()
        self.engine = PdfReaderEngine(max_cached_pages=4)
        self.current_page = 1
        self.zoom = 1.0
        self.show_outline = False
        self.default_doc = default_doc
        self.expand = True

        self._build_ui()

    def _build_ui(self):
        # 1. Selector de Manual
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.repo_dir = base_dir

        self.doc_dropdown = ft.Dropdown(
            label="Manual / Documento PDF",
            width=280,
            value=self.default_doc,
            border_color=BORDER_GOLD,
            options=[
                ft.dropdown.Option("Manual del Jugador 2024.pdf", "📘 Manual del Jugador 2024"),
                ft.dropdown.Option("Guia de Xanathar Para Todo.pdf", "🔮 Guía de Xanathar para Todo"),
                ft.dropdown.Option("Caldero de Tasha para Todo.pdf", "🧪 Caldero de Tasha para Todo"),
                ft.dropdown.Option("Artanis LVL 4.pdf", "📜 Hoja Artanis LVL 4"),
            ],
            on_change=self._on_doc_change
        )

        # 2. Botón de Índice (TOC)
        self.btn_outline = ft.ElevatedButton(
            text="📑 Índice",
            style=ft.ButtonStyle(
                bgcolor=BG_INPUT,
                color=GOLD_LIGHT,
                side=ft.BorderSide(1, BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._toggle_outline
        )

        # 3. Paginación
        self.btn_first = ft.IconButton(icon=ft.Icons.FIRST_PAGE, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Primera página", on_click=lambda e: self.goto_page(1))
        self.btn_prev = ft.IconButton(icon=ft.Icons.NAVIGATE_BEFORE, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Página anterior", on_click=lambda e: self.goto_page(self.current_page - 1))
        self.page_input = ft.TextField(
            value=str(self.current_page),
            width=55,
            height=36,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.padding.all(4),
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff",
            cursor_color=GOLD_LIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=self._on_page_input_submit
        )
        self.total_pages_label = ft.Text("/ 1", size=12, color=TEXT_MUTED)
        self.btn_next = ft.IconButton(icon=ft.Icons.NAVIGATE_NEXT, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Página siguiente", on_click=lambda e: self.goto_page(self.current_page + 1))
        self.btn_last = ft.IconButton(icon=ft.Icons.LAST_PAGE, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Última página", on_click=lambda e: self.goto_page(self.engine.page_count))

        # 4. Controles de Zoom
        self.btn_zoom_out = ft.IconButton(icon=ft.Icons.ZOOM_OUT, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Alejar", on_click=self._zoom_out)
        self.zoom_label = ft.Text("100%", size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT)
        self.btn_zoom_in = ft.IconButton(icon=ft.Icons.ZOOM_IN, icon_color=GOLD_LIGHT, icon_size=20, tooltip="Acercar", on_click=self._zoom_in)
        self.btn_zoom_fit = ft.OutlinedButton(
            text="Ajustar",
            style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM)),
            on_click=self._zoom_fit
        )

        self.btn_fullscreen = ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            icon_color=GOLD_LIGHT,
            icon_size=20,
            tooltip="Alternar Pantalla Completa",
            on_click=self._toggle_fullscreen
        )

        # Barra Superior del Lector
        toolbar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=[self.btn_outline, self.doc_dropdown], spacing=8),
                    ft.Row(controls=[self.btn_first, self.btn_prev, self.page_input, self.total_pages_label, self.btn_next, self.btn_last], spacing=4),
                    ft.Row(controls=[self.btn_zoom_out, self.zoom_label, self.btn_zoom_in, self.btn_zoom_fit, self.btn_fullscreen], spacing=4),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                wrap=True
            ),
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            padding=8
        )

        # 5. Barra Lateral de Índice (TOC)
        self.outline_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=8
        )
        self.outline_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("📑 Índice de Contenidos", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.IconButton(icon=ft.Icons.CLOSE, icon_size=16, on_click=self._toggle_outline)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(color=BORDER_DIM, height=1),
                    self.outline_list
                ]
            ),
            width=280,
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(8),
            padding=10,
            visible=False
        )

        # 6. Imagen de la Página Renderizada
        self.page_image = ft.Image(
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(4)
        )

        # Barra de saltos rápidos de enlaces de página (si la página actual tiene enlaces)
        self.page_links_row = ft.Row(wrap=True, spacing=6, visible=False)

        # Viewport de lectura
        self.viewport = ft.Container(
            content=ft.Column(
                controls=[
                    self.page_links_row,
                    ft.Container(
                        content=self.page_image,
                        alignment=ft.alignment.center,
                        padding=12
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            bgcolor="#05070a",
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(8),
            expand=True
        )

        self.main_area = ft.Row(
            controls=[
                self.outline_sidebar,
                self.viewport
            ],
            expand=True,
            spacing=10
        )

        self.content = ft.Column(
            controls=[
                toolbar,
                self.main_area
            ],
            spacing=8,
            expand=True
        )

    def did_mount(self):
        # Cargar documento por defecto al montar
        self.load_doc(self.default_doc)

    def load_doc(self, doc_filename: str):
        full_path = os.path.join(self.repo_dir, doc_filename)
        success = self.engine.open_document(full_path)
        if success:
            self.current_page = 1
            self.total_pages_label.value = f"/ {self.engine.page_count}"
            self._populate_outline()
            self.render_current_page()
        else:
            print(f"[PdfViewerView] No se pudo abrir {full_path}")

    def render_current_page(self):
        if not self.engine.is_open:
            return

        b64 = self.engine.render_page_base64(self.current_page, zoom=self.zoom)
        if b64:
            self.page_image.src_base64 = b64
            self.page_input.value = str(self.current_page)
            self._update_page_links()
            if self.page:
                self.page.update()

    def _update_page_links(self):
        links = self.engine.get_page_links(self.current_page)
        self.page_links_row.controls.clear()

        if links:
            self.page_links_row.visible = True
            # Mostrar hasta 12 enlaces más relevantes de la página
            self.page_links_row.controls.append(
                ft.Text("🔗 Enlaces en esta página:", size=11, color=GOLD_LIGHT, weight=ft.FontWeight.BOLD)
            )
            for lk in links[:10]:
                tgt = lk["target_page"]
                btn = ft.TextButton(
                    text=f"Pág. {tgt}",
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=6, vertical=2)),
                    on_click=lambda e, p=tgt: self.goto_page(p)
                )
                self.page_links_row.controls.append(btn)
        else:
            self.page_links_row.visible = False

    def _populate_outline(self):
        self.outline_list.controls.clear()
        toc = self.engine.get_toc()

        if not toc:
            self.outline_list.controls.append(
                ft.Text("Este documento no contiene índice digital incorporado.", size=12, color=TEXT_MUTED, italic=True)
            )
            return

        for item in toc:
            lvl = item["level"]
            title = item["title"]
            page_target = item["page"]
            indent = max(0, (lvl - 1) * 14)

            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(title, size=12, color=GOLD_LIGHT, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(str(page_target), size=10, color=TEXT_MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=ft.padding.only(left=indent, top=4, bottom=4, right=4),
                border_radius=ft.border_radius.all(4),
                ink=True,
                on_click=lambda e, p=page_target: self.goto_page(p)
            )
            self.outline_list.controls.append(btn)

    def goto_page(self, page_num: int):
        if not self.engine.is_open:
            return
        target = max(1, min(self.engine.page_count, page_num))
        if target != self.current_page:
            self.current_page = target
            self.render_current_page()

    def _on_page_input_submit(self, e):
        try:
            val = int(self.page_input.value)
            self.goto_page(val)
        except ValueError:
            self.page_input.value = str(self.current_page)
            if self.page:
                self.page.update()

    def _zoom_in(self, e):
        self.zoom = min(2.5, round(self.zoom + 0.2, 1))
        self.zoom_label.value = f"{int(self.zoom * 100)}%"
        self.render_current_page()

    def _zoom_out(self, e):
        self.zoom = max(0.5, round(self.zoom - 0.2, 1))
        self.zoom_label.value = f"{int(self.zoom * 100)}%"
        self.render_current_page()

    def _zoom_fit(self, e):
        self.zoom = 1.0
        self.zoom_label.value = "100%"
        self.render_current_page()

    def _toggle_outline(self, e):
        self.show_outline = not self.show_outline
        self.outline_sidebar.visible = self.show_outline
        if self.page:
            self.page.update()

    def _toggle_fullscreen(self, e):
        if self.page:
            self.page.window.full_screen = not self.page.window.full_screen
            self.btn_fullscreen.icon = ft.Icons.FULLSCREEN_EXIT if self.page.window.full_screen else ft.Icons.FULLSCREEN
            self.page.update()

    def _on_doc_change(self, e):
        doc_name = e.control.value
        self.load_doc(doc_name)

