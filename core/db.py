"""
Motor de Persistencia Local SQLite para Visualizador & Editor D&D 5e.
Conexión optimizada con modo WAL, transacciones atómicas, almacenamiento relacional y migración JSON.
"""
import os
import sys
import json
import sqlite3
import shutil
import contextlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator
from .models import CharacterSheet, SessionLog, NetworkNode, NetworkEdge
from .paths import get_default_db_path, get_user_data_dir, get_bundle_dir


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self._init_db()

    @contextlib.contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager que además CIERRA la conexión al salir.
        `sqlite3.Connection.__exit__` solo hace commit/rollback de la transacción,
        nunca cierra el handle del archivo: en Windows eso deja el .db bloqueado
        (PermissionError [WinError 32]) hasta que el GC recoja la conexión, lo que
        rompe la limpieza de bases de datos temporales en tests y en migraciones.
        """
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # WAL mode para máxima concurrencia y velocidad
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Crea y migra las tablas relacionales según PRAGMA user_version."""
        db_existed = os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version;")
            row_v = cursor.fetchone()
            current_version = row_v[0] if row_v else 0

            # Si la base de datos existía pero user_version era 0, realizar copia de seguridad antes de migrar
            if db_existed and current_version == 0:
                backup_path = f"{self.db_path}.bak_v0"
                if not os.path.exists(backup_path):
                    try:
                        shutil.copy2(self.db_path, backup_path)
                    except Exception as e:
                        print(f"[DatabaseManager] Advertencia al respaldar BD v0: {e}")

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Migración a versión 1: Control de invitaciones y autenticación de jugadores (TOFU)
            if current_version < 1:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trusted_players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        token_hash TEXT NOT NULL UNIQUE,
                        approved_by_dm INTEGER DEFAULT 0,
                        is_revoked INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dm_invitations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        invite_token TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        is_used INTEGER DEFAULT 0,
                        used_by_token_hash TEXT
                    );
                """)
                cursor.execute("PRAGMA user_version = 1;")

            # Migración a versión 2: Compendio Relacional-Documental D&D 5.5e (2024 PHB/SRD)
            if current_version < 2:
                if db_existed and current_version >= 1:
                    backup_path_v1 = f"{self.db_path}.bak_v1"
                    if not os.path.exists(backup_path_v1):
                        try:
                            shutil.copy2(self.db_path, backup_path_v1)
                        except Exception as e:
                            print(f"[DatabaseManager] Advertencia al respaldar BD v1: {e}")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS compendium_monsters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        name_en TEXT,
                        cr REAL NOT NULL DEFAULT 0.0,
                        cr_text TEXT NOT NULL DEFAULT '0',
                        size TEXT,
                        monster_type TEXT,
                        alignment TEXT,
                        ac INTEGER DEFAULT 10,
                        hp_avg INTEGER DEFAULT 10,
                        hp_formula TEXT DEFAULT '',
                        speed TEXT DEFAULT '',
                        edition TEXT NOT NULL DEFAULT '5.5e',
                        language TEXT NOT NULL DEFAULT 'en',
                        data_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_monsters_cr ON compendium_monsters(cr);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_monsters_type ON compendium_monsters(monster_type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_monsters_name ON compendium_monsters(name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_monsters_edition_lang ON compendium_monsters(edition, language);")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS compendium_spells (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        name_en TEXT,
                        level INTEGER NOT NULL DEFAULT 0,
                        school TEXT NOT NULL DEFAULT 'Evocation',
                        casting_time TEXT NOT NULL DEFAULT '1 action',
                        range_area TEXT NOT NULL DEFAULT '60 feet',
                        components TEXT NOT NULL DEFAULT 'V, S',
                        duration TEXT NOT NULL DEFAULT 'Instantaneous',
                        is_concentration INTEGER DEFAULT 0,
                        is_ritual INTEGER DEFAULT 0,
                        classes TEXT DEFAULT '',
                        edition TEXT NOT NULL DEFAULT '5.5e',
                        language TEXT NOT NULL DEFAULT 'en',
                        description TEXT NOT NULL DEFAULT '',
                        data_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_spells_level ON compendium_spells(level);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_spells_school ON compendium_spells(school);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_spells_name ON compendium_spells(name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_spells_edition_lang ON compendium_spells(edition, language);")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS compendium_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        name_en TEXT,
                        item_type TEXT NOT NULL DEFAULT 'gear',
                        rarity TEXT DEFAULT 'common',
                        cost TEXT DEFAULT '',
                        weight TEXT DEFAULT '',
                        weapon_mastery TEXT DEFAULT '',
                        damage TEXT DEFAULT '',
                        damage_type TEXT DEFAULT '',
                        ac_bonus INTEGER DEFAULT 0,
                        edition TEXT NOT NULL DEFAULT '5.5e',
                        language TEXT NOT NULL DEFAULT 'en',
                        description TEXT NOT NULL DEFAULT '',
                        data_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON compendium_items(item_type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_rarity ON compendium_items(rarity);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON compendium_items(name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_mastery ON compendium_items(weapon_mastery);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_edition_lang ON compendium_items(edition, language);")

                cursor.execute("PRAGMA user_version = 2;")

            # Migración a versión 3: Tabla compendium_entities (clases, especies, trasfondos, etc.)
            if current_version < 3:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS compendium_entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        name_en TEXT,
                        category TEXT NOT NULL,
                        edition TEXT NOT NULL DEFAULT '5.5e',
                        language TEXT NOT NULL DEFAULT 'es',
                        snippet TEXT DEFAULT '',
                        content_markdown TEXT NOT NULL DEFAULT '',
                        data_json TEXT NOT NULL DEFAULT '{}',
                        source TEXT NOT NULL DEFAULT 'PHB 2024',
                        expansion_tag TEXT NOT NULL DEFAULT 'phb_2024',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_cat_lang ON compendium_entities(category, language);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON compendium_entities(name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_edition_lang ON compendium_entities(edition, language);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_entity_id ON compendium_entities(entity_id);")

                cursor.execute("PRAGMA user_version = 3;")

            # Migración a versión 4: Columnas source y expansion_tag para compendio y expansiones (Xanathar / Tasha)
            if current_version < 4:
                for tbl in ("compendium_monsters", "compendium_spells", "compendium_items", "compendium_entities"):
                    cursor.execute(f"PRAGMA table_info({tbl});")
                    cols = [row[1] for row in cursor.fetchall()]
                    if "source" not in cols:
                        cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN source TEXT DEFAULT '';")
                    if "expansion_tag" not in cols:
                        cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN expansion_tag TEXT DEFAULT '';")
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_source ON {tbl}(source);")
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_expansion_tag ON {tbl}(expansion_tag);")

                # Backfill de fuentes en datos existentes
                cursor.execute("""
                    UPDATE compendium_monsters SET source = 'SRD 5.2 (2024)', expansion_tag = 'phb_2024'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5.5e', '2024');
                """)
                cursor.execute("""
                    UPDATE compendium_monsters SET source = 'SRD 5.1 (2014)', expansion_tag = 'srd_2014'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5e', '2014');
                """)

                cursor.execute("""
                    UPDATE compendium_spells SET source = 'SRD 5.2 (2024)', expansion_tag = 'phb_2024'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5.5e', '2024');
                """)
                cursor.execute("""
                    UPDATE compendium_spells SET source = 'SRD 5.1 (2014)', expansion_tag = 'srd_2014'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5e', '2014');
                """)

                cursor.execute("""
                    UPDATE compendium_items SET source = 'SRD 5.2 (2024)', expansion_tag = 'phb_2024'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5.5e', '2024');
                """)
                cursor.execute("""
                    UPDATE compendium_items SET source = 'SRD 5.1 (2014)', expansion_tag = 'srd_2014'
                    WHERE (source = '' OR source IS NULL) AND edition IN ('5e', '2014');
                """)

                cursor.execute("""
                    UPDATE compendium_entities SET source = "Tasha's Cauldron of Everything", expansion_tag = 'tce'
                    WHERE (source = '' OR source IS NULL) AND (LOWER(data_json) LIKE '%tasha%');
                """)
                cursor.execute("""
                    UPDATE compendium_entities SET source = "Xanathar's Guide to Everything", expansion_tag = 'xge'
                    WHERE (source = '' OR source IS NULL) AND (LOWER(data_json) LIKE '%xanathar%');
                """)
                cursor.execute("""
                    UPDATE compendium_entities SET source = 'PHB 2024', expansion_tag = 'phb_2024'
                    WHERE source = '' OR source IS NULL;
                """)

                cursor.execute("PRAGMA user_version = 4;")

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
                    bonus_attack, bonus_damage, ac_bonus, properties_json, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    description = excluded.description;
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

    # =========================================================================
    # GESTIÓN DE JUGADORES DE CONFIANZA E INVITACIONES (TOFU & HARDENING)
    # =========================================================================

    def create_invitation(self, session_id: str, invite_token: str, expires_seconds: int = 3600) -> bool:
        """Registra un token de invitación temporal de un solo uso para una sesión DM."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            mod_str = f"{expires_seconds:+d} seconds"
            cursor.execute("""
                INSERT INTO dm_invitations (session_id, invite_token, expires_at)
                VALUES (?, ?, datetime('now', ?));
            """, (session_id, invite_token, mod_str))
            conn.commit()
            return True

    def get_invitation(self, invite_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de una invitación válida y no expirada."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dm_invitations
                WHERE invite_token = ?
                  AND is_used = 0
                  AND (expires_at IS NULL OR expires_at > datetime('now'))
                LIMIT 1;
            """, (invite_token,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def mark_invitation_used(self, invite_token: str, token_hash: str) -> bool:
        """Marca una invitación como consumida por un token_hash específico."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dm_invitations
                SET is_used = 1, used_by_token_hash = ?
                WHERE invite_token = ?;
            """, (token_hash, invite_token))
            conn.commit()
            return cursor.rowcount > 0

    def register_trusted_player(self, name: str, token_hash: str, approved: bool = False) -> int:
        """Registra o actualiza un jugador de confianza en la base de datos."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trusted_players (name, token_hash, approved_by_dm, last_seen)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(token_hash) DO UPDATE SET
                    name = excluded.name,
                    last_seen = datetime('now');
            """, (name, token_hash, 1 if approved else 0))
            conn.commit()
            return cursor.lastrowid or 0

    def get_trusted_player_by_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Busca un jugador por el hash SHA-256 de su clave secreta."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trusted_players WHERE token_hash = ? LIMIT 1;
            """, (token_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def approve_trusted_player(self, token_hash: str) -> bool:
        """Aprueba manualmente a un jugador para permitir su acceso a la sesión."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trusted_players
                SET approved_by_dm = 1, is_revoked = 0, last_seen = datetime('now')
                WHERE token_hash = ?;
            """, (token_hash,))
            conn.commit()
            return cursor.rowcount > 0

    def revoke_trusted_player(self, token_hash: str) -> bool:
        """Revoca a un jugador impidiendo su acceso futuro a sesiones remotas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trusted_players
                SET is_revoked = 1, approved_by_dm = 0
                WHERE token_hash = ?;
            """, (token_hash,))
            conn.commit()
            return cursor.rowcount > 0

    def list_trusted_players(self) -> List[Dict[str, Any]]:
        """Lista todos los jugadores registrados con su estado de aprobación."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trusted_players ORDER BY last_seen DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def update_player_last_seen(self, token_hash: str):
        """Actualiza la marca temporal de última actividad de un jugador."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trusted_players SET last_seen = datetime('now') WHERE token_hash = ?;
            """, (token_hash,))
            conn.commit()

    # =========================================================================
    # COMPENDIO RELACIONAL-DOCUMENTAL (MONSTRUOS, CONJUROS, EQUIPO)
    # =========================================================================

    def upsert_compendium_monster(self, monster_data: Dict[str, Any]) -> str:
        """Inserta o actualiza un monstruo en el compendio relacional SQLite."""
        entity_id = monster_data.get("entity_id") or monster_data.get("id") or monster_data["name"].lower().replace(" ", "_")
        name = monster_data["name"]
        name_en = monster_data.get("name_en")
        cr = float(monster_data.get("cr", 0.0))
        cr_text = str(monster_data.get("cr_text", monster_data.get("cr", "0")))
        size = monster_data.get("size", "Medium")
        m_type = monster_data.get("monster_type") or monster_data.get("type", "Monstrosity")
        alignment = monster_data.get("alignment", "Unaligned")
        ac = int(monster_data.get("ac", 10))
        hp_avg = int(monster_data.get("hp_avg") or monster_data.get("hp", 10))
        hp_formula = str(monster_data.get("hp_formula", ""))
        speed = str(monster_data.get("speed", "30 ft."))
        edition = str(monster_data.get("edition", "5.5e"))
        language = str(monster_data.get("language", "en"))
        source = str(monster_data.get("source", "SRD 5.2 (2024)" if edition == "5.5e" else "SRD 5.1 (2014)"))
        expansion_tag = str(monster_data.get("expansion_tag", "phb_2024" if edition == "5.5e" else "srd_2014"))
        raw_json = monster_data.get("data_json")
        data_json = raw_json if isinstance(raw_json, str) else json.dumps(monster_data, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compendium_monsters (
                    entity_id, name, name_en, cr, cr_text, size, monster_type,
                    alignment, ac, hp_avg, hp_formula, speed, edition, language,
                    source, expansion_tag, data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(entity_id) DO UPDATE SET
                    name = excluded.name,
                    name_en = excluded.name_en,
                    cr = excluded.cr,
                    cr_text = excluded.cr_text,
                    size = excluded.size,
                    monster_type = excluded.monster_type,
                    alignment = excluded.alignment,
                    ac = excluded.ac,
                    hp_avg = excluded.hp_avg,
                    hp_formula = excluded.hp_formula,
                    speed = excluded.speed,
                    edition = excluded.edition,
                    language = excluded.language,
                    source = excluded.source,
                    expansion_tag = excluded.expansion_tag,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                entity_id, name, name_en, cr, cr_text, size, m_type,
                alignment, ac, hp_avg, hp_formula, speed, edition, language,
                source, expansion_tag, data_json
            ))
            conn.commit()
            return entity_id

    def search_compendium_monsters(
        self,
        query: str = "",
        min_cr: Optional[float] = None,
        max_cr: Optional[float] = None,
        monster_type: Optional[str] = None,
        size: Optional[str] = None,
        edition: Optional[str] = None,
        language: str = "en",
        expansions: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Búsqueda y filtrado rápido de monstruos indexados con soporte de paginación y expansiones."""
        sql = "SELECT id, entity_id, name, name_en, cr, cr_text, size, monster_type, alignment, ac, hp_avg, hp_formula, speed, edition, language, source, expansion_tag FROM compendium_monsters WHERE 1=1"
        params: List[Any] = []

        if query:
            sql += " AND (name LIKE ? OR name_en LIKE ? OR entity_id LIKE ?)"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like])
        if min_cr is not None:
            sql += " AND cr >= ?"
            params.append(min_cr)
        if max_cr is not None:
            sql += " AND cr <= ?"
            params.append(max_cr)
        if monster_type:
            sql += " AND LOWER(monster_type) = LOWER(?)"
            params.append(monster_type)
        if size:
            sql += " AND LOWER(size) = LOWER(?)"
            params.append(size)
        if edition:
            if edition in ("5.5e", "2024"):
                sql += " AND edition IN ('5.5e', '2024')"
            elif edition in ("5e", "2014"):
                sql += " AND edition IN ('5e', '2014')"
            else:
                sql += " AND edition = ?"
                params.append(edition)
        if language:
            sql += " AND language = ?"
            params.append(language)
        if expansions:
            valid_exp = [e.lower() for e in expansions if e and e.lower() != "all"]
            if valid_exp:
                placeholders = ",".join("?" for _ in valid_exp)
                sql += f" AND (LOWER(expansion_tag) IN ({placeholders}) OR LOWER(source) IN ({placeholders}))"
                params.extend(valid_exp)
                params.extend(valid_exp)

        sql += " ORDER BY cr ASC, name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_compendium_monster_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna el registro completo de un monstruo con su data_json deserializado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compendium_monsters WHERE entity_id = ? OR name = ? OR name_en = ? LIMIT 1;", (entity_id, entity_id, entity_id))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["details"] = json.loads(res["data_json"])
            except Exception:
                res["details"] = {}
            return res

    def upsert_compendium_spell(self, spell_data: Dict[str, Any]) -> str:
        """Inserta o actualiza un conjuro en el compendio relacional."""
        entity_id = spell_data.get("entity_id") or spell_data.get("id") or spell_data["name"].lower().replace(" ", "_")
        name = spell_data["name"]
        name_en = spell_data.get("name_en")
        level = int(spell_data.get("level", 0))
        school = spell_data.get("school", "Evocation")
        casting_time = spell_data.get("casting_time") or spell_data.get("cast_time", "1 action")
        range_area = spell_data.get("range_area") or spell_data.get("range", "60 feet")
        components = spell_data.get("components", "V, S")
        duration = spell_data.get("duration", "Instantaneous")
        is_conc = 1 if spell_data.get("is_concentration") or spell_data.get("concentration") else 0
        is_rit = 1 if spell_data.get("is_ritual") or spell_data.get("ritual") else 0
        raw_classes = spell_data.get("classes", "")
        classes_str = ", ".join(raw_classes) if isinstance(raw_classes, list) else str(raw_classes)
        edition = str(spell_data.get("edition", "5.5e"))
        language = str(spell_data.get("language", "en"))
        source = str(spell_data.get("source", "SRD 5.2 (2024)" if edition == "5.5e" else "SRD 5.1 (2014)"))
        expansion_tag = str(spell_data.get("expansion_tag", "phb_2024" if edition == "5.5e" else "srd_2014"))
        desc = str(spell_data.get("description") or spell_data.get("notes", ""))
        raw_json = spell_data.get("data_json")
        data_json = raw_json if isinstance(raw_json, str) else json.dumps(spell_data, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compendium_spells (
                    entity_id, name, name_en, level, school, casting_time, range_area,
                    components, duration, is_concentration, is_ritual, classes,
                    edition, language, source, expansion_tag, description, data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(entity_id) DO UPDATE SET
                    name = excluded.name,
                    name_en = excluded.name_en,
                    level = excluded.level,
                    school = excluded.school,
                    casting_time = excluded.casting_time,
                    range_area = excluded.range_area,
                    components = excluded.components,
                    duration = excluded.duration,
                    is_concentration = excluded.is_concentration,
                    is_ritual = excluded.is_ritual,
                    classes = excluded.classes,
                    edition = excluded.edition,
                    language = excluded.language,
                    source = excluded.source,
                    expansion_tag = excluded.expansion_tag,
                    description = excluded.description,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                entity_id, name, name_en, level, school, casting_time, range_area,
                components, duration, is_conc, is_rit, classes_str,
                edition, language, source, expansion_tag, desc, data_json
            ))
            conn.commit()
            return entity_id

    def search_compendium_spells(
        self,
        query: str = "",
        level: Optional[int] = None,
        max_level: Optional[int] = None,
        school: Optional[str] = None,
        class_name: Optional[str] = None,
        is_concentration: Optional[bool] = None,
        is_ritual: Optional[bool] = None,
        edition: Optional[str] = None,
        language: str = "en",
        expansions: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Búsqueda y filtrado de conjuros indexados con soporte de expansiones."""
        sql = "SELECT id, entity_id, name, name_en, level, school, casting_time, range_area, components, duration, is_concentration, is_ritual, classes, edition, language, source, expansion_tag, description FROM compendium_spells WHERE 1=1"
        params: List[Any] = []

        if query:
            sql += " AND (name LIKE ? OR name_en LIKE ? OR description LIKE ?)"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like])
        if level is not None:
            sql += " AND level = ?"
            params.append(level)
        elif max_level is not None:
            sql += " AND level <= ?"
            params.append(max_level)
        if school:
            sql += " AND LOWER(school) = LOWER(?)"
            params.append(school)
        if class_name:
            sql += " AND classes LIKE ?"
            params.append(f"%{class_name}%")
        if is_concentration is not None:
            sql += " AND is_concentration = ?"
            params.append(1 if is_concentration else 0)
        if is_ritual is not None:
            sql += " AND is_ritual = ?"
            params.append(1 if is_ritual else 0)
        if edition:
            if edition in ("5.5e", "2024"):
                sql += " AND edition IN ('5.5e', '2024')"
            elif edition in ("5e", "2014"):
                sql += " AND edition IN ('5e', '2014')"
            else:
                sql += " AND edition = ?"
                params.append(edition)
        if language:
            sql += " AND language = ?"
            params.append(language)
        if expansions:
            valid_exp = [e.lower() for e in expansions if e and e.lower() != "all"]
            if valid_exp:
                placeholders = ",".join("?" for _ in valid_exp)
                sql += f" AND (LOWER(expansion_tag) IN ({placeholders}) OR LOWER(source) IN ({placeholders}))"
                params.extend(valid_exp)
                params.extend(valid_exp)

        sql += " ORDER BY level ASC, name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_compendium_spell_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna un conjuro por id o nombre con su data_json deserializado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compendium_spells WHERE entity_id = ? OR name = ? OR name_en = ? LIMIT 1;", (entity_id, entity_id, entity_id))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["details"] = json.loads(res["data_json"])
            except Exception:
                res["details"] = {}
            return res

    def upsert_compendium_item(self, item_data: Dict[str, Any]) -> str:
        """Inserta o actualiza un objeto/arma/armadura en el compendio relacional."""
        entity_id = item_data.get("entity_id") or item_data.get("id") or item_data["name"].lower().replace(" ", "_")
        name = item_data["name"]
        name_en = item_data.get("name_en")
        item_type = item_data.get("item_type", "gear")
        rarity = item_data.get("rarity", "common")
        cost = str(item_data.get("cost", ""))
        weight = str(item_data.get("weight", ""))
        weapon_mastery = str(item_data.get("weapon_mastery", ""))
        damage = str(item_data.get("damage", ""))
        damage_type = str(item_data.get("damage_type", ""))
        ac_bonus = int(item_data.get("ac_bonus", 0))
        edition = str(item_data.get("edition", "5.5e"))
        language = str(item_data.get("language", "en"))
        source = str(item_data.get("source", "SRD 5.2 (2024)" if edition == "5.5e" else "SRD 5.1 (2014)"))
        expansion_tag = str(item_data.get("expansion_tag", "phb_2024" if edition == "5.5e" else "srd_2014"))
        desc = str(item_data.get("description", ""))
        raw_json = item_data.get("data_json")
        data_json = raw_json if isinstance(raw_json, str) else json.dumps(item_data, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compendium_items (
                    entity_id, name, name_en, item_type, rarity, cost, weight,
                    weapon_mastery, damage, damage_type, ac_bonus, edition,
                    language, source, expansion_tag, description, data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(entity_id) DO UPDATE SET
                    name = excluded.name,
                    name_en = excluded.name_en,
                    item_type = excluded.item_type,
                    rarity = excluded.rarity,
                    cost = excluded.cost,
                    weight = excluded.weight,
                    weapon_mastery = excluded.weapon_mastery,
                    damage = excluded.damage,
                    damage_type = excluded.damage_type,
                    ac_bonus = excluded.ac_bonus,
                    edition = excluded.edition,
                    language = excluded.language,
                    source = excluded.source,
                    expansion_tag = excluded.expansion_tag,
                    description = excluded.description,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                entity_id, name, name_en, item_type, rarity, cost, weight,
                weapon_mastery, damage, damage_type, ac_bonus, edition,
                language, source, expansion_tag, desc, data_json
            ))
            conn.commit()
            return entity_id

    def search_compendium_items(
        self,
        query: str = "",
        item_type: Optional[str] = None,
        rarity: Optional[str] = None,
        weapon_mastery: Optional[str] = None,
        edition: Optional[str] = None,
        language: str = "en",
        expansions: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Búsqueda y filtrado de equipo, armas y objetos mágicos con soporte de expansiones."""
        sql = "SELECT id, entity_id, name, name_en, item_type, rarity, cost, weight, weapon_mastery, damage, damage_type, ac_bonus, edition, language, source, expansion_tag, description FROM compendium_items WHERE 1=1"
        params: List[Any] = []

        if query:
            sql += " AND (name LIKE ? OR name_en LIKE ? OR description LIKE ?)"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like])
        if item_type:
            sql += " AND LOWER(item_type) = LOWER(?)"
            params.append(item_type)
        if rarity:
            sql += " AND LOWER(rarity) = LOWER(?)"
            params.append(rarity)
        if weapon_mastery:
            sql += " AND LOWER(weapon_mastery) = LOWER(?)"
            params.append(weapon_mastery)
        if edition:
            if edition in ("5.5e", "2024"):
                sql += " AND edition IN ('5.5e', '2024')"
            elif edition in ("5e", "2014"):
                sql += " AND edition IN ('5e', '2014')"
            else:
                sql += " AND edition = ?"
                params.append(edition)
        if language:
            sql += " AND language = ?"
            params.append(language)
        if expansions:
            valid_exp = [e.lower() for e in expansions if e and e.lower() != "all"]
            if valid_exp:
                placeholders = ",".join("?" for _ in valid_exp)
                sql += f" AND (LOWER(expansion_tag) IN ({placeholders}) OR LOWER(source) IN ({placeholders}))"
                params.extend(valid_exp)
                params.extend(valid_exp)

        sql += " ORDER BY name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_compendium_item_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna un objeto por id o nombre con su data_json deserializado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compendium_items WHERE entity_id = ? OR name = ? OR name_en = ? LIMIT 1;", (entity_id, entity_id, entity_id))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["details"] = json.loads(res["data_json"])
            except Exception:
                res["details"] = {}
            return res

    def upsert_compendium_entity(self, entity_data: Dict[str, Any]) -> str:
        """Inserta o actualiza una entidad de compendio (clase, especie, trasfondo, dote, regla)."""
        entity_id = entity_data.get("entity_id") or entity_data.get("id") or entity_data["name"].lower().replace(" ", "_")
        name = entity_data["name"]
        name_en = entity_data.get("name_en")
        category = entity_data.get("category", "regla")
        edition = str(entity_data.get("edition", "5.5e"))
        language = str(entity_data.get("language", "es"))
        source = str(entity_data.get("source", "PHB 2024"))
        expansion_tag = str(entity_data.get("expansion_tag", "phb_2024"))
        snippet = str(entity_data.get("snippet", ""))
        content_md = str(entity_data.get("content_markdown") or entity_data.get("content") or entity_data.get("description", ""))
        raw_json = entity_data.get("data_json")
        if isinstance(raw_json, str):
            data_json = raw_json
        elif isinstance(raw_json, dict):
            data_json = json.dumps(raw_json, ensure_ascii=False)
        else:
            data_json = json.dumps(entity_data, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compendium_entities (
                    entity_id, name, name_en, category, edition,
                    language, source, expansion_tag, snippet, content_markdown, data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(entity_id) DO UPDATE SET
                    name = excluded.name,
                    name_en = excluded.name_en,
                    category = excluded.category,
                    edition = excluded.edition,
                    language = excluded.language,
                    source = excluded.source,
                    expansion_tag = excluded.expansion_tag,
                    snippet = excluded.snippet,
                    content_markdown = excluded.content_markdown,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                entity_id, name, name_en, category, edition,
                language, source, expansion_tag, snippet, content_md, data_json
            ))
            conn.commit()
            return entity_id

    def search_compendium_entities(
        self,
        query: str = "",
        category: Optional[str] = None,
        categories: Optional[List[str]] = None,
        language: str = "es",
        edition: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        limit: int = 150,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Búsqueda y listado de entidades en compendium_entities con soporte de expansiones."""
        sql = "SELECT id, entity_id, name, name_en, category, edition, language, source, expansion_tag, snippet, content_markdown, data_json FROM compendium_entities WHERE 1=1"
        params: List[Any] = []

        if query:
            sql += " AND (name LIKE ? OR name_en LIKE ? OR content_markdown LIKE ? OR snippet LIKE ?)"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like, q_like])

        if category:
            sql += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        elif categories:
            placeholders = ",".join("?" for _ in categories)
            sql += f" AND LOWER(category) IN ({placeholders})"
            params.extend([c.lower() for c in categories])

        if edition:
            if edition in ("5.5e", "2024"):
                sql += " AND edition IN ('5.5e', '2024')"
            elif edition in ("5e", "2014"):
                sql += " AND edition IN ('5e', '2014')"
            else:
                sql += " AND edition = ?"
                params.append(edition)

        if language:
            sql += " AND language = ?"
            params.append(language)

        if expansions:
            valid_exp = [e.lower() for e in expansions if e and e.lower() != "all"]
            if valid_exp:
                placeholders = ",".join("?" for _ in valid_exp)
                sql += f" AND (LOWER(expansion_tag) IN ({placeholders}) OR LOWER(source) IN ({placeholders}))"
                params.extend(valid_exp)
                params.extend(valid_exp)

        sql += " ORDER BY name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                try:
                    d["metadata"] = json.loads(d.get("data_json") or "{}")
                except Exception:
                    d["metadata"] = {}
                rows.append(d)
            return rows

    def get_compendium_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una entidad de compendio por su entity_id, name o name_en."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM compendium_entities 
                WHERE entity_id = ? OR name = ? OR name_en = ? 
                   OR LOWER(entity_id) = LOWER(?) OR LOWER(name) = LOWER(?)
                LIMIT 1;
            """, (entity_id, entity_id, entity_id, entity_id, entity_id))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["details"] = json.loads(res.get("data_json") or "{}")
            except Exception:
                res["details"] = {}
            return res

    def count_compendium_entries(
        self,
        category: str,
        categories: Optional[List[str]] = None,
        edition: Optional[str] = None,
        language: Optional[str] = None,
        expansions: Optional[List[str]] = None,
    ) -> int:
        """Retorna el conteo total de entradas en una tabla del compendio o por categoría y expansión."""
        cat_lower = category.lower() if category else ""
        if cat_lower in ("monsters", "monstruos"):
            tbl = "compendium_monsters"
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE 1=1"
            params: List[Any] = []
        elif cat_lower in ("spells", "conjuros"):
            tbl = "compendium_spells"
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE 1=1"
            params: List[Any] = []
        elif cat_lower in ("items", "equipo", "equipo_y_armamento"):
            tbl = "compendium_items"
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE 1=1"
            params: List[Any] = []
        else:
            tbl = "compendium_entities"
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE 1=1"
            params = []
            if categories:
                placeholders = ",".join("?" for _ in categories)
                sql += f" AND LOWER(category) IN ({placeholders})"
                params.extend([c.lower() for c in categories])
            elif category and cat_lower not in ("all", "entities"):
                sql += " AND LOWER(category) = LOWER(?)"
                params.append(category)

        if edition:
            if edition in ("5.5e", "2024"):
                sql += " AND edition IN ('5.5e', '2024')"
            elif edition in ("5e", "2014"):
                sql += " AND edition IN ('5e', '2014')"
            else:
                sql += " AND edition = ?"
                params.append(edition)
        if language:
            sql += " AND language = ?"
            params.append(language)
        if expansions:
            valid_exp = [e.lower() for e in expansions if e and e.lower() != "all"]
            if valid_exp:
                placeholders = ",".join("?" for _ in valid_exp)
                sql += f" AND (LOWER(expansion_tag) IN ({placeholders}) OR LOWER(source) IN ({placeholders}))"
                params.extend(valid_exp)
                params.extend(valid_exp)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row[0] if row else 0
