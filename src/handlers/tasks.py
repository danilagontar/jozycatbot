from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards.tasks import (
    create_active_task_keyboard,
    create_assignee_keyboard,
    create_deadline_keyboard,
    create_task_accept_keyboard,
    create_tasks_list_keyboard,
)
from services.tasks import (
    accept_task,
    cancel_task,
    complete_task,
    create_task,
    get_task,
    get_user_tasks,
)


router = Router()


USERS = {
    2008737156: "Артем",
    431869701: "Даня",
    540028179: "Мама",
    982526654: "Женя",
}


CREATOR_NAMES = {
    2008737156: "Артема",
    431869701: "Дани",
    540028179: "Мамы",
    982526654: "Жени",
}


MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


class TaskCreation(StatesGroup):
    waiting_assignee = State()
    waiting_text = State()
    waiting_deadline = State()
    waiting_custom_deadline = State()


def format_deadline(deadline):
    month = MONTHS[deadline.month]

    return (
        f"{deadline.day} {month} "
        f"в {deadline.strftime('%H:%M')}"
    )


def get_deadline_status(deadline):
    now = datetime.now()
    remaining = deadline - now

    if remaining.total_seconds() <= 0:
        return "🔴"

    if remaining.total_seconds() <= 60 * 60:
        return "🔴"

    if remaining.total_seconds() <= 3 * 60 * 60:
        return "🟡"

    return "🟢"


def create_task_card(task):
    deadline = datetime.fromisoformat(task["deadline"])

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

    text = (
        f"📋 Задача #{task['id']}\n\n"
        f"👤 От: {creator_name}\n\n"
        f"📝 {task['text']}\n\n"
        f"{get_deadline_status(deadline)} "
        f"⏰ Срок: {format_deadline(deadline)}\n\n"
        f"📌 Статус: "
        f"{status_names.get(task['status'], task['status'])}"
    )

    return text


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

    deadline_text = format_deadline(deadline)

    creator_name = CREATOR_NAMES.get(
        user.id,
        user.full_name,
    )

    await state.clear()

    task_message = (
        f"📋 Новая задача #{task_id}\n\n"
        f"👤 От: {creator_name}\n\n"
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


@router.callback_query(
    F.data.startswith("task:accept:")
)
async def task_accept_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "❌ Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
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

    accept_task(task_id)

    await callback.message.edit_reply_markup(
        reply_markup=create_active_task_keyboard(task_id),
    )

    await callback.answer("✅ Задача принята!")

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"✅ {USERS.get(callback.from_user.id, callback.from_user.full_name)} "
            f"принял задачу #{task_id}."
        ),
    )


@router.message(F.text == "/mytasks")
async def my_tasks_handler(message: Message):
    tasks = get_user_tasks(message.from_user.id)

    if not tasks:
        await message.answer(
            "📋 У тебя сейчас нет активных задач."
        )
        return

    await message.answer(
        "📋 Твои активные задачи:\n\n"
        "🟢 — больше 3 часов\n"
        "🟡 — меньше 3 часов\n"
        "🔴 — меньше часа или срок прошёл",
        reply_markup=create_tasks_list_keyboard(tasks),
    )


@router.callback_query(
    F.data.startswith("task:view:")
)
async def task_view_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "❌ Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
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
                else create_task_accept_keyboard(task_id)
            ),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=(
                create_active_task_keyboard(task_id)
                if task["status"] == "accepted"
                else create_task_accept_keyboard(task_id)
            ),
        )


@router.callback_query(
    F.data.startswith("task:complete:")
)
async def task_complete_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "❌ Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
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

    await callback.answer("✅ Задача выполнена!")

    await callback.message.edit_reply_markup(
        reply_markup=None,
    )

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"🎉 Задача #{task_id} выполнена!\n\n"
            f"👤 Исполнитель: "
            f"{USERS.get(callback.from_user.id, callback.from_user.full_name)}"
        ),
    )


@router.callback_query(
    F.data.startswith("task:cancel:")
)
async def task_cancel_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[-1])
    task = get_task(task_id)

    if not task:
        await callback.answer(
            "❌ Задача не найдена.",
            show_alert=True,
        )
        return

    if task["assignee_telegram_id"] != callback.from_user.id:
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

    await callback.answer("❌ Задача отменена.")

    await callback.message.edit_reply_markup(
        reply_markup=None,
    )

    await callback.bot.send_message(
        chat_id=task["creator_telegram_id"],
        text=(
            f"❌ Задача #{task_id} отменена.\n\n"
            f"👤 Исполнитель: "
            f"{USERS.get(callback.from_user.id, callback.from_user.full_name)}"
        ),
    )