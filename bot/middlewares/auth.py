from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from typing import Callable, Awaitable, Dict, Any
from bot.models.models import User
from sqlalchemy.future import select

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        message: Message = data.get('event_message') or getattr(event, 'message', None)
        if message and message.text and message.text.startswith('/start'):
            return await handler(event, data)
        session = data.get('session')
        if not session or not message or not message.from_user:
            return await handler(event, data)
        user_id = message.from_user.id
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            # Можно отправить сообщение или просто игнорировать
            return  # Не авторизован — не обрабатываем
        data['user'] = user
        return await handler(event, data) 