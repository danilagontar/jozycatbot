from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.task_creation import USERS
from services.tasks import (
    accept_task,
    cancel_task,
    complete_task,
    get_task,
)


router = Router()


def truncate_task_text(text, max_words=20):
    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]) + "..."


@router.callback_query(
    F.data.startswith("task:accept:")
)
async def task_accept_handler(
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

    if task["status"] != "pending_acceptance":
        await callback.answer(
            "Задача уже была принята.",
            show_alert=True,
        )
        return

    accepted = accept_task(task_id)

    if not accepted:
        await callback.answer(
            "❌ Не удалось принять задачу.",
            show_alert=True,
        )
        return

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer(
        "✅ Задача принята!"
    )

    task_text = truncate_task_text(
        task["text"]
    )

    executor_name = USERS.get(
        callback.from_user.id,
        callback.from_user.full_name,
    )

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"✅ {executor_name} "
            f"принял задачу #{task_id}.\n\n"
            f"📝 {task_text}"
        ),
    )


@router.callback_query(
    F.data.startswith("task:complete:")
)
async def task_complete_handler(
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

    if task["status"] != "accepted":
        await callback.answer(
            "❌ Задачу нельзя завершить.",
            show_alert=True,
        )
        return

    complete_task(task_id)

    await callback.answer(
        "✅ Задача выполнена!"
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    task_text = truncate_task_text(
        task["text"]
    )

    executor_name = USERS.get(
        callback.from_user.id,
        callback.from_user.full_name,
    )

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"🎉 Задача #{task_id} выполнена!\n\n"
            f"👤 Исполнитель: {executor_name}\n\n"
            f"📝 {task_text}"
        ),
    )


@router.callback_query(
    F.data.startswith("task:cancel:")
)
async def task_cancel_handler(
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

    if task["status"] not in (
        "pending_acceptance",
        "accepted",
    ):
        await callback.answer(
            "❌ Задачу уже нельзя отменить.",
            show_alert=True,
        )
        return

    cancel_task(task_id)

    await callback.answer(
        "❌ Задача отменена."
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    task_text = truncate_task_text(
        task["text"]
    )

    executor_name = USERS.get(
        callback.from_user.id,
        callback.from_user.full_name,
    )

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"❌ Задача #{task_id} отменена.\n\n"
            f"👤 Исполнитель: {executor_name}\n\n"
            f"📝 {task_text}"
        ),
    )