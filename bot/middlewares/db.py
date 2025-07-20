from aiogram import BaseMiddleware
from db.connection import AsyncSessionLocal
from typing import Callable, Awaitable, Dict, Any
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

class DatabaseSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            try:
                data['session'] = session
                response = await handler(event, data)
                await session.commit()  # Явный коммит после успешного хендлера
                return response
            except Exception as e:
                await session.rollback()  # Откат при ошибке
                raise
