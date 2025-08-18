from aiogram import BaseMiddleware
from aiogram.types import Message, Update, CallbackQuery
from typing import Callable, Awaitable, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio.client import Redis
from bot.config import CACHE_TTL
from bot.models.models import User
import json

class AuthMiddleware(BaseMiddleware):
    def __init__(self, force_auth: bool = False):
        self.force_auth = force_auth  # Требовать ли авторизацию всегда

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = data.get("session")
        redis: Redis = data.get("redis")
        user_id: int | None = None

        # Получаем telegram_id из разных типов событий
        if message := data.get('event_message') or getattr(event, 'message', None):
            if message.text and message.text.startswith("/start"):
                return await handler(event, data)
            user_id = message.from_user.id if message.from_user else None
        elif callback := getattr(event, 'callback_query', None):
            user_id = callback.from_user.id
        elif inline := getattr(event, 'inline_query', None):
            user_id = inline.from_user.id

        # Если мы не можем получить telegram_id или нет сессии — пропускаем
        if not user_id or not session:
            return await handler(event, data)

        # Пытаемся достать пользователя из Redis
        user: User | None = None
        if redis:
            raw = await redis.get(f"user:{user_id}")
            if raw:
                try:
                    user_data = json.loads(raw)
                    user = User(**user_data)
                except Exception:
                    pass  # Кеш повреждён, идём в базу

        # Если не нашли — берём из базы и обновляем кеш
        if not user:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if user and redis:
                try:
                    # Простой сериализуемый словарь, без relationships
                    payload = {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "name": user.name,
                        "username": user.username,
                        "language": user.language,
                        "role": user.role,
                        # Храним только примитивы: используем referred_by_id вместо relationship
                        "referred_by_id": user.referred_by_id,
                        "referral_code": user.referral_code,
                        "cash": float(user.cash) if user.cash else 0.0,
                        "free_posts_used": user.free_posts_used,
                        "free_posts_limit": user.free_posts_limit,
                    }
                    await redis.set(f"user:{user_id}", json.dumps(payload), ex=CACHE_TTL)
                except Exception:
                    pass  # Redis временно недоступен — не страшно

        # Если не найден, но авторизация обязательна — игнорируем
        if not user and self.force_auth:
            return  # Можно отправить сообщение о неавторизованности

        # При наличии пользователя — кладём его в data
        if user:
            data["user"] = user

        return await handler(event, data)
