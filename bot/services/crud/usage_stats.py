from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import UsageStats, Subscription

ALLOWED_FIELDS = {"posts_used", "manual_posts_used", "channels_connected"}

async def create_usage_stats(session: AsyncSession, **kwargs) -> UsageStats:
    """Создать статистику использования"""
    stats = UsageStats(**kwargs)
    session.add(stats)
    await session.commit()
    await session.refresh(stats)
    return stats

async def get_usage_stats_by_id(session: AsyncSession, stats_id: int) -> UsageStats:
    """Получить статистику по ID"""
    result = await session.execute(select(UsageStats).where(UsageStats.id == stats_id))
    return result.scalar_one_or_none()

async def get_usage_stats_by_subscription_id(session: AsyncSession, subscription_id: int) -> UsageStats:
    """Получить статистику по ID подписки"""
    result = await session.execute(
        select(UsageStats).where(UsageStats.subscription_id == subscription_id)
    )
    return result.scalar_one_or_none()

async def get_user_usage_stats(session: AsyncSession, user_id: int) -> UsageStats | None:
    """Получить статистику использования пользователя по активной подписке"""
    from bot.services.crud.subscription import get_active_subscription
    
    # Получаем активную подписку пользователя
    subscription = await get_active_subscription(session, user_id)
    if not subscription:
        return None
    
    # Получаем статистику использования для этой подписки
    return await get_usage_stats_by_subscription_id(session, subscription.id)

async def get_all_usage_stats(session: AsyncSession) -> list[UsageStats]:
    """Получить всю статистику"""
    result = await session.execute(select(UsageStats))
    return result.scalars().all()

async def update_usage_stats(session: AsyncSession, stats_id: int, **kwargs) -> UsageStats:
    """Обновить статистику"""
    stats = await get_usage_stats_by_id(session, stats_id)
    if not stats:
        return None
    
    # Обновляем только разрешенные поля
    for field, value in kwargs.items():
        if field in ALLOWED_FIELDS:
            setattr(stats, field, value)
    
    await session.commit()
    await session.refresh(stats)
    return stats

async def delete_usage_stats(session: AsyncSession, stats_id: int) -> bool:
    """Удалить статистику"""
    stats = await get_usage_stats_by_id(session, stats_id)
    if not stats:
        return False
    
    await session.delete(stats)
    await session.commit()
    return True

async def increment_posts_used(session: AsyncSession, subscription_id: int, count: int = 1) -> bool:
    """Увеличить количество использованных постов"""
    stats = await get_usage_stats_by_subscription_id(session, subscription_id)
    if not stats:
        return False
    
    stats.posts_used += count
    await session.commit()
    return True

async def increment_manual_posts_used(session: AsyncSession, subscription_id: int, count: int = 1) -> bool:
    """Увеличить количество использованных ручных постов"""
    stats = await get_usage_stats_by_subscription_id(session, subscription_id)
    if not stats:
        return False
    
    stats.manual_posts_used += count
    await session.commit()
    return True

async def increment_channels_connected(session: AsyncSession, subscription_id: int, count: int = 1) -> bool:
    """Увеличить количество подключенных каналов"""
    stats = await get_usage_stats_by_subscription_id(session, subscription_id)
    if not stats:
        return False
    
    stats.channels_connected += count
    await session.commit()
    return True

async def reset_usage_stats(session: AsyncSession, subscription_id: int) -> bool:
    """Сбросить статистику использования"""
    stats = await get_usage_stats_by_subscription_id(session, subscription_id)
    if not stats:
        return False
    
    stats.posts_used = 0
    stats.manual_posts_used = 0
    stats.channels_connected = 0
    await session.commit()
    return True

async def get_usage_stats_by_posts_used_range(session: AsyncSession, min_posts: int, max_posts: int) -> list[UsageStats]:
    """Получить статистику по диапазону использованных постов"""
    result = await session.execute(
        select(UsageStats).where(
            UsageStats.posts_used >= min_posts,
            UsageStats.posts_used <= max_posts
        )
    )
    return result.scalars().all()

async def get_usage_stats_by_manual_posts_used_range(session: AsyncSession, min_posts: int, max_posts: int) -> list[UsageStats]:
    """Получить статистику по диапазону использованных ручных постов"""
    result = await session.execute(
        select(UsageStats).where(
            UsageStats.manual_posts_used >= min_posts,
            UsageStats.manual_posts_used <= max_posts
        )
    )
    return result.scalars().all()

async def get_usage_stats_by_channels_connected_range(session: AsyncSession, min_channels: int, max_channels: int) -> list[UsageStats]:
    """Получить статистику по диапазону подключенных каналов"""
    result = await session.execute(
        select(UsageStats).where(
            UsageStats.channels_connected >= min_channels,
            UsageStats.channels_connected <= max_channels
        )
    )
    return result.scalars().all()

async def get_top_usage_by_posts(session: AsyncSession, limit: int = 10) -> list[UsageStats]:
    """Получить топ статистику по использованным постам"""
    result = await session.execute(
        select(UsageStats).order_by(UsageStats.posts_used.desc()).limit(limit)
    )
    return result.scalars().all()

async def get_top_usage_by_manual_posts(session: AsyncSession, limit: int = 10) -> list[UsageStats]:
    """Получить топ статистику по использованным ручным постам"""
    result = await session.execute(
        select(UsageStats).order_by(UsageStats.manual_posts_used.desc()).limit(limit)
    )
    return result.scalars().all()

async def get_top_usage_by_channels(session: AsyncSession, limit: int = 10) -> list[UsageStats]:
    """Получить топ статистику по подключенным каналам"""
    result = await session.execute(
        select(UsageStats).order_by(UsageStats.channels_connected.desc()).limit(limit)
    )
    return result.scalars().all() 