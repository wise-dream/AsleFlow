from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Awaitable, Dict, Any
from redis.asyncio.client import Redis
import logging

logger = logging.getLogger(__name__)


class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis):
        super().__init__()
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Inject shared Redis client instance into handler context
        data["redis"] = self.redis
        logger.debug("Redis instance injected into handler context")
        return await handler(event, data)
