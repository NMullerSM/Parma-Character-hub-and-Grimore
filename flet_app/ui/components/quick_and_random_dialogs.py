"""
Diálogos de Creación Rápida (QuickBuildDialog) y Generación Procedural (RandomizeDialog).
Inspirados en los modos 2 y 3 de D&D Beyond:
- Quick Build: Asistido en 1 minuto eligiendo Nombre, Especie y Clase.
- Randomize: Generación procedural con tiradas 4d6, selector de nivel (1-20) y botón Re-Roll.
"""
import flet as ft
from typing import Callable, Optional, Dict, Any

from ...core.models import CharacterSheet, CharacterFeature, WeaponAction, SpellSlotTier
from ...core.quick_build import QuickBuildEngine, CLASS_ABILITY_PRIORITIES
from ...core.random_generator import RandomCharacterGenerator, CLASSES_LIST, SPECIES_LIST
from ...core.rules import calc_modifier, calc_proficiency_bonus
from ..theme import (
    TTUI_BG_CANVAS, TTUI_SURFACE_CARD, TTUI_BORDER_SLATE, TTUI_GOLD,
    TTUI_GOLD_LIGHT, TTUI_CRIMSON, TTUI_PARCHMENT, TTUI_RUNIC_GREY,
    BG_INPUT, BG_CARD, BORDER_DIM, BORDER_GOLD, COLOR_GREEN,
    create_badge, create_crimson_button, create_gold_button
)

HD_BY_CLASS = {
    "Bárbaro": 12, "Guerrero": 10, "Paladín": 10, "Explorador": 10,
    "Bardo": 8, "Clérigo": 8, "Druida": 8, "Monje": 8, "Pícaro": 8, "Brujo": 8,
    "Hechicero": 6, "Mago": 6
}

SAVES_BY_CLASS = {
    "Bárbaro": ["FUE", "CON"], "Bardo": ["DES", "CAR"], "Clérigo": ["SAB", "CAR"],
    "Druida": ["INT", "SAB"], "Guerrero": ["FUE", "CON"], "Monje": ["FUE", "DES"],
    "Paladín": ["SAB", "CAR"], "Explorador": ["FUE", "DES"], "Pícaro": ["DES", "INT"],
    "Hechicero": ["CON", "CAR"], "Brujo": ["SAB", "CAR"], "Mago": ["INT", "SAB"]
}


