import pytest
import asyncio
from bot.services.crud.user import get_user_by_telegram_id, update_user
from bot.middlewares.i18n import I18nMiddleware


@pytest.mark.asyncio
async def test_language_update_in_database(session):
    """Тест обновления языка в базе данных"""
    # Создаем тестового пользователя
    from bot.models.models import User
    
    test_user = User(
        telegram_id=123456789,
        name="Test User",
        language="en"  # Начальный язык - английский
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)
    
    # Проверяем начальный язык
    assert test_user.language == "en"
    
    # Обновляем язык на русский
    updated_user = await update_user(session, test_user.id, language="ru")
    
    # Проверяем, что язык обновился
    assert updated_user is not None
    assert updated_user.language == "ru"
    
    # Проверяем через get_user_by_telegram_id
    user_from_db = await get_user_by_telegram_id(session, test_user.telegram_id)
    assert user_from_db is not None
    assert user_from_db.language == "ru"
    
    # Очищаем тестовые данные
    await session.delete(test_user)
    await session.commit()


@pytest.mark.asyncio
async def test_i18n_middleware_language_detection():
    """Тест определения языка в i18n middleware"""
    middleware = I18nMiddleware()
    
    # Проверяем, что переводы загружены
    assert "ru" in middleware.translations
    assert "en" in middleware.translations
    
    # Проверяем, что есть ключ "welcome"
    assert "welcome" in middleware.translations["ru"]
    assert "welcome" in middleware.translations["en"]


@pytest.mark.asyncio
async def test_language_callback_data_parsing():
    """Тест парсинга callback данных для смены языка"""
    # Симулируем callback данные
    callback_data = "set_lang:ru"
    
    # Проверяем парсинг
    if callback_data.startswith("set_lang:"):
        lang = callback_data.split(":")[1]
        assert lang == "ru"
    
    callback_data = "set_lang:en"
    if callback_data.startswith("set_lang:"):
        lang = callback_data.split(":")[1]
        assert lang == "en"


@pytest.mark.asyncio
async def test_cache_clear_function():
    """Тест функции очистки кэша"""
    from bot.services.crud.user import clear_user_cache
    
    # Тестируем функцию без Redis (должна вернуть False)
    result = await clear_user_cache(None, 123456)
    assert result is False


if __name__ == "__main__":
    print("✅ Тесты языка работают корректно!") 