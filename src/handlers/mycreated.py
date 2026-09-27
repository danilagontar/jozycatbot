from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.tasks import create_created_tasks_list_keyboard
from services.tasks import get_created_tasks

router = Router()


def get_created_task_status(task):
    status_names = {
        "pending_acceptance": "⏳",
        "accepted": "🔵",
        "completed": "✅",
        "cancelled": "❌",
    }

    return status_names.get(
        task["status"],
        "❓",
    )


@router.message(F.text == "/mycreated")
async def my_created_tasks_handler(message: Message):
    tasks = get_created_tasks(message.from_user.id)

    tasks = sorted(
        tasks,
        key=lambda task: datetime.fromisoformat(
            task["created_at"]
        ),
        reverse=True,
    )[:10]

    if not tasks:
        await message.answer(
            "📋 Ты пока не создавал задач."
        )
        return

    await message.answer(
        "📋 Последние созданные тобой задачи:",
        reply_markup=create_created_tasks_list_keyboard(
            tasks,
            get_created_task_status,
        ),
    )


@router.callback_query(F.data.startswith("created_task:view:"))
async def created_task_view_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[-1])

    tasks = get_created_tasks(callback.from_user.id)

    task = next(
        (
            task
            for task in tasks
            if task["id"] == task_id
        ),
        None,
    )

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    status_names = {
        "pending_acceptance": "⏳ Ожидает принятия",
        "accepted": "🔵 Принята",
        "completed": "✅ Выполнена",
        "cancelled": "❌ Отменена",
    }

    deadline = datetime.fromisoformat(task["deadline"])
    created_at = datetime.fromisoformat(task["created_at"])

    text = (
        f"📋 Задача #{task['id']}\n\n"
        f"👤 Для: {task['assignee_name']}\n\n"
        f"📝 {task['text']}\n\n"
        f"⏰ Срок: {deadline.strftime('%d.%m в %H:%M')}\n\n"
        f"📌 Статус: "
        f"{status_names.get(task['status'], task['status'])}\n\n"
        f"📅 Создана: "
        f"{created_at.strftime('%d.%m в %H:%M')}"
    )

    await callback.answer()

    if task["photo_file_id"]:
        await callback.message.answer_photo(
            photo=task["photo_file_id"],
            caption=text,
        )
    else:
        await callback.message.answer(text)