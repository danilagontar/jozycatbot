from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


CREATOR_NAMES = {
    2008737156: "Артема",
    431869701: "Дани",
    540028179: "Мамы",
    982526654: "Жени",
}


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


def create_active_task_keyboard(task_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"task:complete:{task_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"task:cancel:{task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Перенести дедлайн",
                    callback_data=f"task:move:{task_id}",
                )
            ],
        ]
    )


def create_deadline_change_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏱ +30 минут",
                    callback_data="task:move_time:30m",
                ),
                InlineKeyboardButton(
                    text="⏱ +3 часа",
                    callback_data="task:move_time:3h",
                ),
            ]
        ]
    )


def create_deadline_change_confirmation_keyboard(
    change_id
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=(
                        f"task:deadline:approve:{change_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=(
                        f"task:deadline:reject:{change_id}"
                    ),
                ),
            ]
        ]
    )


def create_tasks_list_keyboard(tasks, get_status):
    buttons = []

    for task in tasks:
        text = task["text"]

        if len(text) > 30:
            text = f"{text[:30]}..."

        status = get_status(task)

        creator_name = CREATOR_NAMES.get(
            task["creator_telegram_id"],
            task["creator_name"],
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} #{task['id']} — "
                        f"От {creator_name} — {text}"
                    ),
                    callback_data=f"task:view:{task['id']}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def create_created_tasks_list_keyboard(tasks, get_status):
    buttons = []

    for task in tasks:
        text = task["text"]

        if len(text) > 30:
            text = f"{text[:30]}..."

        status = get_status(task)

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} #{task['id']} — "
                        f"Для {task['assignee_name']} — {text}"
                    ),
                    callback_data=f"created_task:view:{task['id']}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )