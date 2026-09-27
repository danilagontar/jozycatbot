from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_assignee_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Артем",
                    callback_data="task:user:2008737156",
                ),
                InlineKeyboardButton(
                    text="👤 Даня",
                    callback_data="task:user:431869701",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👩 Мама",
                    callback_data="task:user:540028179",
                ),
                InlineKeyboardButton(
                    text="👤 Женя",
                    callback_data="task:user:982526654",
                ),
            ],
        ]
    )


def create_deadline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏱ 15 минут",
                    callback_data="task:deadline:15m",
                ),
                InlineKeyboardButton(
                    text="⏱ 1 час",
                    callback_data="task:deadline:1h",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🌙 Сегодня",
                    callback_data="task:deadline:today",
                ),
                InlineKeyboardButton(
                    text="📅 Завтра",
                    callback_data="task:deadline:tomorrow",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗓 Свой срок",
                    callback_data="task:deadline:custom",
                ),
            ],
        ]
    )


def create_task_accept_keyboard(task_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Принять задачу",
                    callback_data=f"task:accept:{task_id}",
                )
            ]
        ]
    )