"""
Tema y Paleta Visual Dark Fantasy para Visualizador Dnd (Flet)
Inspirado en D&D 5e oficial: Oro envejecido, Obsidiana y Superficies místicas.
"""
import flet as ft
from typing import Optional

# Paleta de Colores
BG_PRIMARY = "#090a0f"
BG_SURFACE = "#11141e"
BG_CARD = "#171b26"
BG_CARD_ALT = "#1f2433"
BG_INPUT = "#0e111a"

GOLD_PRIMARY = "#c9a45c"
GOLD_LIGHT = "#e6ca85"
GOLD_GLOW = "#ffd700"
GOLD_MUTED = "rgba(201, 164, 92, 0.25)"

BORDER_GOLD = "#c9a45c"
BORDER_DIM = "#2d3345"

TEXT_MAIN = "#f0f2f5"
TEXT_MUTED = "#9ba3b5"

COLOR_RED = "#ef4444"
COLOR_RED_DIM = "rgba(239, 68, 68, 0.18)"
COLOR_GREEN = "#22c55e"
COLOR_GREEN_DIM = "rgba(34, 197, 94, 0.18)"
COLOR_BLUE = "#3b82f6"
COLOR_BLUE_DIM = "rgba(59, 130, 246, 0.18)"
COLOR_PURPLE = "#a855f7"
COLOR_PURPLE_DIM = "rgba(168, 85, 247, 0.18)"
COLOR_AMBER = "#f59e0b"

# Estilos de Contenedores y Tarjetas
def create_card_container(
    content: ft.Control,
    padding: int = 14,
    border_color: str = BORDER_DIM,
    bg_color: str = BG_CARD,
    expand: bool = False
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=bg_color,
        border=ft.border.all(1, border_color),
        border_radius=ft.border_radius.all(8),
        expand=expand
    )

def create_badge(text: str, bg_color: str = BG_CARD_ALT, text_color: str = GOLD_LIGHT, border_color: str = BORDER_GOLD) -> ft.Container:
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=text_color),
        bgcolor=bg_color,
        border=ft.border.all(1, border_color),
        border_radius=ft.border_radius.all(4),
        padding=ft.padding.symmetric(horizontal=8, vertical=3)
    )

def create_gold_button(
    text: str,
    icon: Optional[str] = None,
    on_click = None,
    tooltip: str = ""
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        style=ft.ButtonStyle(
            bgcolor=GOLD_PRIMARY,
            color="#111111",
            shape=ft.RoundedRectangleBorder(radius=6)
        )
    )

def get_app_theme() -> ft.Theme:
    """Configuración del tema global para alto contraste y tipografía legible."""
    return ft.Theme(
        font_family="Segoe UI",
        color_scheme_seed=GOLD_PRIMARY,
        color_scheme=ft.ColorScheme(
            primary=GOLD_PRIMARY,
            on_primary="#111111",
            surface=BG_SURFACE,
            on_surface="#f0f2f5",
            background=BG_PRIMARY,
            on_background="#f0f2f5"
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(color="#f0f2f5"),
            body_medium=ft.TextStyle(color="#f0f2f5"),
            body_small=ft.TextStyle(color=TEXT_MUTED),
            title_large=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            title_medium=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            title_small=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            label_large=ft.TextStyle(color="#f0f2f5"),
            label_medium=ft.TextStyle(color="#f0f2f5"),
            label_small=ft.TextStyle(color=TEXT_MUTED),
        )
    )
