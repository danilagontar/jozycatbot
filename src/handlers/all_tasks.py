from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USER_ID
from services.tasks import get_all_tasks


router = Router()


@router.message(Command("all"))
async def all_tasks_handler(message: Message):
    if message.from_user.id != ADMIN_USER_ID:
        return

    tasks = get_all_tasks(15)

    if not tasks:
        await message.answer("Задач пока нет.")
        return

    status_names = {
        "pending_acceptance": "⏳ Ожидает принятия",
        "accepted": "🔵 В работе",
        "completed": "✅ Выполнена",
        "cancelled": "❌ Отменена",
    }

    lines = ["📋 Последние 15 задач:\n"]

    for task in tasks:
        status = status_names.get(
            task["status"],
            task["status"],
        )

        lines.append(
            f"#{task['id']} — {status}\n"
            f"👤 От: {task['creator_name']}\n"
            f"🎯 Для: {task['assignee_name']}\n"
            f"📝 {task['text']}\n"
        )
    print(
        "USER ID:",
        message.from_user.id,
        "ADMIN ID:",
        ADMIN_USER_ID,
    )
    await message.answer("\n".join(lines))