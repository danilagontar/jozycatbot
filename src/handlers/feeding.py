from datetime import datetime

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from keyboards.feeding import create_feeding_keyboard
from services.feeding import (
    feed_cat,
    get_status_button_text,
    get_today_feedings,
)

router = Router()


def format_time(value):
    return datetime.fromisoformat(value).strftime("%H:%M")


def get_status_text():
    feedings = get_today_feedings()

    morning = None
    evening = None

    for feeding in feedings:
        if feeding["period"] == "morning":
            morning = feeding

        elif feeding["period"] == "evening":
            evening = feeding

    lines = ["🐱 Жози", ""]

    if morning:
        lines.append(
            f"🌅 Утро — {format_time(morning['fed_at'])} "
            f"({morning['name']})"
        )
    else:
        lines.append("🌅 Утро — ❌")

    if evening:
        lines.append(
            f"🌙 Вечер — {format_time(evening['fed_at'])} "
            f"({evening['name']})"
        )
    else:
        lines.append("🌙 Вечер — ❌")

    return "\n".join(lines)


@router.callback_query(
    lambda callback: callback.data == "feeding:feed"
)
async def feed_callback(callback: CallbackQuery):
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
            "🐱 Кошку уже покормили в этот период."
        )
        return

    period_name = (
        "утром"
        if result["period"] == "morning"
        else "вечером"
    )

    time = format_time(result["fed_at"])

    await callback.answer(
        f"🐱 Покормлено {period_name} в {time}."
    )

    status_text = get_status_button_text()

    await callback.message.edit_reply_markup(
        reply_markup=create_feeding_keyboard(status_text)
    )


@router.callback_query(
    lambda callback: callback.data == "feeding:status"
)
async def status_callback(callback: CallbackQuery):
    await callback.answer()


async def send_feeding_message(message: Message):
    await message.answer(
        "🐱 Жози\n\n"
        "Отметьте кормление:",
        reply_markup=create_feeding_keyboard(
            get_status_button_text()
        ),
    )