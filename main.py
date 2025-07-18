import asyncio
from bot import config
from sqlalchemy import text
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from db.connection import AsyncSessionLocal, get_redis
from bot.middlewares.db import DatabaseSessionMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import I18nMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.redis import RedisMiddleware
from bot.handlers.basic import register_basic_handlers

def register_all_handlers(dp: Dispatcher):
    register_basic_handlers(dp)

async def set_middlewares(dp: Dispatcher):
    redis = await get_redis()
    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware())
    dp.update.middleware(I18nMiddleware())
    dp.update.middleware(AuthMiddleware())
    dp.update.middleware(RedisMiddleware(redis))

async def on_startup():
    async with AsyncSessionLocal() as session:
        await session.execute(text('SELECT 1'))

async def on_shutdown():
    redis = await get_redis()
    await redis.aclose()

async def main():
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    await set_middlewares(dp)
    register_all_handlers(dp)

    await on_startup()
    print("Bot started!")
    await dp.start_polling(bot, shutdown=on_shutdown)

if __name__ == "__main__":
    asyncio.run(main())
