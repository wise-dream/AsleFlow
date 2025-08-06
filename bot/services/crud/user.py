from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import User
from bot.utils.referral import generate_unique_referral_code, is_referral_code_unique, get_user_by_referral_code, validate_referral_code

ALLOWED_FIELDS = {
    "name", "email", "password", "username", "language", "timezone", "role", 
    "cash", "referral_code", "referred_by", "free_posts_used", "free_posts_limit",
    "notify_new_posts", "notify_scheduled", "notify_errors", "notify_payments",
    "default_language", "default_style", "default_length", "default_moderation",
    "two_factor_enabled", "last_login", "login_count", "theme", "compact_mode"
}

async def create_user(session: AsyncSession, **kwargs) -> User:
    user = User(**kwargs)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()

async def update_user(session: AsyncSession, user_id: int, **kwargs) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user

async def delete_user(session: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(session, user_id)
    if not user:
        return False

    await session.delete(user)
    await session.commit()
    return True

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
    ref_code: str | None = None,
    default_lang: str = 'en',
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)

    if not user:
        # Проверяем реферальный код пригласителя, если он передан
        referred_by_user = None
        if ref_code:
            referred_by_user = await get_user_by_referral_code(session, ref_code)
            if not referred_by_user:
                # Если код не найден, сбрасываем его
                ref_code = None
        
        # Генерируем уникальный реферальный код для нового пользователя
        # ПОВТОРЯЕМ ПОПЫТКИ ДО УСПЕХА - пользователь НЕ ДОЛЖЕН создаваться без кода!
        referral_code = None
        max_attempts = 50  # Увеличиваем количество попыток
        
        for attempt in range(max_attempts):
            referral_code = await generate_unique_referral_code(session, length=8)
            if referral_code:
                break
            print(f"Попытка {attempt + 1}/{max_attempts}: Не удалось сгенерировать реферальный код для пользователя {telegram_id}")
        
        if not referral_code:
            # Если все попытки исчерпаны, создаем код вручную
            import random
            import string
            for attempt in range(100):
                # Генерируем код вручную
                chars = string.ascii_uppercase + string.digits
                chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
                manual_code = ''.join(random.choice(chars) for _ in range(8))
                
                # Проверяем уникальность
                existing_user = await get_user_by_referral_code(session, manual_code)
                if not existing_user:
                    referral_code = manual_code
                    print(f"Создан реферальный код вручную: {manual_code}")
                    break
        
        if not referral_code:
            raise Exception(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать реферальный код для пользователя {telegram_id} после всех попыток!")
        
        user = User(
            telegram_id=telegram_id,
            name=full_name,
            username=username,
            language=default_lang,
            referred_by_id=referred_by_user.id if referred_by_user else None,
            referral_code=referral_code  # ← Теперь ВСЕГДА будет код!
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Если есть пригласитель, добавляем бонусы
        if referred_by_user:
            await add_referral_bonus(session, referred_by_user.id, user.id)

    elif ref_code and not user.referred_by_id:
        # Проверяем реферальный код пригласителя
        referred_by_user = await get_user_by_referral_code(session, ref_code)
        if referred_by_user:
            user.referred_by_id = referred_by_user.id
            await session.commit()
            await session.refresh(user)
            
            # Если у пользователя нет реферального кода, генерируем его
            if not user.referral_code:
                referral_code = await generate_unique_referral_code(session, length=8)
                if referral_code:
                    user.referral_code = referral_code
                    await session.commit()
                    await session.refresh(user)
                else:
                    print(f"Warning: Не удалось сгенерировать реферальный код для существующего пользователя {user.id}")
        else:
            # Если код не найден, игнорируем его
            pass

    return user

async def exists_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(select(User.id).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none() is not None


async def generate_user_referral_code(session: AsyncSession, user_id: int) -> str | None:
    """
    Генерирует и сохраняет реферальный код для пользователя
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Сгенерированный реферальный код или None, если не удалось сгенерировать
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    
    # Если у пользователя уже есть код, возвращаем его
    if user.referral_code:
        return user.referral_code
    
    # Генерируем новый уникальный код
    referral_code = await generate_unique_referral_code(session)
    if not referral_code:
        return None
    
    # Сохраняем код
    user.referral_code = referral_code
    await session.commit()
    await session.refresh(user)
    
    return referral_code


async def update_user_referral_code(session: AsyncSession, user_id: int, new_code: str) -> bool:
    """
    Обновляет реферальный код пользователя
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        new_code: Новый реферальный код
    
    Returns:
        True, если код успешно обновлен, False - если произошла ошибка
    """
    # Валидируем код
    if not validate_referral_code(new_code):
        return False
    
    # Проверяем, что код уникален
    if not await is_referral_code_unique(session, new_code):
        return False
    
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    # Обновляем код
    user.referral_code = new_code
    await session.commit()
    await session.refresh(user)
    
    return True


async def get_users_without_referral_codes(session: AsyncSession) -> list[User]:
    """
    Получает список пользователей без реферальных кодов
    
    Args:
        session: Сессия базы данных
    
    Returns:
        Список пользователей без реферальных кодов
    """
    result = await session.execute(
        select(User).where(User.referral_code.is_(None))
    )
    return result.scalars().all()


async def generate_referral_codes_for_existing_users(session: AsyncSession, batch_size: int = 100) -> int:
    """
    Генерирует реферальные коды для существующих пользователей, у которых их нет
    
    Args:
        session: Сессия базы данных
        batch_size: Размер пакета для обработки
    
    Returns:
        Количество пользователей, для которых были сгенерированы коды
    """
    users_without_codes = await get_users_without_referral_codes(session)
    generated_count = 0
    
    for user in users_without_codes[:batch_size]:
        referral_code = await generate_unique_referral_code(session)
        if referral_code:
            user.referral_code = referral_code
            generated_count += 1
            print(f"Generated referral code {referral_code} for user {user.id}")
        else:
            print(f"Failed to generate referral code for user {user.id}")
    
    if generated_count > 0:
        await session.commit()
    
    return generated_count

async def get_users_by_role(session: AsyncSession, role: str) -> list[User]:
    """Получить пользователей по роли"""
    result = await session.execute(select(User).where(User.role == role))
    return result.scalars().all()

async def get_users_by_language(session: AsyncSession, language: str) -> list[User]:
    """Получить пользователей по языку"""
    result = await session.execute(select(User).where(User.language == language))
    return result.scalars().all()

async def get_users_by_timezone(session: AsyncSession, timezone: str) -> list[User]:
    """Получить пользователей по часовому поясу"""
    result = await session.execute(select(User).where(User.timezone == timezone))
    return result.scalars().all()

async def get_users_by_referral_code(session: AsyncSession, referral_code: str) -> list[User]:
    """Получить пользователей по реферальному коду"""
    result = await session.execute(select(User).where(User.referred_by == referral_code))
    return result.scalars().all()

async def get_users_with_two_factor(session: AsyncSession) -> list[User]:
    """Получить пользователей с включенной двухфакторной аутентификацией"""
    result = await session.execute(select(User).where(User.two_factor_enabled == True))
    return result.scalars().all()

async def get_users_by_theme(session: AsyncSession, theme: str) -> list[User]:
    """Получить пользователей по теме интерфейса"""
    result = await session.execute(select(User).where(User.theme == theme))
    return result.scalars().all()

async def get_users_by_compact_mode(session: AsyncSession, compact_mode: bool) -> list[User]:
    """Получить пользователей по режиму компактности"""
    result = await session.execute(select(User).where(User.compact_mode == compact_mode))
    return result.scalars().all()

async def get_users_by_notification_settings(
    session: AsyncSession, 
    notify_new_posts: bool = None,
    notify_scheduled: bool = None,
    notify_errors: bool = None,
    notify_payments: bool = None
) -> list[User]:
    """Получить пользователей по настройкам уведомлений"""
    query = select(User)
    conditions = []
    
    if notify_new_posts is not None:
        conditions.append(User.notify_new_posts == notify_new_posts)
    if notify_scheduled is not None:
        conditions.append(User.notify_scheduled == notify_scheduled)
    if notify_errors is not None:
        conditions.append(User.notify_errors == notify_errors)
    if notify_payments is not None:
        conditions.append(User.notify_payments == notify_payments)
    
    if conditions:
        for condition in conditions:
            query = query.where(condition)
    
    result = await session.execute(query)
    return result.scalars().all()

async def get_users_by_content_settings(
    session: AsyncSession,
    default_language: str = None,
    default_style: str = None,
    default_length: str = None,
    default_moderation: bool = None
) -> list[User]:
    """Получить пользователей по настройкам контента"""
    query = select(User)
    conditions = []
    
    if default_language is not None:
        conditions.append(User.default_language == default_language)
    if default_style is not None:
        conditions.append(User.default_style == default_style)
    if default_length is not None:
        conditions.append(User.default_length == default_length)
    if default_moderation is not None:
        conditions.append(User.default_moderation == default_moderation)
    
    if conditions:
        for condition in conditions:
            query = query.where(condition)
    
    result = await session.execute(query)
    return result.scalars().all()

async def update_user_last_login(session: AsyncSession, user_id: int) -> bool:
    """Обновить время последнего входа пользователя"""
    from datetime import datetime, timezone
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.last_login = datetime.now(timezone.utc)
    user.login_count += 1
    await session.commit()
    return True

async def get_users_by_cash_range(session: AsyncSession, min_cash: float, max_cash: float) -> list[User]:
    """Получить пользователей по диапазону баланса"""
    result = await session.execute(
        select(User).where(
            User.cash >= min_cash,
            User.cash <= max_cash
        )
    )
    return result.scalars().all()

async def get_users_by_free_posts_used_range(session: AsyncSession, min_posts: int, max_posts: int) -> list[User]:
    """Получить пользователей по диапазону использованных бесплатных постов"""
    result = await session.execute(
        select(User).where(
            User.free_posts_used >= min_posts,
            User.free_posts_used <= max_posts
        )
    )
    return result.scalars().all()

async def can_create_free_post(session: AsyncSession, user_id: int) -> bool:
    """
    Проверяет, может ли пользователь создать бесплатный пост
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        True, если пользователь может создать бесплатный пост, False - если нет
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    return user.free_posts_used < user.free_posts_limit

async def increment_free_posts_used(session: AsyncSession, user_id: int) -> bool:
    """
    Увеличивает счетчик использованных бесплатных постов
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        True, если счетчик успешно увеличен, False - если произошла ошибка
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.free_posts_used += 1
    await session.commit()
    await session.refresh(user)
    return True

async def get_free_posts_remaining(session: AsyncSession, user_id: int) -> int:
    """
    Получает количество оставшихся бесплатных постов
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Количество оставшихся бесплатных постов
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return 0
    
    remaining = user.free_posts_limit - user.free_posts_used
    return max(0, remaining)


async def get_free_posts_info(session: AsyncSession, user_id: int) -> dict:
    """
    Получает полную информацию о бесплатных постах пользователя
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Словарь с информацией о бесплатных постах:
        {
            'used': количество использованных постов,
            'limit': максимальное количество постов,
            'remaining': количество оставшихся постов,
            'can_create': может ли создать новый пост
        }
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return {
            'used': 0,
            'limit': 0,
            'remaining': 0,
            'can_create': False
        }
    
    used = user.free_posts_used
    limit = user.free_posts_limit
    remaining = max(0, limit - used)
    can_create = used < limit
    
    return {
        'used': used,
        'limit': limit,
        'remaining': remaining,
        'can_create': can_create
    }


async def set_free_posts_limit(session: AsyncSession, user_id: int, limit: int) -> bool:
    """Устанавливает индивидуальный лимит бесплатных постов для пользователя"""
    if limit < 0:
        return False
    
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.free_posts_limit = limit
    await session.commit()
    await session.refresh(user)
    return True


async def add_free_posts(session: AsyncSession, user_id: int, count: int) -> bool:
    """Добавляет бесплатные посты к лимиту пользователя"""
    if count <= 0:
        return False
    
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.free_posts_limit += count
    await session.commit()
    await session.refresh(user)
    return True


async def reset_free_posts_used(session: AsyncSession, user_id: int) -> bool:
    """Сбрасывает счетчик использованных бесплатных постов"""
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.free_posts_used = 0
    await session.commit()
    await session.refresh(user)
    return True


async def get_users_by_free_posts_limit_range(session: AsyncSession, min_limit: int, max_limit: int) -> list[User]:
    """Получить пользователей по диапазону лимита бесплатных постов"""
    result = await session.execute(
        select(User).where(
            User.free_posts_limit >= min_limit,
            User.free_posts_limit <= max_limit
        )
    )
    return result.scalars().all()

async def clear_user_cache(redis, telegram_id: int) -> bool:
    """
    Очищает кэш пользователя в Redis
    
    Args:
        redis: Redis клиент
        telegram_id: Telegram ID пользователя
    
    Returns:
        True, если кэш успешно очищен, False - если произошла ошибка
    """
    if not redis:
        return False
    
    try:
        await redis.delete(f"user:{telegram_id}")
        return True
    except Exception as e:
        print(f"Ошибка очистки кэша пользователя: {e}")
        import traceback
        traceback.print_exc()
        return False


async def update_user_with_cache_clear(
    session: AsyncSession, 
    user_id: int, 
    redis=None, 
    **kwargs
) -> User | None:
    """
    Обновляет пользователя и очищает его кэш в Redis
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        redis: Redis клиент (опционально)
        **kwargs: Поля для обновления
    
    Returns:
        Обновленный пользователь или None
    """
    user = await update_user(session, user_id, **kwargs)
    
    if user and redis:
        await clear_user_cache(redis, user.telegram_id)
    
    return user


async def add_referral_bonus(session: AsyncSession, referrer_id: int, referred_id: int) -> bool:
    """
    Добавляет бонусы приглашенному пользователю за ввод реферального кода
    
    Args:
        session: Сессия базы данных
        referrer_id: ID пригласителя
        referred_id: ID приглашенного пользователя
    
    Returns:
        True, если бонусы добавлены успешно
    """
    try:
        referred_user = await get_user_by_id(session, referred_id)
        if not referred_user:
            return False
        
        # Добавляем бонусы приглашенному пользователю
        # +50 рублей на баланс
        current_cash = referred_user.cash or 0
        # Преобразуем в Decimal для корректного сложения
        from decimal import Decimal
        referred_user.cash = Decimal(str(current_cash)) + Decimal('50')
        
        # +1 бесплатный пост
        current_limit = referred_user.free_posts_limit or 5
        referred_user.free_posts_limit = current_limit + 1
        
        await session.commit()
        await session.refresh(referred_user)
        
        return True
        
    except Exception as e:
        print(f"Ошибка при добавлении реферального бонуса: {e}")
        return False


async def add_balance_to_user(session: AsyncSession, user_id: int, amount: float, redis=None) -> bool:
    """
    Пополняет баланс пользователя и добавляет бонус пригласившему
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        amount: Сумма пополнения
        redis: Redis клиент для очистки кеша (опционально)
    
    Returns:
        True, если баланс пополнен успешно
    """
    try:
        user = await get_user_by_id(session, user_id)
        if not user:
            return False
        
        # Пополняем баланс пользователя
        current_cash = user.cash or 0
        # Преобразуем в Decimal для корректного сложения
        from decimal import Decimal
        user.cash = Decimal(str(current_cash)) + Decimal(str(amount))
        
        # Добавляем бонус пригласившему (10% от суммы пополнения)
        if user.referred_by_id:
            await add_referrer_bonus_from_payment(session, user_id, amount, redis)
        
        await session.commit()
        await session.refresh(user)
        
        # Очищаем кеш пользователя, если передан redis клиент
        if redis and user.telegram_id:
            await clear_user_cache(redis, user.telegram_id)
        
        return True
        
    except Exception as e:
        print(f"Ошибка при пополнении баланса: {e}")
        import traceback
        traceback.print_exc()
        return False


async def add_referrer_bonus_from_payment(session: AsyncSession, referred_user_id: int, payment_amount: float, redis=None) -> bool:
    """
    Добавляет бонус пригласившему от пополнения баланса реферала
    
    Args:
        session: Сессия базы данных
        referred_user_id: ID реферала (кто пополняет баланс)
        payment_amount: Сумма пополнения
        redis: Redis клиент для очистки кеша (опционально)
    
    Returns:
        True, если бонус добавлен успешно
    """
    try:
        referred_user = await get_user_by_id(session, referred_user_id)
        if not referred_user or not referred_user.referred_by_id:
            return False
        
        referrer = await get_user_by_id(session, referred_user.referred_by_id)
        if not referrer:
            return False
        
        # Пригласивший получает 10% от суммы пополнения
        bonus_amount = payment_amount * 0.1
        
        current_cash = referrer.cash or 0
        # Преобразуем в Decimal для корректного сложения
        from decimal import Decimal
        referrer.cash = Decimal(str(current_cash)) + Decimal(str(bonus_amount))
        
        await session.commit()
        await session.refresh(referrer)
        
        # Очищаем кеш пригласившего, если передан redis клиент
        if redis and referrer.telegram_id:
            await clear_user_cache(redis, referrer.telegram_id)
        
        return True
        
    except Exception as e:
        print(f"Ошибка при добавлении бонуса пригласившему: {e}")
        return False


async def get_referral_stats(session: AsyncSession, user_id: int) -> dict:
    """
    Получает статистику рефералов пользователя
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Словарь со статистикой
    """
    try:
        user = await get_user_by_id(session, user_id)
        if not user:
            return {
                "referral_code": None,
                "referred_count": 0,
                "referred_users": []
            }
        
        # Подсчитываем количество приглашенных пользователей
        result = await session.execute(
            select(User.id).where(User.referred_by_id == user.id)
        )
        referred_users = result.scalars().all()
        
        return {
            "referral_code": user.referral_code,
            "referred_count": len(referred_users),
            "referred_users": referred_users
        }
        
    except Exception as e:
        print(f"Ошибка при получении статистики рефералов: {e}")
        return {
            "referral_code": None,
            "referred_count": 0,
            "referred_users": []
        }
