from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Awaitable, Dict, Any
import logging

logger = logging.getLogger('bot')

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        logger.info(f"Update: {event}")
        try:
            result = await handler(event, data)
            logger.info(f"Handler result: {result}")
            return result
        except Exception as e:
            logger.exception(f"Exception in handler: {e}")
            raise 