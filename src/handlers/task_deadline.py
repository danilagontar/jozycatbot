from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards.tasks import (
    create_deadline_change_confirmation_keyboard,
    create_deadline_change_keyboard,
)
from services.tasks import (
    approve_deadline_change,
    get_deadline_change,
    get_task,
    reject_deadline_change,
    request_deadline_change,
)


router = Router()


class TaskDeadlineChange(StatesGroup):
    waiting_new_deadline = State()


def format_deadline(deadline):
    return deadline.strftime("%d.%m %H:%M")


async def send_deadline_change_request(
    bot,
    task,
    new_deadline,
):
    change_id = request_deadline_change(
        task_id=task["id"],
        old_deadline=task["deadline"],
        new_deadline=new_deadline.isoformat(
            timespec="seconds"
        ),
    )

    await bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"🗓 Запрос на перенос дедлайна "
            f"задачи #{task['id']}.\n\n"
            f"📝 {task['text']}\n\n"
            f"⏰ Новый срок: "
            f"{format_deadline(new_deadline)}"
        ),
        reply_markup=(
            create_deadline_change_confirmation_keyboard(
                change_id
            )
        ),
    )


@router.callback_query(F.data.startswith("task:move:"))
async def move_deadline_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    value = callback.data.split(":")[-1]

    if value in ("30m", "3h"):
        return

    task_id = int(value)
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
            "Перенести дедлайн можно только принятой задачи.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(
        TaskDeadlineChange.waiting_new_deadline
    )
    await state.update_data(task_id=task_id)

    await callback.message.answer(
        "🗓 Введи новый срок:\n\n"
        "Или выбери быстрый вариант:",
        reply_markup=create_deadline_change_keyboard(),
    )

    await callback.message.answer(
        "Или введи дату и время сообщением:\n"
        "ДД.ММ ЧЧ:ММ\n\n"
        "Например:\n"
        "27.09 23:30"
    )

    await callback.answer()


@router.callback_query(F.data == "task:move_time:30m")
async def move_deadline_30_minutes_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    task_id = data.get("task_id")

    if not task_id:
        await callback.answer(
            "Сначала выбери перенос дедлайна.",
            show_alert=True,
        )
        return

    task = get_task(task_id)

    if not task:
        await state.clear()
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
        await state.clear()
        await callback.answer(
            "Эта задача назначена другому пользователю.",
            show_alert=True,
        )
        return

    new_deadline = datetime.now() + timedelta(
        minutes=30
    )

    await send_deadline_change_request(
        callback.bot,
        task,
        new_deadline,
    )

    await state.clear()

    await callback.answer(
        "Запрос на перенос отправлен."
    )


@router.callback_query(F.data == "task:move_time:3h")
async def move_deadline_3_hours_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    task_id = data.get("task_id")

    if not task_id:
        await callback.answer(
            "Сначала выбери перенос дедлайна.",
            show_alert=True,
        )
        return

    task = get_task(task_id)

    if not task:
        await state.clear()
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
        await state.clear()
        await callback.answer(
            "Эта задача назначена другому пользователю.",
            show_alert=True,
        )
        return

    new_deadline = datetime.now() + timedelta(
        hours=3
    )

    await send_deadline_change_request(
        callback.bot,
        task,
        new_deadline,
    )

    await state.clear()

    await callback.answer(
        "Запрос на перенос отправлен."
    )


@router.message(TaskDeadlineChange.waiting_new_deadline)
async def custom_deadline_handler(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    task_id = data.get("task_id")

    if not task_id:
        await state.clear()
        return

    try:
        new_deadline = datetime.strptime(
            message.text.strip(),
            "%d.%m %H:%M",
        )

        new_deadline = new_deadline.replace(
            year=datetime.now().year
        )
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Введи дату и время так:\n"
            "ДД.ММ ЧЧ:ММ\n\n"
            "Например:\n"
            "27.09 23:30"
        )
        return

    if new_deadline <= datetime.now():
        await message.answer(
            "❌ Новый срок должен быть в будущем."
        )
        return

    task = get_task(task_id)

    if not task:
        await state.clear()
        await message.answer(
            "❌ Задача не найдена."
        )
        return

    if task["assignee_telegram_id"] != message.from_user.id:
        await state.clear()
        await message.answer(
            "❌ Эта задача назначена другому пользователю."
        )
        return

    if task["status"] != "accepted":
        await state.clear()
        await message.answer(
            "❌ Эту задачу уже нельзя перенести."
        )
        return

    await send_deadline_change_request(
        message.bot,
        task,
        new_deadline,
    )

    await state.clear()

    await message.answer(
        "✅ Запрос на перенос дедлайна "
        "отправлен создателю задачи."
    )


@router.callback_query(
    F.data.startswith("task:deadline:approve:")
)
async def approve_deadline_handler(
    callback: CallbackQuery,
):
    change_id = int(callback.data.split(":")[-1])
    change = get_deadline_change(change_id)

    if not change:
        await callback.answer(
            "Запрос не найден.",
            show_alert=True,
        )
        return

    task = get_task(change["task_id"])

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["creator_telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Только создатель задачи может "
            "подтвердить перенос.",
            show_alert=True,
        )
        return

    if change["status"] != "pending":
        await callback.answer(
            "Этот запрос уже обработан.",
            show_alert=True,
        )
        return

    if not approve_deadline_change(change_id):
        await callback.answer(
            "Не удалось изменить дедлайн.",
            show_alert=True,
        )
        return

    new_deadline = datetime.fromisoformat(
        change["new_deadline"]
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer("Дедлайн изменён.")

    await callback.bot.send_message(
        chat_id=task["assignee_telegram_id"],
        text=(
            f"✅ Перенос дедлайна задачи #{task['id']} "
            f"подтверждён.\n\n"
            f"⏰ Новый срок: "
            f"{format_deadline(new_deadline)}"
        ),
    )


@router.callback_query(
    F.data.startswith("task:deadline:reject:")
)
async def reject_deadline_handler(
    callback: CallbackQuery,
):
    change_id = int(callback.data.split(":")[-1])
    change = get_deadline_change(change_id)

    if not change:
        await callback.answer(
            "Запрос не найден.",
            show_alert=True,
        )
        return

    task = get_task(change["task_id"])

    if not task:
        await callback.answer(
            "Задача не найдена.",
            show_alert=True,
        )
        return

    if task["creator_telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Только создатель задачи может "
            "отклонить перенос.",
            show_alert=True,
        )
        return

    if change["status"] != "pending":
        await callback.answer(
            "Этот запрос уже обработан.",
            show_alert=True,
        )
        return

    if not reject_deadline_change(change_id):
        await callback.answer(
            "Не удалось обработать запрос.",
            show_alert=True,
        )
        return

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer("Перенос отклонён.")

    await callback.bot.send_message(
        chat_id=task["assignee_telegram_id"],
        text=(
            f"❌ Перенос дедлайна задачи #{task['id']} "
            f"отклонён."
        ),
    )