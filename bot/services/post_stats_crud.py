from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import PostStats

async def create_post_stats(session: AsyncSession, **kwargs) -> PostStats:
    stats = PostStats(**kwargs)
    session.add(stats)
    await session.commit()
    await session.refresh(stats)
    return stats

async def get_post_stats_by_id(session: AsyncSession, stats_id: int) -> PostStats | None:
    result = await session.execute(select(PostStats).where(PostStats.id == stats_id))
    return result.scalar_one_or_none()

async def get_all_post_stats(session: AsyncSession) -> list[PostStats]:
    result = await session.execute(select(PostStats))
    return result.scalars().all()

async def update_post_stats(session: AsyncSession, stats_id: int, **kwargs) -> PostStats | None:
    stats = await get_post_stats_by_id(session, stats_id)
    if not stats:
        return None
    for key, value in kwargs.items():
        setattr(stats, key, value)
    await session.commit()
    await session.refresh(stats)
    return stats

async def delete_post_stats(session: AsyncSession, stats_id: int) -> bool:
    stats = await get_post_stats_by_id(session, stats_id)
    if not stats:
        return False
    await session.delete(stats)
    await session.commit()
    return True 