from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import Payment

ALLOWED_FIELDS = {"amount", "status", "payment_date"}


async def create_payment(session: AsyncSession, **kwargs) -> Payment:
    payment = Payment(**kwargs)
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_id(session: AsyncSession, payment_id: int) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_all_payments(session: AsyncSession) -> list[Payment]:
    result = await session.execute(select(Payment))
    return result.scalars().all()


async def get_payments_by_user(session: AsyncSession, user_id: int) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.user_id == user_id))
    return result.scalars().all()


async def get_payments_by_status(session: AsyncSession, status: str) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.status == status))
    return result.scalars().all()


async def update_payment(session: AsyncSession, payment_id: int, **kwargs) -> Payment | None:
    payment = await get_payment_by_id(session, payment_id)
    if not payment:
        return None
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(payment, key, value)
    await session.commit()
    await session.refresh(payment)
    return payment


async def delete_payment(session: AsyncSession, payment_id: int) -> bool:
    payment = await get_payment_by_id(session, payment_id)
    if not payment:
        return False
    await session.delete(payment)
    await session.commit()
    return True
