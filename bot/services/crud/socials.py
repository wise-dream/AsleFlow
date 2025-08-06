from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import SocialAccount

ALLOWED_FIELDS = {
    "platform", "channel_name", "channel_id", "channel_type", 
    "access_token", "telegram_chat_id"
}

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

async def get_social_accounts_by_user_id(session: AsyncSession, user_id: int) -> list[SocialAccount]:
    result = await session.execute(select(SocialAccount).where(SocialAccount.user_id == user_id))
    return result.scalars().all()

async def update_social_account(session: AsyncSession, account_id: int, **kwargs) -> SocialAccount | None:
    account = await get_social_account_by_id(session, account_id)
    if not account:
        return None
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
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

async def get_social_account_by_platform_and_channel(
    session: AsyncSession, user_id: int, platform: str, channel_id: str
) -> SocialAccount | None:
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == platform,
            SocialAccount.channel_id == channel_id
        )
    )
    return result.scalar_one_or_none()

async def get_social_accounts_by_platform(session: AsyncSession, user_id: int, platform: str) -> list[SocialAccount]:
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == platform
        )
    )
    return result.scalars().all()

async def get_social_account_by_telegram_chat_id(session: AsyncSession, telegram_chat_id: str) -> SocialAccount | None:
    result = await session.execute(
        select(SocialAccount).where(SocialAccount.telegram_chat_id == telegram_chat_id)
    )
    return result.scalar_one_or_none()

async def get_social_accounts_by_channel_type(session: AsyncSession, user_id: int, channel_type: str) -> list[SocialAccount]:
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.channel_type == channel_type
        )
    )
    return result.scalars().all()
