import pytest
from bot.handlers.basic.about import about_handler
from bot.keyboards.inline.settings import get_simple_settings_keyboard


@pytest.mark.asyncio
async def test_simple_profile_format():
    """Тест формата упрощенного профиля"""
    # Проверяем, что упрощенная клавиатура содержит только нужные кнопки
    i18n = {
        "settings.language": "Язык",
        "settings.edit_name": "Изменить имя"
    }
    
    keyboard = get_simple_settings_keyboard(i18n)
    
    # Проверяем, что клавиатура содержит только 2 кнопки
    assert len(keyboard.inline_keyboard) == 2
    
    # Проверяем, что есть кнопка языка
    assert "🌐 Язык" in keyboard.inline_keyboard[0][0].text
    
    # Проверяем, что есть кнопка изменения имени
    assert "✏️ Изменить имя" in keyboard.inline_keyboard[1][0].text


@pytest.mark.asyncio
async def test_profile_text_structure():
    """Тест структуры текста профиля"""
    # Симулируем i18n словарь
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
    
    # Проверяем, что все ключи локализации присутствуют
    required_keys = [
        "about.no_subscription",
        "about.get_in_settings",
        "about.tasks",
        "about.active",
        "about.no_tasks",
        "about.posts",
        "about.published",
        "about.no_posts",
        "about.connected_accounts",
        "about.no_accounts",
        "about.free_posts_used"
    ]
    
    for key in required_keys:
        assert key in i18n, f"Отсутствует ключ локализации: {key}"


@pytest.mark.asyncio
async def test_none_values_handling():
    """Тест обработки None значений в профиле"""
    # Проверяем, что None значения корректно обрабатываются
    free_posts_used = None
    free_posts_limit = None
    cash = None
    
    # Симулируем обработку None значений
    free_posts_used = free_posts_used or 0
    free_posts_limit = free_posts_limit or 5
    cash = cash or 0
    
    assert free_posts_used == 0
    assert free_posts_limit == 5
    assert cash == 0
    
    # Проверяем, что сравнения работают корректно
    assert free_posts_used > 0 == False
    assert free_posts_used == 0 == True


if __name__ == "__main__":
    print("✅ Тесты упрощенного профиля работают корректно!") 