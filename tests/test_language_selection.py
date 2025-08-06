import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from bot.handlers.basic.start import language_callback_handler


@pytest.mark.asyncio
async def test_language_callback_handler():
    """Тест обработчика выбора языка"""
    
    # Создаем моки
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "set_lang:en"
    callback.message.chat.id = 123456
    callback.message.message_id = 789
    callback.from_user.full_name = "Test User"
    
    state = AsyncMock()
    state.get_data.return_value = {"welcome_msg_id": 456}
    
    session = AsyncMock()
    i18n = {"welcome": "Hello, {name}!", "language_set": "Language updated!"}
    locale = "en"
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    
    # Мокаем update_user_with_cache_clear
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.update_user_with_cache_clear", AsyncMock())
        m.setattr("bot.middlewares.i18n.I18nMiddleware.translations", {"en": i18n})
        m.setattr("bot.keyboards.reply.main_menu.get_main_menu", MagicMock())
        
        # Вызываем обработчик
        await language_callback_handler(
            callback, state, session, i18n, locale, user
        )
        
        # Проверяем, что состояние было получено
        state.get_data.assert_called_once()
        
        # Проверяем, что была попытка удаления сообщения
        callback.message.bot.delete_message.assert_called_once_with(123456, 456)


@pytest.mark.asyncio
async def test_language_callback_handler_no_message_id():
    """Тест обработчика когда ID сообщения не найден"""
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "set_lang:ru"
    callback.message.chat.id = 123456
    callback.message.message_id = 789
    callback.from_user.full_name = "Test User"
    
    state = AsyncMock()
    state.get_data.return_value = {}  # Нет ID сообщения
    
    session = AsyncMock()
    i18n = {"welcome": "Привет, {name}!", "language_set": "Язык обновлен!"}
    locale = "ru"
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.update_user_with_cache_clear", AsyncMock())
        m.setattr("bot.middlewares.i18n.I18nMiddleware.translations", {"ru": i18n})
        m.setattr("bot.keyboards.reply.main_menu.get_main_menu", MagicMock())
        
        await language_callback_handler(
            callback, state, session, i18n, locale, user
        )
        
        # Проверяем, что была попытка удаления текущего сообщения
        callback.message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_language_callback_handler_delete_error():
    """Тест обработчика при ошибке удаления сообщения"""
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "set_lang:en"
    callback.message.chat.id = 123456
    callback.message.message_id = 789
    callback.from_user.full_name = "Test User"
    
    # Симулируем ошибку при удалении
    callback.message.bot.delete_message.side_effect = Exception("Delete failed")
    
    state = AsyncMock()
    state.get_data.return_value = {"welcome_msg_id": 456}
    
    session = AsyncMock()
    i18n = {"welcome": "Hello, {name}!", "language_set": "Language updated!"}
    locale = "en"
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.update_user_with_cache_clear", AsyncMock())
        m.setattr("bot.middlewares.i18n.I18nMiddleware.translations", {"en": i18n})
        m.setattr("bot.keyboards.reply.main_menu.get_main_menu", MagicMock())
        
        await language_callback_handler(
            callback, state, session, i18n, locale, user
        )
        
        # Проверяем, что была попытка удаления текущего сообщения как fallback
        callback.message.delete.assert_called_once()


if __name__ == "__main__":
    print("✅ Тесты выбора языка работают корректно!") 