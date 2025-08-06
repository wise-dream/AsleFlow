from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Plan

ALLOWED_FIELDS = {"name", "price", "channels_limit", "posts_limit", "manual_posts_limit", "ai_priority", "description", "is_active"}


async def create_plan(session: AsyncSession, **kwargs) -> Plan:
    plan = Plan(**kwargs)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def get_plan_by_id(session: AsyncSession, plan_id: int) -> Plan | None:
    result = await session.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()


async def get_all_plans(session: AsyncSession) -> list[Plan]:
    result = await session.execute(select(Plan))
    return result.scalars().all()


async def get_all_active_plans(session: AsyncSession) -> list[Plan]:
    result = await session.execute(select(Plan).where(Plan.is_active == True))
    return result.scalars().all()


async def update_plan(session: AsyncSession, plan_id: int, **kwargs) -> Plan | None:
    plan = await get_plan_by_id(session, plan_id)
    if not plan:
        return None
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(plan, key, value)
    await session.commit()
    await session.refresh(plan)
    return plan


async def delete_plan(session: AsyncSession, plan_id: int) -> bool:
    plan = await get_plan_by_id(session, plan_id)
    if not plan:
        return False
    await session.delete(plan)
    await session.commit()
    return True


async def get_plans_by_price_range(session: AsyncSession, min_price: float, max_price: float) -> list[Plan]:
    result = await session.execute(
        select(Plan).where(
            Plan.price >= min_price,
            Plan.price <= max_price
        )
    )
    return result.scalars().all()


async def get_plans_by_channels_limit(session: AsyncSession, channels_limit: int) -> list[Plan]:
    result = await session.execute(
        select(Plan).where(Plan.channels_limit >= channels_limit)
    )
    return result.scalars().all()


async def get_plans_by_posts_limit(session: AsyncSession, posts_limit: int) -> list[Plan]:
    result = await session.execute(
        select(Plan).where(Plan.posts_limit >= posts_limit)
    )
    return result.scalars().all()


async def get_plans_with_ai_priority(session: AsyncSession) -> list[Plan]:
    result = await session.execute(
        select(Plan).where(Plan.ai_priority == True)
    )
    return result.scalars().all() 