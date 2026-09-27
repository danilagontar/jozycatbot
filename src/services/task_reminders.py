from datetime import datetime

from services.tasks import (
    get_reminder_tasks,
    mark_overdue,
    mark_reminder_10_sent,
    mark_reminder_20_sent,
)


def format_remaining_time(seconds):
    if seconds <= 0:
        return "0 минут"

    total_minutes = int(seconds // 60)

    if total_minutes < 1:
        return "меньше минуты"

    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60

    parts = []

    if days:
        parts.append(
            f"{days} "
            f"{'день' if days == 1 else 'дня' if days < 5 else 'дней'}"
        )

    if hours:
        parts.append(
            f"{hours} "
            f"{'час' if hours == 1 else 'часа' if hours < 5 else 'часов'}"
        )

    if minutes:
        parts.append(
            f"{minutes} "
            f"{'минута' if minutes == 1 else 'минуты' if minutes < 5 else 'минут'}"
        )

    return " ".join(parts)


def truncate_task_text(text, max_words=20):
    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]) + "..."


def get_reminder_message(task, reminder_type, remaining_seconds):
    task_text = truncate_task_text(task["text"])

    if reminder_type == "20":
        return (
            f"⏰ До дедлайна задачи #{task['id']} "
            f"осталось {format_remaining_time(remaining_seconds)}!\n\n"
            f"📝 {task_text}"
        )

    if reminder_type == "10":
        return (
            f"🔴 До дедлайна задачи #{task['id']} "
            f"осталось {format_remaining_time(remaining_seconds)}!\n\n"
            f"📝 {task_text}"
        )

    return (
        f"⚠️ Задача #{task['id']} просрочена!\n\n"
        f"📝 {task_text}\n"
        f"⏰ Срок уже истёк."
    )


async def check_task_reminders(bot):
    tasks = get_reminder_tasks()
    now = datetime.now()

    for task in tasks:
        created_at = datetime.fromisoformat(
            task["created_at"]
        )
        deadline = datetime.fromisoformat(
            task["deadline"]
        )

        total_seconds = (
            deadline - created_at
        ).total_seconds()

        remaining_seconds = (
            deadline - now
        ).total_seconds()

        if total_seconds <= 0:
            continue

        elapsed_ratio = (
            total_seconds - remaining_seconds
        ) / total_seconds

        if (
            elapsed_ratio >= 0.8
            and not task["reminder_20_sent"]
            and remaining_seconds > 0
        ):
            try:
                await bot.send_message(
                    chat_id=task["assignee_telegram_id"],
                    text=get_reminder_message(
                        task,
                        "20",
                        remaining_seconds,
                    ),
                )

                mark_reminder_20_sent(task["id"])

            except Exception:
                pass

        if (
            elapsed_ratio >= 0.9
            and not task["reminder_10_sent"]
            and remaining_seconds > 0
        ):
            try:
                await bot.send_message(
                    chat_id=task["assignee_telegram_id"],
                    text=get_reminder_message(
                        task,
                        "10",
                        remaining_seconds,
                    ),
                )

                mark_reminder_10_sent(task["id"])

            except Exception:
                pass

        if (
            remaining_seconds <= 0
            and not task["overdue_notified"]
        ):
            try:
                await bot.send_message(
                    chat_id=task["assignee_telegram_id"],
                    text=get_reminder_message(
                        task,
                        "overdue",
                        remaining_seconds,
                    ),
                )

                mark_overdue(task["id"])

            except Exception:
                pass