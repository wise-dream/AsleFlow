# middlewares/redis.py
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)

class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis):
        self.redis = redis
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["redis"] = self.redis
        logger.debug("Redis instance injected into handler context")
        return await handler(event, data)
