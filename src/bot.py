import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand

from config import BOT_TOKEN, PROXY_URL
from database import init_database
from handlers.feeding import router as feeding_router
from handlers.tasks import router as tasks_router


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
    ]

    await bot.set_my_commands(commands)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env")

    init_database()

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

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())