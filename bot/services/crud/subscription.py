from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Subscription
from datetime import datetime, timezone

ALLOWED_FIELDS = {"user_id", "plan_id", "start_date", "end_date", "status", "auto_renew"}

async def create_subscription(session: AsyncSession, **kwargs) -> Subscription:
    subscription = Subscription(**kwargs)
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription

async def get_subscription_by_id(session: AsyncSession, subscription_id: int) -> Subscription | None:
    result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
    return result.scalar_one_or_none()


async def get_user_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    """Получить активную подписку пользователя"""
    from datetime import datetime, timezone
    
    result = await session.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == 'active',
            Subscription.end_date > datetime.now(timezone.utc)
        )
        .order_by(Subscription.end_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_all_subscriptions(session: AsyncSession) -> list[Subscription]:
    result = await session.execute(select(Subscription))
    return result.scalars().all()

async def update_subscription(session: AsyncSession, subscription_id: int, **kwargs) -> Subscription | None:
    subscription = await get_subscription_by_id(session, subscription_id)
    if not subscription:
        return None

    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(subscription, key, value)

    await session.commit()
    await session.refresh(subscription)
    return subscription

async def delete_subscription(session: AsyncSession, subscription_id: int) -> bool:
    subscription = await get_subscription_by_id(session, subscription_id)
    if not subscription:
        return False

    await session.delete(subscription)
    await session.commit()
    return True

async def get_active_subscriptions(session: AsyncSession) -> list[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.status == 'active'))
    return result.scalars().all()

async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    """Получить активную подписку пользователя"""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == 'active',
            Subscription.start_date <= now,
            Subscription.end_date > now
        ).order_by(Subscription.end_date.desc())
    )
    return result.scalar_one_or_none()

async def get_subscriptions_by_user_id(session: AsyncSession, user_id: int) -> list[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    return result.scalars().all()

async def get_subscriptions_by_status(session: AsyncSession, status: str) -> list[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.status == status))
    return result.scalars().all()

async def get_expired_subscriptions(session: AsyncSession) -> list[Subscription]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    result = await session.execute(select(Subscription).where(Subscription.end_date < now))
    return result.scalars().all()

async def get_expiring_soon_subscriptions(session: AsyncSession, days: int = 7) -> list[Subscription]:
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)
    result = await session.execute(
        select(Subscription).where(
            Subscription.end_date >= now,
            Subscription.end_date <= future_date,
            Subscription.status == 'active'
        )
    )
    return result.scalars().all()
