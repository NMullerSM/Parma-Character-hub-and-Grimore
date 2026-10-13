"""
Componente OkfDrawer: Panel Lateral Deslizante (Side Drawer / Split Detail) para el Compendio OKF.
Inspirado en el Side Drawer de D&D Beyond:
Permite inspeccionar el compendio íntegro en Markdown oficial (con tablas, rasgos y requisitos)
de cualquier Especie, Clase, Dote o Conjuro sin abandonar el asistente ni perder el contexto de creación.
"""
import flet as ft
from typing import Optional, Callable, Dict, Any
from ...core.okf_engine import OkfEngine
from ..theme import (
    TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD, TTUI_GOLD_LIGHT,
    TTUI_PARCHMENT, TTUI_RUNIC_GREY, TTUI_CRIMSON, BG_INPUT, BORDER_GOLD,
    create_badge, create_crimson_button
)


class OkfDrawer(ft.Container):
    def __init__(
        self,
        okf_engine: OkfEngine,
        on_select_item: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_close: Optional[Callable[[], None]] = None
    ):
        self.okf = okf_engine
        self.on_select_item = on_select_item
        self.on_close = on_close
        self.current_item: Optional[Dict[str, Any]] = None

        self.title_text = ft.Text("Detalle del Compendio", size=16, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT)
        self.type_badge = create_badge("OKF", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD)
        self.markdown_viewer = ft.Markdown(
            value="*Selecciona un elemento para consultar su ficha del compendio.*",
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            selectable=True
        )

        self.btn_select = ft.ElevatedButton(
            text="✔ Seleccionar",
            bgcolor=TTUI_GOLD,
            color="#000000",
            style=ft.ButtonStyle(bgcolor=TTUI_GOLD, color="#000000"),
            on_click=self._on_select_click
        )

        btn_close = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=TTUI_RUNIC_GREY,
            icon_size=20,
            tooltip="Cerrar panel",
            on_click=self._on_close_click
        )

        content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row([self.type_badge, self.title_text], spacing=8),
                        btn_close
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                ft.Container(
                    content=ft.ListView(
                        controls=[self.markdown_viewer],
                        spacing=8,
                        expand=True
                    ),
                    expand=True
                ),
                ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                ft.Row(
                    controls=[
                        ft.TextButton("Cerrar", style=ft.ButtonStyle(color=TTUI_RUNIC_GREY), on_click=self._on_close_click),
                        self.btn_select
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ],
            spacing=8,
            expand=True
        )

        super().__init__(
            content=content,
            width=360,
            bgcolor=TTUI_SURFACE_CARD,
            border=ft.border.only(left=ft.BorderSide(1.5, TTUI_BORDER_SLATE)),
            padding=14,
            visible=False,
            expand=False
        )

    def show_entity(self, item_metadata: Dict[str, Any], can_select: bool = True):
        """Muestra los detalles de una entidad buscando su archivo OKF o datos en memoria."""
        self.current_item = item_metadata
        self.visible = True
        self.btn_select.visible = can_select

        name = item_metadata.get("nombre", item_metadata.get("name", "Detalle"))
        tipo = item_metadata.get("tipo", "Regla").capitalize()
        self.title_text.value = name
        self.type_badge.content.value = tipo

        # Cargar Markdown real
        rel_path = item_metadata.get("archivo", "")
        body_text = ""
        if rel_path:
            parsed = self.okf.read_entity_file(rel_path)
            if parsed:
                body_text = parsed.get("body", "")

        if not body_text:
            desc = item_metadata.get("descripcion", item_metadata.get("desc", ""))
            body_text = f"### {name}\n\n{desc}"

        self.markdown_viewer.value = body_text
        if self.page:
            self.update()

    def hide(self):
        self.visible = False
        self.current_item = None
        if self.page:
            self.update()

    def _on_close_click(self, e):
        self.hide()
        if self.on_close:
            self.on_close()

    def _on_select_click(self, e):
        if self.current_item and self.on_select_item:
            self.on_select_item(self.current_item)
        self.hide()
