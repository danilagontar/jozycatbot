from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from handlers.task_creation import CREATOR_NAMES, MONTHS
from keyboards.tasks import (
    create_active_task_keyboard,
    create_task_accept_keyboard,
    create_tasks_list_keyboard,
)
from services.tasks import get_task, get_user_tasks


router = Router()


def format_deadline(deadline):
    month = MONTHS[deadline.month]

    return (
        f"{deadline.day} {month} "
        f"в {deadline.strftime('%H:%M')}"
    )


def get_deadline_status(task):
    if task["status"] == "pending_acceptance":
        return "⏳"

    if task["status"] in ("completed", "cancelled"):
        return "❌"

    if task["overdue_at"]:
        return "❌"

    if not task["accepted_at"]:
        return "⏳"

    accepted_at = datetime.fromisoformat(
        task["accepted_at"]
    )
    deadline = datetime.fromisoformat(
        task["deadline"]
    )
    now = datetime.now()

    total_time = (
        deadline - accepted_at
    ).total_seconds()

    remaining_time = (
        deadline - now
    ).total_seconds()

    if remaining_time <= 0:
        return "❌"

    if total_time <= 0:
        return "❌"

    remaining_percent = (
        remaining_time / total_time
    ) * 100

    if remaining_percent >= 60:
        return "🟢"

    if remaining_percent >= 20:
        return "🟡"

    return "🔴"


def create_task_card(task):
    status_names = {
        "pending_acceptance": "⏳ Ожидает принятия",
        "accepted": "🔵 Принята",
        "completed": "✅ Выполнена",
        "cancelled": "❌ Отменена",
    }

    creator_name = CREATOR_NAMES.get(
        task["creator_telegram_id"],
        task["creator_name"],
    )

    if (
        task["status"] == "pending_acceptance"
        and task["deadline_type"] == "relative"
    ):
        if task["deadline_minutes"] == 15:
            deadline_text = "через 15 минут"
        elif task["deadline_minutes"] == 60:
            deadline_text = "через 1 час"
        else:
            deadline_text = "после принятия"
    else:
        deadline = datetime.fromisoformat(
            task["deadline"]
        )

        deadline_text = format_deadline(deadline)

    text = (
        f"📋 Задача #{task['id']}\n\n"
        f"👤 От: {creator_name}\n\n"
        f"📝 {task['text']}\n\n"
        f"{get_deadline_status(task)} "
        f"⏰ Срок: {deadline_text}\n\n"
        f"📌 Статус: "
        f"{status_names.get(task['status'], task['status'])}"
    )

    if task["overdue_at"]:
        text += "\n\n⚠️ Срок истёк."

    return text


@router.message(F.text == "/mytasks")
async def my_tasks_handler(
    message: Message,
):
    tasks = get_user_tasks(
        message.from_user.id
    )

    tasks = sorted(
        tasks,
        key=lambda task: datetime.fromisoformat(
            task["deadline"]
        ),
    )

    if not tasks:
        await message.answer(
            "📋 У тебя сейчас нет активных задач."
        )
        return

    await message.answer(
        "📋 Твои активные задачи:",
        reply_markup=create_tasks_list_keyboard(
            tasks,
            get_deadline_status,
        ),
    )


@router.callback_query(
    F.data.startswith("task:view:")
)
async def task_view_handler(
    callback: CallbackQuery,
):
    task_id = int(
        callback.data.split(":")[-1]
    )

    task = get_task(task_id)

    if not task:
        await callback.answer(
            "❌ Задача не найдена.",
            show_alert=True,
        )
        return

    if (
        task["assignee_telegram_id"]
        != callback.from_user.id
    ):
        await callback.answer(
            "❌ Эта задача назначена не вам.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = create_task_card(task)

    if task["photo_file_id"]:
        await callback.message.answer_photo(
            photo=task["photo_file_id"],
            caption=text,
            reply_markup=(
                create_active_task_keyboard(task_id)
                if task["status"] == "accepted"
                else create_task_accept_keyboard(
                    task_id
                )
            ),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=(
                create_active_task_keyboard(task_id)
                if task["status"] == "accepted"
                else create_task_accept_keyboard(
                    task_id
                )
            ),
        )