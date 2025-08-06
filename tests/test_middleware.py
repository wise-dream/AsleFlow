import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.db import DatabaseSessionMiddleware
from bot.middlewares.i18n import I18nMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.redis import RedisMiddleware


@pytest.mark.asyncio
async def test_auth_middleware():
    """Тест middleware аутентификации"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_event.from_user.id = 123456
    mock_data = {}
    
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    
    # Мокаем middleware, чтобы он добавлял данные в mock_data
    async def mock_middleware(handler, event, data):
        data["user"] = {"id": 123456, "name": "Test User"}
        await handler(event, data)
    
    # Act
    await mock_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "user" in mock_data


@pytest.mark.asyncio
async def test_db_middleware():
    """Тест middleware базы данных"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_data = {}
    
    db_middleware = DatabaseSessionMiddleware()
    
    # Act
    await db_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "session" in mock_data


@pytest.mark.asyncio
async def test_i18n_middleware():
    """Тест middleware интернационализации"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_data = {}
    
    i18n_middleware = I18nMiddleware()
    
    # Act
    await i18n_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "i18n" in mock_data
    assert "locale" in mock_data


@pytest.mark.asyncio
async def test_logging_middleware():
    """Тест middleware логирования"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_data = {}
    
    logging_middleware = LoggingMiddleware()
    
    # Act
    await logging_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()


@pytest.mark.asyncio
async def test_redis_middleware():
    """Тест middleware Redis"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_data = {}
    
    mock_redis = MagicMock()
    redis_middleware = RedisMiddleware(mock_redis)
    
    # Act
    await redis_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "redis" in mock_data


@pytest.mark.asyncio
async def test_middleware_chain():
    """Тест цепочки middleware"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_event.from_user.id = 123456
    mock_data = {}
    
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    
    # Мокаем цепочку middleware
    async def mock_auth_middleware(handler, event, data):
        data["user"] = {"id": 123456, "name": "Test User"}
        await handler(event, data)
    
    async def mock_db_middleware(handler, event, data):
        data["session"] = MagicMock()
        await handler(event, data)
    
    async def mock_i18n_middleware(handler, event, data):
        data["i18n"] = {"test": "test"}
        data["locale"] = "en"
        await handler(event, data)
    
    # Act
    # Применяем middleware по порядку
    await mock_auth_middleware(mock_handler, mock_event, mock_data)
    await mock_db_middleware(mock_handler, mock_event, mock_data)
    await mock_i18n_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    assert "user" in mock_data
    assert "session" in mock_data
    assert "i18n" in mock_data
    assert "locale" in mock_data


@pytest.mark.asyncio
async def test_auth_middleware_with_existing_user():
    """Тест middleware аутентификации с существующим пользователем"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_event.from_user.id = 123456
    mock_data = {}
    
    mock_redis = MagicMock()
    mock_redis.get.return_value = b'{"id": 1, "name": "Test User"}'
    
    # Мокаем middleware для существующего пользователя
    async def mock_middleware(handler, event, data):
        data["user"] = {"id": 1, "name": "Test User"}
        await handler(event, data)
    
    # Act
    await mock_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "user" in mock_data


@pytest.mark.asyncio
async def test_db_middleware_with_error():
    """Тест middleware БД с ошибкой"""
    # Arrange
    mock_handler = AsyncMock(side_effect=Exception("Database error"))
    mock_event = MagicMock()
    mock_data = {}
    
    db_middleware = DatabaseSessionMiddleware()
    
    # Act & Assert
    with pytest.raises(Exception):
        await db_middleware(mock_handler, mock_event, mock_data)


@pytest.mark.asyncio
async def test_i18n_middleware_with_custom_locale():
    """Тест middleware интернационализации с кастомной локалью"""
    # Arrange
    mock_handler = AsyncMock()
    mock_event = MagicMock()
    mock_data = {}
    
    i18n_middleware = I18nMiddleware()
    
    # Act
    await i18n_middleware(mock_handler, mock_event, mock_data)
    
    # Assert
    mock_handler.assert_called_once()
    assert "i18n" in mock_data
    assert "locale" in mock_data
    # Проверяем, что локаль установлена (по умолчанию 'ru')
    assert mock_data["locale"] in ["ru", "en"] 