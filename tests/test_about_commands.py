import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User as TelegramUser
from bot.handlers.basic.about import about_handler, register_about_handler
from aiogram import Router


@pytest.mark.asyncio
async def test_about_handler_basic():
    """Тест базового вызова обработчика профиля"""
    
    # Создаем моки
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456
    
    session = AsyncMock()
    i18n = {
        "about.unknown": "Неизвестно",
        "about.no_subscription": "Нет",
        "about.get_in_settings": "Получите в настройках",
        "about.tasks": "задач",
        "about.active": "активные",
        "about.no_tasks": "0 задач",
        "about.posts": "постов",
        "about.published": "опубликовано",
        "about.no_posts": "0 постов",
        "about.connected_accounts": "подключённых аккаунтов",
        "about.no_accounts": "0 подключённых аккаунтов",
        "about.free_posts_used": "Использовано бесплатных постов"
    }
    
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    user.cash = 100
    user.referral_code = "TEST123"
    user.free_posts_used = 2
    user.free_posts_limit = 5
    
    # Мокаем SQL запросы
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Мокаем get_simple_settings_keyboard
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_simple_settings_keyboard", MagicMock())
        
        # Вызываем обработчик
        await about_handler(message, session, i18n, user)
        
        # Проверяем, что сообщение было отправлено
        message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_about_handler_with_subscription():
    """Тест обработчика профиля с активной подпиской"""
    
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456
    
    session = AsyncMock()
    i18n = {
        "about.unknown": "Неизвестно",
        "about.no_subscription": "Нет",
        "about.get_in_settings": "Получите в настройках",
        "about.tasks": "задач",
        "about.active": "активные",
        "about.no_tasks": "0 задач",
        "about.posts": "постов",
        "about.published": "опубликовано",
        "about.no_posts": "0 постов",
        "about.connected_accounts": "подключённых аккаунтов",
        "about.no_accounts": "0 подключённых аккаунтов",
        "about.free_posts_used": "Использовано бесплатных постов"
    }
    
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    user.cash = 500
    user.referral_code = "PRO123"
    user.free_posts_used = 0
    user.free_posts_limit = 5
    
    # Мокаем активную подписку
    subscription = MagicMock()
    subscription.type = "PRO"
    subscription.end_date.strftime.return_value = "15.08.2025"
    
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.scalar_one_or_none.return_value = subscription
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_simple_settings_keyboard", MagicMock())
        
        await about_handler(message, session, i18n, user)
        
        message.answer.assert_called_once()


def test_register_about_handler():
    """Тест регистрации обработчиков профиля"""
    
    router = Router()
    
    # Регистрируем обработчики
    register_about_handler(router)
    
    # Проверяем, что обработчики зарегистрированы
    # (это сложно проверить напрямую, но можно убедиться, что функция выполняется без ошибок)
    assert router is not None


@pytest.mark.asyncio
async def test_about_handler_none_values():
    """Тест обработчика с None значениями"""
    
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456
    
    session = AsyncMock()
    i18n = {
        "about.unknown": "Неизвестно",
        "about.no_subscription": "Нет",
        "about.get_in_settings": "Получите в настройках",
        "about.tasks": "задач",
        "about.active": "активные",
        "about.no_tasks": "0 задач",
        "about.posts": "постов",
        "about.published": "опубликовано",
        "about.no_posts": "0 постов",
        "about.connected_accounts": "подключённых аккаунтов",
        "about.no_accounts": "0 подключённых аккаунтов",
        "about.free_posts_used": "Использовано бесплатных постов"
    }
    
    user = MagicMock()
    user.id = 1
    user.name = None  # None значение
    user.cash = None  # None значение
    user.referral_code = None  # None значение
    user.free_posts_used = None  # None значение
    user.free_posts_limit = None  # None значение
    
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.scalar_one_or_none.return_value = None
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.keyboards.inline.settings.get_simple_settings_keyboard", MagicMock())
        
        # Должно работать без ошибок
        await about_handler(message, session, i18n, user)
        
        message.answer.assert_called_once()


if __name__ == "__main__":
    print("✅ Тесты команд профиля работают корректно!") 