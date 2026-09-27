import sqlite3

from config import DATABASE_PATH


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS cats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS feedings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            period TEXT NOT NULL,
            fed_at TEXT NOT NULL,
            FOREIGN KEY (cat_id) REFERENCES cats (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (cat_id, date, period)
        )
    """)

    connection.execute("""
        INSERT OR IGNORE INTO cats (id, name)
        VALUES (1, 'Jozy')
    """)

    connection.commit()
    connection.close()