from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards.tasks import (
    create_assignee_keyboard,
    create_deadline_keyboard,
    create_task_accept_keyboard,
)
from services.tasks import create_task


router = Router()


USERS = {
    2008737156: "Артем",
    431869701: "Даня",
    540028179: "Мама",
    982526654: "Женя",
}


class TaskCreation(StatesGroup):
    waiting_assignee = State()
    waiting_text = State()
    waiting_deadline = State()
    waiting_custom_deadline = State()


@router.message(F.text == "/task")
async def task_start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(TaskCreation.waiting_assignee)

    await message.answer(
        "📋 Создание новой задачи\n\n"
        "👤 Кому назначить задачу?",
        reply_markup=create_assignee_keyboard(),
    )


@router.callback_query(
    TaskCreation.waiting_assignee,
    F.data.startswith("task:user:"),
)
async def task_assignee_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    assignee_id = int(callback.data.split(":")[-1])
    assignee_name = USERS.get(assignee_id)

    if not assignee_name:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await state.update_data(
        assignee_id=assignee_id,
        assignee_name=assignee_name,
    )
    await state.set_state(TaskCreation.waiting_text)

    await callback.answer()

    await callback.message.edit_text(
        f"👤 Задача для: {assignee_name}\n\n"
        "📝 Напиши текст задачи или отправь фото "
        "с подписью."
    )


@router.message(TaskCreation.waiting_text)
async def task_text_handler(
    message: Message,
    state: FSMContext,
):
    text = message.text or message.caption
    photo_file_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id

    if not text and not photo_file_id:
        await message.answer(
            "❌ Не удалось получить задачу.\n\n"
            "Отправь текст или фото с подписью."
        )
        return

    await state.update_data(
        task_text=text or "",
        photo_file_id=photo_file_id,
    )
    await state.set_state(TaskCreation.waiting_deadline)

    await message.answer(
        "⏰ Выбери срок выполнения:",
        reply_markup=create_deadline_keyboard(),
    )


@router.callback_query(
    TaskCreation.waiting_deadline,
    F.data.startswith("task:deadline:"),
)
async def task_deadline_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    deadline_type = callback.data.split(":")[-1]

    if deadline_type == "custom":
        await state.set_state(
            TaskCreation.waiting_custom_deadline
        )

        await callback.answer()

        await callback.message.edit_text(
            "🗓 Введи срок выполнения в формате:\n\n"
            "ДД.ММ ЧЧ:ММ\n\n"
            "Например: 28.09 21:30"
        )
        return

    now = datetime.now()

    if deadline_type == "15m":
        deadline = now + timedelta(minutes=15)
    elif deadline_type == "1h":
        deadline = now + timedelta(hours=1)
    elif deadline_type == "today":
        deadline = now.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )
    elif deadline_type == "tomorrow":
        tomorrow = now + timedelta(days=1)
        deadline = tomorrow.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )
    else:
        await callback.answer(
            "❌ Неизвестный срок.",
            show_alert=True,
        )
        return

    await create_task_from_state(
        callback.message,
        callback.from_user,
        state,
        deadline,
    )

    await callback.answer()


@router.message(TaskCreation.waiting_custom_deadline)
async def task_custom_deadline_handler(
    message: Message,
    state: FSMContext,
):
    try:
        deadline = datetime.strptime(
            message.text.strip(),
            "%d.%m %H:%M",
        )

        now = datetime.now()

        deadline = deadline.replace(
            year=now.year,
            second=0,
            microsecond=0,
        )

        if deadline <= now:
            await message.answer(
                "❌ Этот срок уже прошёл.\n\n"
                "Введи будущую дату в формате "
                "ДД.ММ ЧЧ:ММ."
            )
            return

    except (ValueError, AttributeError):
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используй:\n"
            "ДД.ММ ЧЧ:ММ\n\n"
            "Например: 28.09 21:30"
        )
        return

    await create_task_from_state(
        message,
        message.from_user,
        state,
        deadline,
    )


async def create_task_from_state(
    message,
    user,
    state: FSMContext,
    deadline,
):
    data = await state.get_data()

    task_id = create_task(
        creator_telegram_id=user.id,
        creator_name=user.full_name,
        assignee_telegram_id=data["assignee_id"],
        text=data["task_text"],
        photo_file_id=data["photo_file_id"],
        deadline=deadline,
    )

    task_text = data["task_text"]
    assignee_id = data["assignee_id"]
    assignee_name = data["assignee_name"]
    photo_file_id = data["photo_file_id"]

    deadline_text = deadline.strftime("%d.%m.%Y %H:%M")

    await state.clear()

    task_message = (
        f"📋 Новая задача #{task_id}\n\n"
        f"👤 От: {user.full_name}\n\n"
        f"📝 {task_text}\n\n"
        f"⏰ Срок: {deadline_text}"
    )

    try:
        if photo_file_id:
            await message.bot.send_photo(
                chat_id=assignee_id,
                photo=photo_file_id,
                caption=task_message,
                reply_markup=create_task_accept_keyboard(task_id),
            )
        else:
            await message.bot.send_message(
                chat_id=assignee_id,
                text=task_message,
                reply_markup=create_task_accept_keyboard(task_id),
            )

        await message.answer(
            f"✅ Задача #{task_id} создана!\n\n"
            f"👤 Исполнитель: {assignee_name}\n"
            f"📝 {task_text}\n"
            f"⏰ Срок: {deadline_text}"
        )

    except Exception:
        await message.answer(
            f"⚠️ Задача #{task_id} создана, "
            "но отправить её исполнителю не удалось.\n\n"
            "Возможно, он ещё не запускал бота через /start."
        )