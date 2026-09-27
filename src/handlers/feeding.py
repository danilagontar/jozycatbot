from datetime import datetime

from aiogram import Router
from aiogram.types import Message

from keyboards.feeding import create_feeding_keyboard
from services.feeding import (
    feed_cat,
    get_status_button_text,
)

router = Router()


def format_time(value):
    return datetime.fromisoformat(value).strftime("%H:%M")


@router.message(lambda message: message.text == "🐱 Покормить")
async def feed_handler(message: Message):
    await message.delete()

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


@router.message(
    lambda message: message.text
    and message.text.startswith(("🌅 Утро", "🌙 Вечер"))
)
async def status_handler(message: Message):
    await message.delete()


async def send_feeding_message(message: Message):
    await message.answer(
        "🐱 Жози\n\n"
        "Отметьте кормление:",
        reply_markup=create_feeding_keyboard(
            get_status_button_text()
        ),
    )