from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import SocialAccount

async def create_social_account(session: AsyncSession, **kwargs) -> SocialAccount:
    account = SocialAccount(**kwargs)
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account

async def get_social_account_by_id(session: AsyncSession, account_id: int) -> SocialAccount | None:
    result = await session.execute(select(SocialAccount).where(SocialAccount.id == account_id))
    return result.scalar_one_or_none()

async def get_all_social_accounts(session: AsyncSession) -> list[SocialAccount]:
    result = await session.execute(select(SocialAccount))
    return result.scalars().all()

async def update_social_account(session: AsyncSession, account_id: int, **kwargs) -> SocialAccount | None:
    account = await get_social_account_by_id(session, account_id)
    if not account:
        return None
    for key, value in kwargs.items():
        setattr(account, key, value)
    await session.commit()
    await session.refresh(account)
    return account

async def delete_social_account(session: AsyncSession, account_id: int) -> bool:
    account = await get_social_account_by_id(session, account_id)
    if not account:
        return False
    await session.delete(account)
    await session.commit()
    return True 