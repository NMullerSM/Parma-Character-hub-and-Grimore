"""
Tema y Paleta Visual Dark Fantasy para Visualizador Dnd (Flet)
Inspirado en D&D 5e oficial: Oro envejecido, Obsidiana y Superficies místicas.
"""
import flet as ft
from typing import Optional

# Paleta de Colores Base
BG_PRIMARY = "#0e1418"     # Profundidad oscura / Obsidian bedrock
BG_SURFACE = "#161c20"     # Superficie elevada
BG_CARD = "#1a2024"        # Tarjetas principales
BG_CARD_ALT = "#232b2f"    # Tarjetas alternas / seleccionadas
BG_INPUT = "#12181c"       # Entradas y cavidades

GOLD_PRIMARY = "#c9a45c"   # Oro envejecido oficial
GOLD_LIGHT = "#e8c176"     # Oro luminoso
GOLD_GLOW = "#ffd700"
GOLD_MUTED = "rgba(201, 164, 92, 0.25)"

BORDER_GOLD = "#c9a45c"
BORDER_DIM = "#323d42"      # Borde de piedra forjada TTUI

TEXT_MAIN = "#ede3d2"      # Pergamino iluminado oficial
TEXT_MUTED = "#8c979e"     # Gris rúnico templado

# Acentos oficiales TTUI (TableTop UI D&D Beyond)
TTUI_BG_CANVAS = "#12181c"
TTUI_SURFACE_CARD = "#232b2f"
TTUI_BORDER_SLATE = "#323d42"
TTUI_CRIMSON = "#c50009"
TTUI_CRIMSON_DARK = "#800006"
TTUI_GOLD = "#c9a45c"
TTUI_GOLD_LIGHT = "#e8c176"
TTUI_PARCHMENT = "#ede3d2"
TTUI_PARCHMENT_LIGHT = "#f5f3ee"
TTUI_RUNIC_GREY = "#8c979e"

COLOR_RED = "#c50009"
COLOR_RED_DIM = "rgba(197, 0, 9, 0.22)"
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
        border_radius=ft.border_radius.all(6),
        expand=expand
    )

def create_badge(
    text: str,
    bg_color: str = BG_CARD_ALT,
    text_color: str = GOLD_LIGHT,
    border_color: str = BORDER_GOLD
) -> ft.Container:
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
        color="#000000",
        bgcolor=GOLD_PRIMARY,
        style=ft.ButtonStyle(
            bgcolor=GOLD_PRIMARY,
            color="#000000",
            shape=ft.RoundedRectangleBorder(radius=6)
        )
    )

def create_crimson_button(
    text: str,
    icon: Optional[str] = None,
    on_click = None,
    tooltip: str = ""
) -> ft.ElevatedButton:
    """Botón de acción épica / primaria con carmesí oficial D&D Beyond y ribete dorado."""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        color="#ffffff",
        bgcolor=TTUI_CRIMSON,
        style=ft.ButtonStyle(
            bgcolor=TTUI_CRIMSON,
            color="#ffffff",
            side=ft.BorderSide(1, BORDER_GOLD),
            shape=ft.RoundedRectangleBorder(radius=6)
        )
    )

def create_secondary_button(
    text: str,
    icon: Optional[str] = None,
    on_click = None,
    tooltip: str = ""
) -> ft.OutlinedButton:
    """Botón secundario de hierro cepillado y ribete dorado suave."""
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        style=ft.ButtonStyle(
            bgcolor=TTUI_SURFACE_CARD,
            color=TTUI_PARCHMENT,
            side=ft.BorderSide(1, BORDER_DIM),
            shape=ft.RoundedRectangleBorder(radius=6)
        )
    )

def create_success_button(
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
        color="#ffffff",
        bgcolor=COLOR_GREEN,
        style=ft.ButtonStyle(
            bgcolor=COLOR_GREEN,
            color="#ffffff",
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
            on_primary="#000000",
            surface=BG_SURFACE,
            on_surface=TEXT_MAIN,
            background=BG_PRIMARY,
            on_background=TEXT_MAIN
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(color=TEXT_MAIN),
            body_medium=ft.TextStyle(color=TEXT_MAIN),
            body_small=ft.TextStyle(color=TEXT_MUTED),
            title_large=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            title_medium=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            title_small=ft.TextStyle(color=GOLD_LIGHT, weight=ft.FontWeight.BOLD),
            label_large=ft.TextStyle(color=TEXT_MAIN),
            label_medium=ft.TextStyle(color=TEXT_MAIN),
            label_small=ft.TextStyle(color=TEXT_MUTED),
        )
    )

