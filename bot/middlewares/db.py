from aiogram import BaseMiddleware
from db.connection import AsyncSessionLocal
from typing import Callable, Awaitable, Dict, Any
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

class DatabaseSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        async with AsyncSessionLocal() as session:
            data['session'] = session
            return await handler(event, data) 