import sqlite3
from datetime import datetime

from config import (
    EVENING_END,
    EVENING_START,
    MORNING_END,
    MORNING_START,
)
from database import get_connection


def get_current_period():
    current_time = datetime.now().time()

    if MORNING_START <= current_time < MORNING_END:
        return "morning"

    if EVENING_START <= current_time <= EVENING_END:
        return "evening"

    return None


def create_user(user_id, name):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO users (telegram_id, name, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET name = excluded.name
        """,
        (
            user_id,
            name,
            datetime.now().isoformat(timespec="seconds"),
        ),
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
        VALUES (?, ?, ?, ?)
        ON CONFLICT(telegram_chat_id)
        DO UPDATE SET
            type = excluded.type,
            title = excluded.title
        """,
        (
            chat_id,
            chat_type,
            title,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()


def feed_cat(user_id, user_name):
    period = get_current_period()

    if period is None:
        return {
            "success": False,
            "period": None,
        }

    create_user(user_id, user_name)

    connection = get_connection()

    user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    today = datetime.now().date().isoformat()
    fed_at = datetime.now().isoformat(timespec="seconds")

    try:
        connection.execute(
            """
            INSERT INTO feedings (
                cat_id,
                user_id,
                date,
                period,
                fed_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1,
                user["id"],
                today,
                period,
                fed_at,
            ),
        )

        connection.commit()

        return {
            "success": True,
            "already_fed": False,
            "period": period,
            "fed_at": fed_at,
        }

    except sqlite3.IntegrityError:
        connection.rollback()

        feeding = connection.execute(
            """
            SELECT fed_at
            FROM feedings
            WHERE cat_id = 1
              AND date = ?
              AND period = ?
            """,
            (today, period),
        ).fetchone()

        return {
            "success": True,
            "already_fed": True,
            "period": period,
            "fed_at": feeding["fed_at"] if feeding else None,
        }

    finally:
        connection.close()


def get_today_feedings():
    connection = get_connection()

    today = datetime.now().date().isoformat()

    feedings = connection.execute(
        """
        SELECT
            feedings.period,
            feedings.fed_at,
            users.name
        FROM feedings
        JOIN users ON users.id = feedings.user_id
        WHERE feedings.cat_id = 1
          AND feedings.date = ?
        ORDER BY feedings.fed_at
        """,
        (today,),
    ).fetchall()

    connection.close()

    return feedings


def get_status_button_text():
    feedings = get_today_feedings()

    morning = None
    evening = None

    for feeding in feedings:
        if feeding["period"] == "morning":
            morning = feeding

        if feeding["period"] == "evening":
            evening = feeding

    current_period = get_current_period()

    if current_period == "morning":
        if morning:
            time = datetime.fromisoformat(
                morning["fed_at"]
            ).strftime("%H:%M")

            return f"🌅 Утро — {time}"

        return "🌅 Утро — ❌"

    if current_period == "evening":
        if evening:
            time = datetime.fromisoformat(
                evening["fed_at"]
            ).strftime("%H:%M")

            return f"🌙 Вечер — {time}"

        if morning:
            time = datetime.fromisoformat(
                morning["fed_at"]
            ).strftime("%H:%M")

            return f"🌅 Утро — {time}"

        return "🌙 Вечер — ❌"

    if evening:
        time = datetime.fromisoformat(
            evening["fed_at"]
        ).strftime("%H:%M")

        return f"🌙 Вечер — {time}"

    if morning:
        time = datetime.fromisoformat(
            morning["fed_at"]
        ).strftime("%H:%M")

        return f"🌅 Утро — {time}"

    return "🐱 Покормить"


def delete_last_feeding():
    connection = get_connection()

    feeding = connection.execute(
        """
        SELECT id
        FROM feedings
        WHERE cat_id = 1
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if not feeding:
        connection.close()
        return False

    connection.execute(
        """
        DELETE FROM feedings
        WHERE id = ?
        """,
        (feeding["id"],),
    )

    connection.commit()
    connection.close()

    return True