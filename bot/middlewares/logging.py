import logging
import time
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from typing import Callable, Awaitable, Dict, Any

logger = logging.getLogger("bot")

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        try:
            user_id = None
            if hasattr(event, 'message') and isinstance(event.message, Message):
                user_id = event.message.from_user.id
                logger.info(f"[Message] from={user_id} text={event.message.text}")
            elif hasattr(event, 'callback_query') and isinstance(event.callback_query, CallbackQuery):
                user_id = event.callback_query.from_user.id
                logger.info(f"[CallbackQuery] from={user_id} data={event.callback_query.data}")
            else:
                logger.info(f"[Update] type={type(event).__name__}")

            start = time.monotonic()
            result = await handler(event, data)
            duration = time.monotonic() - start
            logger.info(f"Handled in {duration:.3f}s")
            return result

        except Exception as e:
            logger.exception(f"Exception while processing update: {e}")
            raise
