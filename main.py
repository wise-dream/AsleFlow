import asyncio
from bot import config
from sqlalchemy import text
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from bot.handlers.workflows import register_workflow_handlers
from db.connection import AsyncSessionLocal, get_redis
from bot.middlewares.db import DatabaseSessionMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import I18nMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.redis import RedisMiddleware
from bot.handlers.basic import register_basic_handlers
from bot.handlers.socials import register_socials_handlers
from bot.handlers.posts import register_posts_handlers


def register_all_handlers(dp: Dispatcher):
    register_basic_handlers(dp)
    register_socials_handlers(dp)
    register_workflow_handlers(dp)
    register_posts_handlers(dp)


async def set_middlewares(dp: Dispatcher, redis):
    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware())
    dp.update.middleware(RedisMiddleware(redis))
    dp.update.middleware(AuthMiddleware(redis))
    dp.update.middleware(I18nMiddleware())


async def set_bot_commands(bot: Bot):
    """Устанавливает меню команд бота"""
    commands = [
        BotCommand(command="start", description="🚀 Начать работу с ботом"),
        BotCommand(command="help", description="❓ Справка по командам"),
        BotCommand(command="workflows", description="🧠 Управление задачами"),
        BotCommand(command="accounts", description="📱 Управление аккаунтами"),
        BotCommand(command="posts", description="📝 Управление постами"),
        BotCommand(command="about", description="👤 Информация о профиле"),
        BotCommand(command="settings", description="⚙️ Настройки бота"),
        BotCommand(command="test_ai", description="🤖 Тест OpenAI API"),
    ]
    await bot.set_my_commands(commands)


async def on_startup():
    from db.connection import test_db_connection
    # Проверяем подключение к базе данных
    db_ok = await test_db_connection()
    if not db_ok:
        print("❌ Ошибка подключения к базе данных!")
        print("Проверьте настройки в файле .env")
        return
    
    print("✅ Подключение к базе данных успешно")


async def on_shutdown():
    # Останавливаем фоновые задачи (шедулер), если запущены
    try:
        global _scheduler_task
        if _scheduler_task:
            _scheduler_task.cancel()
    except Exception:
        pass
    # Закрываем Redis
    redis = await get_redis()
    await redis.aclose()


async def main():
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    redis = await get_redis()
    await set_middlewares(dp, redis)
    register_all_handlers(dp)

    await on_startup()
    await set_bot_commands(bot)
    print("Bot started!")
    # Запускаем фоновый шедулер публикаций
    async def start_scheduler(bot: Bot):
        from bot.services.publishing.publisher import PublishingService
        svc = PublishingService(bot)
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    await svc.run_publishing_cycle(session)
            except Exception as e:
                print(f"Scheduler error: {e}")
            # Пауза между циклами
            await asyncio.sleep(60)

    global _scheduler_task
    _scheduler_task = asyncio.create_task(start_scheduler(bot))
    await dp.start_polling(bot, shutdown=on_shutdown)


if __name__ == "__main__":
    asyncio.run(main())
