"""
Motor de Persistencia Local SQLite para Visualizador & Editor D&D 5e.
Conexión optimizada con modo WAL, transacciones atómicas, almacenamiento relacional y migración JSON.
"""
import os
import sys
import json
import sqlite3
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from .models import CharacterSheet, SessionLog, NetworkNode, NetworkEdge


def get_default_db_path() -> str:
    """Retorna la ruta absoluta hacia dnd_database.db garantizando directorio de datos escribible."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # Detectar raíz del repo buscando hacia arriba
        current = os.path.abspath(__file__)
        base_dir = os.path.dirname(os.path.dirname(current))
        if not os.path.exists(os.path.join(base_dir, "okf_dnd5e")):
            base_dir = os.path.dirname(base_dir)
    
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "dnd_database.db")


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # WAL mode para máxima concurrencia y velocidad
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        """Crea las tablas relacionales si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Tabla de personajes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    char_class TEXT,
                    subclass TEXT,
                    level INTEGER DEFAULT 1,
                    race TEXT,
                    hp_current INTEGER DEFAULT 10,
                    hp_max INTEGER DEFAULT 10,
                    portrait_path TEXT DEFAULT '',
                    data_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Diario de Campaña Relacional
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaign_journals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER,
                    session_date TEXT,
                    title TEXT,
                    summary TEXT,
                    loot TEXT,
                    xp_gained INTEGER DEFAULT 0,
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                );
            """)

            # 3. Nodos de Red Social / Campaña
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_nodes (
                    id TEXT,
                    character_id INTEGER,
                    name TEXT,
                    role TEXT,
                    description TEXT,
                    avatar_base64 TEXT,
                    x REAL DEFAULT 0.0,
                    y REAL DEFAULT 0.0,
                    PRIMARY KEY (id, character_id),
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                );
            """)

            # 4. Vínculos de Red de Campaña
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER,
                    source_id TEXT,
                    target_id TEXT,
                    relation TEXT,
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                );
            """)

            # 5. Configuración de Aplicación (Estado de sesión, páginas leídas, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            # 6. Sesiones de DM Online (Cloudflare Tunnels)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dm_sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    campaign_name TEXT DEFAULT 'Campaña',
                    tunnel_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    notes TEXT DEFAULT ''
                );
            """)

            # 7. Jugadores en Sesión DM
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dm_session_players (
                    session_id TEXT NOT NULL,
                    player_token TEXT NOT NULL,
                    character_id INTEGER,
                    character_name TEXT NOT NULL,
                    character_class TEXT,
                    character_level INTEGER DEFAULT 1,
                    hp_current INTEGER DEFAULT 10,
                    hp_max INTEGER DEFAULT 10,
                    ac INTEGER DEFAULT 10,
                    status TEXT DEFAULT 'ALIVE',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_json TEXT,
                    PRIMARY KEY (session_id, player_token),
                    FOREIGN KEY (session_id) REFERENCES dm_sessions(id) ON DELETE CASCADE
                );
            """)

            # 8. Bitácora de Eventos y Tiradas de Sesión
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dm_session_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    actor_name TEXT NOT NULL,
                    target_name TEXT,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES dm_sessions(id) ON DELETE CASCADE
                );
            """)

            # 9. Forja de Objetos Homebrew del DM
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dm_homebrew_items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    rarity TEXT DEFAULT 'common',
                    requires_attunement INTEGER DEFAULT 0,
                    damage_dice TEXT,
                    damage_type TEXT,
                    secondary_dice TEXT,
                    secondary_type TEXT,
                    bonus_attack INTEGER DEFAULT 0,
                    bonus_damage INTEGER DEFAULT 0,
                    ac_bonus INTEGER DEFAULT 0,
                    properties_json TEXT DEFAULT '[]',
                    description TEXT,
                    scroll_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            try:
                cursor.execute("ALTER TABLE dm_homebrew_items ADD COLUMN scroll_content TEXT;")
            except Exception:
                pass
            conn.commit()

    def get_active_character(self) -> Optional[CharacterSheet]:
        """Obtiene el personaje actualmente marcado como activo."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, data_json, portrait_path FROM characters WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1;")
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row["data_json"])
                    char = CharacterSheet.from_dict(data)
                    char.id = row["id"]
                    if row["portrait_path"] and not char.portrait_path:
                        char.portrait_path = row["portrait_path"]
                    return char
                except Exception as e:
                    print(f"[DatabaseManager] Error al deserializar personaje activo: {e}")

            # Si no hay activo pero hay personajes guardados, tomar el último
            cursor.execute("SELECT id, data_json, portrait_path FROM characters ORDER BY updated_at DESC LIMIT 1;")
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row["data_json"])
                    char = CharacterSheet.from_dict(data)
                    char.id = row["id"]
                    if row["portrait_path"] and not char.portrait_path:
                        char.portrait_path = row["portrait_path"]
                    # Marcarlo activo
                    cursor.execute("UPDATE characters SET is_active = 1 WHERE id = ?;", (row["id"],))
                    conn.commit()
                    return char
                except Exception as e:
                    print(f"[DatabaseManager] Error al deserializar personaje más reciente: {e}")
        return None

    def save_character(self, char: CharacterSheet, set_active: bool = True) -> int:
        """Guarda o actualiza un personaje en la base de datos de manera atómica."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            existing = None
            if char.id is not None:
                cursor.execute("SELECT id, is_active FROM characters WHERE id = ? LIMIT 1;", (char.id,))
                existing = cursor.fetchone()
            if not existing:
                cursor.execute("SELECT id, is_active FROM characters WHERE name = ? LIMIT 1;", (char.name,))
                existing = cursor.fetchone()

            if existing:
                char_id = existing["id"]
                char.id = char_id
                char_dict = char.to_dict()
                data_json = json.dumps(char_dict, ensure_ascii=False)
                if set_active:
                    cursor.execute("UPDATE characters SET is_active = 0;")
                new_active = 1 if set_active else int(existing["is_active"] or 0)
                cursor.execute("""
                    UPDATE characters
                    SET name = ?, char_class = ?, subclass = ?, level = ?, race = ?,
                        hp_current = ?, hp_max = ?, portrait_path = ?,
                        data_json = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (
                    char.name, char.char_class, char.subclass, char.level, char.race,
                    char.hp_current, char.hp_max, char.portrait_path,
                    data_json, new_active, char_id
                ))
            else:
                char_dict = char.to_dict()
                data_json = json.dumps(char_dict, ensure_ascii=False)
                if set_active:
                    cursor.execute("UPDATE characters SET is_active = 0;")
                cursor.execute("""
                    INSERT INTO characters (
                        name, char_class, subclass, level, race,
                        hp_current, hp_max, portrait_path, data_json, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    char.name, char.char_class, char.subclass, char.level, char.race,
                    char.hp_current, char.hp_max, char.portrait_path,
                    data_json, 1 if set_active else 0
                ))
                char_id = cursor.lastrowid
                char.id = char_id
                char_dict["id"] = char_id
                cursor.execute("UPDATE characters SET data_json = ? WHERE id = ?;", (json.dumps(char_dict, ensure_ascii=False), char_id))

            # Sincronizar sesiones en campaign_journals
            cursor.execute("DELETE FROM campaign_journals WHERE character_id = ?;", (char_id,))
            for sess in char.sessions:
                cursor.execute("""
                    INSERT INTO campaign_journals (character_id, session_date, title, summary, loot, xp_gained)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (char_id, sess.date, sess.title, sess.summary, sess.loot, sess.xp_gained))

            # Sincronizar red de personajes
            cursor.execute("DELETE FROM network_nodes WHERE character_id = ?;", (char_id,))
            for n in char.network_nodes:
                cursor.execute("""
                    INSERT OR REPLACE INTO network_nodes (id, character_id, name, role, description, avatar_base64, x, y)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (n.id, char_id, n.name, n.role, n.description, n.avatar_base64, n.x, n.y))

            cursor.execute("DELETE FROM network_edges WHERE character_id = ?;", (char_id,))
            for e in char.network_edges:
                cursor.execute("""
                    INSERT INTO network_edges (character_id, source_id, target_id, relation)
                    VALUES (?, ?, ?, ?);
                """, (char_id, e.source_id, e.target_id, e.relation))

            conn.commit()
            return char_id

    def list_characters(self) -> List[Dict[str, Any]]:
        """Lista todos los personajes disponibles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, char_class, subclass, level, race, hp_current, hp_max, portrait_path, is_active, updated_at FROM characters ORDER BY updated_at DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_character_by_id(self, char_id: int) -> Optional[CharacterSheet]:
        """Obtiene un personaje por su ID sin alterar el estado de activo."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json, portrait_path FROM characters WHERE id = ?;", (char_id,))
            row = cursor.fetchone()
            if row:
                data = json.loads(row["data_json"])
                char = CharacterSheet.from_dict(data)
                char.id = char_id
                if row["portrait_path"] and not char.portrait_path:
                    char.portrait_path = row["portrait_path"]
                return char
        return None

    def set_active_character_by_id(self, char_id: int) -> Optional[CharacterSheet]:
        """Cambia el personaje activo dado su ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE characters SET is_active = 0;")
            cursor.execute("UPDATE characters SET is_active = 1 WHERE id = ?;", (char_id,))
            cursor.execute("SELECT data_json, portrait_path FROM characters WHERE id = ?;", (char_id,))
            row = cursor.fetchone()
            if row:
                conn.commit()
                data = json.loads(row["data_json"])
                char = CharacterSheet.from_dict(data)
                char.id = char_id
                if row["portrait_path"] and not char.portrait_path:
                    char.portrait_path = row["portrait_path"]
                return char
        return None

    def delete_character(self, char_id: int) -> bool:
        """Elimina un personaje y sus datos asociados (diarios, red) de la base de datos."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM characters WHERE id = ?;", (char_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?;", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?);", (key, str(value)))
            conn.commit()

    def migrate_from_json(self, json_path: str) -> Optional[CharacterSheet]:
        """Migra automáticamente el autosave_character.json inicial hacia SQLite si la BD no tiene registros."""
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            char = CharacterSheet.from_dict(data)
            self.save_character(char, set_active=True)
            print(f"[DatabaseManager] Migración exitosa de {json_path} a SQLite.")
            return char
        except Exception as e:
            print(f"[DatabaseManager] Error al migrar JSON: {e}")
            return None

    def save_portrait_file(self, src_path: str, char_name: str) -> str:
        """Copia una imagen de retrato local a data/characters/portraits/ y retorna la nueva ruta."""
        if not os.path.exists(src_path):
            return ""
        base_dir = os.path.dirname(self.db_path)
        portraits_dir = os.path.join(base_dir, "characters", "portraits")
        os.makedirs(portraits_dir, exist_ok=True)

        ext = Path(src_path).suffix or ".png"
        clean_name = "".join(c for c in char_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        dest_filename = f"portrait_{clean_name}_{os.path.basename(src_path)}"
        dest_path = os.path.join(portraits_dir, dest_filename)

        try:
            shutil.copy2(src_path, dest_path)
            return dest_path
        except Exception as e:
            print(f"[DatabaseManager] Error al copiar imagen de retrato: {e}")
            return src_path

    # =========================================================================
    # GESTIÓN DE SESIONES ONLINE (DM CONSOLE & CLOUDFLARE TUNNELS)
    # =========================================================================

    def create_dm_session(self, session_id: str, name: str, campaign_name: str = "Campaña Principal", tunnel_url: str = "") -> bool:
        """Crea o reinicia una sesión de juego del DM."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dm_sessions (id, name, campaign_name, tunnel_url, created_at, notes)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, '')
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    campaign_name = excluded.campaign_name,
                    tunnel_url = excluded.tunnel_url,
                    closed_at = NULL;
            """, (session_id, name, campaign_name, tunnel_url))
            conn.commit()
            return True

    def update_dm_session_tunnel(self, session_id: str, tunnel_url: str) -> bool:
        """Actualiza la URL pública del túnel Cloudflare para la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dm_sessions SET tunnel_url = ? WHERE id = ?;", (tunnel_url, session_id))
            conn.commit()
            return True

    def close_dm_session(self, session_id: str) -> bool:
        """Marca una sesión de DM como finalizada."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dm_sessions SET closed_at = CURRENT_TIMESTAMP WHERE id = ?;", (session_id,))
            conn.commit()
            return True

    def save_dm_session_notes(self, session_id: str, notes: str) -> bool:
        """Guarda notas de campaña de la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dm_sessions SET notes = ? WHERE id = ?;", (notes, session_id))
            conn.commit()
            return True

    def get_dm_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de una sesión por su ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dm_sessions WHERE id = ?;", (session_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def list_dm_sessions(self) -> List[Dict[str, Any]]:
        """Lista todas las sesiones históricas del DM."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dm_sessions ORDER BY created_at DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def upsert_session_player(
        self,
        session_id: str,
        player_token: str,
        character_name: str,
        character_id: Optional[int] = None,
        character_class: str = "",
        character_level: int = 1,
        hp_current: int = 10,
        hp_max: int = 10,
        ac: int = 10,
        status: str = "ALIVE",
        data_json: str = "{}",
    ) -> bool:
        """Registra o actualiza el estado de un jugador en la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dm_session_players (
                    session_id, player_token, character_id, character_name,
                    character_class, character_level, hp_current, hp_max,
                    ac, status, last_seen_at, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(session_id, player_token) DO UPDATE SET
                    character_id = coalesce(excluded.character_id, dm_session_players.character_id),
                    character_name = excluded.character_name,
                    character_class = excluded.character_class,
                    character_level = excluded.character_level,
                    hp_current = excluded.hp_current,
                    hp_max = excluded.hp_max,
                    ac = excluded.ac,
                    status = excluded.status,
                    last_seen_at = CURRENT_TIMESTAMP,
                    data_json = excluded.data_json;
            """, (session_id, player_token, character_id, character_name, character_class, character_level, hp_current, hp_max, ac, status, data_json))
            conn.commit()
            return True

    def update_player_hp(self, session_id: str, player_token: str, new_hp: int) -> bool:
        """Actualiza los puntos de vida de un jugador y su estado de combate."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            status = "UNCONSCIOUS" if new_hp <= 0 else "ALIVE"
            cursor.execute("""
                UPDATE dm_session_players
                SET hp_current = ?, status = ?, last_seen_at = CURRENT_TIMESTAMP
                WHERE session_id = ? AND player_token = ?;
            """, (new_hp, status, session_id, player_token))
            conn.commit()
            return True

    def update_player_status(self, session_id: str, player_token: str, status: str) -> bool:
        """Actualiza el estado de conexión o combate de un jugador en la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dm_session_players
                SET status = ?, last_seen_at = CURRENT_TIMESTAMP
                WHERE session_id = ? AND player_token = ?;
            """, (status, session_id, player_token))
            conn.commit()
            return True

    def get_session_players(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtiene la lista de jugadores participantes de una sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dm_session_players
                WHERE session_id = ?
                ORDER BY character_name ASC;
            """, (session_id,))
            return [dict(r) for r in cursor.fetchall()]

    def log_session_event(
        self,
        session_id: str,
        event_type: str,
        actor_name: str,
        target_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Registra un evento en la bitácora de la sesión (tiradas, daño, curación, etc.)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            details_json = json.dumps(details or {}, ensure_ascii=False)
            cursor.execute("""
                INSERT INTO dm_session_logs (session_id, event_type, actor_name, target_name, details_json)
                VALUES (?, ?, ?, ?, ?);
            """, (session_id, event_type, actor_name, target_name, details_json))
            conn.commit()
            return cursor.lastrowid or 0

    def get_session_logs(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene los registros históricos de eventos de la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dm_session_logs
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (session_id, limit))
            logs = []
            for row in cursor.fetchall():
                d = dict(row)
                try:
                    d["details"] = json.loads(d.get("details_json", "{}"))
                except Exception:
                    d["details"] = {}
                logs.append(d)
            return logs

    # =========================================================================
    # FORJA Y DISTRIBUCIÓN DE OBJETOS HOMEBREW DEL DM
    # =========================================================================

    def save_homebrew_item(self, item: Dict[str, Any]) -> str:
        """Guarda o actualiza un objeto Homebrew creado por el DM."""
        item_id = item.get("id") or f"hb_{int(os.urandom(4).hex(), 16)}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            props = json.dumps(item.get("properties", []), ensure_ascii=False)
            cursor.execute("""
                INSERT INTO dm_homebrew_items (
                    id, name, category, rarity, requires_attunement,
                    damage_dice, damage_type, secondary_dice, secondary_type,
                    bonus_attack, bonus_damage, ac_bonus, properties_json, description, scroll_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    category = excluded.category,
                    rarity = excluded.rarity,
                    requires_attunement = excluded.requires_attunement,
                    damage_dice = excluded.damage_dice,
                    damage_type = excluded.damage_type,
                    secondary_dice = excluded.secondary_dice,
                    secondary_type = excluded.secondary_type,
                    bonus_attack = excluded.bonus_attack,
                    bonus_damage = excluded.bonus_damage,
                    ac_bonus = excluded.ac_bonus,
                    properties_json = excluded.properties_json,
                    description = excluded.description,
                    scroll_content = excluded.scroll_content;
            """, (
                item_id,
                item.get("name", "Objeto sin nombre"),
                item.get("category", "wondrous"),
                item.get("rarity", "common"),
                1 if item.get("requires_attunement") else 0,
                item.get("damage_dice"),
                item.get("damage_type"),
                item.get("secondary_dice"),
                item.get("secondary_type"),
                int(item.get("bonus_attack") or 0),
                int(item.get("bonus_damage") or 0),
                int(item.get("ac_bonus") or 0),
                props,
                item.get("description", ""),
                item.get("scroll_content", ""),
            ))
            conn.commit()
            return item_id

    def list_homebrew_items(self) -> List[Dict[str, Any]]:
        """Lista todos los objetos Homebrew guardados en la forja."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dm_homebrew_items ORDER BY name ASC;")
            items = []
            for row in cursor.fetchall():
                d = dict(row)
                try:
                    d["properties"] = json.loads(d.get("properties_json", "[]"))
                except Exception:
                    d["properties"] = []
                items.append(d)
            return items

    def delete_homebrew_item(self, item_id: str) -> bool:
        """Elimina un objeto Homebrew de la forja."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dm_homebrew_items WHERE id = ?;", (item_id,))
            conn.commit()
            return True

