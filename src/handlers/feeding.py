from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_all_chats
from keyboards.feeding import create_feeding_keyboard
from services.feeding import (
    create_chat,
    delete_last_feeding,
    feed_cat,
    get_status_button_text,
)

router = Router()


def format_time(value):
    return datetime.fromisoformat(value).strftime("%H:%M")


async def update_all_keyboards(bot):
    keyboard = create_feeding_keyboard(
        get_status_button_text()
    )

    chats = get_all_chats()

    for chat in chats:
        try:
            message = await bot.send_message(
                chat_id=chat["telegram_chat_id"],
                text=" ",
                reply_markup=keyboard,
            )

            await message.delete()

        except Exception:
            continue


@router.message(Command("delete"))
async def delete_handler(message: Message):
    await message.delete()

    deleted = delete_last_feeding()

    if not deleted:
        return

    await update_all_keyboards(message.bot)


@router.message(lambda message: message.text == "🐱 Покормить")
async def feed_handler(message: Message):
    await message.delete()

    create_chat(
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        title=message.chat.title,
    )

    user = message.from_user

    result = feed_cat(
        user_id=user.id,
        user_name=user.full_name,
    )

    if not result["success"]:
        return

    if result["already_fed"]:
        return

    period_name = (
        "утром"
        if result["period"] == "morning"
        else "вечером"
    )

    time = format_time(result["fed_at"])

    await message.answer(
        f"🐱 Покормлено {period_name} в {time}.",
        reply_markup=create_feeding_keyboard(
            get_status_button_text()
        ),
    )

    await update_all_keyboards(message.bot)


@router.message(
    lambda message: message.text
    and message.text.startswith(("🌅 Утро", "🌙 Вечер"))
)
async def status_handler(message: Message):
    await message.delete()


async def send_feeding_message(message: Message):
    create_chat(
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        title=message.chat.title,
    )

    await message.answer(
        "🐱 Жози\n\n"
        "Отметьте кормление:",
        reply_markup=create_feeding_keyboard(
            get_status_button_text()
        ),
    )