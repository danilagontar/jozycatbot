from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.tasks import create_active_task_keyboard
from services.tasks import (
    accept_task,
    cancel_task,
    complete_task,
    get_task,
)


router = Router()


@router.callback_query(F.data.startswith("task:accept:"))
async def accept_task_handler(
    callback: CallbackQuery,
):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Эта задача назначена другому пользователю.",
            show_alert=True,
        )
        return

    if task["status"] != "pending_acceptance":
        await callback.answer(
            "Эту задачу уже нельзя принять.",
            show_alert=True,
        )
        return

    if not accept_task(task_id):
        await callback.answer(
            "Не удалось принять задачу.",
            show_alert=True,
        )
        return

    task = get_task(task_id)

    await callback.message.edit_reply_markup(
        reply_markup=create_active_task_keyboard(task_id)
    )

    await callback.answer("Задача принята.")

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"✅ {task['assignee_name']} "
            f"принял задачу #{task_id}."
        ),
    )


@router.callback_query(F.data.startswith("task:complete:"))
async def complete_task_handler(
    callback: CallbackQuery,
):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Эта задача назначена другому пользователю.",
            show_alert=True,
        )
        return

    if task["status"] != "accepted":
        await callback.answer(
            "Эту задачу нельзя выполнить.",
            show_alert=True,
        )
        return

    complete_task(task_id)

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer("Задача выполнена.")

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"✅ Задача #{task_id} выполнена!\n\n"
            f"📝 {task['text']}"
        ),
    )


@router.callback_query(F.data.startswith("task:cancel:"))
async def cancel_task_handler(
    callback: CallbackQuery,
):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Эта задача назначена другому пользователю.",
            show_alert=True,
        )
        return

    if task["status"] not in (
        "pending_acceptance",
        "accepted",
    ):
        await callback.answer(
            "Эту задачу уже нельзя отменить.",
            show_alert=True,
        )
        return

    cancel_task(task_id)

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer("Задача отменена.")

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"❌ Задача #{task_id} отменена.\n\n"
            f"📝 {task['text']}"
        ),
    )