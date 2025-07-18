from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Post

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

async def update_post(session: AsyncSession, post_id: int, **kwargs) -> Post | None:
    post = await get_post_by_id(session, post_id)
    if not post:
        return None
    for key, value in kwargs.items():
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