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

async def get_payments_by_subscription_id(session: AsyncSession, subscription_id: int) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.subscription_id == subscription_id))
    return result.scalars().all()

async def get_payments_by_date_range(session: AsyncSession, start_date, end_date) -> list[Payment]:
    result = await session.execute(
        select(Payment).where(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
    )
    return result.scalars().all()

async def get_payments_by_amount_range(session: AsyncSession, min_amount, max_amount) -> list[Payment]:
    result = await session.execute(
        select(Payment).where(
            Payment.amount >= min_amount,
            Payment.amount <= max_amount
        )
    )
    return result.scalars().all()

async def get_completed_payments(session: AsyncSession) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.status == 'completed'))
    return result.scalars().all()

async def get_pending_payments(session: AsyncSession) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.status == 'pending'))
    return result.scalars().all()

async def get_failed_payments(session: AsyncSession) -> list[Payment]:
    result = await session.execute(select(Payment).where(Payment.status == 'failed'))
    return result.scalars().all()

async def complete_payment(session: AsyncSession, payment_id: int) -> bool:
    payment = await get_payment_by_id(session, payment_id)
    if not payment:
        return False
    payment.status = 'completed'
    await session.commit()
    return True

async def fail_payment(session: AsyncSession, payment_id: int) -> bool:
    payment = await get_payment_by_id(session, payment_id)
    if not payment:
        return False
    payment.status = 'failed'
    await session.commit()
    return True
