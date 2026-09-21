"""
Diálogo de Referencia Rápida de Reglas y Mecánicas (D&D 5e PHB 2024 / Xanathar)
"""
import flet as ft
from ..theme import (
    BG_CARD, BG_INPUT, BORDER_DIM, BORDER_GOLD, GOLD_LIGHT,
    GOLD_PRIMARY, TEXT_MUTED, create_card_container
)


class RulesDialog:
    def __init__(self, page: ft.Page):
        self.page = page
        self._build_ui()

    def _build_ui(self):
        rules_content = ft.Column(
            controls=[
                self._rule_card(
                    "⛺ Descanso Corto (1 hora)",
                    "Puedes gastar uno o más Dados de Golpe para curarte. Por cada dado gastado, tiras el dado correspondiente (p. ej. 1d8) + tu modificador de Constitución. Canción de Descanso (Bardo) añade +1d6 extra de curación."
                ),
                self._rule_card(
                    "🏕️ Descanso Largo (8 horas / 4h Trance)",
                    "Recuperas todos los Puntos de Golpe perdidos. Recuperas la mitad de tus Dados de Golpe máximos gastados (mínimo 1). Recuperas todos los espacios de conjuro gastados y usos de rasgos limitados."
                ),
                self._rule_card(
                    "💀 Salvaciones Contra la Muerte",
                    "A 0 PG, al inicio de cada turno tiras 1d20 sin modificadores:\n• 10 o más: Éxito (3 éxitos = estabilizado a 0 PG).\n• 9 o menos: Fallo (3 fallos = muerte).\n• 1 natural: Cuenta como 2 fallos.\n• 20 natural: Recuperas 1 PG inmediatamente y eres consciente."
                ),
                self._rule_card(
                    "⚔️ Acciones Principales en Combate",
                    "• Atacar (Cuerpo a cuerpo o a distancia)\n• Lanzar un Conjuro (Acción o Acción Adicional)\n• Destrabarse (Evita ataques de oportunidad durante el turno)\n• Esquivar (Ataques contra ti tienen desventaja; ventaja en salvaciones de DES)\n• Ayudar (Otorga ventaja a un aliado en su siguiente tirada)\n• Esconderse (Prueba de Destreza / Sigilo superando percepción pasiva)\n• Buscar (Prueba de Sabiduría / Percepción o Inteligencia / Investigación)"
                ),
                self._rule_card(
                    "👁️ Linaje Drow & Magia Feérica",
                    "• Visión en la Oscuridad Superior: 36 metros.\n• Sensibilidad a la Luz Solar: Desventaja en tiradas de ataque y Percepción basada en la vista bajo luz solar directa.\n• Magia Drow: Truco Luces Danzantes (Niv 1), Fuego Feérico (Niv 3, 1/descanso largo), Oscuridad (Niv 5, 1/descanso largo). Carisma es la aptitud mágica."
                ),
                self._rule_card(
                    "🗡️ Bardo: Colegio de Susurros (Xanathar)",
                    "• Hojas Psíquicas: Al impactar con un arma, gasta un uso de Inspiración Bárdica para infligir +2d6 de daño psíquico (+3d6 a nivel 5, +5d6 a nivel 10).\n• Palabras de Terror: Hablar a solas 1 minuto provoca paranoia; salvación de Sabiduría contra tu CD o asustado durante 1 hora."
                )
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE
        )

        self.dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("📖 Compendio Rápido de Reglas (D&D 5e)", size=18, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            content=ft.Container(
                content=rules_content,
                width=680,
                height=480
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    style=ft.ButtonStyle(color=GOLD_LIGHT),
                    on_click=self._close
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def _rule_card(self, title: str, text: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ft.Text(text, size=12, color="#e5e7eb", selectable=True),
                ],
                spacing=4
            ),
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(6),
            padding=10
        )

    def show(self):
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close(self, e=None):
        self.dialog.open = False
        if self.dialog in self.page.overlay:
            self.page.overlay.remove(self.dialog)
        self.page.update()
