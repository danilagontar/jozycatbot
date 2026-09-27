from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message

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
            task["deadline"]
        ),
    )

    if not tasks:
        await message.answer(
            "📋 Ты пока не создавал задач."
        )
        return

    await message.answer(
        "📋 Созданные тобой задачи:",
        reply_markup=create_created_tasks_list_keyboard(
            tasks,
            get_created_task_status,
        ),
    )