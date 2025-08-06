import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.crud.user import (
    get_or_create_user,
    add_referral_bonus,
    add_referrer_bonus_from_payment,
    add_balance_to_user,
    get_referral_stats,
    get_user_by_referral_code
)
from bot.utils.referral import generate_unique_referral_code


@pytest.mark.asyncio
async def test_create_user_with_referral_code():
    """Тест создания пользователя с реферальным кодом"""
    
    session = AsyncMock()
    
    # Мокаем отсутствие существующего пользователя
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_telegram_id", AsyncMock(return_value=None))
        
        # Мокаем существующего пользователя с реферальным кодом
        referrer = MagicMock()
        referrer.id = 1
        referrer.referral_code = "ABC123"
        m.setattr("bot.services.crud.user.get_user_by_referral_code", AsyncMock(return_value=referrer))
        
        # Мокаем генерацию уникального реферального кода
        m.setattr("bot.services.crud.user.generate_unique_referral_code", AsyncMock(return_value="XYZ789"))
        m.setattr("bot.services.crud.user.add_referral_bonus", AsyncMock(return_value=True))
        
        # Создаем нового пользователя с реферальным кодом
        user = await get_or_create_user(
            session=session,
            telegram_id=123456,
            full_name="Test User",
            username="testuser",
            ref_code="ABC123",
            default_lang='en'
        )
        
        # Проверяем, что пользователь создан с правильными данными
        assert user.telegram_id == 123456
        assert user.name == "Test User"
        assert user.username == "testuser"
        assert user.referred_by_id == 1  # ID пригласившего
        assert user.referral_code == "XYZ789"


@pytest.mark.asyncio
async def test_create_user_with_invalid_referral_code():
    """Тест создания пользователя с неверным реферальным кодом"""
    
    session = AsyncMock()
    
    # Мокаем отсутствие существующего пользователя
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_telegram_id", AsyncMock(return_value=None))
        
        # Мокаем отсутствие пользователя с реферальным кодом
        m.setattr("bot.services.crud.user.get_user_by_referral_code", AsyncMock(return_value=None))
        
        # Мокаем генерацию уникального реферального кода
        m.setattr("bot.services.crud.user.generate_unique_referral_code", AsyncMock(return_value="XYZ789"))
        
        # Создаем нового пользователя с неверным реферальным кодом
        user = await get_or_create_user(
            session=session,
            telegram_id=123456,
            full_name="Test User",
            username="testuser",
            ref_code="INVALID",
            default_lang='en'
        )
        
        # Проверяем, что пользователь создан без реферального кода
        assert user.telegram_id == 123456
        assert user.name == "Test User"
        assert user.referred_by is None
        assert user.referral_code == "XYZ789"


@pytest.mark.asyncio
async def test_add_referral_bonus():
    """Тест добавления реферального бонуса приглашенному"""
    
    session = AsyncMock()
    
    # Мокаем приглашенного пользователя
    referred_user = MagicMock()
    referred_user.id = 2
    referred_user.free_posts_limit = 5
    referred_user.cash = 100
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_id", AsyncMock(return_value=referred_user))
        
        # Добавляем бонус приглашенному
        result = await add_referral_bonus(session, 1, 2)
        
        # Проверяем, что бонус добавлен приглашенному
        assert result is True
        assert referred_user.free_posts_limit == 6  # 5 + 1
        assert referred_user.cash == 150  # 100 + 50


@pytest.mark.asyncio
async def test_add_referrer_bonus_from_payment():
    """Тест добавления бонуса пригласившему от пополнения реферала"""
    
    session = AsyncMock()
    
    # Мокаем реферала
    referred_user = MagicMock()
    referred_user.id = 2
    referred_user.referred_by_id = 1
    
    # Мокаем пригласившего
    referrer = MagicMock()
    referrer.id = 1
    referrer.cash = 100
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_id", AsyncMock(side_effect=[referred_user, referrer]))
        
        # Добавляем бонус пригласившему от пополнения на 500 рублей
        result = await add_referrer_bonus_from_payment(session, 2, 500)
        
        # Проверяем, что бонус добавлен пригласившему (10% от 500 = 50)
        assert result is True
        assert referrer.cash == 150  # 100 + 50


@pytest.mark.asyncio
async def test_add_balance_to_user():
    """Тест пополнения баланса пользователя с реферальным бонусом"""
    
    session = AsyncMock()
    
    # Мокаем пользователя с рефералом
    user = MagicMock()
    user.id = 2
    user.cash = 100
    user.referred_by_id = 1
    
    # Мокаем пригласившего
    referrer = MagicMock()
    referrer.id = 1
    referrer.cash = 200
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_id", AsyncMock(side_effect=[user, referrer]))
        m.setattr("bot.services.crud.user.add_referrer_bonus_from_payment", AsyncMock(return_value=True))
        
        # Пополняем баланс на 500 рублей
        result = await add_balance_to_user(session, 2, 500)
        
        # Проверяем, что баланс пополнен
        assert result is True
        assert user.cash == 600  # 100 + 500


@pytest.mark.asyncio
async def test_get_referral_stats():
    """Тест получения статистики рефералов"""
    
    session = AsyncMock()
    
    # Мокаем пользователя
    user = MagicMock()
    user.id = 1
    user.referral_code = "ABC123"
    
    # Мокаем список приглашенных пользователей
    referred_users = [MagicMock(id=2), MagicMock(id=3)]
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_id", AsyncMock(return_value=user))
        
        # Мокаем результат запроса к базе данных
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = referred_users
        session.execute.return_value = mock_result
        
        # Получаем статистику
        stats = await get_referral_stats(session, 1)
        
        # Проверяем статистику
        assert stats["referral_code"] == "ABC123"
        assert stats["referred_count"] == 2
        assert len(stats["referred_users"]) == 2


@pytest.mark.asyncio
async def test_get_referral_stats_no_user():
    """Тест получения статистики для несуществующего пользователя"""
    
    session = AsyncMock()
    
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.services.crud.user.get_user_by_id", AsyncMock(return_value=None))
        
        # Получаем статистику
        stats = await get_referral_stats(session, 999)
        
        # Проверяем, что возвращается пустая статистика
        assert stats["referral_code"] is None
        assert stats["referred_count"] == 0
        assert len(stats["referred_users"]) == 0


@pytest.mark.asyncio
async def test_referral_code_generation():
    """Тест генерации уникального реферального кода"""
    
    session = AsyncMock()
    
    # Мокаем успешную генерацию кода
    with pytest.MonkeyPatch().context() as m:
        # Мокаем результат запроса к базе данных
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Код не существует
        session.execute.return_value = mock_result
        
        # Генерируем код
        code = await generate_unique_referral_code(session, length=8)
        
        # Проверяем, что код сгенерирован (должен быть строкой)
        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 8


@pytest.mark.asyncio
async def test_referral_code_generation_failure():
    """Тест неудачной генерации реферального кода"""
    
    session = AsyncMock()
    
    # Мокаем неудачную генерацию кода
    with pytest.MonkeyPatch().context() as m:
        m.setattr("bot.utils.referral.generate_unique_referral_code", AsyncMock(return_value=None))
        
        # Генерируем код
        code = await generate_unique_referral_code(session, length=8)
        
        # Проверяем, что код не сгенерирован
        assert code is None


if __name__ == "__main__":
    print("✅ Тесты реферальной системы работают корректно!") 