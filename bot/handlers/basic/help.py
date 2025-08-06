from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.services.ai import OpenAIService


async def help_handler(message: Message, i18n, **_):
    await message.answer(i18n.get("help", "ℹ️ <b>Доступные команды:</b>\n\n🚀 /start – начать работу с ботом\n❓ /help – показать эту справку\n⚙️ /settings – открыть настройки аккаунта\n👤 /about – информация о вашем профиле\n\n📌 Используйте меню ниже для навигации"), parse_mode="HTML")


async def test_ai_handler(message: Message, i18n, **_):
    """Тестирует подключение к OpenAI API"""
    ai_service = OpenAIService()
    
    # Отправляем сообщение о тестировании
    test_msg = await message.answer("🤖 Тестирую подключение к OpenAI API...")
    
    # Тестируем подключение
    if ai_service.api_key:
        connection_ok = await ai_service.test_connection()
        if connection_ok:
            await test_msg.edit_text(
                "✅ OpenAI API подключен и работает!\n\n"
                "🤖 Вы можете использовать AI генерацию контента при создании постов."
            )
        else:
            await test_msg.edit_text(
                "❌ Ошибка подключения к OpenAI API.\n\n"
                "🔧 Проверьте правильность API ключа."
            )
    else:
        await test_msg.edit_text(
            "⚠️ OpenAI API ключ не настроен.\n\n"
            "💡 Без API ключа будет использоваться демо-режим с шаблонами.\n\n"
            "🔧 Для настройки добавьте переменную окружения:\n"
            "<code>OPENAI_API_KEY=your-key-here</code>"
        )


def register_help_handler(router):
    router.message.register(help_handler, Command("help"))
    router.message.register(test_ai_handler, Command("test_ai"))

__all__ = ["register_help_handler"]
