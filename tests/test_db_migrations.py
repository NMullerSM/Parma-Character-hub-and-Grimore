import os
import sqlite3
import tempfile
import pytest
from core.db import DatabaseManager


def test_schema_user_version_and_migration():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # 1. Simular base de datos 1.0.3 (user_version = 0) con datos preexistentes
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE characters (
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
    cursor.execute("""
        INSERT INTO characters (name, char_class, level, data_json)
        VALUES ('Elminster', 'Wizard', 20, '{"name": "Elminster"}');
    """)
    conn.commit()
    conn.close()

    # 2. Inicializar DatabaseManager con la BD versión 0 existente
    db = DatabaseManager(db_path=path)

    # 3. Comprobar que se generó la copia de respaldo de seguridad
    backup_path = f"{path}.bak_v0"
    assert os.path.exists(backup_path), "No se creó el respaldo .bak_v0 antes de migrar"

    # 4. Comprobar que user_version fue actualizado a la versión vigente (v2 en 1.0.5)
    with db._get_connection() as c:
        cur = c.cursor()
        cur.execute("PRAGMA user_version;")
        assert cur.fetchone()[0] == 2

        # 5. Comprobar que las nuevas tablas existen
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trusted_players';")
        assert cur.fetchone() is not None
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dm_invitations';")
        assert cur.fetchone() is not None
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compendium_monsters';")
        assert cur.fetchone() is not None

        # 6. Comprobar que los datos del personaje previo se conservaron intactos
        cur.execute("SELECT name, char_class, level FROM characters WHERE name='Elminster';")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "Elminster"
        assert row[1] == "Wizard"
        assert row[2] == 20

    # Limpieza
    if os.path.exists(path):
        os.remove(path)
    if os.path.exists(backup_path):
        os.remove(backup_path)
