from datetime import datetime

from database import create_user, get_connection


def create_task(
    creator_telegram_id,
    creator_name,
    assignee_telegram_id,
    text,
    photo_file_id,
    deadline,
):
    create_user(
        telegram_id=creator_telegram_id,
        name=creator_name,
    )

    connection = get_connection()

    creator = connection.execute(
        """
        SELECT id
        FROM users
        WHERE telegram_id = ?
        """,
        (creator_telegram_id,),
    ).fetchone()

    assignee = connection.execute(
        """
        SELECT id
        FROM users
        WHERE telegram_id = ?
        """,
        (assignee_telegram_id,),
    ).fetchone()

    if not assignee:
        connection.execute(
            """
            INSERT INTO users (
                telegram_id,
                name,
                created_at
            )
            VALUES (?, ?, datetime('now'))
            """,
            (
                assignee_telegram_id,
                "Пользователь",
            ),
        )

        connection.commit()

        assignee = connection.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (assignee_telegram_id,),
        ).fetchone()

    cursor = connection.execute(
        """
        INSERT INTO tasks (
            creator_user_id,
            assignee_user_id,
            text,
            photo_file_id,
            created_at,
            deadline,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            creator["id"],
            assignee["id"],
            text,
            photo_file_id,
            datetime.now().isoformat(timespec="seconds"),
            deadline.isoformat(timespec="seconds"),
            "pending_acceptance",
        ),
    )

    connection.commit()

    task_id = cursor.lastrowid

    connection.close()

    return task_id


def get_task(task_id):
    connection = get_connection()

    task = connection.execute(
        """
        SELECT
            tasks.*,
            creator.telegram_id AS creator_telegram_id,
            creator.name AS creator_name,
            assignee.telegram_id AS assignee_telegram_id,
            assignee.name AS assignee_name
        FROM tasks
        JOIN users AS creator
            ON creator.id = tasks.creator_user_id
        JOIN users AS assignee
            ON assignee.id = tasks.assignee_user_id
        WHERE tasks.id = ?
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    return task


def get_user_tasks(telegram_id):
    connection = get_connection()

    tasks = connection.execute(
        """
        SELECT
            tasks.*,
            creator.telegram_id AS creator_telegram_id,
            creator.name AS creator_name
        FROM tasks
        JOIN users AS assignee
            ON assignee.id = tasks.assignee_user_id
        JOIN users AS creator
            ON creator.id = tasks.creator_user_id
        WHERE assignee.telegram_id = ?
          AND tasks.status IN (
              'pending_acceptance',
              'accepted'
          )
        ORDER BY tasks.deadline
        """,
        (telegram_id,),
    ).fetchall()

    connection.close()

    return tasks


def get_created_tasks(telegram_id):
    connection = get_connection()

    tasks = connection.execute(
        """
        SELECT
            tasks.*,
            assignee.telegram_id AS assignee_telegram_id,
            assignee.name AS assignee_name
        FROM tasks
        JOIN users AS creator
            ON creator.id = tasks.creator_user_id
        JOIN users AS assignee
            ON assignee.id = tasks.assignee_user_id
        WHERE creator.telegram_id = ?
        ORDER BY tasks.deadline
        """,
        (telegram_id,),
    ).fetchall()

    connection.close()

    return tasks


def get_reminder_tasks():
    connection = get_connection()

    tasks = connection.execute(
        """
        SELECT
            tasks.*,
            assignee.telegram_id AS assignee_telegram_id
        FROM tasks
        JOIN users AS assignee
            ON assignee.id = tasks.assignee_user_id
        WHERE tasks.status IN (
            'pending_acceptance',
            'accepted'
        )
        ORDER BY tasks.deadline
        """
    ).fetchall()

    connection.close()

    return tasks


def mark_reminder_20_sent(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET reminder_20_sent = 1
        WHERE id = ?
        """,
        (task_id,),
    )

    connection.commit()
    connection.close()


def mark_reminder_10_sent(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET reminder_10_sent = 1
        WHERE id = ?
        """,
        (task_id,),
    )

    connection.commit()
    connection.close()


def mark_overdue(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET
            overdue_at = ?,
            overdue_notified = 1
        WHERE id = ?
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            task_id,
        ),
    )

    connection.commit()
    connection.close()


def accept_task(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET
            status = 'accepted',
            accepted_at = ?
        WHERE id = ?
          AND status = 'pending_acceptance'
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            task_id,
        ),
    )

    connection.commit()
    connection.close()


def complete_task(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET
            status = 'completed',
            completed_at = ?
        WHERE id = ?
          AND status = 'accepted'
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            task_id,
        ),
    )

    connection.commit()
    connection.close()


def cancel_task(task_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET
            status = 'cancelled',
            cancelled_at = ?
        WHERE id = ?
          AND status IN (
              'pending_acceptance',
              'accepted'
          )
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            task_id,
        ),
    )

    connection.commit()
    connection.close()


def request_deadline_change(
    task_id,
    old_deadline,
    new_deadline,
):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO task_deadline_changes (
            task_id,
            old_deadline,
            new_deadline,
            requested_at,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            task_id,
            old_deadline,
            new_deadline,
            datetime.now().isoformat(timespec="seconds"),
            "pending",
        ),
    )

    connection.commit()

    change_id = cursor.lastrowid

    connection.close()

    return change_id


def get_deadline_change(change_id):
    connection = get_connection()

    change = connection.execute(
        """
        SELECT *
        FROM task_deadline_changes
        WHERE id = ?
        """,
        (change_id,),
    ).fetchone()

    connection.close()

    return change


def approve_deadline_change(change_id):
    connection = get_connection()

    change = connection.execute(
        """
        SELECT *
        FROM task_deadline_changes
        WHERE id = ?
          AND status = 'pending'
        """,
        (change_id,),
    ).fetchone()

    if not change:
        connection.close()
        return False

    connection.execute(
        """
        UPDATE tasks
        SET
            deadline = ?,
            overdue_at = NULL,
            reminder_20_sent = 0,
            reminder_10_sent = 0,
            overdue_notified = 0
        WHERE id = ?
        """,
        (
            change["new_deadline"],
            change["task_id"],
        ),
    )

    connection.execute(
        """
        UPDATE task_deadline_changes
        SET
            status = 'approved',
            decided_at = ?
        WHERE id = ?
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            change_id,
        ),
    )

    connection.commit()
    connection.close()

    return True


def reject_deadline_change(change_id):
    connection = get_connection()

    result = connection.execute(
        """
        UPDATE task_deadline_changes
        SET
            status = 'rejected',
            decided_at = ?
        WHERE id = ?
          AND status = 'pending'
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            change_id,
        ),
    )

    connection.commit()

    updated = result.rowcount > 0

    connection.close()

    return updated