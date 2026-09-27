from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_feeding_keyboard(status_text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐱 Покормить",
                    callback_data="feeding:feed"
                ),
                InlineKeyboardButton(
                    text=status_text,
                    callback_data="feeding:status"
                )
            ]
        ]
    )