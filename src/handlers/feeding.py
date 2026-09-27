from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database import (
    create_chat,
    get_all_chats,
    save_keyboard_message_id,
)
from keyboards.feeding import create_feeding_keyboard
from services.feeding import (
    delete_last_feeding,
    feed_cat,
    get_feeding_status,
)

router = Router()


def format_time(value):
    return datetime.fromisoformat(value).strftime("%H:%M")


def create_feeding_text():
    status = get_feeding_status()

    if status["morning"]:
        morning_time = format_time(status["morning"]["fed_at"])
        morning_text = f"🌅 Утро — ✅ {morning_time}"
    else:
        morning_text = "🌅 Утро — ❌"

    if status["evening"]:
        evening_time = format_time(status["evening"]["fed_at"])
        evening_text = f"🌙 Вечер — ✅ {evening_time}"
    else:
        evening_text = "🌙 Вечер — ❌"

    return (
        "🐱 Жозя\n\n"
        f"{morning_text}\n"
        f"{evening_text}"
    )


async def update_chat_message(bot, chat_id, message_id):
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=create_feeding_text(),
            reply_markup=create_feeding_keyboard(),
        )
    except Exception:
        pass


async def update_all_messages(bot):
    chats = get_all_chats()

    for chat in chats:
        await update_chat_message(
            bot=bot,
            chat_id=chat["telegram_chat_id"],
            message_id=chat["keyboard_message_id"],
        )


async def send_feeding_message(message: Message):
    create_chat(
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        title=message.chat.title,
    )

    sent_message = await message.answer(
        create_feeding_text(),
        reply_markup=create_feeding_keyboard(),
    )

    save_keyboard_message_id(
        chat_id=message.chat.id,
        message_id=sent_message.message_id,
    )


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🐱 Привет!\n\n"
        "Это бот для отметки кормления Жози.\n"
        "Используй /feed, чтобы посмотреть состояние "
        "кормления и отметить кормление.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("feed"))
async def feed_handler(message: Message):
    await send_feeding_message(message)


@router.message(Command("delete"))
async def delete_handler(message: Message):
    feeding = delete_last_feeding()

    if not feeding:
        await message.answer(
            "Записей о кормлении нет."
        )
        return

    time = format_time(feeding["fed_at"])

    await message.answer(
        f"Удалена запись: {time} — "
        f"{feeding['name']}."
    )

    await update_all_messages(message.bot)


@router.callback_query(
    lambda callback: callback.data == "feeding:feed"
)
async def feed_button_handler(callback: CallbackQuery):
    user = callback.from_user

    result = feed_cat(
        user_id=user.id,
        user_name=user.full_name,
    )

    if not result["success"]:
        await callback.answer()
        return

    if result["already_fed"]:
        await callback.answer(
            "Кормление уже отмечено."
        )
        return

    await callback.answer()

    await update_all_messages(callback.bot)

    period_name = (
        "утром"
        if result["period"] == "morning"
        else "вечером"
    )

    time = format_time(result["fed_at"])

    await callback.message.answer(
        f"🐱 Жозю покормили {period_name} в {time}."
    )


@router.callback_query(
    lambda callback: callback.data == "feeding:status"
)
async def status_button_handler(callback: CallbackQuery):
    await callback.answer()