"""
Componente DiceTray (Constructor de Pool de Dados y Puente TaleSpire 3D / Motor Local).
Soporta:
1. Máquina de estados persistente para TaleSpire (NOT_INSTALLED, INSTALLED_CLOSED, RUNNING_IDLE, CONNECTED).
2. Selector de Modo TaleSpire (👤 Jugador vs 👑 DM/Host) para calibración exacta de altura de bandeja.
3. Multi-Dice Pool Builder con selección de caras (d20, d12, d10, d8, d6, d4, d100), Stepper ergonómico (◄ [cant] ►) y botón [+ Añadir].
4. Sincronización en vivo e inmediata con la bandeja 3D de TaleSpire al añadir dados.
5. Simulación de micro-impulso físico instantáneo (< 25ms) para lanzar en la mesa 3D de TaleSpire sin cursor visible.
6. Fallback transparente y simultáneo al motor local SRD 5e con cálculo exacto de sumatoria total.
7. Preservación 100% de tiradas directas de armas, conjuros, habilidades y salvaciones.
8. Historial efímero de sesión en memoria RAM (SessionRollLedger) con sumatoria total visible y purga total.
"""
from typing import Optional, Callable, Dict, Any, List
import flet as ft

from ...core.talespire_bridge import TaleSpireBridge, TaleSpireState
from ...core.session_ledger import SessionRollLedger, RollEntry
from ...core.rules import roll_dice_pool, roll_dice_multiple
from ...core.models import CharacterSheet
from ..theme import (
    BG_CARD, BG_CARD_ALT, BG_INPUT, BG_SURFACE, BORDER_GOLD, BORDER_DIM,
    GOLD_LIGHT, GOLD_PRIMARY, TEXT_MUTED, COLOR_GREEN, COLOR_RED, COLOR_AMBER
)


