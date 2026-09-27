from datetime import timedelta

from aiogram import F, Router
from aiogram.types import Message

from services.tasks import get_weekly_task_top


router = Router()


@router.message(F.text == "/top")
async def top_handler(message: Message):
    top, monday, next_monday = get_weekly_task_top()

    period_end = next_monday - timedelta(days=1)

    if not top:
        await message.answer(
            "🏆 Топ за неделю\n\n"
            "Пока нет выполненных задач.\n\n"
            f"📅 {monday.strftime('%d.%m')} — "
            f"{period_end.strftime('%d.%m')}"
        )
        return

    lines = [
        "🏆 Топ за неделю",
        "",
    ]

    for position, item in enumerate(top, start=1):
        lines.append(
            f"{position}. {item['name']} — "
            f"{item['completed_on_time']} "
            f"({item['total']})"
        )

    lines.extend(
        [
            "",
            f"📅 {monday.strftime('%d.%m')} — "
            f"{period_end.strftime('%d.%m')}",
            "",
            "ℹ️ В скобках — общее количество "
            "выполненных задач.",
            "Например: 6 (7) = 6 выполнены "
            "вовремя + 1 просроченная.",
        ]
    )

    await message.answer("\n".join(lines))