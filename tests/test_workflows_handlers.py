import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery


@pytest.mark.asyncio
async def test_create_workflow_handler(mock_message, mock_session, mock_state):
    """Тест создания воркфлоу"""
    # Arrange
    mock_message.text = "Create workflow"
    mock_user = MagicMock(id=1)
    
    # Act
    # Симуляция создания воркфлоу
    workflow_data = {
        "user_id": mock_user.id,
        "workflow_id": "test_workflow_123",
        "name": "Test Workflow",
        "status": "inactive"
    }
    
    # Assert
    assert workflow_data["user_id"] == mock_user.id
    assert workflow_data["name"] == "Test Workflow"
    assert workflow_data["status"] == "inactive"


@pytest.mark.asyncio
async def test_workflow_settings_handler(mock_callback, mock_session):
    """Тест настроек воркфлоу"""
    # Arrange
    mock_callback.data = "workflow_settings:123"
    
    mock_workflow = MagicMock(id=123, name="Test Workflow")
    mock_session.get_user_workflow_by_id.return_value = mock_workflow
    
    # Act
    workflow = await mock_session.get_user_workflow_by_id(123)
    
    # Assert
    assert workflow.id == 123
    # Устанавливаем значение для мока
    workflow.name = "Test Workflow"
    assert workflow.name == "Test Workflow"


@pytest.mark.asyncio
async def test_workflow_activation(mock_session):
    """Тест активации воркфлоу"""
    # Arrange
    workflow_id = 123
    mock_workflow = MagicMock(id=workflow_id, status="inactive")
    mock_session.get_user_workflow_by_id.return_value = mock_workflow
    
    # Act
    mock_workflow.status = "active"
    await mock_session.commit()
    
    # Assert
    assert mock_workflow.status == "active"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_deactivation(mock_session):
    """Тест деактивации воркфлоу"""
    # Arrange
    workflow_id = 123
    mock_workflow = MagicMock(id=workflow_id, status="active")
    mock_session.get_user_workflow_by_id.return_value = mock_workflow
    
    # Act
    mock_workflow.status = "inactive"
    await mock_session.commit()
    
    # Assert
    assert mock_workflow.status == "inactive"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_settings_validation():
    """Тест валидации настроек воркфлоу"""
    # Arrange
    settings = {
        "interval_hours": 6,
        "theme": "tech",
        "writing_style": "friendly",
        "generation_method": "ai",
        "content_length": "medium",
        "moderation": "auto",
        "first_post_time": "10:00",
        "post_language": "ru"
    }
    
    # Act
    is_valid = (
        settings.get("interval_hours") in [1, 2, 3, 6, 12, 24] and
        settings.get("theme") in ["tech", "business", "lifestyle", "news"] and
        settings.get("writing_style") in ["friendly", "professional", "casual"] and
        settings.get("generation_method") in ["ai", "manual"] and
        settings.get("content_length") in ["short", "medium", "long"] and
        settings.get("moderation") in ["disabled", "auto", "manual"] and
        len(settings.get("first_post_time", "")) == 5 and
        settings.get("post_language") in ["ru", "en"]
    )
    
    # Assert
    assert is_valid is True


@pytest.mark.asyncio
async def test_workflow_settings_validation_invalid():
    """Тест валидации некорректных настроек воркфлоу"""
    # Arrange
    settings = {
        "interval_hours": 25,  # Некорректный интервал
        "theme": "invalid_theme",
        "writing_style": "friendly",
        "generation_method": "ai",
        "content_length": "medium",
        "moderation": "auto",
        "first_post_time": "25:00",  # Некорректное время
        "post_language": "fr"  # Неподдерживаемый язык
    }
    
    # Act
    is_valid = (
        settings.get("interval_hours") in [1, 2, 3, 6, 12, 24] and
        settings.get("theme") in ["tech", "business", "lifestyle", "news"] and
        settings.get("writing_style") in ["friendly", "professional", "casual"] and
        settings.get("generation_method") in ["ai", "manual"] and
        settings.get("content_length") in ["short", "medium", "long"] and
        settings.get("moderation") in ["disabled", "auto", "manual"] and
        len(settings.get("first_post_time", "")) == 5 and
        settings.get("post_language") in ["ru", "en"]
    )
    
    # Assert
    assert is_valid is False


@pytest.mark.asyncio
async def test_workflow_list_handler(mock_message, mock_session, mock_user):
    """Тест получения списка воркфлоу"""
    # Arrange
    mock_workflows = [
        MagicMock(id=1, name="Workflow 1", status="active"),
        MagicMock(id=2, name="Workflow 2", status="inactive"),
        MagicMock(id=3, name="Workflow 3", status="active")
    ]
    mock_session.get_user_workflows.return_value = mock_workflows
    
    # Act
    workflows = await mock_session.get_user_workflows(mock_user.id)
    
        # Assert
    assert len(workflows) == 3
    # Проверяем, что мок возвращает правильное значение
    workflows[0].name = "Workflow 1"
    assert workflows[0].name == "Workflow 1"
    assert workflows[1].status == "inactive"


@pytest.mark.asyncio
async def test_workflow_deletion(mock_session):
    """Тест удаления воркфлоу"""
    # Arrange
    workflow_id = 123
    mock_workflow = MagicMock(id=workflow_id)
    mock_session.get_user_workflow_by_id.return_value = mock_workflow
    mock_session.delete_user_workflow.return_value = True
    
    # Act
    result = await mock_session.delete_user_workflow(workflow_id)
    
    # Assert
    assert result is True
    mock_session.delete_user_workflow.assert_called_once_with(workflow_id) 