"""
Vista de Diario de Campaña & Registro de Sesiones
"""
import flet as ft
from datetime import datetime
from typing import Callable, Optional
from ...core.models import CharacterSheet, SessionLog
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, create_card_container
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

        self._build_ui()

    def _build_ui(self):
        # Campos de entrada de nueva sesión
        self.date_input = ft.TextField(
            label="Fecha",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=140,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )
        self.title_input = ft.TextField(
            label="Título de la Sesión",
            hint_text="Ej. El Enclave de los Susurros...",
            expand=True,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )
        self.summary_input = ft.TextField(
            label="Resumen de Acontecimientos",
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )
        self.loot_input = ft.TextField(
            label="Botín Obtenido",
            hint_text="Ej. 150 PO, Daga ceremonial de plata...",
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8)
        )
        self.xp_input = ft.TextField(
            label="PX Ganados",
            value="300",
            width=120,
            border_color=BORDER_DIM,
            content_padding=ft.padding.all(8),
            keyboard_type=ft.KeyboardType.NUMBER
        )

        btn_add_session = ft.ElevatedButton(
            text="+ Registrar Sesión",
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#000000",
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._on_add_session
        )

        new_session_box = create_card_container(
            content=ft.Column(
                controls=[
                    ft.Text("✍️ Nueva Entrada en la Crónica", size=15, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Row(controls=[self.date_input, self.title_input], spacing=8),
                    self.summary_input,
                    ft.Row(controls=[self.loot_input, self.xp_input, btn_add_session], spacing=8),
                ],
                spacing=10
            )
        )

        # Historial de Sesiones
        self.logs_column = ft.Column(spacing=10)
        self._populate_logs()

        self.content = ft.ListView(
            controls=[
                ft.Text("📖 Crónica & Diario de Campaña", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ft.Text("Registra las aventuras, decisiones épicas, tesoros encontrados y experiencia acumulada.", size=12, color=TEXT_MUTED),
                ft.Divider(color=BORDER_DIM, height=1),
                new_session_box,
                ft.Text("📜 Historial Cronológico", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                self.logs_column
            ],
            spacing=12,
            expand=True
        )

    def _populate_logs(self):
        self.logs_column.controls.clear()
        if not self.char.sessions:
            self.logs_column.controls.append(
                ft.Container(
                    content=ft.Text("Aún no hay sesiones registradas. ¡Escribe la primera aventura arriba!", size=12, color=TEXT_MUTED, italic=True),
                    padding=16,
                    alignment=ft.alignment.center
                )
            )
            return

        for sess in reversed(self.char.sessions):
            card = create_card_container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"📅 {sess.date} - {sess.title}", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                                ft.Text(f"+{sess.xp_gained} PX", size=12, weight=ft.FontWeight.BOLD, color=GOLD_PRIMARY),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(sess.summary, size=12, color="#d1d5db"),
                        ft.Text(f"💎 Botín: {sess.loot}", size=11, color=TEXT_MUTED, italic=True) if sess.loot else ft.Container(),
                    ],
                    spacing=6
                )
            )
            self.logs_column.controls.append(card)

    def _on_add_session(self, e):
        title = self.title_input.value.strip()
        if not title:
            return

        xp = 0
        try:
            xp = int(self.xp_input.value)
        except ValueError:
            pass

        log = SessionLog(
            id=str(len(self.char.sessions) + 1),
            date=self.date_input.value.strip(),
            title=title,
            summary=self.summary_input.value.strip(),
            loot=self.loot_input.value.strip(),
            xp_gained=xp
        )

        self.char.sessions.append(log)
        self.char.xp += xp

        # Limpiar formulario
        self.title_input.value = ""
        self.summary_input.value = ""
        self.loot_input.value = ""

        self._populate_logs()
        if self.page:
            self.page.update()
        if self.on_state_change:
            self.on_state_change()

    def update_data(self, char: CharacterSheet):
        self.char = char
        self._populate_logs()
        if self.page:
            self.update()
