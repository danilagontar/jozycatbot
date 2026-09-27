from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def create_feeding_keyboard(status_text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🐱 Покормить"),
                KeyboardButton(text=status_text),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )