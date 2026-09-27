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
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_chat_id INTEGER UNIQUE NOT NULL,
            type TEXT NOT NULL,
            title TEXT,
            keyboard_message_id INTEGER,
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
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_user_id INTEGER NOT NULL,
            assignee_user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            photo_file_id TEXT,
            created_at TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_acceptance',
            accepted_at TEXT,
            completed_at TEXT,
            cancelled_at TEXT,
            reminder_sent INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (creator_user_id) REFERENCES users (id),
            FOREIGN KEY (assignee_user_id) REFERENCES users (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS task_deadline_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            old_deadline TEXT NOT NULL,
            new_deadline TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            decided_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)

    connection.execute("""
        INSERT OR IGNORE INTO cats (id, name)
        VALUES (1, 'Жозя')
    """)

    connection.commit()
    connection.close()


def create_user(telegram_id, name):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO users (
            telegram_id,
            name,
            created_at
        )
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(telegram_id)
        DO UPDATE SET name = excluded.name
        """,
        (telegram_id, name),
    )

    connection.commit()
    connection.close()


def create_chat(chat_id, chat_type, title):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO chats (
            telegram_chat_id,
            type,
            title,
            created_at
        )
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(telegram_chat_id)
        DO UPDATE SET
            type = excluded.type,
            title = excluded.title
        """,
        (
            chat_id,
            chat_type,
            title,
        ),
    )

    connection.commit()
    connection.close()


def save_keyboard_message_id(chat_id, message_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE chats
        SET keyboard_message_id = ?
        WHERE telegram_chat_id = ?
        """,
        (
            message_id,
            chat_id,
        ),
    )

    connection.commit()
    connection.close()


def get_all_chats():
    connection = get_connection()

    chats = connection.execute(
        """
        SELECT
            telegram_chat_id,
            keyboard_message_id
        FROM chats
        WHERE keyboard_message_id IS NOT NULL
        """
    ).fetchall()

    connection.close()

    return chats