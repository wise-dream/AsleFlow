import random
import string
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.models.models import User


def generate_referral_code(length: int = 8) -> str:
    """
    Генерирует уникальный реферальный код
    
    Args:
        length: Длина кода (по умолчанию 8 символов)
    
    Returns:
        Строка с реферальным кодом
    """
    # Используем только буквы и цифры, исключая похожие символы (0, O, 1, I, l)
    characters = string.ascii_uppercase + string.digits
    # Исключаем только действительно похожие символы
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    
    return ''.join(random.choice(characters) for _ in range(length))


async def generate_unique_referral_code(session: AsyncSession, length: int = 8, max_attempts: int = 50) -> Optional[str]:
    """
    Генерирует уникальный реферальный код, проверяя его на существование в базе
    
    Args:
        session: Сессия базы данных
        length: Длина кода
        max_attempts: Максимальное количество попыток генерации
    
    Returns:
        Уникальный реферальный код или None, если не удалось сгенерировать
    """
    for attempt in range(max_attempts):
        code = generate_referral_code(length)
        
        # Проверяем, существует ли такой код
        result = await session.execute(
            select(User.id).where(User.referral_code == code)
        )
        
        if not result.scalar_one_or_none():
            return code
        
        # Логируем каждые 10 попыток
        if (attempt + 1) % 10 == 0:
            print(f"Попытка {attempt + 1}/{max_attempts}: Код {code} уже существует")
    
    return None


async def is_referral_code_unique(session: AsyncSession, code: str) -> bool:
    """
    Проверяет, уникален ли реферальный код
    
    Args:
        session: Сессия базы данных
        code: Реферальный код для проверки
    
    Returns:
        True, если код уникален, False - если уже существует
    """
    result = await session.execute(
        select(User.id).where(User.referral_code == code)
    )
    return result.scalar_one_or_none() is None


async def get_user_by_referral_code(session: AsyncSession, referral_code: str) -> Optional[User]:
    """
    Находит пользователя по реферальному коду
    
    Args:
        session: Сессия базы данных
        referral_code: Реферальный код
    
    Returns:
        Пользователь или None, если не найден
    """
    result = await session.execute(
        select(User).where(User.referral_code == referral_code)
    )
    return result.scalar_one_or_none()


def validate_referral_code(code: str) -> bool:
    """
    Валидирует реферальный код
    
    Args:
        code: Реферальный код для валидации
    
    Returns:
        True, если код валиден, False - если нет
    """
    if not code:
        return False
    
    # Проверяем длину (от 6 до 12 символов)
    if len(code) < 6 or len(code) > 12:
        return False
    
    # Проверяем, что код содержит только буквы и цифры
    if not code.isalnum():
        return False
    
    # Проверяем, что код содержит только заглавные буквы
    if not code.isupper():
        return False
    
    return True 