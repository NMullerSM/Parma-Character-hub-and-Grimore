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
        # flet_app/core/db.py -> raíz del repo
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
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
                    id TEXT PRIMARY KEY,
                    character_id INTEGER,
                    name TEXT,
                    role TEXT,
                    description TEXT,
                    avatar_base64 TEXT,
                    x REAL DEFAULT 0.0,
                    y REAL DEFAULT 0.0,
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
        char_dict = char.to_dict()
        data_json = json.dumps(char_dict, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Buscar si ya existe por nombre
            cursor.execute("SELECT id FROM characters WHERE name = ? LIMIT 1;", (char.name,))
            existing = cursor.fetchone()

            if existing:
                char_id = existing["id"]
                if set_active:
                    cursor.execute("UPDATE characters SET is_active = 0;")
                cursor.execute("""
                    UPDATE characters
                    SET char_class = ?, subclass = ?, level = ?, race = ?,
                        hp_current = ?, hp_max = ?, portrait_path = ?,
                        data_json = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (
                    char.char_class, char.subclass, char.level, char.race,
                    char.hp_current, char.hp_max, char.portrait_path,
                    data_json, 1 if set_active else 0, char_id
                ))
            else:
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
                    INSERT INTO network_nodes (id, character_id, name, role, description, avatar_base64, x, y)
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
            cursor.execute("SELECT id, name, char_class, level, race, hp_current, hp_max, portrait_path, is_active, updated_at FROM characters ORDER BY updated_at DESC;")
            return [dict(r) for r in cursor.fetchall()]

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
