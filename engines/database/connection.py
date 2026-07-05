# engines/database/connection.py
"""
Gestion de la connexion SQLite et initialisation du schéma.
Responsabilité unique : ouvrir/fermer des connexions et créer les tables.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import sqlite3
from pathlib import Path
from loguru import logger

from config import DB_PATH
from engines.database.schema import SCHEMA_SQL

# Garantit que le dossier data/ existe
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """
    Ouvre et retourne une connexion SQLite.
    Active les foreign keys à chaque connexion — obligation SQLite.
    Le appelant est responsable de fermer la connexion (conn.close()).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """
    Initialise la base de données en créant toutes les tables.
    Idempotent — peut être appelé plusieurs fois sans erreur
    grâce aux CREATE TABLE IF NOT EXISTS dans le schéma.
    """
    logger.info(f"Initialisation DB : {DB_PATH}")
    try:
        conn = get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        logger.success("Base initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur init DB : {e}")
        raise


def test_db() -> list:
    """
    Vérifie que les tables ont bien été créées.
    Retourne la liste des noms de tables présentes.
    Utilisé dans les tests et le diagnostic.
    """
    conn = get_connection()
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables