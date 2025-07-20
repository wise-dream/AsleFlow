from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Post

ALLOWED_FIELDS = {
    "topic", "content", "media_type", "media_url",
    "status", "scheduled_time", "moderated", "origin_topic"
}


async def create_post(session: AsyncSession, **kwargs) -> Post:
    post = Post(**kwargs)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


async def get_post_by_id(session: AsyncSession, post_id: int) -> Post | None:
    result = await session.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


async def get_all_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post))
    return result.scalars().all()


async def get_posts_by_status(session: AsyncSession, status: str) -> list[Post]:
    result = await session.execute(select(Post).where(Post.status == status))
    return result.scalars().all()


async def get_posts_by_workflow(session: AsyncSession, workflow_id: int) -> list[Post]:
    result = await session.execute(select(Post).where(Post.user_workflow_id == workflow_id))
    return result.scalars().all()


async def update_post(session: AsyncSession, post_id: int, **kwargs) -> Post | None:
    post = await get_post_by_id(session, post_id)
    if not post:
        return None
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(post, key, value)
    await session.commit()
    await session.refresh(post)
    return post


async def delete_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post_by_id(session, post_id)
    if not post:
        return False
    await session.delete(post)
    await session.commit()
    return True


async def approve_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post_by_id(session, post_id)
    if not post:
        return False
    post.status = 'scheduled'
    post.moderated = True
    await session.commit()
    return True


async def reject_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post_by_id(session, post_id)
    if not post:
        return False
    post.status = 'failed'
    post.moderated = True
    await session.commit()
    return True
