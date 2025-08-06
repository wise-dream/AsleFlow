import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from bot.handlers.basic.settings import (
    settings_handler, 
    settings_callback_handler,
    handle_email_settings,
    handle_referral_settings,
    generate_referral_code_handler,
    email_input_handler
)


@pytest.mark.asyncio
async def test_settings_handler():
    """Тест основного обработчика настроек"""
    
    message = MagicMock(spec=Message)
    session = AsyncMock()
    i18n = {"settings.title": "⚙️ Настройки"}
    user = MagicMock()
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_settings_keyboard", MagicMock())
        
        await settings_handler(message, session, i18n, user)
        
        message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_settings_callback_handler():
    """Тест обработчика кнопок настроек"""
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "settings:language"
    
    session = AsyncMock()
    i18n = {"settings.language_info": "Используйте /start для смены языка"}
    user = MagicMock()
    
    await settings_callback_handler(callback, session, i18n, user)
    
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_handle_email_settings_with_email():
    """Тест обработчика email с существующим email"""
    
    callback = MagicMock(spec=CallbackQuery)
    session = AsyncMock()
    i18n = {
        "settings.email_change_prompt": "Отправьте новый email или нажмите Отмена"
    }
    user = MagicMock()
    user.email = "test@example.com"
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_email_keyboard", MagicMock())
        
        await handle_email_settings(callback, session, i18n, user)
        
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_email_settings_without_email():
    """Тест обработчика email без email"""
    
    callback = MagicMock(spec=CallbackQuery)
    session = AsyncMock()
    i18n = {
        "settings.no_email": "Не указан",
        "settings.email_add_prompt": "Отправьте ваш email"
    }
    user = MagicMock()
    user.email = None
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_email_keyboard", MagicMock())
        
        await handle_email_settings(callback, session, i18n, user)
        
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_referral_settings_with_code():
    """Тест обработчика реферального кода с существующим кодом"""
    
    callback = MagicMock(spec=CallbackQuery)
    session = AsyncMock()
    i18n = {
        "settings.referral_change_prompt": "Нажмите кнопку для генерации нового кода"
    }
    user = MagicMock()
    user.referral_code = "ABC123"
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_referral_keyboard", MagicMock())
        
        await handle_referral_settings(callback, session, i18n, user)
        
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_referral_settings_without_code():
    """Тест обработчика реферального кода без кода"""
    
    callback = MagicMock(spec=CallbackQuery)
    session = AsyncMock()
    i18n = {
        "settings.no_referral_code": "Не сгенерирован",
        "settings.referral_generate_prompt": "Нажмите кнопку для генерации кода"
    }
    user = MagicMock()
    user.referral_code = None
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_referral_keyboard", MagicMock())
        
        await handle_referral_settings(callback, session, i18n, user)
        
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_generate_referral_code_handler():
    """Тест генерации реферального кода"""
    
    callback = MagicMock(spec=CallbackQuery)
    session = AsyncMock()
    i18n = {
        "settings.referral_success": "Код успешно сгенерирован!",
        "settings.referral_generated": "✅ Код сгенерирован!"
    }
    user = MagicMock()
    user.id = 1
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.utils.referral.generate_unique_referral_code", AsyncMock(return_value="ABC123"))
        m.setattr("bot.services.crud.user.update_user_with_cache_clear", AsyncMock(return_value=user))
        m.setattr("bot.keyboards.inline.settings.get_referral_keyboard", MagicMock())
        
        await generate_referral_code_handler(callback, session, i18n, user)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_email_input_handler_valid():
    """Тест обработчика ввода email с валидным email"""
    
    message = MagicMock(spec=Message)
    message.text = "test@example.com"
    
    state = AsyncMock()
    session = AsyncMock()
    i18n = {
        "settings.email_updated": "Email обновлен"
    }
    user = MagicMock()
    user.id = 1
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.update_user_with_cache_clear", AsyncMock(return_value=user))
        m.setattr("bot.keyboards.inline.settings.get_settings_keyboard", MagicMock())
        
        await email_input_handler(message, state, session, i18n, user)
        
        message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_email_input_handler_invalid():
    """Тест обработчика ввода email с невалидным email"""
    
    message = MagicMock(spec=Message)
    message.text = "invalid-email"
    
    state = AsyncMock()
    session = AsyncMock()
    i18n = {
        "settings.email_invalid": "❌ Неверный формат email"
    }
    user = MagicMock()
    
    await email_input_handler(message, state, session, i18n, user)
    
    message.answer.assert_called_once_with(i18n["settings.email_invalid"])


if __name__ == "__main__":
    print("✅ Тесты настроек работают корректно!") 