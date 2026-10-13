"""
Componente BuilderHub: Hub Central de Selección de Modo de Creación.
Inspirado en la pantalla de bienvenida de D&D Beyond (/characters/builder):
Presenta los 3 modos oficiales de forja:
1. Standard Build (Paso a paso en 7 fases con control total de reglas y point buy)
2. Quick Build (Creación asistida en 60 segundos por arquetipos)
3. Randomize (Generación procedural con filtros de nivel 1-20 y re-roll)
"""
import flet as ft
from typing import Callable, Optional
from ..theme import (
    TTUI_BG_CANVAS, TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD,
    TTUI_GOLD_LIGHT, TTUI_CRIMSON, TTUI_PARCHMENT, TTUI_RUNIC_GREY,
    BG_INPUT, create_badge, create_crimson_button, create_gold_button
)


class BuilderHubDialog:
    def __init__(
        self,
        page: ft.Page,
        on_start_standard: Callable[[], None],
        on_start_quick: Callable[[], None],
        on_start_random: Callable[[], None],
        on_open_saved: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.on_start_standard = on_start_standard
        self.on_start_quick = on_start_quick
        self.on_start_random = on_start_random
        self.on_open_saved = on_open_saved

        self._build_dialog()

    def show(self):
        self.page.open(self.dialog)

    def close(self):
        self.page.close(self.dialog)

    def _build_dialog(self):
        # 1. Tarjeta Standard Build
        card_standard = self._build_pathway_card(
            title="Standard Build",
            subtitle="Constructor Detallado (7 Fases)",
            badge_text="RECOMENDADO PARA CAMPAÑAS",
            badge_color=TTUI_GOLD,
            icon=ft.Icons.AUTO_STORIES,
            description=(
                "Control minucioso sobre cada decisión: compra de atributos por puntos (Point Buy), "
                "linajes de especie, subclases y arquetipos, dotes de origen PHB 2024, equipo pieza por pieza y grimorio."
            ),
            features=[
                "✓ Stepper guiado en 7 fases fluidas",
                "✓ Point Buy 27 pts & Standard Array",
                "✓ Compendio oficial OKF en Markdown",
                "✓ Niveles 1-20 & Multiclase"
            ],
            btn_text="Comenzar Forja (7 Fases) ➔",
            btn_primary=True,
            on_click=lambda e: (self.close(), self.on_start_standard())
        )

        # 2. Tarjeta Quick Build
        card_quick = self._build_pathway_card(
            title="Quick Build",
            subtitle="Creación Asistida (60 Segundos)",
            badge_text="PARTIDAS ONE-SHOT",
            badge_color=TTUI_CRIMSON,
            icon=ft.Icons.FLASH_ON,
            description=(
                "Forja un aventurero listo para combatir en menos de un minuto. Elige únicamente Nombre, Especie "
                "y Clase: el algoritmo asigna automáticamente atributos por jerarquía óptima, equipo y conjuros."
            ),
            features=[
                "✓ Solo 3 decisiones clave",
                "✓ Standard Array balanceado por clase",
                "✓ Equipo y conjuros sugeridos",
                "✓ Exportación directa a PDF y ficha"
            ],
            btn_text="Crear en 60 Segundos ⚔",
            btn_primary=False,
            on_click=lambda e: (self.close(), self.on_start_quick())
        )

        # 3. Tarjeta Randomize
        card_random = self._build_pathway_card(
            title="Randomize",
            subtitle="Los Dados del Destino (Procedural)",
            badge_text="GENERADOR CAÓTICO",
            badge_color="#a855f7",
            icon=ft.Icons.CASINO,
            description=(
                "Entrega tu destino al azar. Genera combinaciones impredecibles y coherentes de nivel 1 a 20 con "
                "tiradas oficiales 4d6, trasfondos aleatorios, rasgos de personalidad y botón de re-tirada instantánea."
            ),
            features=[
                "✓ Tiradas reales 4d6 drop lowest",
                "✓ Selector de nivel configurable (1-20)",
                "✓ Filtros opcionales de clase/especie",
                "✓ Botón Re-Roll ilimitado"
            ],
            btn_text="Tirar Destino (d20) 🎲",
            btn_primary=False,
            on_click=lambda e: (self.close(), self.on_start_random())
        )

        cards_row = ft.Row(
            controls=[card_standard, card_quick, card_random],
            spacing=14,
            alignment=ft.MainAxisAlignment.CENTER
        )

        btn_saved = ft.OutlinedButton(
            text="📂 Abrir Mis Personajes Guardados",
            icon=ft.Icons.FOLDER_SHARED,
            style=ft.ButtonStyle(color=TTUI_GOLD_LIGHT, side=ft.BorderSide(1, TTUI_BORDER_SLATE)),
            on_click=lambda e: (self.close(), self.on_open_saved() if self.on_open_saved else None)
        )

        header_row = ft.Row(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=TTUI_GOLD, size=26),
                    ft.Column([
                        ft.Text("Forja de Personajes D&D 5e", size=20, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                        ft.Text("Elige tu senda de creación según el tiempo disponible y nivel de detalle deseado:", size=12, color=TTUI_RUNIC_GREY),
                    ], spacing=1)
                ], spacing=10),
                ft.Row([
                    btn_saved,
                    ft.IconButton(ft.Icons.CLOSE, icon_color=TTUI_RUNIC_GREY, on_click=lambda e: self.close())
                ], spacing=6)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=header_row,
            content=ft.Container(
                content=ft.ListView(
                    controls=[
                        cards_row
                    ],
                    spacing=12,
                    expand=True
                ),
                width=960,
                height=490,
                padding=ft.padding.only(top=10)
            ),
            actions=[
                ft.Text("Inspirado en la arquitectura oficial de D&D Beyond (PHB 2024 / Compendios OKF)", size=11, color=TTUI_RUNIC_GREY, italic=True)
            ]
        )

    def _build_pathway_card(
        self,
        title: str,
        subtitle: str,
        badge_text: str,
        badge_color: str,
        icon: str,
        description: str,
        features: list,
        btn_text: str,
        btn_primary: bool,
        on_click: Callable
    ) -> ft.Container:
        feature_texts = [ft.Text(f, size=11, color=TTUI_PARCHMENT) for f in features]

        if btn_primary:
            btn_action = ft.ElevatedButton(
                text=btn_text,
                bgcolor=TTUI_GOLD,
                color="#000000",
                style=ft.ButtonStyle(bgcolor=TTUI_GOLD, color="#000000", shape=ft.RoundedRectangleBorder(radius=6)),
                on_click=on_click
            )
        else:
            btn_action = ft.ElevatedButton(
                text=btn_text,
                bgcolor=TTUI_CRIMSON if badge_color == TTUI_CRIMSON else BG_INPUT,
                color="#ffffff" if badge_color == TTUI_CRIMSON else TTUI_GOLD_LIGHT,
                style=ft.ButtonStyle(
                    bgcolor=TTUI_CRIMSON if badge_color == TTUI_CRIMSON else BG_INPUT,
                    color="#ffffff" if badge_color == TTUI_CRIMSON else TTUI_GOLD_LIGHT,
                    side=ft.BorderSide(1, TTUI_BORDER_SLATE if badge_color != TTUI_CRIMSON else TTUI_GOLD),
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=on_click
            )

        card = ft.Container(
            content=ft.Column(
                controls=[
                    create_badge(badge_text, bg_color=BG_INPUT, text_color=badge_color, border_color=badge_color),
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=TTUI_GOLD_LIGHT, size=28),
                            ft.Column([
                                ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                                ft.Text(subtitle, size=11, color=TTUI_RUNIC_GREY),
                            ], spacing=1)
                        ],
                        spacing=8
                    ),
                    ft.Divider(color=TTUI_BORDER_SLATE, height=1),
                    ft.Text(description, size=12, color="#dcdfe1", height=70),
                    ft.Column(controls=feature_texts, spacing=3),
                    ft.Container(expand=True),
                    btn_action
                ],
                spacing=8,
                expand=True
            ),
            width=290,
            height=440,
            bgcolor=TTUI_SURFACE_CARD,
            border=ft.border.all(1.5 if btn_primary else 1, TTUI_GOLD if btn_primary else TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(8),
            padding=14
        )
        return card
