# database.py
# Minimal SQLite setup for Evidence AI.
# Phase 1 only needs the database to exist with one simple table.
# Full create/read/update/delete features will be added in a later phase.

import sqlite3

from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database file."""
    # DATABASE_PATH is a Path object; sqlite3 accepts it directly.
    return sqlite3.connect(DATABASE_PATH)


def init_db() -> None:
    """Create the database file and the 'cases' table if they don't exist yet."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            case_type TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()
