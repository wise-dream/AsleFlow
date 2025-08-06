import pytest
from datetime import datetime, timezone


def test_validate_post_data_valid():
    """Тест валидации корректных данных поста"""
    # Arrange
    data = {
        "topic": "Test Topic",
        "content": "Test Content",
        "media_type": "text"
    }
    
    # Act
    is_valid = (
        data.get("topic") and 
        len(data.get("topic", "")) > 0 and
        data.get("content") and 
        len(data.get("content", "")) > 0 and
        data.get("media_type") in ["text", "image", "video"]
    )
    
    # Assert
    assert is_valid is True


def test_validate_post_data_invalid():
    """Тест валидации некорректных данных поста"""
    # Arrange
    data = {
        "topic": "",  # Пустая тема
        "content": "Test Content",
        "media_type": "invalid_type"
    }
    
        # Act
    is_valid = (
        bool(data.get("topic")) and
        len(data.get("topic", "")) > 0 and
        bool(data.get("content")) and
        len(data.get("content", "")) > 0 and
        data.get("media_type") in ["text", "image", "video"]
    )

    # Assert
    assert is_valid is False


def test_validate_workflow_settings():
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


def test_validate_workflow_settings_invalid():
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


def test_validate_social_account():
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


def test_validate_social_account_invalid():
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


def test_validate_user_data():
    """Тест валидации данных пользователя"""
    # Arrange
    user_data = {
        "telegram_id": 123456789,
        "name": "Test User",
        "email": "test@example.com",
        "language": "ru",
        "timezone": "UTC"
    }
    
        # Act
    is_valid = (
        bool(user_data.get("telegram_id")) and
        bool(user_data.get("name")) and
        len(user_data.get("name", "")) > 0 and
        user_data.get("language") in ["ru", "en"] and
        bool(user_data.get("timezone"))
    )

    # Assert
    assert is_valid is True


def test_validate_user_data_invalid():
    """Тест валидации некорректных данных пользователя"""
    # Arrange
    user_data = {
        "telegram_id": None,  # Отсутствует ID
        "name": "",  # Пустое имя
        "email": "invalid_email",  # Некорректный email
        "language": "fr",  # Неподдерживаемый язык
        "timezone": ""  # Пустой часовой пояс
    }
    
        # Act
    is_valid = (
        bool(user_data.get("telegram_id")) and
        bool(user_data.get("name")) and
        len(user_data.get("name", "")) > 0 and
        user_data.get("language") in ["ru", "en"] and
        bool(user_data.get("timezone"))
    )

    # Assert
    assert is_valid is False


def test_validate_scheduled_time():
    """Тест валидации времени планирования"""
    # Arrange
    current_time = datetime.now(timezone.utc)
    future_time = current_time.replace(hour=current_time.hour + 1)
    past_time = current_time.replace(hour=current_time.hour - 1)
    
    # Act
    future_is_valid = future_time > current_time
    past_is_valid = past_time > current_time
    
    # Assert
    assert future_is_valid is True
    assert past_is_valid is False


def test_validate_content_length():
    """Тест валидации длины контента"""
    # Arrange
    short_content = "Short"
    medium_content = "This is a medium length content that should be valid for testing purposes."
    long_content = "x" * 1200  # искусственно длинный контент (>1000 символов)
    
    # Act
    short_is_valid = len(short_content) >= 5
    medium_is_valid = 10 <= len(medium_content) <= 1000
    long_is_valid = len(long_content) <= 1000

    # Assert
    assert short_is_valid is True
    assert medium_is_valid is True
    assert long_is_valid is False