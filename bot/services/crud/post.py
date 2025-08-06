from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Post

ALLOWED_FIELDS = {
    "topic", "content", "media_type", "media_url",
    "status", "scheduled_time", "moderated", "origin_topic",
    "social_account_id", "user_workflow_id"
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

async def publish_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post_by_id(session, post_id)
    if not post:
        return False
    from datetime import datetime, timezone
    post.status = 'published'
    post.published_time = datetime.now(timezone.utc)
    await session.commit()
    return True

async def get_posts_by_media_type(session: AsyncSession, media_type: str) -> list[Post]:
    result = await session.execute(select(Post).where(Post.media_type == media_type))
    return result.scalars().all()

async def get_posts_by_scheduled_time_range(session: AsyncSession, start_time, end_time) -> list[Post]:
    result = await session.execute(
        select(Post).where(
            Post.scheduled_time >= start_time,
            Post.scheduled_time <= end_time
        )
    )
    return result.scalars().all()

async def get_pending_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.status == 'pending'))
    return result.scalars().all()

async def get_scheduled_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.status == 'scheduled'))
    return result.scalars().all()

async def get_published_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.status == 'published'))
    return result.scalars().all()

async def get_failed_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.status == 'failed'))
    return result.scalars().all()

async def get_editable_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.is_editable == True))
    return result.scalars().all()

async def get_moderated_posts(session: AsyncSession) -> list[Post]:
    result = await session.execute(select(Post).where(Post.moderated == True))
    return result.scalars().all()

async def get_posts_by_topic(session: AsyncSession, topic: str) -> list[Post]:
    result = await session.execute(select(Post).where(Post.topic.contains(topic)))
    return result.scalars().all()
