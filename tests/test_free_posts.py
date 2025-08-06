import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.crud.user import (
    can_create_free_post, 
    increment_free_posts_used, 
    get_free_posts_remaining,
    create_user
)
from bot.models.models import User


@pytest.mark.asyncio
async def test_can_create_free_post(session: AsyncSession):
    """Тест проверки возможности создания бесплатного поста"""
    # Создаем пользователя
    user = await create_user(session, telegram_id=123456, name="Test User")
    
    # Проверяем, что новый пользователь может создать бесплатный пост
    assert await can_create_free_post(session, user.id) == True
    
    # Используем все бесплатные посты (по умолчанию лимит 5)
    for i in range(5):
        await increment_free_posts_used(session, user.id)
    
    # Проверяем, что больше нельзя создать бесплатный пост
    assert await can_create_free_post(session, user.id) == False


@pytest.mark.asyncio
async def test_increment_free_posts_used(session: AsyncSession):
    """Тест увеличения счетчика бесплатных постов"""
    # Создаем пользователя
    user = await create_user(session, telegram_id=123457, name="Test User 2")
    
    # Проверяем начальное значение
    assert user.free_posts_used == 0
    
    # Увеличиваем счетчик
    result = await increment_free_posts_used(session, user.id)
    assert result == True
    
    # Обновляем объект пользователя
    from bot.services.crud.user import get_user_by_id
    user = await get_user_by_id(session, user.id)
    assert user.free_posts_used == 1


@pytest.mark.asyncio
async def test_get_free_posts_remaining(session: AsyncSession):
    """Тест получения количества оставшихся бесплатных постов"""
    # Создаем пользователя
    user = await create_user(session, telegram_id=123458, name="Test User 3")
    
    # Проверяем начальное количество (по умолчанию лимит 5)
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 5
    
    # Используем 2 поста
    await increment_free_posts_used(session, user.id)
    await increment_free_posts_used(session, user.id)
    
    # Проверяем оставшееся количество
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 3
    
    # Используем все посты
    for i in range(3):
        await increment_free_posts_used(session, user.id)
    
    # Проверяем, что осталось 0
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 0


@pytest.mark.asyncio
async def test_individual_free_posts_limit(session: AsyncSession):
    """Тест индивидуальных лимитов бесплатных постов"""
    from bot.services.crud.user import set_free_posts_limit, add_free_posts, reset_free_posts_used
    
    # Создаем пользователя
    user = await create_user(session, telegram_id=123459, name="Test User 4")
    
    # Проверяем начальный лимит (по умолчанию 5)
    assert user.free_posts_limit == 5
    
    # Устанавливаем индивидуальный лимит
    result = await set_free_posts_limit(session, user.id, 10)
    assert result == True
    
    # Обновляем объект пользователя
    from bot.services.crud.user import get_user_by_id
    user = await get_user_by_id(session, user.id)
    assert user.free_posts_limit == 10
    
    # Проверяем, что может создать больше постов
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 10
    
    # Добавляем еще посты к лимиту
    result = await add_free_posts(session, user.id, 5)
    assert result == True
    
    user = await get_user_by_id(session, user.id)
    assert user.free_posts_limit == 15
    
    # Используем несколько постов
    for i in range(3):
        await increment_free_posts_used(session, user.id)
    
    # Проверяем оставшиеся
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 12
    
    # Сбрасываем использованные посты
    result = await reset_free_posts_used(session, user.id)
    assert result == True
    
    user = await get_user_by_id(session, user.id)
    assert user.free_posts_used == 0
    
    remaining = await get_free_posts_remaining(session, user.id)
    assert remaining == 15 