class DiceTray(ft.Container):
    """
    Bandeja interactiva y Constructor de Pool de Dados para D&D 5e.
    Permite acumular múltiples dados de diferentes tipos y lanzarlos en un único paquete.
    """

    def __init__(self, char: Optional[CharacterSheet] = None, on_roll_event: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__()
        self.char = char
        self.on_roll_event = on_roll_event

        self.bridge = TaleSpireBridge()
        self.ledger = SessionRollLedger.get_current()

        # Pool de dados acumulativo: {cara_dado: cantidad} ej: {20: 1, 6: 2}
        self.pool: Dict[int, int] = {}
        self.active_die: int = 20
        self.pending_qty: int = 1
        self.ts_mode: str = "dm"  # Por defecto Modo DM / Host calibrado a 17.5% de altura
        self.mode = "normal"
        self.mod_val = 0

        self.bgcolor = BG_CARD
        self.border = ft.border.all(1, BORDER_GOLD)
        self.border_radius = ft.border_radius.all(10)
        self.padding = 12
        self.width = 340

        self._build_ui()

    def set_character(self, char: Optional[CharacterSheet]):
        """Actualiza el personaje activo vinculado a las tiradas."""
        self.char = char

    def _build_ui(self):
        # 1. Cabecera y Barra de Control de Conexión TaleSpire
        self.status_container = ft.Row(
            controls=self._build_connection_controls(),
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Selector de Modo de Interfaz TaleSpire (Jugador vs DM/Host)
        self.btn_mode_player = ft.Container(
            content=ft.Text("👤 Jugador", size=10, weight=ft.FontWeight.NORMAL, color=TEXT_MUTED),
            bgcolor=BG_CARD_ALT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(4),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            on_click=lambda e: self._set_ts_mode("player"),
            tooltip="Bandeja calibrada para mesa de jugador (~24% altura)"
        )
        self.btn_mode_dm = ft.Container(
            content=ft.Text("👑 DM / Host", size=10, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_GOLD),
            border_radius=ft.border_radius.all(4),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            on_click=lambda e: self._set_ts_mode("dm"),
            tooltip="Bandeja calibrada para mesa de Master/Build Mode (~30% altura, sobre caja de dados preparados [1 D20])"
        )
        mode_row = ft.Row(
            controls=[
                ft.Text("Modo TaleSpire:", size=10, color=TEXT_MUTED),
                ft.Row(controls=[self.btn_mode_player, self.btn_mode_dm], spacing=4)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        header_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("🎲 Tirador & Pool de Dados", size=14, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                self.status_container,
                mode_row,
            ],
            spacing=4
        )

        # 2. Selector de Tipos de Dados (d20, d12, d10, d8, d6, d4, d100)
        self.dice_buttons_row = ft.Row(
            controls=self._build_dice_buttons(),
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4
        )

        # 3. Stepper Ergonómico con Flechas Laterales [ ◄ ] [ Cantidad ] [ ► ] y botón [+ Añadir]
        self.active_die_label = ft.Text(f"d{self.active_die}:", size=12, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT)

        self.btn_dec_qty = ft.Container(
            content=ft.Text("◄", size=11, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            bgcolor=BG_CARD_ALT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(4),
            alignment=ft.alignment.center,
            width=28,
            height=28,
            on_click=self._on_decrement_qty,
            tooltip="Disminuir cantidad (mínimo 1)"
        )

        self.qty_text = ft.Text(str(self.pending_qty), size=12, weight=ft.FontWeight.BOLD, color="#ffffff")
        self.qty_display = ft.Container(
            content=self.qty_text,
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(4),
            alignment=ft.alignment.center,
            width=34,
            height=28
        )

        self.btn_inc_qty = ft.Container(
            content=ft.Text("►", size=11, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            bgcolor=BG_CARD_ALT,
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(4),
            alignment=ft.alignment.center,
            width=28,
            height=28,
            on_click=self._on_increment_qty,
            tooltip="Aumentar cantidad"
        )

        self.btn_add_to_pool = ft.ElevatedButton(
            text="+ Añadir",
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#000000",
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=12, vertical=6)
            ),
            on_click=self._on_add_to_pool_click,
            tooltip="Añadir dados al pool activo"
        )

        self.stepper_row = ft.Row(
            controls=[
                ft.Row(
                    controls=[self.active_die_label, self.btn_dec_qty, self.qty_display, self.btn_inc_qty],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                self.btn_add_to_pool
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 4. Visor Reactivo de Dados Acumulados en el Pool
        self.pool_chips_row = ft.Row(wrap=True, spacing=6)
        self.pool_display_container = ft.Container(
            content=self.pool_chips_row,
            bgcolor=BG_INPUT,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            border=ft.border.all(1, BORDER_DIM),
            border_radius=ft.border_radius.all(6),
            width=316
        )
        self._refresh_pool_display()

        # 5. Modificador y Modo de Tirada
        self.mod_input = ft.TextField(
            value="0",
            label="Mod",
            width=65,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.padding.all(4),
            border_color=BORDER_DIM,
            focused_border_color=BORDER_GOLD,
            color="#ffffff",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_mod_change
        )

        self.mode_group = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="normal", label="Normal"),
                    ft.Radio(value="advantage", label="Ventaja"),
                    ft.Radio(value="disadvantage", label="Desv"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            value=self.mode,
            on_change=self._on_mode_change
        )

        options_row = ft.Row(
            controls=[self.mode_group, self.mod_input],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 6. Botón de Lanzamiento de Pool y Botón Limpiar
        self.btn_roll_pool = ft.ElevatedButton(
            text="🎲 Lanzar Dados",
            color="#000000",
            bgcolor=GOLD_PRIMARY,
            style=ft.ButtonStyle(
                bgcolor=GOLD_PRIMARY,
                color="#000000",
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=12, vertical=8)
            ),
            on_click=self._on_launch_pool_click,
            expand=True
        )

        self.btn_clear_pool = ft.OutlinedButton(
            text="Limpiar",
            style=ft.ButtonStyle(
                color=TEXT_MUTED,
                side=ft.BorderSide(1, BORDER_DIM),
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=8, vertical=8)
            ),
            on_click=self._on_clear_pool_click,
            tooltip="Vaciar dados del pool"
        )

        launch_row = ft.Row(
            controls=[self.btn_roll_pool, self.btn_clear_pool],
            spacing=8
        )

        # 7. Historial de Sesión Volátil
        self.log_column = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            height=130,
            spacing=4
        )
        self._refresh_ui_log()

        # 8. Acciones Inferiores (Salida Limpia y Purga de Sesión)
        btn_clear_view = ft.TextButton(
            text="Limpiar Vista",
            style=ft.ButtonStyle(color=TEXT_MUTED),
            on_click=self._clear_view_log,
            tooltip="Limpiar las tiradas visibles en pantalla"
        )

        btn_end_session = ft.OutlinedButton(
            text="Finalizar Sesión & Purgar",
            style=ft.ButtonStyle(
                color=COLOR_RED,
                side=ft.BorderSide(1, COLOR_RED),
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            on_click=self._prompt_destroy_session,
            tooltip="Purga permanentemente todo el historial de la sesión de la memoria RAM"
        )

        footer_row = ft.Row(
            controls=[btn_clear_view, btn_end_session],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.content = ft.Column(
            controls=[
                header_section,
                ft.Divider(color=BORDER_DIM, height=1),
                ft.Text("Seleccionar Dado:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                self.dice_buttons_row,
                self.stepper_row,
                self.pool_display_container,
                options_row,
                launch_row,
                ft.Divider(color=BORDER_DIM, height=1),
                self.log_column,
                ft.Divider(color=BORDER_DIM, height=1),
                footer_row
            ],
            spacing=6
        )

    def _set_ts_mode(self, mode: str):
        """Conmuta el perfil de altura de la bandeja de TaleSpire (Jugador vs DM/Host)."""
        self.ts_mode = mode
        self.btn_mode_player.bgcolor = BG_INPUT if mode == "player" else BG_CARD_ALT
        self.btn_mode_player.border = ft.border.all(1, BORDER_GOLD if mode == "player" else BORDER_DIM)
        self.btn_mode_player.content.weight = ft.FontWeight.BOLD if mode == "player" else ft.FontWeight.NORMAL
        self.btn_mode_player.content.color = GOLD_LIGHT if mode == "player" else TEXT_MUTED

        self.btn_mode_dm.bgcolor = BG_INPUT if mode == "dm" else BG_CARD_ALT
        self.btn_mode_dm.border = ft.border.all(1, BORDER_GOLD if mode == "dm" else BORDER_DIM)
        self.btn_mode_dm.content.weight = ft.FontWeight.BOLD if mode == "dm" else ft.FontWeight.NORMAL
        self.btn_mode_dm.content.color = GOLD_LIGHT if mode == "dm" else TEXT_MUTED

        if self.page:
            self.update()

    def _build_connection_controls(self) -> List[ft.Control]:
        """Construye los controles reactivos según la máquina de estados de TaleSpire."""
        st = self.bridge.state

        if st == TaleSpireState.CONNECTED:
            badge = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=7, height=7, border_radius=ft.border_radius.all(4), bgcolor=COLOR_GREEN),
                        ft.Text("TaleSpire Conectado", size=11, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                    ],
                    spacing=5
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border=ft.border.all(1, BORDER_GOLD),
                border_radius=ft.border_radius.all(10)
            )
            btn = ft.TextButton(
                text="Desconectar",
                style=ft.ButtonStyle(color=COLOR_RED),
                on_click=self._on_disconnect_click,
                tooltip="Volver a modo mesa local sin cerrar TaleSpire"
            )
            return [badge, btn]

        elif st == TaleSpireState.RUNNING_IDLE:
            badge = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=7, height=7, border_radius=ft.border_radius.all(4), bgcolor=COLOR_AMBER),
                        ft.Text("TaleSpire Abierto", size=11, weight=ft.FontWeight.W_500, color=COLOR_AMBER),
                    ],
                    spacing=5
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(10)
            )
            btn = ft.ElevatedButton(
                text="Conectar",
                color="#000000",
                bgcolor=GOLD_PRIMARY,
                style=ft.ButtonStyle(bgcolor=GOLD_PRIMARY, color="#000000", shape=ft.RoundedRectangleBorder(radius=6)),
                on_click=self._on_connect_click,
                tooltip="Enganchar sesión activa con TaleSpire"
            )
            return [badge, btn]

        else:
            status_text = "Mesa Local"
            badge = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=7, height=7, border_radius=ft.border_radius.all(4), bgcolor=TEXT_MUTED),
                        ft.Text(status_text, size=11, color=TEXT_MUTED),
                    ],
                    spacing=5
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border=ft.border.all(1, BORDER_DIM),
                border_radius=ft.border_radius.all(10)
            )
            btn = ft.OutlinedButton(
                text="Conectar TaleSpire",
                style=ft.ButtonStyle(color=GOLD_LIGHT, side=ft.BorderSide(1, BORDER_DIM), shape=ft.RoundedRectangleBorder(radius=6)),
                on_click=self._on_connect_click,
                tooltip="Conectar sesión con TaleSpire"
            )
            return [badge, btn]

    def _update_connection_ui(self):
        self.status_container.controls = self._build_connection_controls()
        if self.page:
            self.update()

    def _on_connect_click(self, e):
        success, msg = self.bridge.connect()
        self._update_connection_ui()
        if success:
            self._sync_staging_to_talespire()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), duration=2500)
            self.page.snack_bar.open = True
            self.page.update()

    def _on_disconnect_click(self, e):
        self.bridge.disconnect()
        self._update_connection_ui()
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Desconectado de TaleSpire. Operando en modo mesa local."), duration=2000)
            self.page.snack_bar.open = True
            self.page.update()

    def _build_dice_buttons(self) -> List[ft.Control]:
        """Construye botones de dados ordenados de mayor a menor con estilo uniforme sin amarillo fijo."""
        faces = [20, 12, 10, 8, 6, 4, 100]
        buttons = []
        for sides in faces:
            is_active = (sides == self.active_die)
            border_color = BORDER_GOLD if is_active else BORDER_DIM
            text_color = GOLD_LIGHT if is_active else "#b0b0b0"
            bg = BG_INPUT if is_active else BG_CARD_ALT

            btn = ft.Container(
                content=ft.Text(f"d{sides}", size=11, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL, color=text_color),
                bgcolor=bg,
                border=ft.border.all(1.5 if is_active else 1, border_color),
                border_radius=ft.border_radius.all(5),
                alignment=ft.alignment.center,
                width=38,
                height=28,
                on_click=lambda e, s=sides: self._on_die_select_click(s),
                tooltip=f"Seleccionar d{sides}"
            )
            buttons.append(btn)
        return buttons

    def _refresh_dice_buttons(self):
        self.dice_buttons_row.controls = self._build_dice_buttons()
        if self.dice_buttons_row.page:
            self.dice_buttons_row.update()

    def _on_die_select_click(self, sides: int):
        self.active_die = sides
        self.active_die_label.value = f"d{sides}:"
        self._refresh_dice_buttons()
        if self.page:
            if self.active_die_label.page:
                self.active_die_label.update()
            self.update()

    def _on_decrement_qty(self, e):
        if self.pending_qty > 1:
            self.pending_qty -= 1
            self.qty_text.value = str(self.pending_qty)
            if self.qty_display.page:
                self.qty_display.update()

    def _on_increment_qty(self, e):
        if self.pending_qty < 30:
            self.pending_qty += 1
            self.qty_text.value = str(self.pending_qty)
            if self.qty_display.page:
                self.qty_display.update()

    def _on_quantity_click(self, count: int):
        """Asigna directamente la cantidad al dado activo y sincroniza (retrocompatibilidad)."""
        self.pending_qty = max(1, count)
        self.qty_text.value = str(self.pending_qty)
        self.pool[self.active_die] = self.pending_qty
        self._refresh_pool_display()
        self._sync_staging_to_talespire()
        if self.page:
            if self.qty_display.page:
                self.qty_display.update()
            if self.pool_display_container.page:
                self.pool_display_container.update()
            self.update()

    def _on_add_to_pool_click(self, e):
        """Añade la cantidad configurada del dado activo al pool y sincroniza."""
        self.pool[self.active_die] = self.pool.get(self.active_die, 0) + self.pending_qty
        self._refresh_pool_display()
        self._sync_staging_to_talespire()
        if self.page:
            if self.pool_display_container.page:
                self.pool_display_container.update()
            self.update()

    def _format_pool_formula(self) -> str:
        if not self.pool:
            return "1d20"
        sorted_faces = sorted(self.pool.keys(), key=lambda f: (0 if f == 20 else 1, -f))
        parts = [f"{self.pool[f]}d{f}" for f in sorted_faces]
        mod_str = f"+{self.mod_val}" if self.mod_val > 0 else (f"{self.mod_val}" if self.mod_val < 0 else "")
        return f"{' + '.join(parts)}{(' ' + mod_str) if mod_str else ''}"

    def _add_die_to_pool(self, sides: int):
        """Añade 1 dado de la cara especificada al pool (retrocompatibilidad)."""
        self.active_die = sides
        self.active_die_label.value = f"d{sides}:"
        self.pool[sides] = self.pool.get(sides, 0) + 1
        self._refresh_dice_buttons()
        self._refresh_pool_display()
        self._sync_staging_to_talespire()
        if self.page:
            if self.pool_display_container.page:
                self.pool_display_container.update()
            self.update()

    def _remove_die_from_pool(self, sides: int):
        if sides in self.pool:
            if self.pool[sides] > 1:
                self.pool[sides] -= 1
            else:
                del self.pool[sides]
        self._refresh_pool_display()
        self._sync_staging_to_talespire()
        if self.page:
            if self.pool_display_container.page:
                self.pool_display_container.update()
            self.update()

    def _on_clear_pool_click(self, e):
        """Limpia completamente el pool y actualiza la vista garantizando el ciclo Flet."""
        self.pool.clear()
        self._refresh_pool_display()
        if self.page:
            if self.pool_display_container.page:
                self.pool_display_container.update()
            self.update()

    def _sync_staging_to_talespire(self):
        """Sincroniza en tiempo real los dados acumulados con la bandeja 3D de TaleSpire."""
        if not self.bridge.is_session_connected() or not self.pool:
            return
        try:
            pool_url = self.bridge.build_pool_url(self.pool, modifier=self.mod_val, label="Pool")
            self.bridge.send_roll(pool_url)
        except Exception:
            pass

    def _refresh_pool_display(self):
        if not self.pool:
            self.pool_chips_row.controls = [
                ft.Text("Pool vacío. Selecciona dados y pulsa [+ Añadir].", size=11, color=TEXT_MUTED, italic=True)
            ]
        else:
            chips = []
            sorted_faces = sorted(self.pool.keys(), key=lambda f: (0 if f == 20 else 1, -f))
            for sides in sorted_faces:
                count = self.pool[sides]
                chip = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(f"{count}d{sides}", size=11, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
                            ft.GestureDetector(
                                content=ft.Text("✕", size=10, weight=ft.FontWeight.BOLD, color=COLOR_RED),
                                on_tap=lambda e, s=sides: self._remove_die_from_pool(s)
                            )
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    bgcolor=BG_CARD_ALT,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border=ft.border.all(1, BORDER_GOLD if sides == self.active_die else BORDER_DIM),
                    border_radius=ft.border_radius.all(4),
                    tooltip=f"Clic en ✕ para retirar 1d{sides}"
                )
                chips.append(chip)
            self.pool_chips_row.controls = chips

        if self.pool_display_container.page:
            self.pool_display_container.update()

    def _on_mod_change(self, e):
        try:
            self.mod_val = int(e.control.value)
        except ValueError:
            self.mod_val = 0
        self._sync_staging_to_talespire()

    def _on_mode_change(self, e):
        self.mode = e.control.value

    def _on_launch_pool_click(self, e):
        active_pool = dict(self.pool) if self.pool else {20: 1}
        self.execute_pool_roll(active_pool, reason="Pool de Dados")
        # Mantener los dados en el constructor para permitir re-tiradas inmediatas sin reiniciar a 1d20
        # El usuario puede vaciar el pool cuando desee con el botón [Limpiar]
        if self.page:
            self.update()

    def execute_pool_roll(self, pool: Dict[int, int], reason: str = "Tirada"):
        """Despacha un pool combinado a TaleSpire y/o motor local sin inventar números falsos en 3D."""
        char_name = self.char.name if self.char else "Héroe"
        is_connected = self.bridge.is_session_connected()

        if is_connected:
            channel = "TaleSpire 3D"
            try:
                roll_url = self.bridge.build_pool_url(pool, modifier=self.mod_val, label=reason)
                self.bridge.send_roll(roll_url)
                # Ejecutar el micro-impulso físico con altura calibrada según ts_mode
                self.bridge.execute_throw_gesture(ts_mode=self.ts_mode)
            except Exception:
                pass
            formula = self._format_pool_formula()
            detail = f"Física en mesa 3D • {formula}"
            total = "🎲 En mesa 3D"
            is_crit = False
            is_fumble = False
            raw_result = {
                "channel": channel,
                "pool": pool,
                "modifier": self.mod_val,
                "detail": detail,
                "total": total,
                "formula": formula,
                "is_crit": False,
                "is_fumble": False
            }
        else:
            channel = "Motor Local"
            local_res = roll_dice_pool(pool, modifier=self.mod_val, mode=self.mode)
            formula = local_res["formula"]
            detail = local_res["detail"]
            total = local_res["total"]
            is_crit = local_res.get("is_crit", False)
            is_fumble = local_res.get("is_fumble", False)
            raw_result = local_res
            raw_result["channel"] = channel

        entry = self.ledger.record_roll(
            character_name=char_name,
            reason=reason,
            formula=formula,
            detail=detail,
            total=total,
            is_crit=is_crit,
            is_fumble=is_fumble,
            channel=channel
        )

        self._refresh_ui_log()
        if self.page:
            if self.log_column.page:
                self.log_column.update()
            self.update()

        if self.on_roll_event:
            self.on_roll_event(raw_result)

    def do_roll(
        self,
        sides: int,
        custom_mod: Optional[int] = None,
        custom_mode: Optional[str] = None,
        reason: str = "",
        count: Optional[int] = None
    ):
        """
        Método retrocompatible de tirada directa (invocado por CombatView, SheetView, etc.).
        Despacha directamente la tirada individual o agrupada al canal activo.
        """
        mod = custom_mod if custom_mod is not None else self.mod_val
        mode = custom_mode if custom_mode is not None else self.mode
        c = count if count is not None else 1
        char_name = self.char.name if self.char else "Héroe"
        eff_reason = reason or f"d{sides}"

        is_connected = self.bridge.is_session_connected()
        mod_str = f"+{mod}" if mod > 0 else (f"{mod}" if mod < 0 else "")
        formula = f"{c}d{sides}{mod_str}"

        if is_connected:
            channel = "TaleSpire 3D"
            groups = []
            if sides == 20 and mode in ("advantage", "disadvantage"):
                tag_a = "Ventaja A" if mode == "advantage" else "Desv A"
                tag_b = "Ventaja B" if mode == "advantage" else "Desv B"
                groups.append({"label": f"{eff_reason} {tag_a}", "count": 1, "sides": 20, "mod": mod})
                groups.append({"label": f"{eff_reason} {tag_b}", "count": 1, "sides": 20, "mod": mod})
            else:
                groups.append({"label": eff_reason, "count": c, "sides": sides, "mod": mod})

            try:
                roll_url = self.bridge.build_roll_url(groups)
                self.bridge.send_roll(roll_url)
                # Ejecutar el micro-impulso físico con altura calibrada según ts_mode
                self.bridge.execute_throw_gesture(ts_mode=self.ts_mode)
            except Exception:
                pass

            detail = f"Física en mesa 3D • {formula}"
            total = "🎲 En mesa 3D"
            is_crit = False
            is_fumble = False
            raw_result = {
                "channel": channel,
                "sides": sides,
                "count": c,
                "modifier": mod,
                "detail": detail,
                "total": total,
                "formula": formula,
                "is_crit": False,
                "is_fumble": False
            }
        else:
            channel = "Motor Local"
            local_res = roll_dice_multiple(count=c, sides=sides, mode=mode, modifier=mod)
            detail = local_res["detail"]
            total = local_res["total"]
            is_crit = local_res.get("is_crit", False)
            is_fumble = local_res.get("is_fumble", False)
            raw_result = local_res
            raw_result["channel"] = channel

        entry = self.ledger.record_roll(
            character_name=char_name,
            reason=eff_reason,
            formula=formula,
            detail=detail,
            total=total,
            is_crit=is_crit,
            is_fumble=is_fumble,
            channel=channel
        )

        self._refresh_ui_log()
        if self.page:
            if self.log_column.page:
                self.log_column.update()
            self.update()

        if self.on_roll_event:
            self.on_roll_event(raw_result)

    def _refresh_ui_log(self):
        """Reconstruye el listado visual del historial de sesión mostrando sumatoria total clara."""
        history = self.ledger.get_history()
        if not history:
            self.log_column.controls = [
                ft.Text("Historial de sesión vacío.", size=11, color=TEXT_MUTED, italic=True)
            ]
            return

        controls = []
        for entry in history[:25]:
            val_color = GOLD_LIGHT
            status_text = ""
            if entry.is_crit:
                val_color = COLOR_GREEN
                status_text = " ★ CRÍTICO"
            elif entry.is_fumble:
                val_color = COLOR_RED
                status_text = " ⚠ PIFIA"

            item = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{entry.time_str} • {entry.reason}", size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    entry.total if entry.channel == "TaleSpire 3D" else f"Total: {entry.total}{status_text}",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=val_color
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(entry.detail, size=10, color=TEXT_MUTED),
                    ],
                    spacing=2
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=ft.border_radius.all(4)
            )
            controls.append(item)

        self.log_column.controls = controls

    def _clear_view_log(self, e):
        self.ledger.clear_history()
        self._refresh_ui_log()
        if self.page:
            if self.log_column.page:
                self.log_column.update()
            self.update()

    def _prompt_destroy_session(self, e):
        """Muestra diálogo de confirmación claro con salidas de escape (Ley de Hick)."""
        def cancel_dlg(ev):
            if self.page:
                self.page.close(dlg)

        def confirm_destroy(ev):
            if self.page:
                self.page.close(dlg)
            self.ledger.destroy_session()
            self._refresh_ui_log()
            if self.page:
                if self.log_column.page:
                    self.log_column.update()
                self.update()
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Sesión de juego finalizada. Registro de tiradas purgado permanentemente."),
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text("¿Finalizar Sesión de Juego?", size=16, weight=ft.FontWeight.BOLD, color=GOLD_LIGHT),
            content=ft.Text(
                "El registro de tiradas de esta partida será eliminado permanentemente de la memoria RAM.",
                size=13,
                color=TEXT_MUTED
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_MUTED), on_click=cancel_dlg),
                ft.ElevatedButton(
                    "Finalizar & Purgar",
                    style=ft.ButtonStyle(bgcolor=COLOR_RED, color="#ffffff"),
                    on_click=confirm_destroy
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if self.page:
            self.page.open(dlg)
