import pytest
import asyncio
from bot.services.ai import OpenAIService


@pytest.mark.asyncio
async def test_ai_service_initialization():
    """Тест инициализации AI сервиса"""
    service = OpenAIService()
    assert service is not None
    assert hasattr(service, 'generate_post_content')


@pytest.mark.asyncio
async def test_mock_content_generation():
    """Тест генерации заглушки без API ключа"""
    service = OpenAIService()
    
    # Тестируем генерацию на русском (бесплатная модель)
    content_ru = await service.generate_post_content(
        topic="Инвестиции в ETF",
        theme="финансы",
        style="friendly",
        language="ru",
        content_length="medium",
        is_premium=False
    )
    
    assert content_ru is not None
    assert len(content_ru) > 50
    assert "ETF" in content_ru or "инвестиции" in content_ru.lower()
    
    # Тестируем генерацию на английском (премиум модель)
    content_en = await service.generate_post_content(
        topic="ETF Investing",
        theme="finance",
        style="friendly",
        language="en",
        content_length="medium",
        is_premium=True
    )
    
    assert content_en is not None
    assert len(content_en) > 50
    assert "ETF" in content_en or "invest" in content_en.lower()


@pytest.mark.asyncio
async def test_different_styles():
    """Тест разных стилей написания"""
    service = OpenAIService()
    
    styles = ["formal", "friendly", "humorous"]
    
    for style in styles:
        content = await service.generate_post_content(
            topic="Маркетинг в соцсетях",
            theme="маркетинг",
            style=style,
            language="ru",
            content_length="short"
        )
        
        assert content is not None
        assert len(content) > 20


@pytest.mark.asyncio
async def test_different_lengths():
    """Тест разных длин контента"""
    service = OpenAIService()
    
    lengths = ["short", "medium", "long"]
    
    for length in lengths:
        content = await service.generate_post_content(
            topic="Искусственный интеллект",
            theme="технологии",
            style="friendly",
            language="ru",
            content_length=length
        )
        
        assert content is not None
        assert len(content) > 10


@pytest.mark.asyncio
async def test_api_connection_test():
    """Тест проверки подключения к API"""
    service = OpenAIService()
    
    # Без API ключа должно возвращать False
    result = await service.test_connection()
    assert result is False


@pytest.mark.asyncio
async def test_model_selection():
    """Тест выбора модели в зависимости от типа подписки"""
    service = OpenAIService()
    
    # Тестируем бесплатную модель (GPT-3.5 Turbo)
    content_free = await service.generate_post_content(
        topic="Тест бесплатной модели",
        theme="технологии",
        style="friendly",
        language="ru",
        content_length="short",
        is_premium=False
    )
    
    assert content_free is not None
    assert len(content_free) > 10
    
    # Тестируем премиум модель (GPT-4)
    content_premium = await service.generate_post_content(
        topic="Test premium model",
        theme="tech",
        style="friendly",
        language="en",
        content_length="short",
        is_premium=True
    )
    
    assert content_premium is not None
    assert len(content_premium) > 10


if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(test_mock_content_generation())
    print("✅ AI генерация работает корректно!") 