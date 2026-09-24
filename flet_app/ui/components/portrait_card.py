"""
Componente de Retrato y Avatar Artístico del Personaje (D&D 5e).
Marco ornamental dorado, soporte para imágenes locales y fallback estilizado con iniciales e icono de clase.
"""
import os
import flet as ft
from typing import Optional, Callable
from ...core.models import CharacterSheet
from ...core.db import DatabaseManager
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_GOLD, GOLD_LIGHT, GOLD_PRIMARY,
    TEXT_MUTED, COLOR_AMBER, create_card_container
)

# Mapeo de iconos temáticos según la clase
CLASS_ICONS = {
    "bardo": ft.Icons.MUSIC_NOTE,
    "brujo": ft.Icons.LOCAL_FIRE_DEPARTMENT,
    "clérigo": ft.Icons.SHIELD,
    "druida": ft.Icons.FOREST,
    "explorador": ft.Icons.NAVIGATION,
    "guerrero": ft.Icons.SPORTS_MARTIAL_ARTS,
    "hechicero": ft.Icons.AUTO_AWESOME,
    "mago": ft.Icons.AUTO_STORIES,
    "monje": ft.Icons.SELF_IMPROVEMENT,
    "paladín": ft.Icons.SECURITY,
    "pícaro": ft.Icons.VISIBILITY_OFF,
    "bárbaro": ft.Icons.FITNESS_CENTER,
}


class CharacterPortraitCard(ft.Container):
    def __init__(
        self,
        char: CharacterSheet,
        size: int = 96,
        on_portrait_changed: Optional[Callable[[], None]] = None,
        page: Optional[ft.Page] = None
    ):
        super().__init__()
        self.char = char
        self.size = size
        self.on_portrait_changed = on_portrait_changed
        self.page_ref = page
        self.file_picker: Optional[ft.FilePicker] = None

        self.width = self.size
        self.height = self.size
        self.border_radius = ft.border_radius.all(10)
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS

        self._build_ui()

    def _get_class_icon(self) -> str:
        cls_lower = (self.char.char_class or "").lower()
        for k, icon in CLASS_ICONS.items():
            if k in cls_lower:
                return icon
        return ft.Icons.PERSON

    def _get_initials(self) -> str:
        parts = (self.char.name or "Héroe").split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "D&D"

    def _build_ui(self):
        # Verificar si hay imagen válida en disco
        has_image = bool(self.char.portrait_path and os.path.exists(self.char.portrait_path))

        if has_image:
            avatar_content = ft.Image(
                src=self.char.portrait_path,
                fit=ft.ImageFit.COVER,
                width=self.size,
                height=self.size,
                border_radius=ft.border_radius.all(8)
            )
        else:
            avatar_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(self._get_class_icon(), size=self.size * 0.38, color=GOLD_LIGHT),
                        ft.Text(self._get_initials(), size=self.size * 0.22, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2
                ),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#241a0d", "#121214"]
                ),
                alignment=ft.alignment.center,
                width=self.size,
                height=self.size,
            )

        # Botón de edición flotante sutil
        edit_overlay = ft.Container(
            content=ft.Icon(ft.Icons.CAMERA_ALT, size=16, color=GOLD_LIGHT),
            bgcolor=ft.Colors.with_opacity(0.65, "#000000"),
            border_radius=ft.border_radius.all(12),
            padding=ft.padding.all(4),
            right=4,
            bottom=4,
            tooltip="Cambiar retrato del personaje"
        )

        self.content = ft.Stack(
            controls=[
                avatar_content,
                edit_overlay
            ]
        )
        self.bgcolor = BG_CARD
        self.border = ft.border.all(2, BORDER_GOLD)
        self.on_click = self._on_card_click
        self.tooltip = f"Retrato de {self.char.name} (clic para cambiar foto)"

    def attach_file_picker(self, picker: ft.FilePicker):
        self.file_picker = picker
        self.file_picker.on_result = self._on_file_selected

    def _on_card_click(self, e):
        if self.file_picker:
            self.file_picker.pick_files(
                dialog_title="Seleccionar Retrato del Personaje",
                allowed_extensions=["png", "jpg", "jpeg", "webp"],
                allow_multiple=False
            )

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            selected_path = e.files[0].path
            if selected_path and os.path.exists(selected_path):
                db = DatabaseManager()
                saved_path = db.save_portrait_file(selected_path, self.char.name)
                self.char.portrait_path = saved_path
                self._build_ui()
                if self.page:
                    self.update()
                if self.on_portrait_changed:
                    self.on_portrait_changed()

    def update_char(self, new_char: CharacterSheet):
        self.char = new_char
        self._build_ui()
        if self.page:
            self.update()
