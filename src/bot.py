import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN, PROXY_URL
from database import init_database
from handlers.feeding import router, send_feeding_message


async def start_handler(message: Message):
    await send_feeding_message(message)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env")

    init_database()

    session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
    )

    dp = Dispatcher()

    dp.include_router(router)

    dp.message.register(start_handler, CommandStart())

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())