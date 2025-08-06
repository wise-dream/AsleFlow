import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from bot.handlers.basic.start import start_handler, language_callback_handler
from bot.services.crud.user import get_user_by_telegram_id, get_or_create_user, update_user


@pytest.mark.asyncio
async def test_start_handler_new_user(mock_message, mock_session, mock_state):
    """Тест обработчика /start для нового пользователя"""
    # Arrange
    mock_message.from_user.id = 123456
    mock_message.from_user.full_name = "Test User"
    mock_message.from_user.username = "testuser"
    
    # Мокаем функции CRUD
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.handlers.basic.start.get_user_by_telegram_id", 
                  AsyncMock(return_value=None))
        m.setattr("bot.handlers.basic.start.get_or_create_user", 
                  AsyncMock(return_value=MagicMock(name="Test User")))
        
        # Act
        await start_handler(mock_message, mock_state, mock_session, MagicMock(), "en")
        
        # Assert
        mock_message.answer.assert_called_once()
        mock_state.update_data.assert_called_once()


@pytest.mark.asyncio
async def test_start_handler_existing_user(mock_message, mock_session):
    """Тест обработчика /start для существующего пользователя"""
    # Arrange
    mock_message.from_user.id = 123456
    mock_message.from_user.full_name = "Test User"
    
    existing_user = MagicMock()
    existing_user.language = "ru"
    existing_user.name = "Test User"
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.handlers.basic.start.get_user_by_telegram_id", 
                  AsyncMock(return_value=existing_user))
        
        # Act
        await start_handler(mock_message, AsyncMock(), mock_session, MagicMock(), "ru")
        
        # Assert
        mock_message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_language_callback_handler(mock_callback, mock_session, mock_state):
    """Тест обработчика смены языка"""
    # Arrange
    mock_callback.data = "set_lang:en"
    mock_callback.from_user.full_name = "Test User"
    mock_callback.message.bot.delete_message = AsyncMock()
    mock_callback.message.answer = AsyncMock()
    mock_callback.answer = AsyncMock()
    
    mock_user = MagicMock(id=1, name="Test User")
    
    mock_state.get_data.return_value = {"welcome_msg_id": 123}
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.handlers.basic.start.update_user", AsyncMock())
        
        # Act
        await language_callback_handler(mock_callback, mock_state, mock_session, MagicMock(), "en", mock_user)
        
        # Assert
        mock_callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_language_callback_handler_invalid_data(mock_callback, mock_session, mock_state):
    """Тест обработчика смены языка с некорректными данными"""
    # Arrange
    mock_callback.data = "invalid_data"
    
    # Act
    await language_callback_handler(mock_callback, mock_state, mock_session, MagicMock(), "en", MagicMock())
    
    # Assert
    mock_callback.answer.assert_not_called() 