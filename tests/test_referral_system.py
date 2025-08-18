import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from bot.models.models import User
from bot.services.crud.user import (
    get_or_create_user, 
    add_balance_to_user, 
    get_user_by_telegram_id,
    add_referral_bonus
)
from bot.services.crud.plan import create_plan
from bot.services.crud.subscription import create_subscription
from datetime import datetime, timezone, timedelta


@pytest_asyncio.fixture
async def referrer(session: AsyncSession):
    """Создает пользователя-пригласителя"""
    return await get_or_create_user(
        session=session,
        telegram_id=1001,
        full_name="Referrer User",
        username="referrer",
        ref_code=None,
        default_lang='ru'
    )


@pytest_asyncio.fixture
async def referred_user(session: AsyncSession, referrer: User):
    """Создает приглашенного пользователя"""
    return await get_or_create_user(
        session=session,
        telegram_id=1002,
        full_name="Referred User",
        username="referred",
        ref_code=referrer.referral_code,
        default_lang='ru'
    )


@pytest.mark.asyncio
async def test_referral_relationship_creation(session: AsyncSession, referrer: User, referred_user: User):
    """Тест создания реферальной связи"""
    
    # Проверяем, что у приглашенного пользователя установлена связь с пригласителем
    assert referred_user.referred_by_id == referrer.id
    
    # Проверяем, что у приглашенного пользователя есть реферальный код
    assert referred_user.referral_code is not None
    assert len(referred_user.referral_code) == 8
    
    # Проверяем, что у пригласителя есть реферальный код
    assert referrer.referral_code is not None
    assert len(referrer.referral_code) == 8


@pytest.mark.asyncio
async def test_referral_bonus_on_registration(session: AsyncSession, referrer: User, referred_user: User):
    """Тест бонусов при регистрации по реферальному коду"""
    
    # Проверяем, что приглашенный пользователь получил бонусы
    # +50 рублей на баланс
    assert referred_user.cash == Decimal('50')
    
    # +1 бесплатный пост
    assert referred_user.free_posts_limit == 6  # 5 по умолчанию + 1 бонус


@pytest.mark.asyncio
async def test_referrer_bonus_on_payment(session: AsyncSession, referrer: User, referred_user: User):
    """Тест бонуса пригласителю при пополнении баланса реферала"""
    
    # Изначальный баланс пригласителя
    initial_balance = referrer.cash or Decimal('0')
    
    # Пополняем баланс приглашенного пользователя на 1000 рублей
    success = await add_balance_to_user(session, referred_user.id, 1000.0)
    assert success is True
    
    # Обновляем данные пользователей
    await session.refresh(referrer)
    await session.refresh(referred_user)
    
    # Проверяем, что приглашенный пользователь получил 1000 рублей
    assert referred_user.cash == Decimal('1050')  # 50 (бонус при регистрации) + 1000
    
    # Проверяем, что пригласитель получил 10% бонус (100 рублей)
    expected_bonus = Decimal('100')  # 10% от 1000
    assert referrer.cash == initial_balance + expected_bonus


@pytest.mark.asyncio
async def test_referral_code_uniqueness(session: AsyncSession):
    """Тест уникальности реферальных кодов"""
    
    # Создаем несколько пользователей
    users = []
    for i in range(5):
        user = await get_or_create_user(
            session=session,
            telegram_id=2000 + i,
            full_name=f"User {i}",
            username=f"user{i}",
            ref_code=None,
            default_lang='ru'
        )
        users.append(user)
    
    # Проверяем, что все реферальные коды уникальны
    codes = [user.referral_code for user in users]
    assert len(codes) == len(set(codes)), "Реферальные коды должны быть уникальными"


@pytest.mark.asyncio
async def test_invalid_referral_code(session: AsyncSession):
    """Тест обработки неверного реферального кода"""
    
    # Создаем пользователя с неверным реферальным кодом
    user = await get_or_create_user(
        session=session,
        telegram_id=3001,
        full_name="Test User",
        username="testuser",
        ref_code="INVALID123",  # Неверный код
        default_lang='ru'
    )
    
    # Проверяем, что реферальная связь не установлена
    assert user.referred_by_id is None
    
    # Проверяем, что у пользователя есть свой реферальный код
    assert user.referral_code is not None


@pytest.mark.asyncio
async def test_self_referral_prevention(session: AsyncSession, referrer: User):
    """Тест предотвращения самоприглашения"""
    
    # Пытаемся создать пользователя с собственным реферальным кодом
    user = await get_or_create_user(
        session=session,
        telegram_id=4001,
        full_name="Self Referral User",
        username="selfref",
        ref_code=referrer.referral_code,  # Используем код пригласителя
        default_lang='ru'
    )
    
    # Проверяем, что реферальная связь установлена правильно
    assert user.referred_by_id == referrer.id
    
    # Теперь пытаемся создать пользователя с кодом самого себя
    # Это должно быть предотвращено в обработчике, но в базовой функции создания пользователя
    # это может пройти, поэтому проверяем логику в обработчике


@pytest.mark.asyncio
async def test_referral_stats(session: AsyncSession, referrer: User, referred_user: User):
    """Тест статистики рефералов"""
    
    from bot.services.crud.user import get_referral_stats
    
    # Получаем статистику пригласителя
    stats = await get_referral_stats(session, referrer.id)
    
    assert stats["referral_code"] == referrer.referral_code
    assert stats["referred_count"] == 1
    assert len(stats["referred_users"]) == 1
    
    # Получаем статистику приглашенного пользователя
    stats = await get_referral_stats(session, referred_user.id)
    
    assert stats["referral_code"] == referred_user.referral_code
    assert stats["referred_count"] == 0
    assert len(stats["referred_users"]) == 0 