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

async def get_post_stats_by_post_id(session: AsyncSession, post_id: int) -> PostStats | None:
    result = await session.execute(select(PostStats).where(PostStats.post_id == post_id))
    return result.scalar_one_or_none()

async def increment_post_stats(
    session: AsyncSession, post_id: int, views: int = 0, likes: int = 0, reposts: int = 0
) -> None:
    stats = await get_post_stats_by_post_id(session, post_id)
    if stats:
        stats.views += views
        stats.likes += likes
        stats.reposts += reposts
        await session.commit()

async def get_top_posts_by_views(session: AsyncSession, limit: int = 10) -> list[PostStats]:
    result = await session.execute(
        select(PostStats).order_by(PostStats.views.desc()).limit(limit)
    )
    return result.scalars().all()

async def get_top_posts_by_likes(session: AsyncSession, limit: int = 10) -> list[PostStats]:
    result = await session.execute(
        select(PostStats).order_by(PostStats.likes.desc()).limit(limit)
    )
    return result.scalars().all()

async def get_top_posts_by_reposts(session: AsyncSession, limit: int = 10) -> list[PostStats]:
    result = await session.execute(
        select(PostStats).order_by(PostStats.reposts.desc()).limit(limit)
    )
    return result.scalars().all()

async def get_stats_by_views_range(session: AsyncSession, min_views: int, max_views: int) -> list[PostStats]:
    result = await session.execute(
        select(PostStats).where(
            PostStats.views >= min_views,
            PostStats.views <= max_views
        )
    )
    return result.scalars().all()

async def get_stats_by_likes_range(session: AsyncSession, min_likes: int, max_likes: int) -> list[PostStats]:
    result = await session.execute(
        select(PostStats).where(
            PostStats.likes >= min_likes,
            PostStats.likes <= max_likes
        )
    )
    return result.scalars().all()

async def reset_post_stats(session: AsyncSession, post_id: int) -> bool:
    stats = await get_post_stats_by_post_id(session, post_id)
    if not stats:
        return False
    
    stats.views = 0
    stats.likes = 0
    stats.reposts = 0
    await session.commit()
    return True
