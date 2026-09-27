from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_feeding_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐱 Покормить",
                    callback_data="feeding:feed",
                )
            ]
        ]
    )