class QuickBuildDialog:
    def __init__(
        self,
        page: ft.Page,
        on_character_created: Callable[[CharacterSheet], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.on_character_created = on_character_created
        self.on_cancel = on_cancel

        self.char_name = "Kaelen el Rápido"
        self.char_species = "Humano"
        self.char_class = "Guerrero"

        self._build_dialog()

    def show(self):
        self._update_preview()
        self.page.open(self.dialog)

    def close(self):
        self.page.close(self.dialog)

    def _update_preview(self):
        raw, final, bg, p2, p1 = QuickBuildEngine.generate_quick_stats(self.char_class, self.char_species)
        preset = QuickBuildEngine.get_preset_for_class(self.char_class)

        stats_pills = []
        for s, v in final.items():
            mod = calc_modifier(v)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            stats_pills.append(
                create_badge(f"{s}: {v} ({mod_str})", bg_color=BG_INPUT, text_color=TTUI_GOLD_LIGHT, border_color=BORDER_GOLD if s in [p2, p1] else BORDER_DIM)
            )

        hd = HD_BY_CLASS.get(self.char_class, 8)
        con_mod = calc_modifier(final.get("CON", 10))
        hp = max(1, hd + con_mod)
        ca = 10 + calc_modifier(final.get("DES", 10))

        self.preview_container.content = ft.Column([
            ft.Text(f"⚔️ Resumen de Nivel 1 ({self.char_class} - {self.char_species}):", size=13, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
            ft.Row(controls=stats_pills, wrap=True, spacing=6),
            ft.Row([
                create_badge(f"❤️ {hp} PG", bg_color=BG_INPUT, text_color=COLOR_GREEN, border_color=COLOR_GREEN),
                create_badge(f"🛡️ {ca} CA", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD),
                create_badge(f"📜 Trasfondo: {bg}", bg_color=BG_INPUT, text_color=TTUI_PARCHMENT, border_color=TTUI_BORDER_SLATE),
            ], spacing=8),
            ft.Text(f"Habilidades recomendadas: {', '.join(preset.get('skills', []))}", size=11, color=TTUI_RUNIC_GREY),
        ], spacing=8)
        if getattr(self.dialog, "page", None):
            self.dialog.update()

    def _build_dialog(self):
        name_input = ft.TextField(
            label="Nombre del Héroe",
            value=self.char_name,
            border_color=BORDER_GOLD,
            expand=True,
            on_change=lambda e: setattr(self, "char_name", e.control.value)
        )

        species_dd = ft.Dropdown(
            label="Especie",
            value=self.char_species,
            options=[ft.dropdown.Option(s, s) for s in SPECIES_LIST],
            width=180,
            border_color=BORDER_DIM,
            on_change=lambda e: (setattr(self, "char_species", e.control.value), self._update_preview())
        )

        class_dd = ft.Dropdown(
            label="Clase",
            value=self.char_class,
            options=[ft.dropdown.Option(c, c) for c in CLASSES_LIST],
            width=180,
            border_color=BORDER_DIM,
            on_change=lambda e: (setattr(self, "char_class", e.control.value), self._update_preview())
        )

        self.preview_container = ft.Container(
            bgcolor=BG_CARD,
            padding=12,
            border=ft.border.all(1, TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(6)
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.FLASH_ON, color=TTUI_CRIMSON, size=24),
                    ft.Text("Quick Build: Creación Asistida en 60 Segundos", size=17, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ], spacing=8),
                ft.IconButton(ft.Icons.CLOSE, icon_color=TTUI_RUNIC_GREY, on_click=lambda e: self.close())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Elige los 3 datos fundamentales. Las reglas oficiales optimizarán el resto automáticamente:", size=12, color=TTUI_RUNIC_GREY),
                    name_input,
                    ft.Row([species_dd, class_dd], spacing=10),
                    self.preview_container
                ], spacing=12),
                width=580,
                height=290
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TTUI_RUNIC_GREY), on_click=lambda e: self.close()),
                ft.ElevatedButton(
                    text="⚔️ ¡Forjar Héroe Rápido!",
                    bgcolor=TTUI_CRIMSON,
                    color="#ffffff",
                    style=ft.ButtonStyle(bgcolor=TTUI_CRIMSON, color="#ffffff", side=ft.BorderSide(1, BORDER_GOLD)),
                    on_click=self._forge_quick
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _forge_quick(self, e):
        raw, final, bg, p2, p1 = QuickBuildEngine.generate_quick_stats(self.char_class, self.char_species)
        preset = QuickBuildEngine.get_preset_for_class(self.char_class)

        hd = HD_BY_CLASS.get(self.char_class, 8)
        con_mod = calc_modifier(final.get("CON", 10))
        des_mod = calc_modifier(final.get("DES", 10))
        hp = max(1, hd + con_mod)
        ca = 10 + des_mod

        weapons = []
        for w_name, w_dmg, w_notes in preset.get("weapons", []):
            weapons.append(WeaponAction(name=w_name, attack_bonus=f"+{des_mod + 2}", damage=w_dmg, damage_type="Físico", notes=w_notes))

        slots = {}
        if self.char_class in ["Bardo", "Clérigo", "Druida", "Hechicero", "Mago"]:
            slots["1"] = SpellSlotTier(level=1, total=2, current=2)
        elif self.char_class == "Brujo":
            slots["1"] = SpellSlotTier(level=1, total=1, current=1)

        new_char = CharacterSheet(
            name=self.char_name.strip() or "Héroe Rápido",
            char_class=self.char_class,
            subclass="",
            level=1,
            race=self.char_species,
            background=bg,
            alignment="Neutral Bueno",
            senses="Visión Normal",
            xp=0,
            hp_current=hp,
            hp_max=hp,
            hit_dice_max=1,
            hit_dice_current=1,
            hit_dice_faces=hd,
            armor_class=ca,
            initiative_bonus=des_mod,
            speed="9 m",
            proficiency_bonus=2,
            abilities=final,
            saving_throw_profs=SAVES_BY_CLASS.get(self.char_class, []),
            weapons=weapons,
            spell_slots=slots
        )

        self.close()
        if self.on_character_created:
            self.on_character_created(new_char)


class RandomizeDialog:
    def __init__(
        self,
        page: ft.Page,
        on_character_created: Callable[[CharacterSheet], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.on_character_created = on_character_created
        self.on_cancel = on_cancel

        self.selected_level = 1
        self.lock_class: Optional[str] = None
        self.lock_species: Optional[str] = None
        self.generated_data: Dict[str, Any] = {}

        self._build_dialog()

    def show(self):
        self._reroll()
        self.page.open(self.dialog)

    def close(self):
        self.page.close(self.dialog)

    def _reroll(self, e=None):
        self.generated_data = RandomCharacterGenerator.generate_random_character(
            forced_class=self.lock_class,
            forced_species=self.lock_species,
            forced_level=self.selected_level
        )
        self._update_preview()

    def _update_preview(self):
        d = self.generated_data
        if not d:
            return

        stats_pills = []
        for s, v in d["final_abilities"].items():
            mod = calc_modifier(v)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            stats_pills.append(
                create_badge(f"{s}: {v} ({mod_str})", bg_color=BG_INPUT, text_color=TTUI_GOLD_LIGHT, border_color=BORDER_GOLD if s in [d["bg_plus2"], d["bg_plus1"]] else BORDER_DIM)
            )

        self.preview_container.content = ft.Column([
            ft.Row([
                ft.Text(f"📜 {d['name']}", size=15, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                create_badge(f"Nivel {d['level']}", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"{d['species']} • {d['char_class']} • {d['alignment']} • Trasfondo: {d['background']}", size=12, color=TTUI_PARCHMENT),
            ft.Row([
                create_badge(f"❤️ {d['hp_max']} PG", bg_color=BG_INPUT, text_color=COLOR_GREEN, border_color=COLOR_GREEN),
                create_badge(f"🛡️ {d['armor_class']} CA", bg_color=BG_INPUT, text_color=TTUI_GOLD, border_color=BORDER_GOLD),
                create_badge(f"Dados: {d['hit_dice_max']}d{d['hit_dice_faces']}", bg_color=BG_INPUT, text_color=TTUI_PARCHMENT, border_color=TTUI_BORDER_SLATE),
                create_badge(f"PB: +{d['proficiency_bonus']}", bg_color=BG_INPUT, text_color=TTUI_GOLD_LIGHT, border_color=BORDER_GOLD)
            ], spacing=6),
            ft.Row(controls=stats_pills, wrap=True, spacing=6),
            ft.Divider(color=TTUI_BORDER_SLATE, height=1),
            ft.Text(f"🎭 Rasgo: \"{d['personality_trait']}\"", size=11, color=TTUI_RUNIC_GREY, italic=True),
            ft.Text(f"⚖️ Ideal: {d['ideal']}", size=11, color=TTUI_RUNIC_GREY),
            ft.Text(f"🔗 Vínculo: {d['bond']}", size=11, color=TTUI_RUNIC_GREY),
            ft.Text(f"⚡ Defecto: {d['flaw']}", size=11, color=TTUI_RUNIC_GREY),
        ], spacing=6)

        if getattr(self.dialog, "page", None):
            self.dialog.update()

    def _build_dialog(self):
        level_opts = [ft.dropdown.Option(str(i), f"Nivel {i}") for i in range(1, 21)]
        level_dd = ft.Dropdown(
            label="Nivel Deseado",
            value=str(self.selected_level),
            options=level_opts,
            width=140,
            border_color=BORDER_GOLD,
            on_change=lambda e: (setattr(self, "selected_level", int(e.control.value)), self._reroll())
        )

        class_opts = [ft.dropdown.Option("", "Cualquier Clase (Azar)")] + [ft.dropdown.Option(c, c) for c in CLASSES_LIST]
        class_dd = ft.Dropdown(
            label="Fijar Clase",
            value="",
            options=class_opts,
            width=180,
            border_color=BORDER_DIM,
            on_change=lambda e: (setattr(self, "lock_class", e.control.value or None), self._reroll())
        )

        species_opts = [ft.dropdown.Option("", "Cualquier Especie (Azar)")] + [ft.dropdown.Option(s, s) for s in SPECIES_LIST]
        species_dd = ft.Dropdown(
            label="Fijar Especie",
            value="",
            options=species_opts,
            width=180,
            border_color=BORDER_DIM,
            on_change=lambda e: (setattr(self, "lock_species", e.control.value or None), self._reroll())
        )

        btn_reroll = ft.ElevatedButton(
            text="🎲 Re-Roll (Tirar Nuevamente)",
            icon=ft.Icons.CASINO,
            bgcolor=BG_INPUT,
            color=TTUI_GOLD_LIGHT,
            style=ft.ButtonStyle(bgcolor=BG_INPUT, color=TTUI_GOLD_LIGHT, side=ft.BorderSide(1, BORDER_GOLD)),
            on_click=self._reroll
        )

        self.preview_container = ft.Container(
            bgcolor=BG_CARD,
            padding=12,
            border=ft.border.all(1, TTUI_BORDER_SLATE),
            border_radius=ft.border_radius.all(6)
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.CASINO, color="#a855f7", size=24),
                    ft.Text("Randomize: Los Dados del Destino (Procedural)", size=17, weight=ft.FontWeight.BOLD, color=TTUI_GOLD_LIGHT),
                ], spacing=8),
                ft.IconButton(ft.Icons.CLOSE, icon_color=TTUI_RUNIC_GREY, on_click=lambda e: self.close())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([level_dd, class_dd, species_dd, btn_reroll], spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.preview_container
                ], spacing=10),
                width=720,
                height=350
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TTUI_RUNIC_GREY), on_click=lambda e: self.close()),
                ft.ElevatedButton(
                    text="✨ Aceptar y Cargar Personaje",
                    bgcolor=COLOR_GREEN,
                    color="#ffffff",
                    style=ft.ButtonStyle(bgcolor=COLOR_GREEN, color="#ffffff"),
                    on_click=self._accept_random
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _accept_random(self, e):
        d = self.generated_data
        if not d:
            return

        des_mod = d["initiative_bonus"]
        weapons = [
            WeaponAction(name="Espada Corta", attack_bonus=f"+{des_mod + d['proficiency_bonus']}", damage=f"1d6+{des_mod}", damage_type="Perforante", notes="Sutil, Ligera"),
            WeaponAction(name="Daga", attack_bonus=f"+{des_mod + d['proficiency_bonus']}", damage=f"1d4+{des_mod}", damage_type="Perforante", notes="Arrojadiza (6/18m)")
        ]

        slots = {}
        if d["char_class"] in ["Bardo", "Clérigo", "Druida", "Hechicero", "Mago"]:
            slots["1"] = SpellSlotTier(level=1, total=4 if d["level"] > 2 else 2, current=4 if d["level"] > 2 else 2)
        elif d["char_class"] == "Brujo":
            slots["1"] = SpellSlotTier(level=1, total=2, current=2)

        new_char = CharacterSheet(
            name=d["name"],
            char_class=d["char_class"],
            subclass="",
            level=d["level"],
            race=d["species"],
            background=d["background"],
            alignment=d["alignment"],
            senses="Visión Normal",
            xp=0,
            hp_current=d["hp_max"],
            hp_max=d["hp_max"],
            hit_dice_max=d["hit_dice_max"],
            hit_dice_current=d["hit_dice_max"],
            hit_dice_faces=d["hit_dice_faces"],
            armor_class=d["armor_class"],
            initiative_bonus=des_mod,
            speed="9 m",
            proficiency_bonus=d["proficiency_bonus"],
            abilities=d["final_abilities"],
            saving_throw_profs=SAVES_BY_CLASS.get(d["char_class"], []),
            weapons=weapons,
            spell_slots=slots
        )

        self.close()
        if self.on_character_created:
            self.on_character_created(new_char)
