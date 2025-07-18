from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Subscription

async def create_subscription(session: AsyncSession, **kwargs) -> Subscription:
    subscription = Subscription(**kwargs)
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription

async def get_subscription_by_id(session: AsyncSession, subscription_id: int) -> Subscription | None:
    result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
    return result.scalar_one_or_none()

async def get_all_subscriptions(session: AsyncSession) -> list[Subscription]:
    result = await session.execute(select(Subscription))
    return result.scalars().all()

async def update_subscription(session: AsyncSession, subscription_id: int, **kwargs) -> Subscription | None:
    subscription = await get_subscription_by_id(session, subscription_id)
    if not subscription:
        return None
    for key, value in kwargs.items():
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