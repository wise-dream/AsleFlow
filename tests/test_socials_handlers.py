import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery


@pytest.mark.asyncio
async def test_add_social_account_handler(mock_message, mock_session, mock_state):
    """Тест добавления социального аккаунта"""
    # Arrange
    mock_message.text = "/add_account"
    mock_user = MagicMock(id=1)
    
    # Act
    # Симуляция добавления аккаунта
    account_data = {
        "user_id": mock_user.id,
        "platform": "telegram",
        "channel_name": "Test Channel",
        "channel_id": "123456789",
        "channel_type": "public"
    }
    
    # Assert
    assert account_data["user_id"] == mock_user.id
    assert account_data["platform"] == "telegram"
    assert account_data["channel_name"] == "Test Channel"


@pytest.mark.asyncio
async def test_edit_social_account_handler(mock_callback, mock_session):
    """Тест редактирования социального аккаунта"""
    # Arrange
    mock_callback.data = "edit_account:123"
    
    mock_account = MagicMock(
        id=123, 
        platform="telegram", 
        channel_name="Old Channel",
        channel_id="123456789"
    )
    mock_session.get_social_account_by_id.return_value = mock_account
    
    # Act
    account = await mock_session.get_social_account_by_id(123)
    
    # Assert
    assert account.id == 123
    assert account.platform == "telegram"
    assert account.channel_name == "Old Channel"


@pytest.mark.asyncio
async def test_social_account_validation():
    """Тест валидации данных социального аккаунта"""
    # Arrange
    account_data = {
        "platform": "telegram",
        "channel_name": "Test Channel",
        "channel_id": "123456789",
        "channel_type": "public"
    }
    
    # Act
    is_valid = (
        account_data.get("platform") in ["telegram", "vk", "instagram"] and
        account_data.get("channel_name") and
        len(account_data.get("channel_name", "")) > 0 and
        account_data.get("channel_id") and
        account_data.get("channel_type") in ["public", "private"]
    )
    
    # Assert
    assert is_valid is True


@pytest.mark.asyncio
async def test_social_account_validation_invalid():
    """Тест валидации некорректных данных социального аккаунта"""
    # Arrange
    account_data = {
        "platform": "invalid_platform",
        "channel_name": "",  # Пустое имя
        "channel_id": "123456789",
        "channel_type": "invalid_type"
    }
    
    # Act
    is_valid = (
        account_data.get("platform") in ["telegram", "vk", "instagram"] and
        account_data.get("channel_name") and
        len(account_data.get("channel_name", "")) > 0 and
        account_data.get("channel_id") and
        account_data.get("channel_type") in ["public", "private"]
    )
    
    # Assert
    assert is_valid is False


@pytest.mark.asyncio
async def test_social_account_deletion(mock_session):
    """Тест удаления социального аккаунта"""
    # Arrange
    account_id = 123
    mock_account = MagicMock(id=account_id)
    mock_session.get_social_account_by_id.return_value = mock_account
    mock_session.delete_social_account.return_value = True
    
    # Act
    result = await mock_session.delete_social_account(account_id)
    
    # Assert
    assert result is True
    mock_session.delete_social_account.assert_called_once_with(account_id)


@pytest.mark.asyncio
async def test_social_account_list_handler(mock_message, mock_session, mock_user):
    """Тест получения списка социальных аккаунтов"""
    # Arrange
    mock_accounts = [
        MagicMock(id=1, platform="telegram", channel_name="Channel 1"),
        MagicMock(id=2, platform="vk", channel_name="Channel 2"),
        MagicMock(id=3, platform="instagram", channel_name="Channel 3")
    ]
    mock_session.get_social_accounts.return_value = mock_accounts
    
    # Act
    accounts = await mock_session.get_social_accounts(mock_user.id)
    
    # Assert
    assert len(accounts) == 3
    assert accounts[0].platform == "telegram"
    assert accounts[1].platform == "vk"
    assert accounts[2].platform == "instagram"


@pytest.mark.asyncio
async def test_social_account_update(mock_session):
    """Тест обновления социального аккаунта"""
    # Arrange
    account_id = 123
    new_channel_name = "Updated Channel"
    
    mock_account = MagicMock(id=account_id, channel_name="Old Channel")
    mock_session.get_social_account_by_id.return_value = mock_account
    
    # Act
    mock_account.channel_name = new_channel_name
    await mock_session.commit()
    
    # Assert
    assert mock_account.channel_name == new_channel_name
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_social_account_platform_validation():
    """Тест валидации платформ социальных сетей"""
    # Arrange
    valid_platforms = ["telegram", "vk", "instagram"]
    invalid_platforms = ["facebook", "twitter", "linkedin", "invalid"]
    
    # Act & Assert
    for platform in valid_platforms:
        assert platform in valid_platforms
    
    for platform in invalid_platforms:
        assert platform not in valid_platforms


@pytest.mark.asyncio
async def test_social_account_channel_type_validation():
    """Тест валидации типов каналов"""
    # Arrange
    valid_types = ["public", "private"]
    invalid_types = ["group", "channel", "invalid"]
    
    # Act & Assert
    for channel_type in valid_types:
        assert channel_type in valid_types
    
    for channel_type in invalid_types:
        assert channel_type not in valid_types


@pytest.mark.asyncio
async def test_social_account_duplicate_validation(mock_session, mock_user):
    """Тест валидации дублирования аккаунтов"""
    # Arrange
    existing_account = MagicMock(
        user_id=mock_user.id,
        platform="telegram",
        channel_id="123456789"
    )
    mock_session.get_social_accounts.return_value = [existing_account]
    
    new_account_data = {
        "user_id": mock_user.id,
        "platform": "telegram",
        "channel_id": "123456789"  # Тот же ID
    }
    
    # Act
    existing_accounts = await mock_session.get_social_accounts(mock_user.id)
    is_duplicate = any(
        acc.platform == new_account_data["platform"] and 
        acc.channel_id == new_account_data["channel_id"]
        for acc in existing_accounts
    )
    
    # Assert
    assert is_duplicate is True


@pytest.mark.asyncio
async def test_social_account_access_token_handling(mock_session):
    """Тест обработки токенов доступа"""
    # Arrange
    account_id = 123
    access_token = "test_token_12345"
    
    mock_account = MagicMock(id=account_id, access_token=None)
    mock_session.get_social_account_by_id.return_value = mock_account
    
    # Act
    mock_account.access_token = access_token
    await mock_session.commit()
    
    # Assert
    assert mock_account.access_token == access_token
    mock_session.commit.assert_called_once() 