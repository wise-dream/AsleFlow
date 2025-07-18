from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.models import User

async def create_user(session: AsyncSession, **kwargs) -> User:
    user = User(**kwargs)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def update_user(session: AsyncSession, user_id: int, **kwargs) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
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
) -> tuple[User, bool]:
    """
    Возвращает (user, is_new).
    Если пользователь новый — создаёт его с языком default_lang и сохраняет реферала.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    is_new = False

    if not user:
        user = User(
            telegram_id=telegram_id,
            name=full_name,
            username=username,
            language=default_lang,
            referred_by=ref_code if ref_code else None
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        is_new = True

    elif ref_code and not user.referred_by:
        user.referred_by = ref_code
        await session.commit()
        await session.refresh(user)

    return user, is_new
