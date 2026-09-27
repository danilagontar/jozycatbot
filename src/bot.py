import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand

from config import BOT_TOKEN, PROXY_URL
from database import init_database
from handlers.feeding import router as feeding_router
from handlers.tasks import router as tasks_router
from services.task_reminders import check_task_reminders
from database import init_database, sync_user_names

async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Приветствие",
        ),
        BotCommand(
            command="feed",
            description="Кормление Жози",
        ),
        BotCommand(
            command="delete",
            description="Удалить последнее кормление",
        ),
        BotCommand(
            command="task",
            description="Создать задачу",
        ),
        BotCommand(
            command="mytasks",
            description="Мои активные задачи",
        ),
        BotCommand(
            command="mycreated",
            description="Мои созданные задачи",
        ),
        BotCommand(
            command="top",
            description="Топ за неделю",
        ),
    ]

    await bot.set_my_commands(commands)


async def reminder_loop(bot: Bot):
    while True:
        try:
            await check_task_reminders(bot)
        except Exception:
            pass

        await asyncio.sleep(60)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env")

    init_database()
    sync_user_names()
    session = (
        AiohttpSession(proxy=PROXY_URL)
        if PROXY_URL
        else None
    )

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
    )

    dp = Dispatcher()

    dp.include_router(feeding_router)
    dp.include_router(tasks_router)

    await set_commands(bot)

    reminder_task = asyncio.create_task(
        reminder_loop(bot)
    )

    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()

        try:
            await reminder_task
        except asyncio.CancelledError:
            pass

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())